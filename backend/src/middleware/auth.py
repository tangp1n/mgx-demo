"""Authentication middleware for bearer token validation."""
from typing import Optional
from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from src.services.session.session_service import validate_session
from src.utils.errors import AuthenticationError, http_exception_from_error
from src.utils.logger import get_logger

logger = get_logger("auth_middleware")

security = HTTPBearer(auto_error=False)


async def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from bearer token in request.

    Supports both Authorization header and query parameter (for SSE/EventSource).
    """
    token: Optional[str] = None

    # Try to get token from Authorization header first
    credentials: Optional[HTTPAuthorizationCredentials] = await security(request)
    if credentials:
        token = credentials.credentials

    # Fallback to query parameter (for EventSource which doesn't support headers)
    if not token:
        token = request.query_params.get("token")

    if not token:
        return None

    try:
        session = await validate_session(token)
        return str(session.user_id)
    except AuthenticationError:
        return None


async def require_auth(request: Request) -> str:
    """Require authentication and return user ID."""
    user_id = await get_current_user_id(request)

    if not user_id:
        raise http_exception_from_error(
            AuthenticationError("Authentication required")
        )

    return user_id


async def get_current_user(request: Request) -> dict:
    """Get current authenticated user as a dictionary."""
    user_id = await require_auth(request)
    return {"user_id": user_id}

