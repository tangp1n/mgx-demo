"""Conversation model for managing dialogues between user and system."""
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field


class ConversationStatus:
    """Conversation status enumeration."""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


class MessageRole:
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"


class EventType:
    """Event type enumeration for agent events."""
    THOUGHT = "thought"
    TOOL_CALL = "tool_call"
    TOOL_CALL_RESULT = "tool_call_result"
    TEXT = "text"
    ERROR = "error"


class Event(BaseModel):
    """
    Represents an agent event within an assistant message.

    Attributes:
        type: Event type (thought, tool_call, tool_call_result, text, error)
        data: Event-specific data
        timestamp: Event timestamp
    """
    type: str = Field(..., description="Event type")
    data: Dict[str, Any] = Field(..., description="Event-specific data")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Message(BaseModel):
    """
    Represents a single message in a conversation.

    Attributes:
        role: Message role (user or assistant)
        content: Message content
        timestamp: Message timestamp
        events: Agent events (for assistant messages)
    """
    role: str = Field(..., description="Message role (user or assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    events: Optional[List[Event]] = Field(
        default=None,
        description="Agent events (for assistant messages)"
    )

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class Conversation(BaseModel):
    """
    Represents a dialogue between user and system for a specific application.

    Attributes:
        id: MongoDB ObjectId (optional, set by database)
        application_id: Reference to the application
        user_id: Reference to the user
        messages: Conversation messages
        status: Conversation status (active, paused, completed, error)
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: Optional[str] = Field(default=None, alias="_id")
    application_id: str = Field(..., description="Application ID")
    user_id: str = Field(..., description="User ID")
    messages: List[Message] = Field(
        default_factory=list,
        description="Conversation messages"
    )
    status: str = Field(
        default=ConversationStatus.ACTIVE,
        description="Conversation status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""
    application_id: str


class MessageCreate(BaseModel):
    """Schema for adding a message to a conversation."""
    content: str


class ConversationResponse(BaseModel):
    """Schema for conversation API responses."""
    id: str = Field(..., alias="_id")
    application_id: str
    user_id: str
    messages: List[Message]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
