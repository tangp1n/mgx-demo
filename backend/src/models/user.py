"""User model."""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, EmailStr, Field, field_validator
from pydantic_core import core_schema


class PyObjectId(str):
    """Pydantic-compatible ObjectId."""

    @classmethod
    def __get_pydantic_core_schema__(cls, _source_type, _handler):
        def validate_from_object_id(value):
            if isinstance(value, ObjectId):
                return str(value)
            if isinstance(value, str) and ObjectId.is_valid(value):
                return value
            raise ValueError("Invalid ObjectId")

        return core_schema.no_info_plain_validator_function(
            validate_from_object_id,
            serialization=core_schema.str_schema()
        )


class User(BaseModel):
    """User model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class UserCreate(BaseModel):
    """User creation schema."""

    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserResponse(BaseModel):
    """User response schema (without password hash)."""

    id: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

