import uuid

from sqlalchemy import (
    Column,
    String,
    DateTime,
    Boolean,
    ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from backend.database.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = Column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )

    shop_name = Column(
        String,
        nullable=False
    )

    shopify_domain = Column(
        String,
        unique=True,
        nullable=False
    )

    access_token = Column(
        String,
        nullable=True
    )

    is_active = Column(
        Boolean,
        default=True
    )

    connected_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

    user = relationship(
        "User",
        back_populates="stores"
    )

    orders = relationship(
        "Order",
        back_populates="store",
        cascade="all, delete"
    )