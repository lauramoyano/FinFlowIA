import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.production.repository import ProductRepository
from src.modules.production.schemas import CreateProductRequest, ProductResponse, UpdateProductRequest
from src.modules.production.service import ProductService
from src.shared.schemas.response import ApiResponse

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(session: AsyncSession = Depends(get_db)) -> ProductService:
    return ProductService(repo=ProductRepository(session))


@router.get(
    "",
    response_model=ApiResponse[list[ProductResponse]],
    summary="List the current user's product catalog",
)
async def list_products(
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> ApiResponse[list[ProductResponse]]:
    products = await service.list_products(user_id=current_user.id)
    return ApiResponse(data=products)


@router.post(
    "",
    response_model=ApiResponse[ProductResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new product",
)
async def create_product(
    request: CreateProductRequest,
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> ApiResponse[ProductResponse]:
    product = await service.create_product(user_id=current_user.id, data=request)
    return ApiResponse(data=product, message="Product created successfully")


@router.put(
    "/{product_id}",
    response_model=ApiResponse[ProductResponse],
    summary="Update a product",
)
async def update_product(
    product_id: uuid.UUID,
    request: UpdateProductRequest,
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> ApiResponse[ProductResponse]:
    product = await service.update_product(
        user_id=current_user.id, product_id=product_id, data=request
    )
    return ApiResponse(data=product, message="Product updated successfully")


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a product",
)
async def delete_product(
    product_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: ProductService = Depends(get_product_service),
) -> None:
    await service.delete_product(user_id=current_user.id, product_id=product_id)
