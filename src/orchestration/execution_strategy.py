from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional
import shutil
import logging
import subprocess
import os
from src.orchestration.docker_manager import DockerManager

logger = logging.getLogger(__name__)

class ExecutionStrategy(ABC):
    """
    Abstract base class for tool execution strategies.
    """
    
    @abstractmethod
    def is_available(self, tool_name: str) -> bool:
        """Check if the tool is available in this strategy."""
        pass

    @abstractmethod
    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        """
        Execute the tool.
        
        Args:
            tool_name: Name of the tool (e.g., 'sherlock')
            command: Command arguments list
            config: Configuration dictionary (including proxies)
            
        Returns:
            Output string (stdout/stderr)
        """
        pass

class DockerExecutionStrategy(ExecutionStrategy):
    """
    Executes tools using Docker containers.
    """
    
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        # Map generic tool names to Docker image names
        self.tool_image_map = {
            "sherlock": "sherlock/sherlock",
            "theharvester": "secsi/theharvester",
            "h8mail": "khast3x/h8mail",
            "holehe": "holehe", # Placeholder, need actual image if different
            "phoneinfoga": "sundowndev/phoneinfoga",
            "sublist3r": "sublist3r", # Placeholder
            "photon": "photon", # Placeholder
            "exiftool": "exiftool" # Placeholder
        }

    def is_available(self, tool_name: str) -> bool:
        return self.docker_manager.is_available and tool_name in self.tool_image_map

    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        if not self.is_available(tool_name):
            raise RuntimeError(f"Tool {tool_name} not available in Docker mode")
            
        image_name = self.tool_image_map[tool_name]
        
        # Construct environment from config if present
        environment = {}
        if "proxy_url" in config:
            # SECURITY: Validate proxy URL to prevent injection
            proxy_url = config["proxy_url"]
            if not self._is_valid_proxy_url(proxy_url):
                logger.warning(f"Invalid proxy URL format: {proxy_url}. Skipping proxy configuration.")
            else:
                environment["HTTP_PROXY"] = proxy_url
                environment["HTTPS_PROXY"] = proxy_url
                environment["ALL_PROXY"] = proxy_url
        
        return self.docker_manager.run_container(
            image_name=image_name,
            command=command,
            environment=environment
        )
    
    def _is_valid_proxy_url(self, url: str) -> bool:
        """
        Validate proxy URL to prevent injection attacks.
        
        SECURITY: Ensures proxy URL is well-formed and uses allowed schemes.
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Must have a valid scheme
            if parsed.scheme not in ['http', 'https', 'socks4', 'socks5', 'socks4h', 'socks5h']:
                logger.warning(f"Invalid proxy scheme: {parsed.scheme}")
                return False
            
            # Must have a netloc (hostname:port)
            if not parsed.netloc:
                logger.warning("Proxy URL missing hostname")
                return False
            
            # Should not contain path, params, query, or fragment (suspicious)
            if any([parsed.path and parsed.path != '/', parsed.params, parsed.query, parsed.fragment]):
                logger.warning("Proxy URL contains suspicious components")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating proxy URL: {e}")
            return False

class NativeExecutionStrategy(ExecutionStrategy):
    """
    Executes tools using locally installed binaries.
    """
    
    def __init__(self):
        pass

    def is_available(self, tool_name: str) -> bool:
        """Check if the tool is in the system PATH."""
        return shutil.which(tool_name) is not None

    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        if not self.is_available(tool_name):
            raise RuntimeError(f"Tool {tool_name} not found locally")
            
        # Prepare environment
        env = os.environ.copy()
        if "proxy_url" in config:
            # SECURITY: Validate proxy URL to prevent injection
            proxy_url = config["proxy_url"]
            if not self._is_valid_proxy_url(proxy_url):
                logger.warning(f"Invalid proxy URL format: {proxy_url}. Skipping proxy configuration.")
            else:
                env["HTTP_PROXY"] = proxy_url
                env["HTTPS_PROXY"] = proxy_url
                env["ALL_PROXY"] = proxy_url

        logger.info(f"Executing native command: {tool_name} {' '.join(command)}")
        
        try:
            # Prepend tool name to command if it's not already there?
            # The adapters usually provide the full command args, but not the executable?
            # Let's assume 'command' is just the arguments.
            full_cmd = [tool_name] + command
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                env=env,
                check=False # We handle return codes manually if needed
            )
            
            if result.returncode != 0:
                logger.warning(f"Native tool {tool_name} exited with code {result.returncode}")
                
            # Combine stdout and stderr
            return result.stdout + "\n" + result.stderr
            
        except Exception as e:
            logger.error(f"Native execution failed: {e}")
            raise
    
    def _is_valid_proxy_url(self, url: str) -> bool:
        """
        Validate proxy URL to prevent injection attacks.
        
        SECURITY: Ensures proxy URL is well-formed and uses allowed schemes.
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Must have a valid scheme
            if parsed.scheme not in ['http', 'https', 'socks4', 'socks5', 'socks4h', 'socks5h']:
                logger.warning(f"Invalid proxy scheme: {parsed.scheme}")
                return False
            
            # Must have a netloc (hostname:port)
            if not parsed.netloc:
                logger.warning("Proxy URL missing hostname")
                return False
            
            # Should not contain path, params, query, or fragment (suspicious)
            if any([parsed.path and parsed.path != '/', parsed.params, parsed.query, parsed.fragment]):
                logger.warning("Proxy URL contains suspicious components")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating proxy URL: {e}")
            return False

class HybridExecutionStrategy(ExecutionStrategy):
    """
    Auto-detects availability: prefers Native, falls back to Docker.
    """
    
    def __init__(self, docker_strategy: DockerExecutionStrategy, native_strategy: NativeExecutionStrategy):
        self.docker = docker_strategy
        self.native = native_strategy

    def is_available(self, tool_name: str) -> bool:
        return self.native.is_available(tool_name) or self.docker.is_available(tool_name)

    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        if self.native.is_available(tool_name):
            logger.info(f"Hybrid: Using native {tool_name}")
            return self.native.execute(tool_name, command, config)
        elif self.docker.is_available(tool_name):
            logger.info(f"Hybrid: Falling back to Docker for {tool_name}")
            return self.docker.execute(tool_name, command, config)
        else:
            raise RuntimeError(f"Tool {tool_name} not available natively or in Docker")
