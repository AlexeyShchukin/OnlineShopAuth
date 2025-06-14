from datetime import datetime, timezone, timedelta

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, ExpiredSignatureError, JWTError

from src.core.config import settings
from src.loggers.loggers import logger

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login/")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=10)


def hash_password(password: str) -> str:
    """Generates a hashed version of the provided password."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_token(data: dict, key: str, algorithm: str, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, key=key, algorithm=algorithm)


def create_access_token(data: dict) -> str:
    return create_token(
        data,
        key=settings.private_key,
        algorithm=settings.ACCESS_TOKEN_ALGORITHM,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )


def create_refresh_token(data: dict) -> str:
    return create_token(
        data,
        algorithm=settings.REFRESH_TOKEN_ALGORITHM,
        key=settings.REFRESH_TOKEN_SECRET_KEY,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    )


def decode_token(token: str, key: str, algorithm: str) -> dict:
    try:
        return jwt.decode(token, key, algorithms=[algorithm])
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError:
        logger.warning("Invalid token", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


def decode_access_token(token: str) -> dict:
    return decode_token(
        token=token,
        key=settings.public_key,
        algorithm=settings.ACCESS_TOKEN_ALGORITHM
    )


def decode_refresh_token(token: str) -> dict:
    return decode_token(
        token=token,
        key=settings.REFRESH_TOKEN_SECRET_KEY,
        algorithm=settings.REFRESH_TOKEN_ALGORITHM
    )
