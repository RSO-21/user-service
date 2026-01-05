from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import List
from datetime import timezone

from app.grpc.orders_client import get_orders_by_user
from app.database import get_db_session as get_db, engine
from app.models import Base, User
from app.schemas import (
    OrderItemOut,
    OrderOut,
    UserUpdate,
    UserOut,
    UserOrderHistory,
)

from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="User Microservice")

instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)


# --------------------
# Startup
# --------------------
@app.on_event("startup")
def on_startup():
    # Dev only (in production use Alembic)
    Base.metadata.create_all(bind=engine)


# --------------------
# Get user by id
# --------------------
@app.get("/users/{user_id}", response_model=UserOut)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


# --------------------
# Update user
# --------------------
@app.patch("/users/{user_id}", response_model=UserOut)
def update_user(
    user_id: str,
    payload: UserUpdate,
    db: Session = Depends(get_db),
):
    user = db.execute(
        select(User).where(User.id == user_id)
    ).scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None:
        user.email = payload.email
    if payload.name is not None:
        user.name = payload.name

    db.commit()
    db.refresh(user)

    return user


# --------------------
# List users
# --------------------
@app.get("/users", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db)):
    users = db.execute(select(User)).scalars().all()
    return users


# --------------------
# Get user order history
# --------------------
@app.get("/users/{user_id}/orders", response_model=UserOrderHistory)
def get_user_orders(user_id: str, db: Session = Depends(get_db)):
    # ensure user exists
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
        created_at = o.created_at.ToDatetime().replace(tzinfo=timezone.utc)
        updated_at = o.updated_at.ToDatetime().replace(tzinfo=timezone.utc)

        partner_id = o.partner_id if o.HasField("partner_id") else None
        payment_id = o.payment_id if o.HasField("payment_id") else None

        items_out = [
            OrderItemOut(
                id=it.id,
                order_id=it.order_id,
                offer_id=it.offer_id,
                quantity=it.quantity,
            )
            for it in o.items
        ]

        orders_out.append(
            OrderOut(
                id=o.id,
                user_id=o.user_id,
                partner_id=partner_id,
                order_status=o.order_status,
                payment_status=o.payment_status,
                payment_id=payment_id,
                created_at=created_at,
                updated_at=updated_at,
                items=items_out,
            )
        )

    return UserOrderHistory(user_id=user_id, orders=orders_out)


# --------------------
# Health
# --------------------
@app.get("/health", tags=["health"])
def health(db: Session = Depends(get_db)):
    try:
        db.execute(select(1))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database unavailable: {e}",
        )
    return {"status": "ok", "db": "ok"}
