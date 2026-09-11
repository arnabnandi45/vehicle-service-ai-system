from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from app.db.database import Base


class JobCard(Base):
    __tablename__ = "job_cards"

    id = Column(Integer, primary_key=True, index=True)

    booking_id = Column(
        Integer,
        ForeignKey("service_bookings.id"),
        nullable=False
    )

    technician_id = Column(
        Integer,
        ForeignKey("technicians.id"),
        nullable=True
    )

    inspection_notes = Column(Text, nullable=True)

    estimate = Column(JSON, nullable=True)

    status = Column(
        String,
        default="open",
        nullable=False
    )