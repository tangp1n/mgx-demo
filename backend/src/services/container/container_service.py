"""Container service for managing container metadata."""
from datetime import datetime
from typing import Optional
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...models.container import (
    Container,
    ContainerCreate,
    ContainerUpdate,
    ContainerStatus
)


class ContainerService:
    """Service for managing container metadata."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize container service with database connection."""
        self.db = db
        self.collection = db.containers

    async def create(self, data: ContainerCreate, container_id: str) -> Container:
        """
        Create a new container record.

        Args:
            data: Container creation data
            container_id: Docker container ID

        Returns:
            Created container record
        """
        container = Container(
            application_id=data.application_id,
            container_id=container_id,
            image=data.image or "node:18-alpine",
            status=ContainerStatus.CREATING,
            resource_limits=data.resource_limits
        )

        result = await self.collection.insert_one(
            container.dict(by_alias=True, exclude={"id"})
        )
        container.id = str(result.inserted_id)

        return container

    async def get(self, container_id: str) -> Optional[Container]:
        """
        Get a container by MongoDB ID.

        Args:
            container_id: MongoDB container ID

        Returns:
            Container if found, None otherwise
        """
        doc = await self.collection.find_one({"_id": ObjectId(container_id)})
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        return Container(**doc)

    async def get_by_docker_id(self, docker_container_id: str) -> Optional[Container]:
        """
        Get a container by Docker container ID.

        Args:
            docker_container_id: Docker container ID

        Returns:
            Container if found, None otherwise
        """
        doc = await self.collection.find_one({"container_id": docker_container_id})
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        return Container(**doc)

    async def get_by_application(self, application_id: str) -> Optional[Container]:
        """
        Get container for an application.

        Args:
            application_id: Application ID

        Returns:
            Container if found, None otherwise
        """
        doc = await self.collection.find_one({"application_id": application_id})
        if not doc:
            return None

        doc["_id"] = str(doc["_id"])
        return Container(**doc)

    async def update(
        self,
        container_id: str,
        data: ContainerUpdate
    ) -> Optional[Container]:
        """
        Update a container.

        Args:
            container_id: MongoDB container ID
            data: Container update data

        Returns:
            Updated container if found, None otherwise
        """
        update_data = {
            k: v for k, v in data.dict(exclude_unset=True).items() if v is not None
        }
        update_data["updated_at"] = datetime.utcnow()

        if data.status == ContainerStatus.STOPPED:
            update_data["stopped_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(container_id)},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Container(**result)

    async def update_status(
        self,
        container_id: str,
        status: str
    ) -> Optional[Container]:
        """
        Update container status.

        Args:
            container_id: MongoDB container ID
            status: New status

        Returns:
            Updated container if found, None otherwise
        """
        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        if status == ContainerStatus.STOPPED:
            update_data["stopped_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(container_id)},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Container(**result)

    async def update_port(
        self,
        container_id: str,
        port: int
    ) -> Optional[Container]:
        """
        Update container port.

        Args:
            container_id: MongoDB container ID
            port: Port number

        Returns:
            Updated container if found, None otherwise
        """
        update_data = {
            "port": port,
            "updated_at": datetime.utcnow()
        }

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(container_id)},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Container(**result)

    async def delete(self, container_id: str) -> bool:
        """
        Delete a container record.

        Args:
            container_id: MongoDB container ID

        Returns:
            True if deleted, False if not found
        """
        result = await self.collection.delete_one({"_id": ObjectId(container_id)})
        return result.deleted_count > 0
