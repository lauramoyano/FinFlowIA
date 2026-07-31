import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from src.config.database import get_db
from src.config.settings import settings
from src.infrastructure.cache.redis_client import get_redis
from src.modules.ai.cache import LLMCache
from src.modules.ai.providers.anthropic import AnthropicProvider
from src.modules.ai.providers.openai import OpenAIProvider
from src.modules.ai.service import AIService
from src.modules.auth.dependencies import get_current_user
from src.modules.auth.models import User
from src.modules.transactions.categorizer import TransactionCategorizer
from src.modules.transactions.category_repository import CategoryRepository
from src.modules.transactions.repository import TransactionRepository
from src.modules.transactions.schemas import (
    CreateTransactionRequest,
    TransactionResponse,
    UpdateTransactionRequest,
)
from src.modules.transactions.service import TransactionService
from src.shared.schemas.response import ApiResponse, PaginatedResponse

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def get_transaction_service(
    session: AsyncSession = Depends(get_db),
    redis_client: Redis | None = Depends(get_redis),
) -> TransactionService:
    # These would normally be injected via a DI container
    repo = TransactionRepository(session)
    fallback = (
        OpenAIProvider(api_key=settings.openai_api_key) if settings.openai_api_key else None
    )
    ai_service = AIService(
        primary=AnthropicProvider(api_key=settings.anthropic_api_key),
        fallback=fallback,
        cache=LLMCache(redis_client=redis_client, ttl_seconds=settings.llm_cache_ttl_seconds),
    )
    categorizer = TransactionCategorizer(ai_service=ai_service)
    category_repo = CategoryRepository(session)
    return TransactionService(repo=repo, categorizer=categorizer, category_repo=category_repo)


@router.post(
    "",
    response_model=ApiResponse[TransactionResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new transaction",
)
async def create_transaction(
    request: CreateTransactionRequest,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> ApiResponse[TransactionResponse]:
    transaction = await service.create(data=request, user_id=current_user.id)
    return ApiResponse(data=transaction, message="Transaction created successfully")


@router.get(
    "",
    response_model=PaginatedResponse[TransactionResponse],
    summary="List transactions for the current user",
)
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    transaction_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> PaginatedResponse[TransactionResponse]:
    transactions, total = await service.list_by_user(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        transaction_type=transaction_type,
        category=category,
        start_date=start_date,
        end_date=end_date,
    )
    return PaginatedResponse.create(
        data=transactions, total=total, page=page, page_size=page_size
    )


@router.get(
    "/{transaction_id}",
    response_model=ApiResponse[TransactionResponse],
    summary="Get a transaction by ID",
)
async def get_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> ApiResponse[TransactionResponse]:
    transaction = await service.get_by_id(transaction_id, current_user.id)
    return ApiResponse(data=transaction)


@router.put(
    "/{transaction_id}",
    response_model=ApiResponse[TransactionResponse],
    summary="Update a transaction",
)
async def update_transaction(
    transaction_id: uuid.UUID,
    request: UpdateTransactionRequest,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> ApiResponse[TransactionResponse]:
    transaction = await service.update(transaction_id, request, current_user.id)
    return ApiResponse(data=transaction, message="Transaction updated successfully")


@router.delete(
    "/{transaction_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a transaction",
)
async def delete_transaction(
    transaction_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service),
) -> None:
    await service.delete(transaction_id, current_user.id)
