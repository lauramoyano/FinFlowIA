import uuid

from src.shared.exceptions.base import AppException


class NotFoundException(AppException):
    """Raised when a requested resource does not exist."""

    def __init__(self, resource: str, resource_id: uuid.UUID | str) -> None:
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            code=f"{resource.upper().replace(' ', '_')}_NOT_FOUND",
            status_code=404,
        )
