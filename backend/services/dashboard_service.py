from sqlalchemy.orm import Session
from backend.models.order import Order


def get_dashboard_stats(db: Session):

    total = db.query(Order).count()

    pending = db.query(Order).filter(
        Order.status == "Pending"
    ).count()

    confirmed = db.query(Order).filter(
        Order.status == "Confirmed"
    ).count()

    cancelled = db.query(Order).filter(
        Order.status == "Cancelled"
    ).count()

    return {
        "total_orders": total,
        "pending_orders": pending,
        "confirmed_orders": confirmed,
        "cancelled_orders": cancelled,
    }