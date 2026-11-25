from src.shared.exceptions.base import AppException


class UnauthorizedException(AppException):
    """Raised when a user is not authenticated or has insufficient permissions."""

    def __init__(self, message: str = "Authentication required") -> None:
        super().__init__(
            message=message,
            code="UNAUTHORIZED",
            status_code=401,
        )


class ForbiddenException(AppException):
    """Raised when a user is authenticated but lacks permission for the action."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(
            message=message,
            code="FORBIDDEN",
            status_code=403,
        )
