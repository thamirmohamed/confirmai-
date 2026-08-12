from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database.database import Base, engine

# Import des modèles
from backend.models.user import User
from backend.models.store import Store
from backend.models.order import Order

# Import des routes
from backend.api.auth import router as auth_router
from backend.api.orders import router as orders_router
from backend.api.shopify import router as shopify_router
from backend.api.dashboard import router as dashboard_router


app = FastAPI(
    title="ConfirmAI API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Création des tables
Base.metadata.create_all(bind=engine)

# Routes
app.include_router(auth_router)
app.include_router(orders_router)
app.include_router(shopify_router)
app.include_router(dashboard_router)


@app.get("/")
def home():
    return {
        "project": "ConfirmAI",
        "status": "Running",
    }