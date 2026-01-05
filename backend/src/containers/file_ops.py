"""Container file operations module."""
import logging
from typing import Dict, Any, Optional
from .docker_client import DockerClient

logger = logging.getLogger(__name__)


async def write_file_to_container(
    container_id: str,
    file_path: str,
    content: str
) -> Dict[str, Any]:
    """
    Write a file to a container.

    Args:
        container_id: Container ID
        file_path: Path to file in container
        content: File content

    Returns:
        Dictionary with operation result
    """
    try:
        docker_client = DockerClient()

        logger.info(f"Writing file {file_path} to container {container_id}")

        docker_client.write_file(container_id, file_path, content)

        return {
            "success": True,
            "file_path": file_path,
            "message": f"File {file_path} written successfully"
        }

    except Exception as e:
        logger.error(f"Failed to write file to container: {str(e)}")
        return {
            "success": False,
            "file_path": file_path,
            "error": str(e),
            "message": f"Failed to write file: {str(e)}"
        }


async def read_file_from_container(
    container_id: str,
    file_path: str
) -> Dict[str, Any]:
    """
    Read a file from a container.

    Args:
        container_id: Container ID
        file_path: Path to file in container

    Returns:
        Dictionary with file content
    """
    try:
        docker_client = DockerClient()

        logger.info(f"Reading file {file_path} from container {container_id}")

        content = docker_client.read_file(container_id, file_path)

        if content is None:
            return {
                "success": False,
                "file_path": file_path,
                "error": "File not found",
                "message": f"File {file_path} not found"
            }

        return {
            "success": True,
            "file_path": file_path,
            "content": content
        }

    except Exception as e:
        logger.error(f"Failed to read file from container: {str(e)}")
        return {
            "success": False,
            "file_path": file_path,
            "error": str(e),
            "message": f"Failed to read file: {str(e)}"
        }


async def copy_files_to_container(
    container_id: str,
    files: Dict[str, str]
) -> Dict[str, Any]:
    """
    Copy multiple files to a container.

    Args:
        container_id: Container ID
        files: Dictionary mapping file paths to content

    Returns:
        Dictionary with operation results
    """
    try:
        docker_client = DockerClient()
        results = {}
        errors = []

        for file_path, content in files.items():
            try:
                docker_client.write_file(container_id, file_path, content)
                results[file_path] = "success"
                logger.info(f"Copied file {file_path} to container {container_id}")
            except Exception as e:
                results[file_path] = "failed"
                errors.append(f"{file_path}: {str(e)}")
                logger.error(f"Failed to copy file {file_path}: {str(e)}")

        return {
            "success": len(errors) == 0,
            "results": results,
            "errors": errors,
            "total_files": len(files),
            "successful": sum(1 for v in results.values() if v == "success"),
            "failed": sum(1 for v in results.values() if v == "failed")
        }

    except Exception as e:
        logger.error(f"Failed to copy files to container: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to copy files: {str(e)}"
        }


async def list_container_files(
    container_id: str,
    directory: str = "/app"
) -> Dict[str, Any]:
    """
    List files in a container directory.

    Args:
        container_id: Container ID
        directory: Directory path

    Returns:
        Dictionary with file list
    """
    try:
        docker_client = DockerClient()

        logger.info(f"Listing files in {directory} from container {container_id}")

        files = docker_client.list_directory(container_id, directory)

        return {
            "success": True,
            "directory": directory,
            "files": files,
            "count": len(files)
        }

    except Exception as e:
        logger.error(f"Failed to list files in container: {str(e)}")
        return {
            "success": False,
            "directory": directory,
            "error": str(e),
            "message": f"Failed to list files: {str(e)}"
        }
