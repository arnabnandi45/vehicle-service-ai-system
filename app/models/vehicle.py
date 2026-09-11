from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func

from app.db.database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)

    customer_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    brand = Column(String(100), nullable=False)
    model = Column(String(100), nullable=False)
    year = Column(Integer)

    created_at = Column(
        DateTime,
        server_default=func.now()
    )