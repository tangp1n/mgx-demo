"""Error handling and response formatting utilities."""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or "internal_error"
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(AppError):
    """Validation error."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="validation_error",
            details=details,
        )


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: Optional[str] = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="not_found",
        )


class AuthenticationError(AppError):
    """Authentication error."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="authentication_error",
        )


class AuthorizationError(AppError):
    """Authorization error."""

    def __init__(self, message: str = "Access denied"):
        super().__init__(
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="authorization_error",
        )


def error_response(error: AppError) -> Dict[str, Any]:
    """Format error response."""
    response = {
        "error": error.error_code,
        "message": error.message,
    }
    if error.details:
        response["details"] = error.details
    return response


def http_exception_from_error(error: AppError) -> HTTPException:
    """Convert AppError to HTTPException."""
    return HTTPException(
        status_code=error.status_code,
        detail=error_response(error),
    )

