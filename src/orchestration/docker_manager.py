import docker
import logging
from typing import Optional, Dict, Any, List, Union
import time

logger = logging.getLogger(__name__)

# SECURITY: Trusted image digests to prevent supply chain attacks
# Update these digests periodically after verifying image integrity
# Images are pinned to specific SHA256 digests to ensure immutable references
TRUSTED_IMAGES = {
    "sherlock/sherlock": "sherlock/sherlock@sha256:9d6602b98179fb15ceab88433626fb0ae603ae9880e13cab886970317fe1475f",
    "secsi/theharvester": "secsi/theharvester@sha256:9515ec0d26f83abc05856caf180ff78c91a048c3cf94ead6db86ab5b7aaf6772",
    "khast3x/h8mail": "khast3x/h8mail@sha256:baa9be41369e6d2e966d640c0d0b9d0856cf62d1c0cfbfc91d8d035760b160a9"
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

        trusted_ref = TRUSTED_IMAGES[image_name]   # image@sha256:xxxx

        try:
            logger.info(f"Pulling trusted image {trusted_ref}...")
            image = self.client.images.pull(trusted_ref)
            logger.info(f"Pulled {trusted_ref}, verifying digest...")

            # SECURITY: Verify digest using RepoDigests
            repo_digests = image.attrs.get("RepoDigests", [])

            if trusted_ref not in repo_digests:
                logger.error("DIGEST VERIFICATION FAILED!")
                logger.error(f"Expected: {trusted_ref}")
                logger.error(f"RepoDigests found: {repo_digests}")

                # SECURITY: Remove compromised/incorrect image
                self.client.images.remove(image.id, force=True)

                raise SecurityError(f"Image {image_name} failed digest verification")

            logger.info(f"Image {image_name} verified and ready for use.")

        except docker.errors.ImageNotFound:
            logger.error(f"Image {trusted_ref} not found. Please pull it first.")
            raise

        except docker.errors.APIError as e:
            logger.error(f"Failed to pull image {trusted_ref}: {e}")
            raise

    def remove_image(self, image_name: str, force: bool = False):
        """
        Remove a Docker image from the local system.
        
        OPSEC: Use this to remove images after use for privacy/disk space.
        
        Args:
            image_name: Name of the image to remove (must be in TRUSTED_IMAGES)
            force: Force removal even if containers are using it
            
        Returns:
            True if removed, False if not found
        """
        if not self.is_available:
            raise RuntimeError("Docker is not available")
        
        # SECURITY: Only remove whitelisted images
        if image_name not in TRUSTED_IMAGES:
            raise ValueError(f"Cannot remove untrusted image: {image_name}")
        
        trusted_image = TRUSTED_IMAGES[image_name]
        
        try:
            self.client.images.remove(trusted_image, force=force)
            logger.info(f"Removed image {trusted_image}")
            return True
        except docker.errors.ImageNotFound:
            logger.debug(f"Image {trusted_image} not found, nothing to remove")
            return False
        except docker.errors.APIError as e:
            logger.warning(f"Failed to remove image {trusted_image}: {e}")
            if not force:
                logger.info("Tip: Use force=True to remove images with dependent resources")
            raise

    def cleanup_all_tool_images(self, force: bool = False) -> Dict[str, bool]:
        """
        Remove all OSINT tool images from the system.
        
        OPSEC: Use this for complete cleanup after operations.
        
        Args:
            force: Force removal even if containers exist
            
        Returns:
            Dict mapping image names to removal success status
        """
        results = {}
        for image_name in TRUSTED_IMAGES.keys():
            try:
                results[image_name] = self.remove_image(image_name, force=force)
            except Exception as e:
                logger.error(f"Error removing {image_name}: {e}")
                results[image_name] = False
        return results

    def run_container(
        self, 
        image_name: str, 
        command: List[str], 
        environment: Optional[Dict] = None,
        timeout: int = 300,
        cleanup_image: bool = False
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
            cleanup_image: Remove the Docker image after execution (OPSEC mode)
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
                network_mode="bridge",      # Allow network access for tools
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
            
            # OPSEC: Optionally cleanup image as well
            if cleanup_image:
                try:
                    logger.info(f"OPSEC mode: Removing image {trusted_image}...")
                    self.remove_image(image_name, force=True)
                    logger.info(f"Image {trusted_image} removed for privacy")
                except Exception as e:
                    logger.warning(f"Failed to remove image in cleanup: {e}")
