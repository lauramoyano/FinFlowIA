from datetime import UTC, datetime, timedelta
from typing import Any

import structlog
from jose import JWTError, jwt

from src.config.settings import settings

logger = structlog.get_logger(__name__)

ALGORITHM = "HS256"


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: Usually the user ID (stored as 'sub' claim).
        expires_delta: Optional custom expiry. Defaults to settings.jwt_expire_minutes.
        extra_claims: Optional additional claims to include in the payload.
    """
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.jwt_expire_minutes)
    )

    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": datetime.now(UTC),
        "type": "access",
    }

    if extra_claims:
        payload.update(extra_claims)

    token = jwt.encode(payload, settings.jwt_secret, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode a JWT token.

    Returns:
        The decoded payload dict if valid, or None if invalid/expired.
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning("jwt_verification_failed", error=str(e))
        return None
