import uuid

from sqlalchemy import Column, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    store_id = Column(
        UUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False
    )

    customer_name = Column(String, nullable=False)

    phone = Column(String, nullable=False)

    product = Column(String, nullable=False)

    price = Column(Float, nullable=False)

    city = Column(String)

    address = Column(String)

    status = Column(String, default="Pending")

    shopify_order_id = Column(String, unique=True, nullable=True)

    currency = Column(String, default="MAD")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    store = relationship("Store", back_populates="orders")