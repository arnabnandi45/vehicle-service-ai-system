from pydantic import BaseModel
from typing import Optional


class VehicleCreate(BaseModel):
    brand: str
    model: str
    year: int


class VehicleUpdate(BaseModel):
    brand: Optional[str] = None
    model: Optional[str] = None
    year: Optional[int] = None


class VehicleResponse(BaseModel):
    id: int
    customer_id: Optional[int] = None
    brand: str
    model: str
    year: Optional[int] = None

    class Config:
        from_attributes = True