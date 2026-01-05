"""Authentication API endpoints."""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from pydantic import BaseModel, EmailStr

from src.models.user import User, UserCreate, UserResponse
from src.models.session import SessionCreate
from src.services.database import get_database
from src.services.auth.auth_service import hash_password, verify_password
from src.services.session.session_service import create_session, revoke_session
from src.utils.errors import ValidationError, NotFoundError, AuthenticationError, http_exception_from_error
from src.utils.logger import get_logger
from src.config import settings

logger = get_logger("auth_api")

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    """Login response."""

    token: str
    user: UserResponse


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(request: RegisterRequest):
    """Register a new user."""
    logger.info(f"Registration attempt for email: {request.email}")
    db = get_database()

    # Check if user already exists
    existing_user = await db.users.find_one({"email": request.email})
    if existing_user:
        raise http_exception_from_error(
            ValidationError(f"User with email {request.email} already exists")
        )

    # Validate password
    if len(request.password) < 8:
        raise http_exception_from_error(
            ValidationError("Password must be at least 8 characters long")
        )

    # Create user
    user_doc = {
        "email": request.email,
        "password_hash": hash_password(request.password),
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }

    result = await db.users.insert_one(user_doc)
    # Convert ObjectId to string for Pydantic validation
    user_doc["_id"] = str(result.inserted_id)

    try:
        user = User(**user_doc)
        response = UserResponse(
            id=str(user.id),
            email=str(user.email),  # Ensure EmailStr is converted to str
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
        logger.info(f"User registered successfully: {response.email}")
        return response
    except Exception as e:
        logger.error(f"Error creating user response: {e}", exc_info=e)
        raise http_exception_from_error(
            ValidationError(f"Failed to create user response: {str(e)}")
        )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Login and create session."""
    db = get_database()

    # Find user
    user_doc = await db.users.find_one({"email": request.email})
    if not user_doc:
        raise http_exception_from_error(
            AuthenticationError("Invalid email or password")
        )

    # Convert ObjectId to string for Pydantic validation
    if "_id" in user_doc and isinstance(user_doc["_id"], ObjectId):
        user_doc["_id"] = str(user_doc["_id"])

    user = User(**user_doc)

    # Verify password
    if not verify_password(request.password, user.password_hash):
        raise http_exception_from_error(
            AuthenticationError("Invalid email or password")
        )

    # Create session
    session_data = SessionCreate(
        user_id=str(user.id),
        expires_at=datetime.utcnow() + timedelta(hours=settings.session_expiry_hours),
    )
    session = await create_session(session_data)

    return LoginResponse(
        token=session.token,
        user=UserResponse(
            id=str(user.id),
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
        ),
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(request: Request):
    """Logout and invalidate session."""
    # Get token from Authorization header
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization[7:]  # Remove "Bearer " prefix
        await revoke_session(token)

    return {"message": "Logged out successfully"}

