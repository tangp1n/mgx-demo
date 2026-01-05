"""File content retrieval from containers."""
from typing import Optional
from .docker_client import DockerClient
from ..utils.logger import get_logger

logger = get_logger("file_content")


class FileContentService:
    """Service for retrieving file content from containers."""

    def __init__(self, docker_client: DockerClient):
        """Initialize file content service."""
        self.docker = docker_client

    def get_file_content(
        self,
        container_id: str,
        file_path: str
    ) -> Optional[str]:
        """
        Get file content from container.

        Args:
            container_id: Docker container ID
            file_path: File path in container

        Returns:
            File content or None if not found
        """
        try:
            content = self.docker.read_file(container_id, file_path)
            return content
        except Exception as e:
            logger.error(f"Failed to get file content for {file_path}: {e}")
            raise

    def write_file_content(
        self,
        container_id: str,
        file_path: str,
        content: str
    ) -> None:
        """
        Write file content to container.

        Args:
            container_id: Docker container ID
            file_path: File path in container
            content: File content
        """
        try:
            self.docker.write_file(container_id, file_path, content)
        except Exception as e:
            logger.error(f"Failed to write file content for {file_path}: {e}")
            raise
