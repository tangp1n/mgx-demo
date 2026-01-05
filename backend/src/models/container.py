"""Container model for managing Docker containers."""
from datetime import datetime
from typing import Optional, Dict, Any
from bson import ObjectId
from pydantic import BaseModel, Field


class ContainerStatus:
    """Container status enumeration."""
    CREATING = "creating"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class ResourceLimits(BaseModel):
    """Resource limits for container."""
    memory_mb: Optional[int] = Field(default=512, description="Memory limit in MB")
    cpu_cores: Optional[float] = Field(default=0.5, description="CPU limit in cores")


class Container(BaseModel):
    """
    Represents an isolated runtime environment for executing user applications.

    Attributes:
        id: MongoDB ObjectId (optional, set by database)
        application_id: Reference to the application
        container_id: Docker container identifier
        image: Docker base image
        status: Container status (creating, running, stopped, error)
        port: Exposed port for application access
        resource_limits: Resource constraints
        created_at: Creation timestamp
        updated_at: Last update timestamp
        stopped_at: Stop timestamp (optional)
    """

    id: Optional[str] = Field(default=None, alias="_id")
    application_id: str = Field(..., description="Application ID")
    container_id: str = Field(..., description="Docker container identifier")
    image: str = Field(default="node:18-alpine", description="Docker base image")
    status: str = Field(
        default=ContainerStatus.CREATING,
        description="Container status"
    )
    port: Optional[int] = Field(default=None, description="Exposed port")
    resource_limits: Optional[ResourceLimits] = Field(
        default_factory=ResourceLimits,
        description="Resource constraints"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    stopped_at: Optional[datetime] = Field(default=None)

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            ObjectId: str,
            datetime: lambda v: v.isoformat()
        }


class ContainerCreate(BaseModel):
    """Schema for creating a new container."""
    application_id: str
    image: Optional[str] = "node:18-alpine"
    resource_limits: Optional[ResourceLimits] = None


class ContainerUpdate(BaseModel):
    """Schema for updating a container."""
    status: Optional[str] = None
    port: Optional[int] = None


class ContainerResponse(BaseModel):
    """Schema for container API responses."""
    id: str = Field(..., alias="_id")
    application_id: str
    container_id: str
    image: str
    status: str
    port: Optional[int]
    resource_limits: Optional[ResourceLimits]
    created_at: datetime
    updated_at: datetime
    stopped_at: Optional[datetime]

    class Config:
        """Pydantic model configuration."""
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
