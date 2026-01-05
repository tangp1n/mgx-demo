"""Container command execution module."""
import logging
from typing import Dict, Any, Optional
from .docker_client import DockerClient

logger = logging.getLogger(__name__)


async def exec_command_in_container(
    container_id: str,
    command: str,
    workdir: str = "/app"
) -> Dict[str, Any]:
    """
    Execute a command in a running container.

    Args:
        container_id: Container ID
        command: Command to execute
        workdir: Working directory for command execution

    Returns:
        Dictionary with execution results
    """
    try:
        docker_client = DockerClient()

        logger.info(f"Executing command in container {container_id}: {command}")

        exit_code, output = docker_client.exec_command(
            container_id,
            command,
            workdir=workdir
        )

        # Split output into stdout and stderr if possible
        lines = output.split('\n')

        return {
            "exit_code": exit_code,
            "output": output,
            "error": "" if exit_code == 0 else output,
            "success": exit_code == 0,
            "command": command
        }

    except Exception as e:
        logger.error(f"Failed to execute command in container: {str(e)}")
        return {
            "exit_code": -1,
            "output": "",
            "error": str(e),
            "success": False,
            "command": command
        }


async def exec_command_streaming(
    container_id: str,
    command: str,
    workdir: str = "/app"
):
    """
    Execute a command and stream output.

    Args:
        container_id: Container ID
        command: Command to execute
        workdir: Working directory

    Yields:
        Output chunks as they become available
    """
    try:
        docker_client = DockerClient()

        # For now, execute and return full output
        # In future, this could use Docker SDK's stream parameter
        exit_code, output = docker_client.exec_command(
            container_id,
            command,
            workdir=workdir
        )

        # Yield output in chunks
        for line in output.split('\n'):
            yield {
                "type": "output",
                "data": line + '\n'
            }

        yield {
            "type": "exit",
            "exit_code": exit_code
        }

    except Exception as e:
        logger.error(f"Failed to execute streaming command: {str(e)}")
        yield {
            "type": "error",
            "error": str(e)
        }
