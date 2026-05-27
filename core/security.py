import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError
import bcrypt
from core.config import settings


def hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_byte = plain_password.encode('utf-8')
    hashed_byte = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_byte, hashed_byte)


def create_access_token(user_id: uuid.UUID, expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    ttl_minutes = expires_minutes or settings.ACCESS_TOKEN_EXPIRE_MINUTES
    expire = now + timedelta(minutes=ttl_minutes)
    payload = {
        "sub": str(user_id),
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
        "jti": str(uuid.uuid4()),
    }
    secret = settings.SECRET_KEY
    algorithm = settings.ALGORITHM
    return jwt.encode(payload, secret, algorithm=algorithm)


def decode_access_token(token: str) -> uuid.UUID:
    secret = settings.SECRET_KEY
    algorithm = settings.ALGORITHM
    payload = jwt.decode(token, secret, algorithms=[algorithm])

    user_id: str | None = payload.get("sub")
    if user_id is None:
        raise JWTError("Missing subject")

    return uuid.UUID(user_id)


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_refresh_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
