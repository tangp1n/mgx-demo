"""Command execution tools for code generation agent."""
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class CommandExecutionTools:
    """Tools for executing commands in containers."""

    def __init__(self, container_service):
        """
        Initialize command execution tools.

        Args:
            container_service: Container service for command execution
        """
        self.container_service = container_service

    async def execute_command(
        self,
        container_id: str,
        command: str,
        workdir: str = "/app"
    ) -> Dict[str, Any]:
        """
        Execute a command in the container.

        Args:
            container_id: Container ID
            command: Command to execute
            workdir: Working directory for command execution

        Returns:
            Result dictionary with command output and exit code
        """
        try:
            logger.info(f"Executing command in container {container_id}: {command}")

            result = await self.container_service.exec_command(
                container_id,
                command,
                workdir=workdir
            )

            return {
                "success": result.get("exit_code") == 0,
                "exit_code": result.get("exit_code", -1),
                "output": result.get("output", ""),
                "error": result.get("error", ""),
                "command": command
            }

        except Exception as e:
            logger.error(f"Failed to execute command '{command}': {str(e)}")
            return {
                "success": False,
                "exit_code": -1,
                "error": str(e),
                "message": f"Failed to execute command: {str(e)}",
                "command": command
            }

    async def install_dependencies(
        self,
        container_id: str,
        package_manager: str = "npm"
    ) -> Dict[str, Any]:
        """
        Install dependencies in the container.

        Args:
            container_id: Container ID
            package_manager: Package manager to use (npm, pip, etc.)

        Returns:
            Result dictionary with installation status
        """
        commands = {
            "npm": "npm install",
            "yarn": "yarn install",
            "pip": "pip install -r requirements.txt",
            "pip3": "pip3 install -r requirements.txt"
        }

        command = commands.get(package_manager, "npm install")

        logger.info(f"Installing dependencies with {package_manager} in container {container_id}")

        return await self.execute_command(container_id, command)

    async def start_dev_server(
        self,
        container_id: str,
        start_command: str = "npm start"
    ) -> Dict[str, Any]:
        """
        Start the development server in the container.

        Args:
            container_id: Container ID
            start_command: Command to start the server

        Returns:
            Result dictionary with server start status
        """
        logger.info(f"Starting dev server in container {container_id}")

        # Start server in background
        return await self.execute_command(
            container_id,
            f"nohup {start_command} > /app/server.log 2>&1 &"
        )

    async def get_command_output(
        self,
        container_id: str,
        command: str
    ) -> Dict[str, Any]:
        """
        Execute a command and return its output.

        Args:
            container_id: Container ID
            command: Command to execute

        Returns:
            Result dictionary with command output
        """
        return await self.execute_command(container_id, command)
