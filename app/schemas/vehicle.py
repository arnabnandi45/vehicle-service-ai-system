from pydantic import BaseModel


class VehicleCreate(BaseModel):
    brand: str
    model: str
    year: int

class VehicleUpdate(BaseModel):
    brand: str
    model: str
    year: int