from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "CHANGE_THIS_SECRET_KEY_BEFORE_PRODUCTION"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


def create_access_token(data: dict):
    payload = data.copy()

    payload["exp"] = (
        datetime.utcnow()
        + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )