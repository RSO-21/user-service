from fastapi import FastAPI, Depends, HTTPException, Header, Query, status, APIRouter
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List, Optional
from datetime import timezone

from app.grpc.orders_client import get_orders_by_user
from app.database import get_db_session, engine
from app.models import Base, User
from app.schemas import (
    UserUpdate,
    UserOut,
    UserOrderHistory,
    OrderSummaryOut
)
from fastapi.middleware.cors import CORSMiddleware

from prometheus_fastapi_instrumentator import Instrumentator
from app.config import settings


app = FastAPI(title="User Microservice")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4200",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)

def get_tenant_id(x_tenant_id: Optional[str] = Header(None)) -> str:
    """Extract tenant ID from header, default to public"""
    return x_tenant_id or "public"

def get_db_with_schema(tenant_id: str = Depends(get_tenant_id)):
    with get_db_session(schema=tenant_id) as db:
        yield db

# --------------------
# Startup
# --------------------
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# --------------------
# Health
# --------------------
@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db_with_schema)):
    try:
        db.execute(select(1))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {e}",
        )
    return {"status": "ok", "db": "ok"}

@app.get("/")
def root():
    return {"message": "User Service is running"}

router = APIRouter()

# --------------------
# List users
# --------------------
@router.get("/list_users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db_with_schema)):
    users = db.execute(select(User)).scalars().all()
    return users

# --------------------
# Get user by id
# --------------------
@router.get("/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db_with_schema)):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# --------------------
# Update user
# --------------------
@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db_with_schema),
):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    update_data = payload.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)

    return user


# --------------------
# Get user order history
# --------------------
@router.get("/{user_id}/orders", response_model=UserOrderHistory)
def get_user_orders(user_id: str, db: Session = Depends(get_db_with_schema)):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        resp = get_orders_by_user(user_id=user_id, timeout_s=2.0)
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Order service unavailable: {e}",
        )

    orders_out = []
    for o in resp.orders:
        dt = o.created_at.ToDatetime().replace(tzinfo=timezone.utc)

        orders_out.append(
            OrderSummaryOut(
                external_id=o.external_id,
                order_id=o.order_id,
                user_id=o.user_id,
                order_status=o.order_status,
                total_amount=o.total_amount,
                created_at=dt,
                tenant_id=o.tenant_id,
                partner_id=o.partner_id
            )
        )

    return UserOrderHistory(user_id=user_id, orders=orders_out)


# --------------------
# Add order to cart (duplicates allowed)
# --------------------
@router.post("/{user_id}/cart/{order_id}", response_model=UserOut)
def add_to_cart(
    user_id: str,
    order_id: int,
    db: Session = Depends(get_db_with_schema),
):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.cart is None:
        user.cart = []

    user.cart.append(order_id)

    db.commit()
    db.refresh(user)

    return user


# --------------------
# Remove ONE order occurrence from cart
# --------------------
@router.delete("/{user_id}/cart/{order_id}", response_model=UserOut)
def remove_from_cart(
    user_id: str,
    order_id: int,
    db: Session = Depends(get_db_with_schema),
):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.cart and order_id in user.cart:
        user.cart.remove(order_id)

    db.commit()
    db.refresh(user)

    return user

# --------------------
# Empty cart
# --------------------
@app.delete("/users/{user_id}/cart", response_model=UserOut)
def clear_cart(
    user_id: str,
    db: Session = Depends(get_db_with_schema),
):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.cart = []

    db.commit()
    db.refresh(user)

    return user


GOOGLE_PLACE_DETAILS = "https://maps.googleapis.com/maps/api/place/details/json"

@app.get("/location/place")
async def resolve_place(
    place_id: str = Query(...),
):
    params = {
        "place_id": place_id,
        "key": settings.google_api_key,
        "fields": "geometry,formatted_address",
    }

    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(GOOGLE_PLACE_DETAILS, params=params)
        resp.raise_for_status()

    data = resp.json()

    result = data.get("result")
    if not result:
        raise HTTPException(status_code=404, detail="Place not found")

    loc = result["geometry"]["location"]

    return {
        "formatted_address": result["formatted_address"],
        "latitude": loc["lat"],
        "longitude": loc["lng"],
    }


GOOGLE_PLACES_AUTOCOMPLETE = "https://maps.googleapis.com/maps/api/place/autocomplete/json"

@app.get("/location/autocomplete")
async def autocomplete_address(
    input: str = Query(..., min_length=2),
):
    params = {
        "input": input,
        "key": settings.google_api_key,
        "components": "country:si",
        "types": "geocode",
    }

    async with httpx.AsyncClient(timeout=5) as client:
        resp = await client.get(GOOGLE_PLACES_AUTOCOMPLETE, params=params)
        resp.raise_for_status()

    data = resp.json()

    return [
        {
            "description": p["description"],
            "place_id": p["place_id"],
        }
        for p in data.get("predictions", [])
    ]


app.include_router(router)