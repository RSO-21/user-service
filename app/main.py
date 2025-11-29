from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import httpx
from datetime import datetime

from database import get_db, engine
from models import Base, User
from schemas import UserCreate, UserUpdate, UserOut, UserOrderHistory, OrderItem

app = FastAPI(title="User Microservice")


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


# 4) List users (optional)
@app.get("/users", response_model=List[UserOut])
async def list_users(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    users = result.scalars().all()
    return users


# 5) Get user order history (FAKE for now)
@app.get("/users/{user_id}/orders", response_model=UserOrderHistory)
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_db)):
    # ensure user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # TODO: call Orders microservice via HTTP
    # For now we return mock data:
    fake_orders = [
        OrderItem(
            order_id=1,
            created_at=datetime(2025, 1, 10, 12, 0),
            total_price=49.99,
            status="delivered",
        ),
        OrderItem(
            order_id=2,
            created_at=datetime(2025, 2, 5, 15, 30),
            total_price=19.99,
            status="shipped",
        ),
    ]

    return UserOrderHistory(user_id=user_id, orders=fake_orders)

"""
ORDER_SERVICE_URL = "http://order-service:8001"  # e.g. Docker compose service name

@app.get("/users/{user_id}/orders", response_model=UserOrderHistory)
async def get_user_orders(user_id: int, db: AsyncSession = Depends(get_db)):
    # check user exists
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{ORDER_SERVICE_URL}/orders", params={"user_id": user_id})

    if resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Order service unavailable")

    data = resp.json()
    # adapt JSON to UserOrderHistory if needed
    return UserOrderHistory(user_id=user_id, orders=data["orders"])
"""
