"""Application model for managing user-created applications."""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from pydantic import BaseModel, Field


class ApplicationStatus:
    """Application status enumeration."""
    DRAFT = "draft"
    REQUIREMENTS_CONFIRMED = "requirements_confirmed"
    GENERATING = "generating"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class Application(BaseModel):
    """
    Represents a user-created application.

    Attributes:
        id: MongoDB ObjectId (optional, set by database)
        user_id: Reference to the user who created the application
        name: User-provided application name (optional)
        requirements: User requirements description
        requirements_confirmed: Whether user confirmed requirements
        status: Application status (draft, requirements_confirmed, generating, etc.)
        container_id: Docker container identifier (optional)
        preview_url: URL to access running application preview (optional)
        port: Port number for preview access (optional)
        created_at: Creation timestamp
        updated_at: Last update timestamp
        last_deployed_at: Last deployment timestamp (optional)
    """

    id: Optional[str] = Field(default=None, alias="_id")
    user_id: str = Field(..., description="User ID who created the application")
    name: Optional[str] = Field(default=None, description="Application name")
    requirements: str = Field(..., description="User requirements description")
    requirements_confirmed: bool = Field(
        default=False,
        description="Whether user confirmed requirements"
    )
    status: str = Field(
        default=ApplicationStatus.DRAFT,
        description="Application status"
    )
    container_id: Optional[str] = Field(
        default=None,
        description="Docker container identifier"
    )
    preview_url: Optional[str] = Field(
        default=None,
        description="URL to access running application"
    )
    port: Optional[int] = Field(
        default=None,
        description="Port number for preview access"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_deployed_at: Optional[datetime] = Field(default=None)

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ApplicationCreate(BaseModel):
    """Schema for creating a new application."""
    name: Optional[str] = None
    requirements: str


class ApplicationUpdate(BaseModel):
    """Schema for updating an application."""
    name: Optional[str] = None
    requirements: Optional[str] = None
    requirements_confirmed: Optional[bool] = None
    status: Optional[str] = None
    container_id: Optional[str] = None
    preview_url: Optional[str] = None
    port: Optional[int] = None


class ApplicationResponse(BaseModel):
    """Schema for application API responses."""
    id: str = Field(..., alias="_id")
    user_id: str
    name: Optional[str]
    requirements: str
    requirements_confirmed: bool
    status: str
    container_id: Optional[str]
    preview_url: Optional[str]
    port: Optional[int]
    created_at: datetime
    updated_at: datetime
    last_deployed_at: Optional[datetime]

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
