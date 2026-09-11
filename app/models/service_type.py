from sqlalchemy import Column, Integer, String, Float
from app.db.database import Base


class ServiceType(Base):
    __tablename__ = "service_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    base_price = Column(Float, nullable=False)
    duration_minutes = Column(Integer, nullable=False)