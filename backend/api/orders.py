from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.services.order_service import create_order, get_orders, update_order_status
from backend.database.database import SessionLocal
from backend.models.schemas import OrderCreate, OrderResponse



router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/orders", response_model=list[OrderResponse])
def read_orders(db: Session = Depends(get_db)):
    return get_orders(db)


@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    status: str,
    db: Session = Depends(get_db)
):
    order = update_order_status(db, order_id, status)

    if not order:
        return {"error": "Order not found"}

    return order