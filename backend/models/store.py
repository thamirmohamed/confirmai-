import uuid
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    shop_name = Column(String, nullable=False)

    shopify_domain = Column(String, unique=True, nullable=False)

    access_token = Column(String, nullable=True)

    is_active = Column(Boolean, default=True)

    connected_at = Column(DateTime(timezone=True), server_default=func.now())

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship("User", back_populates="stores")

    orders = relationship(
        "Order",
        back_populates="store",
        cascade="all, delete"
    )