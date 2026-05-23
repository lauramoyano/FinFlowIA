from fastapi import Query
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Common pagination parameters for list endpoints."""

    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate SQL OFFSET value from page and page_size."""
        return (self.page - 1) * self.page_size


def get_pagination_params(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
) -> PaginationParams:
    """FastAPI dependency for pagination query parameters."""
    return PaginationParams(page=page, page_size=page_size)
