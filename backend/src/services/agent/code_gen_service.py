"""Code generation service for orchestrating the code generation workflow."""
import asyncio
import logging
from typing import AsyncGenerator, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from ...agents.code_gen.agent import CodeGenAgent
from ...models.application import ApplicationStatus
from ...models.container import ResourceLimits
from ..container.container_lifecycle import ContainerLifecycleService
from ..application.application_service import ApplicationService

logger = logging.getLogger(__name__)


class CodeGenService:
    """
    Service for managing code generation workflow.

    Coordinates:
    1. Container creation
    2. Code generation via agent
    3. Application status updates
    4. Preview URL generation
    """

    def __init__(self, db: AsyncIOMotorDatabase):
        """
        Initialize code generation service.

        Args:
            db: MongoDB database connection
        """
        self.db = db
        self.app_service = ApplicationService(db)
        self.container_lifecycle = ContainerLifecycleService(db)

    async def generate_and_deploy(
        self,
        application_id: str,
        requirements: str
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate code and deploy application.

        Args:
            application_id: Application ID
            requirements: User requirements

        Yields:
            Progress events from code generation
        """
        try:
            logger.info(f"🚀 [CodeGenService] Starting code generation for application {application_id}")

            # Update status to generating
            yield {
                "type": "text",
                "data": {
                    "content": "🚀 Starting code generation process..."
                }
            }

            logger.info(f"📝 [CodeGenService] Updating application status to GENERATING...")
            # Direct database update - use await but yield control first to ensure generator continues
            from bson import ObjectId
            from datetime import datetime

            logger.info(f"🔍 [CodeGenService] Directly updating database status for application {application_id}")
            query = {"_id": ObjectId(application_id)}
            update_data = {
                "status": ApplicationStatus.GENERATING,
                "updated_at": datetime.utcnow()
            }

            # Yield control to event loop before await to prevent blocking
            await asyncio.sleep(0)

            # Now execute the database update
            try:
                update_result = await self.app_service.collection.update_one(
                    query,
                    {"$set": update_data}
                )
                if update_result.matched_count > 0:
                    logger.info(f"✅ [CodeGenService] Database status updated successfully (matched: {update_result.matched_count}, modified: {update_result.modified_count})")
                else:
                    logger.warning(f"⚠️  [CodeGenService] No document matched for application {application_id}")
            except Exception as e:
                logger.error(f"❌ [CodeGenService] Error updating status to GENERATING: {e}", exc_info=True)

            # Check if container already exists
            from ..container.container_service import ContainerService
            container_service = ContainerService(self.db)
            logger.info(f"🔍 [CodeGenService] Checking for existing container...")
            # Yield control before await to prevent blocking in nested async generators
            await asyncio.sleep(0)
            existing_container = await container_service.get_by_application(application_id)
            logger.info(f"🔍 [CodeGenService] Container check completed: {'found' if existing_container else 'not found'}")

            if existing_container:
                # Container already exists, use it
                # Ensure application has container_id set (in case it was missing)
                logger.info(f"📝 Updating application {application_id} with existing container_id: {existing_container.container_id}")
                # Yield control before await to prevent blocking
                await asyncio.sleep(0)
                updated_app = await self.app_service.update_container(
                    application_id,
                    existing_container.container_id
                )

                if not updated_app:
                    logger.warning(f"⚠️  Failed to update container_id for application {application_id}, but continuing with existing container")
                else:
                    logger.info(f"✅ Successfully updated application {application_id} with existing container_id")

                yield {
                    "type": "thought",
                    "data": {
                        "content": "Using existing container environment..."
                    }
                }
                yield {
                    "type": "text",
                    "data": {
                        "content": f"✅ Using existing container: {existing_container.container_id[:12]}"
                    }
                }
            else:
                # Create and start container
                yield {
                    "type": "thought",
                    "data": {
                        "content": "Creating isolated container environment..."
                    }
                }

                resource_limits = ResourceLimits(memory_mb=512, cpu_cores=0.5)

                # Yield control before await to prevent blocking
                await asyncio.sleep(0)
                container = await self.container_lifecycle.create_and_start_container(
                    application_id,
                    image="node:18-alpine",
                    resource_limits=resource_limits
                )

                # Update application with container ID
                logger.info(f"📝 Updating application {application_id} with container_id: {container.container_id}")
                # Yield control before await to prevent blocking
                await asyncio.sleep(0)
                updated_app = await self.app_service.update_container(
                    application_id,
                    container.container_id
                )

                if not updated_app:
                    logger.error(f"❌ Failed to update container_id for application {application_id}")
                    raise Exception(f"Failed to update container_id for application {application_id}")

                logger.info(f"✅ Successfully updated application {application_id} with container_id: {container.container_id}")

                yield {
                    "type": "text",
                    "data": {
                        "content": f"✅ Container created: {container.container_id[:12]}"
                    }
                }

            # Update status to deploying
            # Yield control before await to prevent blocking
            await asyncio.sleep(0)
            await self.app_service.update_status(
                application_id,
                ApplicationStatus.DEPLOYING
            )

            # Initialize code generation agent
            code_gen_agent = CodeGenAgent(
                container_lifecycle_service=self.container_lifecycle
            )

            # Get container and ensure it has a port
            await asyncio.sleep(0)
            container = await container_service.get_by_application(application_id)
            if not container:
                raise Exception(f"Container not found for application {application_id}")

            # Get or allocate port (will check Docker if not in database)
            port = await self.container_lifecycle.get_or_allocate_port(application_id)

            # Generate code (streaming) - pass container port 8000 so server starts on correct port
            # Container always uses port 8000 internally, mapped to allocated host port
            # Yield control before starting nested async generator
            await asyncio.sleep(0)
            async for event in code_gen_agent.generate_code(
                application_id,
                requirements,
                port=8000  # Container always uses port 8000 internally
            ):
                # Yield control in nested async generator to prevent blocking
                await asyncio.sleep(0)
                yield event

            # Verify port mapping from Docker
            await asyncio.sleep(0)
            container = await container_service.get_by_application(application_id)
            if container:
                actual_host_port = self.container_lifecycle.docker.get_container_port_mapping(
                    container.container_id,
                    container_port=8000
                )
                if actual_host_port and actual_host_port != port:
                    logger.warning(f"⚠️  Port mismatch: database has {port}, but Docker shows {actual_host_port}. Using Docker port.")
                    port = actual_host_port
                    await container_service.update_port(container.id, port)

            # Generate preview URL using the allocated host port
            # Yield control before await to prevent blocking
            await asyncio.sleep(0)
            preview_url = await self.container_lifecycle.generate_preview_url(
                application_id,
                port
            )

            # Update application with preview URL and port
            # Yield control before await to prevent blocking
            await asyncio.sleep(0)
            await self.app_service.update_preview_info(
                application_id,
                preview_url,
                port
            )

            yield {
                "type": "text",
                "data": {
                    "content": f"🔍 Debug: Preview URL configured as {preview_url} (host port: {port})"
                }
            }

            # Update status to running
            # Yield control before await to prevent blocking
            await asyncio.sleep(0)
            await self.app_service.update_status(
                application_id,
                ApplicationStatus.RUNNING
            )

            yield {
                "type": "text",
                "data": {
                    "content": f"🎉 Application deployed successfully! Preview URL: {preview_url}"
                }
            }

        except Exception as e:
            logger.error(f"Code generation failed for application {application_id}: {str(e)}")

            # Update status to error
            # Yield control before await to prevent blocking
            await asyncio.sleep(0)
            await self.app_service.update_status(
                application_id,
                ApplicationStatus.ERROR
            )

            yield {
                "type": "error",
                "data": {
                    "error": str(e),
                    "message": f"Code generation failed: {str(e)}"
                }
            }

    async def handle_error(
        self,
        application_id: str,
        error: str
    ) -> None:
        """
        Handle code generation error.

        Args:
            application_id: Application ID
            error: Error message
        """
        logger.error(f"Code generation error for {application_id}: {error}")

        await self.app_service.update_status(
            application_id,
            ApplicationStatus.ERROR
        )
