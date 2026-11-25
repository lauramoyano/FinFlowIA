from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """
    Standard API response wrapper for all endpoints.
    Ensures a consistent response envelope across the entire API.
    """

    data: T
    message: str = "Success"


class PaginatedResponse(BaseModel, Generic[T]):
    """
    Paginated API response for list endpoints.
    Includes metadata about current page and total count.
    """

    data: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def create(
        cls,
        data: list[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResponse[T]":
        total_pages = max(1, -(-total // page_size))  # ceiling division
        return cls(
            data=data,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_prev=page > 1,
        )
