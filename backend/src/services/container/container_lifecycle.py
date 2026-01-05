"""Container lifecycle management service."""
import random
from motor.motor_asyncio import AsyncIOMotorDatabase
from ...models.container import ContainerCreate, ContainerStatus, Container, ResourceLimits
from ...containers.docker_client import DockerClient
from ...containers.file_tree import FileTreeService
from ...containers.file_content import FileContentService
from ...containers.exec import exec_command_in_container
from ...containers.file_ops import write_file_to_container, read_file_from_container
from .container_service import ContainerService
from ...utils.logger import get_logger

logger = get_logger("container_lifecycle")


class ContainerLifecycleService:
    """Service for managing container lifecycle."""

    def __init__(self, db: AsyncIOMotorDatabase):
        """Initialize container lifecycle service."""
        self.db = db
        self.container_service = ContainerService(db)
        self.docker = DockerClient()
        self.file_tree_service = FileTreeService(self.docker)
        self.file_content_service = FileContentService(self.docker)

    async def create_and_start_container(
        self,
        application_id: str,
        image: str = "node:18-alpine",
        resource_limits: ResourceLimits = None,
        host_port: int = None
    ) -> Container:
        """
        Create and start a new container for an application.

        Args:
            application_id: Application ID
            image: Docker image to use
            resource_limits: Resource limits for container
            host_port: Host port to map to container port 8000 (optional, will allocate if not provided)

        Returns:
            Created container record
        """
        try:
            # Allocate port if not provided
            if host_port is None:
                host_port = await self.allocate_port(application_id)

            # Container always uses port 8000 internally
            CONTAINER_PORT = 8000
            port_mapping = {CONTAINER_PORT: host_port}

            # Create Docker container with resource limits and port mapping
            docker_container_id = self.docker.create_container(
                image=image,
                name=f"app-{application_id[:8]}",
                resource_limits=resource_limits or ResourceLimits(),
                port_mapping=port_mapping
            )

            # Create container record in database
            container = await self.container_service.create(
                data=ContainerCreate(
                    application_id=application_id,
                    image=image,
                    resource_limits=resource_limits
                ),
                container_id=docker_container_id
            )

            # Store the port in container record
            await self.container_service.update_port(container.id, host_port)

            # Start container
            self.docker.start_container(docker_container_id)

            # Create /app directory if it doesn't exist
            self.docker.exec_command(docker_container_id, "mkdir -p /app", workdir="/")

            # Update status to running
            await self.container_service.update_status(
                container.id,
                ContainerStatus.RUNNING
            )

            logger.info(f"Created and started container for application {application_id} with port mapping {host_port}->{CONTAINER_PORT}")

            return container

        except Exception as e:
            logger.error(f"Failed to create container for application {application_id}: {e}")
            # Update status to error if container was created
            if 'container' in locals():
                await self.container_service.update_status(
                    container.id,
                    ContainerStatus.ERROR
                )
            raise

    async def get_or_create_container(
        self,
        application_id: str,
        image: str = "node:18-alpine",
        resource_limits: ResourceLimits = None
    ) -> Container:
        """
        Get existing container for an application, or create one if it doesn't exist.

        Args:
            application_id: Application ID
            image: Docker image to use (if creating new container)
            resource_limits: Resource limits for container (if creating new container)

        Returns:
            Container record (existing or newly created)
        """
        # Try to get existing container
        container = await self.container_service.get_by_application(application_id)

        if container:
            logger.info(f"Found existing container for application {application_id}: {container.container_id[:12]}")
            return container

        # Container doesn't exist, create a new one
        logger.info(f"No container found for application {application_id}, creating new one...")
        container = await self.create_and_start_container(
            application_id,
            image=image,
            resource_limits=resource_limits
        )

        # Update application with container_id
        from ...services.application.application_service import ApplicationService
        app_service = ApplicationService(self.db)
        updated_app = await app_service.update_container(
            application_id,
            container.container_id
        )

        if updated_app:
            logger.info(f"✅ Successfully created and stored container for application {application_id}")
        else:
            logger.warning(f"⚠️  Created container but failed to update application {application_id} with container_id")

        return container

    async def write_task_file(
        self,
        application_id: str,
        requirements: str
    ) -> None:
        """
        Write task.md file to container with requirements.

        Args:
            application_id: Application ID
            requirements: Requirements text
        """
        try:
            # Get or create container for application
            container = await self.get_or_create_container(application_id)

            # Create task.md content
            task_content = f"""# Task Specification

## Requirements

{requirements}

## Implementation Status

- [ ] Requirements confirmed
- [ ] Initial setup complete
- [ ] Core functionality implemented
- [ ] Testing complete
- [ ] Deployment ready

## Notes

This file was generated from the conversation requirements.
Update the implementation status as you progress through development.
"""

            # Write file to container
            self.file_content_service.write_file_content(
                container.container_id,
                "/app/task.md",
                task_content
            )

            logger.info(f"Wrote task.md to container for application {application_id}")

        except Exception as e:
            logger.error(f"Failed to write task.md for application {application_id}: {e}")
            raise

    async def get_file_tree(self, application_id: str, path: str = "/app"):
        """Get file tree for application container."""
        container = await self.get_or_create_container(application_id)
        return self.file_tree_service.get_file_tree(container.container_id, path)

    async def get_file_content(self, application_id: str, file_path: str):
        """Get file content from application container."""
        container = await self.get_or_create_container(application_id)
        return self.file_content_service.get_file_content(
            container.container_id,
            file_path
        )

    async def stop_container(self, application_id: str) -> None:
        """Stop container for an application."""
        container = await self.container_service.get_by_application(application_id)
        if not container:
            return

        self.docker.stop_container(container.container_id)
        await self.container_service.update_status(
            container.id,
            ContainerStatus.STOPPED
        )

        logger.info(f"Stopped container for application {application_id}")

    async def delete_container(self, application_id: str) -> None:
        """Delete container for an application."""
        container = await self.container_service.get_by_application(application_id)
        if not container:
            return

        # Remove Docker container
        self.docker.remove_container(container.container_id, force=True)

        # Delete container record
        await self.container_service.delete(container.id)

        logger.info(f"Deleted container for application {application_id}")

    async def exec_command(
        self,
        application_id: str,
        command: str,
        workdir: str = "/app"
    ):
        """
        Execute a command in application container.

        Args:
            application_id: Application ID
            command: Command to execute
            workdir: Working directory

        Returns:
            Command execution result
        """
        container = await self.get_or_create_container(application_id)
        return await exec_command_in_container(
            container.container_id,
            command,
            workdir
        )

    async def write_file(
        self,
        application_id: str,
        file_path: str,
        content: str
    ):
        """
        Write a file to application container.

        Args:
            application_id: Application ID
            file_path: File path in container
            content: File content

        Returns:
            Write operation result
        """
        container = await self.get_or_create_container(application_id)
        return await write_file_to_container(
            container.container_id,
            file_path,
            content
        )

    async def read_file(
        self,
        application_id: str,
        file_path: str
    ):
        """
        Read a file from application container.

        Args:
            application_id: Application ID
            file_path: File path in container

        Returns:
            File read result
        """
        container = await self.get_or_create_container(application_id)
        return await read_file_from_container(
            container.container_id,
            file_path
        )

    async def allocate_port(self, application_id: str) -> int:
        """
        Allocate a port for the application.

        Args:
            application_id: Application ID

        Returns:
            Allocated port number
        """
        # For simplicity, allocate a random port in the range 5000-9000
        # In production, this should use proper port management
        port = random.randint(5000, 9000)

        container = await self.container_service.get_by_application(application_id)
        if container:
            await self.container_service.update_port(container.id, port)

        logger.info(f"Allocated port {port} for application {application_id}")
        return port

    async def get_or_allocate_port(self, application_id: str) -> int:
        """
        Get existing port for container, or allocate a new one.
        For existing containers, tries to get port from Docker if not in database.

        Args:
            application_id: Application ID

        Returns:
            Port number
        """
        container = await self.container_service.get_by_application(application_id)
        if not container:
            return await self.allocate_port(application_id)

        # Check if port is already stored in database
        if container.port:
            return container.port

        # Try to get port from Docker container
        host_port = self.docker.get_container_port_mapping(container.container_id, container_port=8000)
        if host_port:
            # Store in database for future reference
            await self.container_service.update_port(container.id, host_port)
            logger.info(f"Retrieved port {host_port} from Docker for container {container.container_id[:12]}")
            return host_port

        # Allocate a new port
        port = await self.allocate_port(application_id)
        logger.warning(f"⚠️  Container {container.container_id[:12]} exists but has no port mapping. "
                      f"Allocated port {port} but preview may not work until container is recreated.")
        return port

    async def generate_preview_url(
        self,
        application_id: str,
        port: int
    ) -> str:
        """
        Generate preview URL for the application.

        Args:
            application_id: Application ID
            port: Application port

        Returns:
            Preview URL
        """
        # For local development, use localhost
        # In production, this would use the actual host/domain
        preview_url = f"http://localhost:{port}"

        logger.info(f"Generated preview URL for application {application_id}: {preview_url}")
        return preview_url

