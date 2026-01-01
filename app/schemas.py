from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional
from uuid import UUID

class UserCreate(BaseModel):
    email: EmailStr
    name: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    name: str | None = None

class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # for SQLAlchemy integration

class OrderItemOut(BaseModel):
    id: UUID               
    order_id: UUID         
    offer_id: UUID          
    quantity: int

class OrderOut(BaseModel):
    id: UUID
    user_id: UUID
    partner_id: Optional[int] = None
    order_status: str
    payment_status: str
    payment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut]

class UserOrderHistory(BaseModel):
    user_id: UUID
    orders: List[OrderOut]
