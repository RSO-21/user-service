from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional

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

class OrderItemOut(BaseModel):
    id: int
    order_id: int
    offer_id: int
    quantity: int

class OrderOut(BaseModel):
    id: int
    user_id: int
    partner_id: Optional[int] = None
    order_status: str
    payment_status: str
    payment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut]

class UserOrderHistory(BaseModel):
    user_id: int
    orders: List[OrderOut]
