from src.shared.exceptions.base import AppException


class ValidationAppException(AppException):
    """Raised when business-level validation fails."""

    def __init__(self, message: str, field: str | None = None) -> None:
        self.field = field
        code = "VALIDATION_ERROR"
        if field:
            message = f"Validation failed for '{field}': {message}"
        super().__init__(
            message=message,
            code=code,
            status_code=422,
        )
