from sqlalchemy import Column, Integer, String, Boolean
from app.db.database import Base


class Technician(Base):
    __tablename__ = "technicians"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    specialization = Column(String, nullable=True)
    is_available = Column(Boolean, default=True)