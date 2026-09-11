from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ServiceBookingCreate(BaseModel):
    vehicle_id: int
    service_type_id: int
    technician_id: Optional[int] = None
    scheduled_at: datetime


class ServiceBookingUpdate(BaseModel):
    scheduled_at: Optional[datetime] = None
    technician_id: Optional[int] = None
    status: Optional[str] = None


class ServiceBookingResponse(BaseModel):
    id: int
    vehicle_id: int
    service_type_id: int
    technician_id: Optional[int] = None
    scheduled_at: datetime
    status: str

    class Config:
        from_attributes = True