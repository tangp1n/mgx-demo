"""File tree retrieval from containers."""
from typing import List, Dict, Any
from .docker_client import DockerClient
from ..utils.logger import get_logger

logger = get_logger("file_tree")


class FileTreeService:
    """Service for retrieving file trees from containers."""

    def __init__(self, docker_client: DockerClient):
        """Initialize file tree service."""
        self.docker = docker_client

    def get_file_tree(
        self,
        container_id: str,
        path: str = "/app"
    ) -> List[Dict[str, Any]]:
        """
        Get file tree from container.

        Args:
            container_id: Docker container ID
            path: Root path to start from

        Returns:
            List of file/directory entries with nested structure
        """
        try:
            return self._build_tree(container_id, path)
        except Exception as e:
            logger.error(f"Failed to get file tree: {e}")
            raise

    def _build_tree(
        self,
        container_id: str,
        path: str,
        max_depth: int = 5,
        current_depth: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Recursively build file tree.

        Args:
            container_id: Docker container ID
            path: Current path
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth

        Returns:
            List of file/directory entries
        """
        if current_depth >= max_depth:
            return []

        try:
            entries = self.docker.list_directory(container_id, path)
            result = []

            for entry in entries:
                # Skip hidden files except .env
                if entry["name"].startswith('.') and entry["name"] not in ['.env', '.gitignore']:
                    continue

                file_entry = {
                    "name": entry["name"],
                    "type": entry["type"],
                    "path": f"{path}/{entry['name']}".replace('//', '/'),
                    "size": entry.get("size", 0)
                }

                # Recursively get children for directories
                if entry["type"] == "directory":
                    file_entry["children"] = self._build_tree(
                        container_id,
                        file_entry["path"],
                        max_depth,
                        current_depth + 1
                    )

                result.append(file_entry)

            # Sort: directories first, then files, alphabetically
            result.sort(key=lambda x: (x["type"] != "directory", x["name"].lower()))

            return result

        except Exception as e:
            logger.warning(f"Failed to build tree for {path}: {e}")
            return []
