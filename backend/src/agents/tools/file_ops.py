"""File operation tools for code generation agent."""
import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileOperationTools:
    """Tools for file operations within containers."""

    def __init__(self, container_service):
        """
        Initialize file operation tools.

        Args:
            container_service: Container service for file operations
        """
        self.container_service = container_service

    async def create_file(
        self,
        container_id: str,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Create a new file in the container.

        Args:
            container_id: Container ID
            file_path: Path to the file within container
            content: File content

        Returns:
            Result dictionary with success status and message
        """
        try:
            logger.info(f"Creating file {file_path} in container {container_id}")

            # Ensure the file path is within /app directory
            if not file_path.startswith('/app/'):
                file_path = f'/app/{file_path.lstrip("/")}'

            # Create parent directory if needed
            parent_dir = str(Path(file_path).parent)
            if parent_dir != '/app':
                await self.container_service.exec_command(
                    container_id,
                    f'mkdir -p {parent_dir}'
                )

            # Write file content
            await self.container_service.write_file(
                container_id,
                file_path,
                content
            )

            return {
                "success": True,
                "message": f"File {file_path} created successfully",
                "file_path": file_path
            }

        except Exception as e:
            logger.error(f"Failed to create file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create file {file_path}: {str(e)}"
            }

    async def write_file(
        self,
        container_id: str,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Write content to an existing file or create new one.

        Args:
            container_id: Container ID
            file_path: Path to the file within container
            content: File content

        Returns:
            Result dictionary with success status and message
        """
        return await self.create_file(container_id, file_path, content)

    async def read_file(
        self,
        container_id: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Read file content from container.

        Args:
            container_id: Container ID
            file_path: Path to the file within container

        Returns:
            Result dictionary with file content
        """
        try:
            logger.info(f"Reading file {file_path} from container {container_id}")

            # Ensure the file path is within /app directory
            if not file_path.startswith('/app/'):
                file_path = f'/app/{file_path.lstrip("/")}'

            content = await self.container_service.read_file(
                container_id,
                file_path
            )

            return {
                "success": True,
                "content": content,
                "file_path": file_path
            }

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to read file {file_path}: {str(e)}"
            }

    async def update_file(
        self,
        container_id: str,
        file_path: str,
        content: str
    ) -> Dict[str, Any]:
        """
        Update an existing file with new content.

        Args:
            container_id: Container ID
            file_path: Path to the file within container
            content: New file content

        Returns:
            Result dictionary with success status and message
        """
        return await self.write_file(container_id, file_path, content)

    async def delete_file(
        self,
        container_id: str,
        file_path: str
    ) -> Dict[str, Any]:
        """
        Delete a file from the container.

        Args:
            container_id: Container ID
            file_path: Path to the file within container

        Returns:
            Result dictionary with success status and message
        """
        try:
            logger.info(f"Deleting file {file_path} from container {container_id}")

            # Ensure the file path is within /app directory
            if not file_path.startswith('/app/'):
                file_path = f'/app/{file_path.lstrip("/")}'

            # Execute delete command
            result = await self.container_service.exec_command(
                container_id,
                f'rm -f {file_path}'
            )

            return {
                "success": result.get("exit_code") == 0,
                "message": f"File {file_path} deleted successfully" if result.get("exit_code") == 0 else f"Failed to delete file {file_path}",
                "file_path": file_path
            }

        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to delete file {file_path}: {str(e)}"
            }

    async def list_directory(
        self,
        container_id: str,
        dir_path: str = "/app"
    ) -> Dict[str, Any]:
        """
        List contents of a directory in the container.

        Args:
            container_id: Container ID
            dir_path: Path to the directory

        Returns:
            Result dictionary with directory contents
        """
        try:
            logger.info(f"Listing directory {dir_path} in container {container_id}")

            # Ensure the path is within /app directory
            if not dir_path.startswith('/app/'):
                dir_path = f'/app/{dir_path.lstrip("/")}'

            result = await self.container_service.exec_command(
                container_id,
                f'ls -la {dir_path}'
            )

            return {
                "success": result.get("exit_code") == 0,
                "output": result.get("output", ""),
                "dir_path": dir_path
            }

        except Exception as e:
            logger.error(f"Failed to list directory {dir_path}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to list directory {dir_path}: {str(e)}"
            }
