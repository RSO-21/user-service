from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import List, Optional


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    surname: Optional[str] = None
    address: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None
    partner_id: Optional[str] = None

class UserOut(BaseModel):
    id: str
    username: str
    email: EmailStr

    name: Optional[str] = None
    surname: Optional[str] = None
    address: Optional[str] = None

    longitude: Optional[float] = None
    latitude: Optional[float] = None

    partner_id: Optional[str] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class OrderItemOut(BaseModel):
    id: int               
    order_id: int         
    offer_id: int          
    quantity: int

class OrderOut(BaseModel):
    id: int
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
