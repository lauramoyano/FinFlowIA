from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.schemas.pagination import PaginationParams
from src.shared.schemas.response import PaginatedResponse

T = TypeVar("T")


async def paginate(
    session: AsyncSession,
    query: Select,
    params: PaginationParams,
    response_model: type[T],
) -> PaginatedResponse[T]:
    """
    Generic pagination helper for SQLAlchemy async queries.
    Executes a count query and a paginated data query, then wraps results.
    """
    # Count total matching records
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await session.execute(count_query)
    total = total_result.scalar_one()

    # Fetch paginated data
    paginated_query = query.offset(params.offset).limit(params.page_size)
    result = await session.execute(paginated_query)
    rows = result.scalars().all()

    items = [response_model.model_validate(row) for row in rows]

    return PaginatedResponse.create(
        data=items,
        total=total,
        page=params.page,
        page_size=params.page_size,
    )
