from sqlalchemy.orm import Session

from backend.models.order import Order


def create_order(db: Session, data):
    order = Order(
        customer_name=data.customer_name,
        phone=data.phone,
        product=data.product,
        price=data.price,
        city=data.city,
        address=data.address,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    return order


def get_orders(db: Session):




    return db.query(Order).all()
def update_order_status(db: Session, order_id: int, status: str):
    order = db.query(Order).filter(Order.id == order_id).first()

    if not order:
        return None

    order.status = status
    db.commit()
    db.refresh(order)

    return order