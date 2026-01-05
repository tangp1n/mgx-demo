"""Session service for session management."""
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
import secrets
from motor.motor_asyncio import AsyncIOMotorDatabase

from src.models.session import Session, SessionCreate
from src.services.database import get_database
from src.utils.errors import NotFoundError, AuthenticationError
from src.utils.logger import get_logger

logger = get_logger("session_service")


def generate_session_token() -> str:
    """Generate a secure random session token."""
    return secrets.token_urlsafe(32)


async def create_session(session_data: SessionCreate) -> Session:
    """Create a new session."""
    db = get_database()
    token = generate_session_token()

    session_doc = {
        "user_id": ObjectId(session_data.user_id),
        "token": token,
        "expires_at": session_data.expires_at,
        "created_at": datetime.utcnow(),
        "ip_address": session_data.ip_address,
        "user_agent": session_data.user_agent,
    }

    result = await db.sessions.insert_one(session_doc)
    session_doc["_id"] = result.inserted_id

    return Session(**session_doc)


async def get_session_by_token(token: str) -> Optional[Session]:
    """Get session by token."""
    db = get_database()
    session_doc = await db.sessions.find_one({"token": token})

    if not session_doc:
        return None

    # Check if session is expired
    if session_doc["expires_at"] < datetime.utcnow():
        # Session expired, delete it
        await db.sessions.delete_one({"_id": session_doc["_id"]})
        return None

    return Session(**session_doc)


async def validate_session(token: str) -> Session:
    """Validate a session token and return the session."""
    session = await get_session_by_token(token)

    if not session:
        raise AuthenticationError("Invalid or expired session token")

    return session


async def revoke_session(token: str) -> bool:
    """Revoke a session by token."""
    db = get_database()
    result = await db.sessions.delete_one({"token": token})
    return result.deleted_count > 0


async def revoke_user_sessions(user_id: str) -> int:
    """Revoke all sessions for a user."""
    db = get_database()
    result = await db.sessions.delete_many({"user_id": ObjectId(user_id)})
    return result.deleted_count

