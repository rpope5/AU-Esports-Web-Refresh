import os
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

from app.core.config import get_settings

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME")
JWT_ALG = os.getenv("JWT_ALG", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "120"))
settings = get_settings()

if settings.is_production and JWT_SECRET == "CHANGE_ME":
    raise RuntimeError("JWT_SECRET must be set in production")

def create_access_token(payload: dict) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=JWT_EXPIRE_MINUTES)
    to_encode = {**payload, "iat": int(now.timestamp()), "exp": exp}
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALG)

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])
    except JWTError:
        return None
