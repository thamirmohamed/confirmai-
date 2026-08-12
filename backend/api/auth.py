from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from backend.database.database import SessionLocal
from backend.models.user import User
from backend.utils.security import hash_password, verify_password
from backend.utils.jwt import create_access_token

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


class RegisterRequest(BaseModel):
    full_name: str
    company_name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/register")
def register(data: RegisterRequest):

    db: Session = SessionLocal()

    try:
        existing = db.query(User).filter(User.email == data.email).first()

        if existing:
            raise HTTPException(status_code=400, detail="Email already exists")

        user = User(
            full_name=data.full_name,
            company_name=data.company_name,
            email=data.email,
            password_hash=hash_password(data.password),
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        return {
            "message": "Account created successfully"
        }

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        db.close()


@router.post("/login")
def login(data: LoginRequest):
    return {
        "message": "LOGIN OK"
    }

    