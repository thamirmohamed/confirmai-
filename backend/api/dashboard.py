from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import SessionLocal
from backend.models.dashboard import DashboardResponse
from backend.services.dashboard_service import get_dashboard_stats
from backend.utils.dependencies import get_current_user
from backend.models.user import User

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=DashboardResponse)
def dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_dashboard_stats(db)