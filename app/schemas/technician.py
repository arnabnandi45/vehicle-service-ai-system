from pydantic import BaseModel
from typing import Optional


class TechnicianCreate(BaseModel):
    name: str
    specialization: Optional[str] = None
    is_available: bool = True


class TechnicianUpdate(BaseModel):
    name: Optional[str] = None
    specialization: Optional[str] = None
    is_available: Optional[bool] = None


class TechnicianResponse(BaseModel):
    id: int
    name: str
    specialization: Optional[str] = None
    is_available: bool

    class Config:
        from_attributes = True