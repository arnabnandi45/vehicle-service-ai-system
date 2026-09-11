from pydantic import BaseModel
from typing import Optional, Dict, Any


class JobCardCreate(BaseModel):
    booking_id: int
    technician_id: Optional[int] = None
    inspection_notes: Optional[str] = None
    estimate: Optional[Dict[str, Any]] = None


class JobCardUpdate(BaseModel):
    technician_id: Optional[int] = None
    inspection_notes: Optional[str] = None
    estimate: Optional[Dict[str, Any]] = None
    status: Optional[str] = None


class JobCardResponse(BaseModel):
    id: int
    booking_id: int
    technician_id: Optional[int] = None
    inspection_notes: Optional[str] = None
    estimate: Optional[Dict[str, Any]] = None
    status: str

    class Config:
        from_attributes = True