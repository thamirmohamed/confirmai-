from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from backend.database.database import SessionLocal
from backend.models.user import User
from backend.utils.security import hash_password, verify_password
from backend.utils.jwt import SECRET_KEY, ALGORITHM, create_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

security = HTTPBearer()


class AuthRequest(BaseModel):
    email: EmailStr
    password: str


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    return user


@router.post("/register")
def register(
    data: AuthRequest,
    db: Session = Depends(get_db)
):
    existing_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    user = User(
        email=data.email,
        password_hash=hash_password(data.password)
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "REGISTER OK",
        "user_id": str(user.id)
    }


@router.post("/login")
def login(
    data: AuthRequest,
    db: Session = Depends(get_db)
):
    user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    access_token = create_access_token({
        "sub": str(user.id)
    })

    return {
        "message": "LOGIN OK",
        "user_id": str(user.id),
        "access_token": access_token,
        "token_type": "bearer"
    }