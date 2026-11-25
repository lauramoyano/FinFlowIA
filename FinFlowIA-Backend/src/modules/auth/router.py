from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.auth.repository import UserRepository
from src.modules.auth.schemas import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from src.modules.auth.service import AuthService
from src.shared.schemas.response import ApiResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service(session: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(repo=UserRepository(session))


@router.post(
    "/register",
    response_model=ApiResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(
    request: RegisterRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[UserResponse]:
    user = await service.register(request)
    return ApiResponse(data=user, message="User registered successfully")


@router.post(
    "/login",
    response_model=ApiResponse[TokenResponse],
    summary="Login and get access token",
)
async def login(
    request: LoginRequest,
    service: AuthService = Depends(get_auth_service),
) -> ApiResponse[TokenResponse]:
    token = await service.login(request)
    return ApiResponse(data=token, message="Login successful")


@router.get(
    "/me",
    response_model=ApiResponse[UserResponse],
    summary="Get current authenticated user profile",
)
async def me(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> ApiResponse[UserResponse]:
    service = AuthService(repo=UserRepository(session))
    user = await service.get_current_user(current_user.id)
    return ApiResponse(data=user)
