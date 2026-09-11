from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.db.database import Base


class ServiceBooking(Base):
    __tablename__ = "service_bookings"

    id = Column(Integer, primary_key=True, index=True)

    vehicle_id = Column(
        Integer,
        ForeignKey("vehicles.id"),
        nullable=False
    )

    service_type_id = Column(
        Integer,
        ForeignKey("service_types.id"),
        nullable=False
    )

    technician_id = Column(
        Integer,
        ForeignKey("technicians.id"),
        nullable=True
    )

    scheduled_at = Column(DateTime, nullable=False)

    status = Column(
        String,
        default="pending",
        nullable=False
    )