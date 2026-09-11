from pydantic import BaseModel
from typing import Optional, Dict, Any


class CustomerCreate(BaseModel):
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None


class CustomerUpdate(BaseModel):
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None


class CustomerResponse(BaseModel):
    id: int
    user_id: int
    phone: Optional[str] = None
    address: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True