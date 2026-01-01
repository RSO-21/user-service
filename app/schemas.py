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
    id: str
    email: EmailStr
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # for SQLAlchemy integration

class OrderItemOut(BaseModel):
    id: str               
    order_id: str         
    offer_id: str          
    quantity: int

class OrderOut(BaseModel):
    id: str
    user_id: str
    partner_id: Optional[int] = None
    order_status: str
    payment_status: str
    payment_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemOut]

class UserOrderHistory(BaseModel):
    user_id: str
    orders: List[OrderOut]
