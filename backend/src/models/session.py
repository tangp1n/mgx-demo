"""Session model."""
from datetime import datetime, timedelta
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field
from pydantic_core import core_schema
from src.models.user import PyObjectId


class Session(BaseModel):
    """Session model."""

    id: Optional[PyObjectId] = Field(default=None, alias="_id")
    user_id: PyObjectId
    token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}


class SessionCreate(BaseModel):
    """Session creation schema."""

    user_id: str
    expires_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    def __init__(self, **data):
        if "expires_at" not in data or data["expires_at"] is None:
            # Default to 24 hours from now
            data["expires_at"] = datetime.utcnow() + timedelta(hours=24)
        super().__init__(**data)


class SessionResponse(BaseModel):
    """Session response schema."""

    id: str
    user_id: str
    token: str
    expires_at: datetime
    created_at: datetime

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}

