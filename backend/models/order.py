from sqlalchemy import Column, Integer, String, Float

from backend.database.database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)

    customer_name = Column(String)

    phone = Column(String)

    product = Column(String)

    price = Column(Float)

    city = Column(String)

    address = Column(String)

    status = Column(String, default="Pending")