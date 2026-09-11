from sqlalchemy import Column, Integer, String, ForeignKey, JSON

from app.db.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )

    phone = Column(
        String,
        nullable=True
    )

    address = Column(
        JSON,
        nullable=True
    )