import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.infrastructure.security.jwt import verify_token
from src.modules.auth.models import User
from src.modules.auth.repository import UserRepository
from src.shared.exceptions.unauthorized import UnauthorizedException

bearer_scheme = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency that validates the JWT token and returns the authenticated User.
    Raises UnauthorizedException if token is invalid or user not found.
    """
    token = credentials.credentials
    payload = verify_token(token)

    if not payload:
        raise UnauthorizedException("Invalid or expired token")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Token missing subject claim")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError as e:
        raise UnauthorizedException("Invalid user ID in token") from e

    repo = UserRepository(session)
    user = await repo.get_by_id(user_id)

    if not user:
        raise UnauthorizedException("User not found")

    if not user.is_active:
        raise UnauthorizedException("Account is deactivated")

    return user
