import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.transactions.category_repository import CategoryRepository
from src.modules.transactions.category_service import CategoryService
from src.modules.transactions.enums import TransactionType
from src.modules.transactions.schemas import CategoryResponse, CreateCategoryRequest
from src.shared.schemas.response import ApiResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


def get_category_service(session: AsyncSession = Depends(get_db)) -> CategoryService:
    return CategoryService(repo=CategoryRepository(session))


@router.get(
    "",
    response_model=ApiResponse[list[CategoryResponse]],
    summary="List categories available to the current user",
)
async def list_categories(
    transaction_type: TransactionType | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> ApiResponse[list[CategoryResponse]]:
    categories = await service.list_categories(
        user_id=current_user.id,
        transaction_type=transaction_type.value if transaction_type else None,
    )
    return ApiResponse(data=categories)


@router.post(
    "",
    response_model=ApiResponse[CategoryResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a custom category",
)
async def create_category(
    request: CreateCategoryRequest,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> ApiResponse[CategoryResponse]:
    category = await service.create_category(user_id=current_user.id, data=request)
    return ApiResponse(data=category, message="Category created successfully")


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a custom category",
)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: CategoryService = Depends(get_category_service),
) -> None:
    await service.delete_category(user_id=current_user.id, category_id=category_id)
