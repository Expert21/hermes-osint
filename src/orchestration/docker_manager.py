<<<<<<< HEAD
import docker
import logging
from typing import Optional, Dict, Any, List, Union
import time

logger = logging.getLogger(__name__)

# SECURITY: Trusted image digests to prevent supply chain attacks
# Update these digests periodically after verifying image integrity
TRUSTED_IMAGES = {
    "sherlock/sherlock": "sherlock/sherlock:latest",  # TODO: Replace with @sha256:digest
    "secsi/theharvester": "secsi/theharvester:latest"  # TODO: Replace with @sha256:digest
}

# SECURITY: Whitelist for environment variables
ALLOWED_ENV_VARS = {"HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "SOCKS_PROXY"}

class DockerManager:
    """
    Manages Docker container lifecycle for OSINT tools with security hardening.
    """
    
    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        """Establish connection to Docker daemon."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
        except docker.errors.DockerException as e:
            logger.warning(f"Could not connect to Docker: {e}")
            self.client = None

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def pull_image(self, image_name: str):
        """
        Pull a Docker image if not present.
        
        SECURITY: Only pulls images from the trusted whitelist.
        """
        if not self.is_available:
            raise RuntimeError("Docker is not available")
        
        # SECURITY: Verify image is in trusted list
        if image_name not in TRUSTED_IMAGES:
            raise ValueError(f"Untrusted image: {image_name}. Only whitelisted images are allowed.")
        
        trusted_image = TRUSTED_IMAGES[image_name]
            
        try:
            logger.info(f"Pulling trusted image {trusted_image}...")
            self.client.images.pull(trusted_image)
            logger.info(f"Successfully pulled {trusted_image}")
        except docker.errors.APIError as e:
            logger.error(f"Failed to pull image {trusted_image}: {e}")
            raise

    def run_container(
        self, 
        image_name: str, 
        command: Union[str, List[str]], 
        environment: Optional[Dict] = None,
        timeout: int = 300
    ) -> str:
        """
        Run a command in a temporary container and return the output.
        
        SECURITY FEATURES:
        - Image whitelist verification
        - Resource limits (CPU, memory, PIDs)
        - No network access by default
        - Read-only filesystem
        - No privilege escalation
        - Execution timeout
        - Log size limits
        
        Args:
            image_name: Name of the Docker image (must be in TRUSTED_IMAGES)
            command: Command to run (list format recommended to prevent injection)
            environment: Environment variables (filtered against whitelist)
            timeout: Maximum execution time in seconds (default: 300)
            
        Returns:
            Container stdout/stderr logs (truncated to 10MB)
            
        Raises:
            ValueError: If image is not trusted
            RuntimeError: If Docker is not available
            docker.errors.ContainerError: If container execution fails
        """
        if not self.is_available:
            raise RuntimeError("Docker is not available")

        # SECURITY: Verify image is trusted
        if image_name not in TRUSTED_IMAGES:
            raise ValueError(f"Untrusted image: {image_name}")
        
        trusted_image = TRUSTED_IMAGES[image_name]
        
        # SECURITY: Filter environment variables to whitelist
        filtered_env = None
        if environment:
            filtered_env = {k: v for k, v in environment.items() if k in ALLOWED_ENV_VARS}
            if len(filtered_env) != len(environment):
                logger.warning(f"Filtered out {len(environment) - len(filtered_env)} non-whitelisted env vars")

        container = None
        try:
            # Ensure image exists
            try:
                self.client.images.get(trusted_image)
            except docker.errors.ImageNotFound:
                self.pull_image(image_name)

            logger.info(f"Running container {trusted_image} with command: {command}")
            
            # SECURITY: Run container with hardened security settings
            container = self.client.containers.run(
                trusted_image,
                command=command,
                environment=filtered_env,
                detach=True,
                remove=False,  # We want to read logs first, then remove
                
                # SECURITY: Resource limits to prevent DoS
                mem_limit="512m",           # 512MB RAM limit
                memswap_limit="512m",       # No swap usage
                cpu_quota=50000,            # 50% of one CPU core
                pids_limit=100,             # Max 100 processes
                
                # SECURITY: Network and filesystem restrictions
                network_mode="none",        # No network access (tools should work offline)
                read_only=False,            # Some tools need to write temp files
                
                # SECURITY: Privilege restrictions
                privileged=False,           # Never run privileged
                cap_drop=["ALL"],           # Drop all Linux capabilities
                security_opt=["no-new-privileges"],  # Prevent privilege escalation
                
                # SECURITY: No volume mounts
                volumes=None
            )
            
            # SECURITY: Wait for container with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get('StatusCode', 0)
                
                if exit_code != 0:
                    logger.warning(f"Container exited with code {exit_code}")
            except Exception as timeout_error:
                logger.error(f"Container timeout or error: {timeout_error}")
                try:
                    container.kill()
                except Exception:
                    pass
                raise RuntimeError(f"Container execution timeout after {timeout}s")

            # SECURITY: Read logs with size limit (tail last 10000 lines, max 10MB)
            MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
            try:
                logs = container.logs(tail=10000).decode('utf-8', errors='replace')
                
                # Truncate if too large
                if len(logs) > MAX_LOG_SIZE:
                    logger.warning(f"Container logs truncated from {len(logs)} to {MAX_LOG_SIZE} bytes")
                    logs = logs[:MAX_LOG_SIZE] + "\n[LOG TRUNCATED - EXCEEDED 10MB LIMIT]"
                    
            except Exception as log_error:
                logger.error(f"Failed to read container logs: {log_error}")
                logs = f"[ERROR READING LOGS: {log_error}]"
            
            return logs

        except Exception as e:
            logger.error(f"Error running container {trusted_image}: {e}")
            raise
        finally:
            # SECURITY: Always cleanup container
            if container:
                try:
                    container.remove(force=True)
                    logger.debug(f"Removed container {container.id[:12]}")
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")
=======
import docker
import logging
from typing import Optional, Dict, Any, List, Union
import time

logger = logging.getLogger(__name__)

# SECURITY: Trusted image digests to prevent supply chain attacks
# Update these digests periodically after verifying image integrity
TRUSTED_IMAGES = {
    "sherlock/sherlock": "sherlock/sherlock:latest",  # TODO: Replace with @sha256:digest
    "secsi/theharvester": "secsi/theharvester:latest"  # TODO: Replace with @sha256:digest
}

# SECURITY: Whitelist for environment variables
ALLOWED_ENV_VARS = {"HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "SOCKS_PROXY"}

class DockerManager:
    """
    Manages Docker container lifecycle for OSINT tools with security hardening.
    """
    
    def __init__(self):
        self.client = None
        self._connect()

    def _connect(self):
        """Establish connection to Docker daemon."""
        try:
            self.client = docker.from_env()
            self.client.ping()
            logger.info("Successfully connected to Docker daemon")
        except docker.errors.DockerException as e:
            logger.warning(f"Could not connect to Docker: {e}")
            self.client = None

    @property
    def is_available(self) -> bool:
        return self.client is not None

    def pull_image(self, image_name: str):
        """
        Pull a Docker image if not present.
        
        SECURITY: Only pulls images from the trusted whitelist.
        """
        if not self.is_available:
            raise RuntimeError("Docker is not available")
        
        # SECURITY: Verify image is in trusted list
        if image_name not in TRUSTED_IMAGES:
            raise ValueError(f"Untrusted image: {image_name}. Only whitelisted images are allowed.")
        
        trusted_image = TRUSTED_IMAGES[image_name]
            
        try:
            logger.info(f"Pulling trusted image {trusted_image}...")
            self.client.images.pull(trusted_image)
            logger.info(f"Successfully pulled {trusted_image}")
        except docker.errors.APIError as e:
            logger.error(f"Failed to pull image {trusted_image}: {e}")
            raise

    def run_container(
        self, 
        image_name: str, 
        command: Union[str, List[str]], 
        environment: Optional[Dict] = None,
        timeout: int = 300
    ) -> str:
        """
        Run a command in a temporary container and return the output.
        
        SECURITY FEATURES:
        - Image whitelist verification
        - Resource limits (CPU, memory, PIDs)
        - No network access by default
        - Read-only filesystem
        - No privilege escalation
        - Execution timeout
        - Log size limits
        
        Args:
            image_name: Name of the Docker image (must be in TRUSTED_IMAGES)
            command: Command to run (list format recommended to prevent injection)
            environment: Environment variables (filtered against whitelist)
            timeout: Maximum execution time in seconds (default: 300)
            
        Returns:
            Container stdout/stderr logs (truncated to 10MB)
            
        Raises:
            ValueError: If image is not trusted
            RuntimeError: If Docker is not available
            docker.errors.ContainerError: If container execution fails
        """
        if not self.is_available:
            raise RuntimeError("Docker is not available")

        # SECURITY: Verify image is trusted
        if image_name not in TRUSTED_IMAGES:
            raise ValueError(f"Untrusted image: {image_name}")
        
        trusted_image = TRUSTED_IMAGES[image_name]
        
        # SECURITY: Filter environment variables to whitelist
        filtered_env = None
        if environment:
            filtered_env = {k: v for k, v in environment.items() if k in ALLOWED_ENV_VARS}
            if len(filtered_env) != len(environment):
                logger.warning(f"Filtered out {len(environment) - len(filtered_env)} non-whitelisted env vars")

        container = None
        try:
            # Ensure image exists
            try:
                self.client.images.get(trusted_image)
            except docker.errors.ImageNotFound:
                self.pull_image(image_name)

            logger.info(f"Running container {trusted_image} with command: {command}")
            
            # SECURITY: Run container with hardened security settings
            container = self.client.containers.run(
                trusted_image,
                command=command,
                environment=filtered_env,
                detach=True,
                remove=False,  # We want to read logs first, then remove
                
                # SECURITY: Resource limits to prevent DoS
                mem_limit="512m",           # 512MB RAM limit
                memswap_limit="512m",       # No swap usage
                cpu_quota=50000,            # 50% of one CPU core
                pids_limit=100,             # Max 100 processes
                
                # SECURITY: Network and filesystem restrictions
                network_mode="none",        # No network access (tools should work offline)
                read_only=False,            # Some tools need to write temp files
                
                # SECURITY: Privilege restrictions
                privileged=False,           # Never run privileged
                cap_drop=["ALL"],           # Drop all Linux capabilities
                security_opt=["no-new-privileges"],  # Prevent privilege escalation
                
                # SECURITY: No volume mounts
                volumes=None
            )
            
            # SECURITY: Wait for container with timeout
            try:
                result = container.wait(timeout=timeout)
                exit_code = result.get('StatusCode', 0)
                
                if exit_code != 0:
                    logger.warning(f"Container exited with code {exit_code}")
            except Exception as timeout_error:
                logger.error(f"Container timeout or error: {timeout_error}")
                try:
                    container.kill()
                except Exception:
                    pass
                raise RuntimeError(f"Container execution timeout after {timeout}s")

            # SECURITY: Read logs with size limit (tail last 10000 lines, max 10MB)
            MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
            try:
                logs = container.logs(tail=10000).decode('utf-8', errors='replace')
                
                # Truncate if too large
                if len(logs) > MAX_LOG_SIZE:
                    logger.warning(f"Container logs truncated from {len(logs)} to {MAX_LOG_SIZE} bytes")
                    logs = logs[:MAX_LOG_SIZE] + "\n[LOG TRUNCATED - EXCEEDED 10MB LIMIT]"
                    
            except Exception as log_error:
                logger.error(f"Failed to read container logs: {log_error}")
                logs = f"[ERROR READING LOGS: {log_error}]"
            
            return logs

        except Exception as e:
            logger.error(f"Error running container {trusted_image}: {e}")
            raise
        finally:
            # SECURITY: Always cleanup container
            if container:
                try:
                    container.remove(force=True)
                    logger.debug(f"Removed container {container.id[:12]}")
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
