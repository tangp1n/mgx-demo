"""Docker client wrapper for container management."""
import docker
from docker.errors import DockerException, NotFound, APIError
from typing import Optional, Dict, Any, List
import tarfile
import io
import os
import subprocess

from ..utils.logger import get_logger
from ..models.container import ResourceLimits

logger = get_logger("docker_client")


class DockerClient:
    """Wrapper for Docker SDK client."""

    def __init__(self):
        """Initialize Docker client."""
        try:
            self.client = docker.from_env()
            # Test connection
            self.client.ping()
            logger.info("Docker client initialized successfully")
        except DockerException as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            raise

    def create_container(
        self,
        image: str = "node:18-alpine",
        name: Optional[str] = None,
        resource_limits: Optional[ResourceLimits] = None,
        port_mapping: Optional[Dict[int, int]] = None
    ) -> str:
        """
        Create a new Docker container.

        Args:
            image: Docker image to use
            name: Container name (optional)
            resource_limits: Resource limits (optional)
            port_mapping: Port mapping dict {container_port: host_port} (optional)

        Returns:
            Container ID

        Raises:
            DockerException: If container creation fails
        """
        try:
            # Pull image if not present
            try:
                self.client.images.get(image)
            except NotFound:
                logger.info(f"Pulling image {image}...")
                # Use subprocess to pull image without proxy to avoid connection issues
                # This works around Docker Desktop proxy configuration problems
                try:
                    # Create environment without proxy variables
                    env = os.environ.copy()
                    proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
                    for var in proxy_vars:
                        env.pop(var, None)

                    # Pull image using docker CLI directly (bypasses proxy)
                    result = subprocess.run(
                        ['docker', 'pull', image],
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )

                    if result.returncode != 0:
                        logger.error(f"Failed to pull image {image}: {result.stderr}")
                        raise DockerException(f"Failed to pull image {image}: {result.stderr}")

                    logger.info(f"Successfully pulled image {image}")
                    # Refresh images to ensure it's available
                    self.client.images.get(image)
                except subprocess.TimeoutExpired:
                    logger.error(f"Timeout while pulling image {image}")
                    raise DockerException(f"Timeout while pulling image {image}")
                except FileNotFoundError:
                    # Fallback to SDK method if docker CLI not available
                    logger.warning("docker CLI not found, falling back to SDK method")
                    self.client.images.pull(image)

            # Prepare resource limits
            mem_limit = None
            nano_cpus = None
            if resource_limits:
                if resource_limits.memory_mb:
                    mem_limit = f"{resource_limits.memory_mb}m"
                if resource_limits.cpu_cores:
                    nano_cpus = int(resource_limits.cpu_cores * 1e9)

            # Prepare port bindings using Docker low-level API
            # create_host_config uses Python-style lowercase parameter names
            exposed_ports = None
            port_bindings = None

            if port_mapping:
                exposed_ports = {}
                port_bindings = {}
                for container_port, host_port in port_mapping.items():
                    port_key = f"{container_port}/tcp"
                    exposed_ports[port_key] = {}
                    # Format: {'8000/tcp': [{'HostPort': '6780'}]}
                    port_bindings[port_key] = [{'HostPort': str(host_port)}]

            # Build host_config parameters using Python-style names
            host_config_kwargs = {}

            if port_bindings:
                host_config_kwargs['port_bindings'] = port_bindings

            # Add resource limits to host config
            if mem_limit:
                # mem_limit is already in format like "512m", convert to bytes
                mem_bytes = int(mem_limit.rstrip('m')) * 1024 * 1024
                host_config_kwargs['mem_limit'] = mem_bytes
            if nano_cpus:
                # CPU quota and period are in microseconds (not nanoseconds)
                # cpu_quota = nano_cpus / cpu_period * 1000000
                # For 0.5 CPU: quota = 0.5 * 100000 = 50000, period = 100000
                cpu_period = 100000  # 100ms in microseconds (default Docker period)
                cpu_quota = int((nano_cpus / 1e9) * cpu_period)  # Convert nano_cpus to quota
                host_config_kwargs['cpu_quota'] = cpu_quota
                host_config_kwargs['cpu_period'] = cpu_period

            # Create host config if we have any parameters
            host_config = None
            if host_config_kwargs:
                host_config = self.client.api.create_host_config(**host_config_kwargs)

            # Create container using low-level API to support host_config
            create_kwargs = {
                'image': image,
                'command': "tail -f /dev/null",
                'name': name,
                'host_config': host_config,
                'ports': exposed_ports if exposed_ports else None,
            }

            # Remove None values
            create_kwargs = {k: v for k, v in create_kwargs.items() if v is not None}

            response = self.client.api.create_container(**create_kwargs)
            container_id = response['Id']

            logger.info(f"Created container {container_id[:12]}")
            if port_mapping:
                logger.info(f"Port mapping configured: {port_mapping}")
            return container_id

        except (DockerException, APIError) as e:
            logger.error(f"Failed to create container: {e}")
            raise

    def start_container(self, container_id: str) -> None:
        """
        Start a container.

        Args:
            container_id: Container ID

        Raises:
            DockerException: If container start fails
        """
        try:
            # Use low-level API to start container
            self.client.api.start(container_id)
            logger.info(f"Started container {container_id[:12]}")
        except (DockerException, NotFound, APIError) as e:
            logger.error(f"Failed to start container {container_id[:12]}: {e}")
            raise

    def stop_container(self, container_id: str, timeout: int = 10) -> None:
        """
        Stop a container.

        Args:
            container_id: Container ID
            timeout: Timeout in seconds

        Raises:
            DockerException: If container stop fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=timeout)
            logger.info(f"Stopped container {container_id[:12]}")
        except (DockerException, NotFound) as e:
            logger.error(f"Failed to stop container {container_id[:12]}: {e}")
            raise

    def remove_container(self, container_id: str, force: bool = False) -> None:
        """
        Remove a container.

        Args:
            container_id: Container ID
            force: Force removal even if running

        Raises:
            DockerException: If container removal fails
        """
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
            logger.info(f"Removed container {container_id[:12]}")
        except (DockerException, NotFound) as e:
            logger.error(f"Failed to remove container {container_id[:12]}: {e}")
            raise

    def exec_command(
        self,
        container_id: str,
        command: str,
        workdir: str = "/app"
    ) -> tuple[int, str]:
        """
        Execute a command in a container.

        Args:
            container_id: Container ID
            command: Command to execute
            workdir: Working directory

        Returns:
            Tuple of (exit_code, output)

        Raises:
            DockerException: If command execution fails
        """
        try:
            container = self.client.containers.get(container_id)
            exec_result = container.exec_run(
                command,
                workdir=workdir,
                demux=True
            )

            # Combine stdout and stderr
            stdout = exec_result.output[0] if exec_result.output[0] else b""
            stderr = exec_result.output[1] if exec_result.output[1] else b""
            output = (stdout + stderr).decode('utf-8')

            logger.info(f"Executed command in container {container_id[:12]}: {command}")
            return exec_result.exit_code, output

        except (DockerException, NotFound) as e:
            logger.error(f"Failed to execute command in container {container_id[:12]}: {e}")
            raise

    def write_file(
        self,
        container_id: str,
        file_path: str,
        content: str
    ) -> None:
        """
        Write a file to container.

        Args:
            container_id: Container ID
            file_path: File path in container
            content: File content

        Raises:
            DockerException: If file write fails
        """
        try:
            container = self.client.containers.get(container_id)

            # Create tar archive in memory
            tar_stream = io.BytesIO()
            tar = tarfile.open(fileobj=tar_stream, mode='w')

            # Add file to tar
            file_data = content.encode('utf-8')
            tarinfo = tarfile.TarInfo(name=os.path.basename(file_path))
            tarinfo.size = len(file_data)
            tar.addfile(tarinfo, io.BytesIO(file_data))
            tar.close()

            # Put archive in container
            tar_stream.seek(0)
            container.put_archive(
                path=os.path.dirname(file_path) or "/",
                data=tar_stream
            )

            logger.info(f"Wrote file {file_path} to container {container_id[:12]}")

        except (DockerException, NotFound) as e:
            logger.error(f"Failed to write file to container {container_id[:12]}: {e}")
            raise

    def read_file(self, container_id: str, file_path: str) -> Optional[str]:
        """
        Read a file from container.

        Args:
            container_id: Container ID
            file_path: File path in container

        Returns:
            File content or None if not found

        Raises:
            DockerException: If file read fails
        """
        try:
            container = self.client.containers.get(container_id)

            # Get file from container
            bits, stat = container.get_archive(file_path)

            # Extract content from tar
            tar_stream = io.BytesIO()
            for chunk in bits:
                tar_stream.write(chunk)
            tar_stream.seek(0)

            tar = tarfile.open(fileobj=tar_stream)
            member = tar.next()
            if member:
                content = tar.extractfile(member).read().decode('utf-8')
                tar.close()
                return content

            return None

        except NotFound:
            logger.warning(f"File {file_path} not found in container {container_id[:12]}")
            return None
        except (DockerException, APIError) as e:
            logger.error(f"Failed to read file from container {container_id[:12]}: {e}")
            raise

    def list_directory(
        self,
        container_id: str,
        path: str = "/app"
    ) -> List[Dict[str, Any]]:
        """
        List contents of a directory in container.

        Args:
            container_id: Container ID
            path: Directory path

        Returns:
            List of file/directory info dicts

        Raises:
            DockerException: If directory listing fails
        """
        try:
            # Execute ls command to list directory
            exit_code, output = self.exec_command(
                container_id,
                f"ls -lA {path}",
                workdir="/"
            )

            if exit_code != 0:
                return []

            # Parse ls output
            files = []
            for line in output.strip().split('\n')[1:]:  # Skip 'total' line
                if not line.strip():
                    continue

                parts = line.split(None, 8)
                if len(parts) < 9:
                    continue

                files.append({
                    "name": parts[8],
                    "type": "directory" if parts[0].startswith('d') else "file",
                    "size": int(parts[4]) if not parts[0].startswith('d') else 0,
                    "permissions": parts[0]
                })

            return files

        except (DockerException, NotFound) as e:
            logger.error(f"Failed to list directory in container {container_id[:12]}: {e}")
            raise

    def get_container_status(self, container_id: str) -> str:
        """
        Get container status.

        Args:
            container_id: Container ID

        Returns:
            Container status string

        Raises:
            DockerException: If status check fails
        """
        try:
            container = self.client.containers.get(container_id)
            return container.status
        except (DockerException, NotFound) as e:
            logger.error(f"Failed to get container status {container_id[:12]}: {e}")
            raise

    def get_container_port_mapping(self, container_id: str, container_port: int = 8000) -> Optional[int]:
        """
        Get the host port mapped to a container port.

        Args:
            container_id: Container ID
            container_port: Container port to check (default: 8000)

        Returns:
            Host port if mapping exists, None otherwise
        """
        try:
            container = self.client.containers.get(container_id)
            port_key = f"{container_port}/tcp"

            # Get port bindings from container attributes
            if hasattr(container, 'attrs') and 'NetworkSettings' in container.attrs:
                ports = container.attrs.get('NetworkSettings', {}).get('Ports', {})
                if port_key in ports:
                    bindings = ports[port_key]
                    if bindings and len(bindings) > 0:
                        host_port = bindings[0].get('HostPort')
                        if host_port:
                            return int(host_port)

            return None
        except (DockerException, NotFound) as e:
            logger.warning(f"Failed to get port mapping for container {container_id[:12]}: {e}")
            return None
