from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import timezone
from app.grpc.orders_client import get_orders_by_user

from app.database import get_db, engine
from app.models import Base, User
from app.schemas import OrderItemOut, OrderOut, UserCreate, UserUpdate, UserOut, UserOrderHistory
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(title="User Microservice")
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)


@app.on_event("startup")
async def on_startup():
    # Dev only (in production use Alembic)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# 1) Create new user
@app.post("/users", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(payload: UserCreate, db: AsyncSession = Depends(get_db)):
    # check if email already exists
    result = await db.execute(select(User).where(User.email == payload.email))
    existing = result.scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = User(email=payload.email, name=payload.name)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# 2) Get user by id
@app.get("/users/{user_id}", response_model=UserOut)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# 3) Update user
@app.patch("/users/{user_id}", response_model=UserOut)
async def update_user(user_id: int, payload: UserUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if payload.email is not None:
        user.email = payload.email
    if payload.name is not None:
        user.name = payload.name

    await db.commit()
    await db.refresh(user)
    return user


# 4) List users
@app.get("/users", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


# 5) Get user order history
@app.get("/users/{user_id}/orders", response_model=UserOrderHistory)
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_db)):
    # ensure user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    try:
        resp = get_orders_by_user(user_id=user_id, timeout_s=2.0)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Order service unavailable: {e}")

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