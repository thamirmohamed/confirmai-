from pydantic import BaseModel

class DashboardResponse(BaseModel):
    total_orders: int
    pending_orders: int
    confirmed_orders: int
    cancelled_orders: int
    