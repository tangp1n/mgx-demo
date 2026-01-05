"""Application service for managing user-created applications."""
from datetime import datetime
from typing import List, Optional
from bson import ObjectId
from bson.errors import InvalidId
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...models.application import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatus
)


class ApplicationService:
    """Service for managing applications."""

    def __init__(self, db: AsyncIOMotorDatabase, container_lifecycle_service=None):
        """Initialize application service with database connection."""
        self.db = db
        self.collection = db.applications
        self.container_lifecycle = container_lifecycle_service

    async def create(self, user_id: str, data: ApplicationCreate) -> Application:
        """
        Create a new application.

        Args:
            user_id: User ID who is creating the application
            data: Application creation data

        Returns:
            Created application
        """
        app = Application(
            user_id=user_id,
            name=data.name,
            requirements=data.requirements,
            requirements_confirmed=False,
            status=ApplicationStatus.DRAFT
        )

        result = await self.collection.insert_one(app.dict(by_alias=True, exclude={"id"}))
        app.id = str(result.inserted_id)

        return app

    async def get(self, application_id: str, user_id: Optional[str] = None) -> Optional[Application]:
        """
        Get an application by ID.

        Args:
            application_id: Application ID
            user_id: Optional user ID to filter by (for authorization)

        Returns:
            Application if found, None otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            query = {"_id": ObjectId(application_id)}
            logger.debug(f"Querying application with ID: {application_id}, user_id: {user_id}")
        except (InvalidId, TypeError) as e:
            # Invalid ObjectId format, return None
            logger.warning(f"Invalid ObjectId format: {application_id}, error: {e}")
            return None

        if user_id:
            query["user_id"] = user_id

        try:
            logger.debug(f"Executing database query: {query}")
            doc = await self.collection.find_one(query)
            logger.debug(f"Database query completed, result: {'found' if doc else 'not found'}")
        except Exception as e:
            logger.error(f"Database query failed: {e}", exc_info=True)
            return None

        if not doc:
            return None

        try:
            doc["_id"] = str(doc["_id"])
            return Application(**doc)
        except Exception as e:
            # Log error if Application model validation fails
            logger.error(f"Failed to create Application from document: {e}", exc_info=True)
            return None

    async def list(self, user_id: str, skip: int = 0, limit: int = 100) -> List[Application]:
        """
        List applications for a user.

        Args:
            user_id: User ID to filter by
            skip: Number of applications to skip (pagination)
            limit: Maximum number of applications to return

        Returns:
            List of applications
        """
        cursor = self.collection.find({"user_id": user_id}).sort("created_at", -1).skip(skip).limit(limit)
        apps = []

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            apps.append(Application(**doc))

        return apps

    async def update(
        self,
        application_id: str,
        user_id: str,
        data: ApplicationUpdate
    ) -> Optional[Application]:
        """
        Update an application.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)
            data: Application update data

        Returns:
            Updated application if found, None otherwise
        """
        update_data = {
            k: v for k, v in data.dict(exclude_unset=True).items() if v is not None
        }
        update_data["updated_at"] = datetime.utcnow()

        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(application_id), "user_id": user_id},
            {"$set": update_data},
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Application(**result)

    async def update_status(
        self,
        application_id: str,
        status: str,
        user_id: Optional[str] = None
    ) -> Optional[Application]:
        """
        Update application status.

        Args:
            application_id: Application ID
            status: New status
            user_id: Optional user ID (for authorization)

        Returns:
            Updated application if found, None otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            query = {"_id": ObjectId(application_id)}
            logger.debug(f"Updating status for application {application_id} to {status}")
        except (InvalidId, TypeError) as e:
            logger.error(f"Invalid ObjectId format in update_status: {application_id}, error: {e}")
            return None

        if user_id:
            query["user_id"] = user_id

        update_data = {
            "status": status,
            "updated_at": datetime.utcnow()
        }

        # Set last_deployed_at when status changes to running
        if status == ApplicationStatus.RUNNING:
            update_data["last_deployed_at"] = datetime.utcnow()

        try:
            logger.info(f"📝 [update_status] Executing database update for application {application_id} to status {status}")
            # Use update_one first to ensure write is acknowledged
            # Motor's update_one waits for write acknowledgment by default
            update_result = await self.collection.update_one(
                query,
                {"$set": update_data}
            )

            # Verify the update was successful
            if update_result.matched_count == 0:
                logger.warning(f"⚠️  [update_status] No document matched for application {application_id}")
                return None

            logger.info(f"✅ [update_status] Database update acknowledged (matched: {update_result.matched_count}, modified: {update_result.modified_count})")

            # Now fetch the updated document to return
            # This ensures the write is fully committed before we return
            result = await self.collection.find_one(query)
            logger.info(f"✅ [update_status] Fetched updated document for application {application_id}, result: {'found' if result else 'not found'}")
        except Exception as e:
            logger.error(f"❌ [update_status] Database update_status failed for application {application_id}: {e}", exc_info=True)
            return None

        if not result:
            return None

        try:
            result["_id"] = str(result["_id"])
            return Application(**result)
        except Exception as e:
            logger.error(f"Failed to create Application from update result: {e}", exc_info=True)
            return None

    async def confirm_requirements(
        self,
        application_id: str,
        user_id: str
    ) -> Optional[Application]:
        """
        Confirm application requirements.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)

        Returns:
            Updated application if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(application_id), "user_id": user_id},
            {
                "$set": {
                    "requirements_confirmed": True,
                    "status": ApplicationStatus.REQUIREMENTS_CONFIRMED,
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Application(**result)

    async def update_container(
        self,
        application_id: str,
        container_id: str
    ) -> Optional[Application]:
        """
        Update application with container ID.

        Args:
            application_id: Application ID
            container_id: Docker container ID

        Returns:
            Updated application if found, None otherwise
        """
        import logging
        logger = logging.getLogger(__name__)

        try:
            logger.info(f"📝 Updating container_id for application {application_id} to {container_id}")
            result = await self.collection.find_one_and_update(
                {"_id": ObjectId(application_id)},
                {
                    "$set": {
                        "container_id": container_id,
                        "updated_at": datetime.utcnow()
                    }
                },
                return_document=True
            )

            if not result:
                logger.warning(f"⚠️  Application {application_id} not found when updating container_id")
                return None

            result["_id"] = str(result["_id"])
            logger.info(f"✅ Successfully updated container_id for application {application_id}")
            return Application(**result)
        except Exception as e:
            logger.error(f"❌ Error updating container_id for application {application_id}: {str(e)}", exc_info=True)
            raise

    async def update_preview_info(
        self,
        application_id: str,
        preview_url: str,
        port: int
    ) -> Optional[Application]:
        """
        Update application with preview URL and port.

        Args:
            application_id: Application ID
            preview_url: Preview URL
            port: Port number

        Returns:
            Updated application if found, None otherwise
        """
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(application_id)},
            {
                "$set": {
                    "preview_url": preview_url,
                    "port": port,
                    "updated_at": datetime.utcnow()
                }
            },
            return_document=True
        )

        if not result:
            return None

        result["_id"] = str(result["_id"])
        return Application(**result)

    async def delete(self, application_id: str, user_id: str) -> bool:
        """
        Delete an application and its associated container.

        Args:
            application_id: Application ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        # Get the application first to check if it has a container
        app = await self.get(application_id, user_id)
        if not app:
            return False

        # Delete the container if it exists
        if app.container_id and self.container_lifecycle:
            try:
                await self.container_lifecycle.delete_container(application_id)
            except Exception as e:
                # Log error but continue with application deletion
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Failed to delete container for application {application_id}: {str(e)}")

        # Delete the application record
        result = await self.collection.delete_one(
            {"_id": ObjectId(application_id), "user_id": user_id}
        )

        return result.deleted_count > 0
