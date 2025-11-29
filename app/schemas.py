from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None

class UserOut(BaseModel):
    id: int
    email: EmailStr
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # for SQLAlchemy integration

# Models for order history (when Order service is made):
class OrderItem(BaseModel):
    order_id: int
    created_at: datetime
    total_price: float
    status: str

class UserOrderHistory(BaseModel):
    user_id: int
    orders: List[OrderItem]
