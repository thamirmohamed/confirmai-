from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.models.schemas import OrderCreate, OrderResponse
from backend.models.user import User
from backend.utils.dependencies import get_current_user

from backend.services.order_service import (
    create_order,
    get_orders,
    update_order_status,
)

router = APIRouter(tags=["Orders"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/orders", response_model=list[OrderResponse])
def read_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_orders(db)


@router.put("/orders/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    status: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = update_order_status(db, order_id, status)

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


@router.post("/shopify/webhook")
async def shopify_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    data = await request.json()

    order = OrderCreate(
        customer_name=data.get("customer", {}).get("first_name", "Client"),
        phone=data.get("shipping_address", {}).get("phone", ""),
        product=data.get("line_items", [{}])[0].get("title", ""),
        price=float(data.get("total_price", 0)),
        city=data.get("shipping_address", {}).get("city", ""),
        address=data.get("shipping_address", {}).get("address1", ""),
    )

    create_order(db, order)

    return {"success": True}