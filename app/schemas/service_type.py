from pydantic import BaseModel
from typing import Optional


class ServiceTypeCreate(BaseModel):
    name: str
    description: Optional[str] = None
    base_price: float
    duration_minutes: int


class ServiceTypeUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    duration_minutes: Optional[int] = None


class ServiceTypeResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    base_price: float
    duration_minutes: int

    class Config:
        from_attributes = True