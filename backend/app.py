
from fastapi import FastAPI
from backend.api.orders import router as orders_router
from backend.database.database import Base, engine
from backend.models.order import Order
app = FastAPI(
    title="ConfirmAI API",
    version="1.0.0"
)
Base.metadata.create_all(bind=engine)

app.include_router(orders_router)

@app.get("/")
def home():
    return {
        "project": "ConfirmAI",
        "status": "Running"
    }