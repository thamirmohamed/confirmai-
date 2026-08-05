from pydantic import BaseModel


class OrderCreate(BaseModel):
    customer_name: str
    phone: str
    product: str
    price: float
    city: str
    address: str


class OrderResponse(OrderCreate):
    id: int
    status: str

    class Config:
        from_attributes = True