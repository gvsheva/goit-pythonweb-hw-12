"""Authentication utilities and dependencies for JWT-based auth."""
from datetime import datetime, timedelta, timezone
from typing import Any
import hashlib
from fastapi_cache.decorator import cache

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.db import get_session
from app.repositories.users import get_user_by_id

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def _user_cache_key_builder(func, namespace, request, response, args, kwargs) -> str:
    token = kwargs.get("token") or (args[0] if args else "")
    try:
        key = hashlib.sha256(str(token).encode("utf-8")).hexdigest()
    except Exception:
        key = "invalid"
    return f"{namespace}:user:{key}"


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password: Plain-text password.

    Returns:
        Hashed password string suitable for storage.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a bcrypt hash.

    Args:
        plain_password: Password provided by the user.
        hashed_password: Stored bcrypt hash.

    Returns:
        True if the password matches the hash, otherwise False.
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    data: dict[str, Any], expires_minutes: int | None = None
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Payload claims to encode into the token (e.g., sub, email, scope).
        expires_minutes: Optional expiration time override in minutes.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=expires_minutes or settings.access_token_expire_minutes
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(data: dict[str, Any], expires_days: int | None = None) -> str:
    """Create a signed JWT refresh token.

    Args:
        data: Payload claims to encode into the token (e.g., sub, email, scope).
        expires_days: Optional expiration time override in days.

    Returns:
        Encoded JWT string.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(
        days=expires_days or settings.refresh_token_expire_days
    )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT, returning its payload.

    Args:
        token: Encoded JWT.

    Returns:
        Decoded payload as a dictionary.

    Raises:
        HTTPException: If the token is invalid or cannot be decoded.
    """
    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from e


@cache(
    expire=settings.access_token_expire_minutes * 60,
    key_builder=_user_cache_key_builder,
    namespace="auth",
)
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_session),
):
    """FastAPI dependency that returns the current authenticated user.

    Uses Redis to cache user info per access token when REDIS_URL is configured.
    Cache TTL is aligned to the JWT access token expiry.
    """
    # cache handled by fastapi-cache2 via decorator

    # Decode token (still required to validate and to compute TTL)
    payload = decode_token(token)
    sub = payload.get("sub")
    if sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload"
        )
    try:
        user_id = int(sub)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject"
        )

    user = await get_user_by_id(session, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
        )

    snapshot = {
        "id": user.id,
        "email": user.email,
        "is_verified": bool(user.is_verified),
        "avatar_url": user.avatar_url,
        "created_at": user.created_at.isoformat()
        if getattr(user, "created_at", None)
        else None,
        "updated_at": user.updated_at.isoformat()
        if getattr(user, "updated_at", None)
        else None,
    }
    return snapshot
