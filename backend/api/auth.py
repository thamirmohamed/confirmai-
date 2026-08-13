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
            raise HTTPException(
                status_code=400,
                detail="Email already exists"
            )

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
            "message": "Account created successfully",
            "user_id": str(user.id),
            "email": user.email
        }

    except HTTPException:
        raise

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:
        db.close()


@router.post("/login")
def login(data: LoginRequest):

    db: Session = SessionLocal()

    try:
        user = db.query(User).filter(
            User.email == data.email
        ).first()

        if not user:
            raise HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect"
            )

        if not verify_password(
            data.password,
            user.password_hash
        ):
            raise HTTPException(
                status_code=401,
                detail="Email ou mot de passe incorrect"
            )

        access_token = create_access_token(
            data={"sub": str(user.id)}
        )

        return {
            "message": "LOGIN OK",
            "user_id": str(user.id),
            "access_token": access_token,
            "token_type": "bearer"
        }

    finally:
        db.close()