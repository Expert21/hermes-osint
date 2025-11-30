# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

from typing import Dict, Any, List, Optional
import logging
import json
import time
import requests
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.docker_manager import DockerManager
from src.core.input_validator import InputValidator

logger = logging.getLogger(__name__)

class SearxngAdapter(ToolAdapter):
    """
    Adapter for SearXNG (Privacy-respecting metasearch engine).
    SearXNG runs as a web service in a Docker container.
    This adapter manages the container lifecycle and queries via HTTP API.
    """

    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.image = "searxng/searxng"
        self.container = None
        self.container_id = None
        self.host_port = 8888  # Port on host machine
        self.container_port = 8080  # Port inside container
        self.base_url = f"http://localhost:{self.host_port}"
        self.is_running = False

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute search query using SearXNG.
        
        Args:
            target: Search query string
            config: Configuration dictionary
            
        Returns:
            Dict containing search results
        """
        # SECURITY: Validate and sanitize search query
        try:
            # Basic validation - prevent injection attacks
            if len(target) > 500:
                raise ValueError("Search query too long (max 500 characters)")
            
            # Validate using existing method
            sanitized_query = InputValidator.validate_target_name(target)
        except ValueError as e:
            raise ValueError(f"Invalid search query: {e}")
        
        try:
            # Ensure service is running
            if not self.is_running:
                logger.info("Starting SearXNG service...")
                if not self.start_service(config):
                    return {
                        "tool": "searxng",
                        "error": "Failed to start SearXNG service",
                        "results": []
                    }
            
            # Query the API
            logger.info(f"Executing SearXNG search for: {sanitized_query}")
            results = self.query_api(sanitized_query, config)
            
            return results
            
        except Exception as e:
            logger.error(f"SearXNG execution failed: {e}")
            return {"error": str(e), "tool": "searxng", "results": []}
        finally:
            # Optionally stop service after query (for ephemeral usage)
            if config.get("ephemeral", True):
                self.stop_service()

    def start_service(self, config: Dict[str, Any]) -> bool:
        """
        Start SearXNG as a background service.
        
        Returns:
            True if service started successfully
        """
        try:
            logger.info(f"Starting SearXNG container on port {self.host_port}")
            
            # Check if Docker is available
            if not self.docker_manager.is_available:
                logger.error("Docker is not available")
                return False
            
            # Pull image if needed
            try:
                self.docker_manager.client.images.get(self.docker_manager.TRUSTED_IMAGES[self.image])
            except Exception:
                logger.info(f"Pulling SearXNG image...")
                self.docker_manager.pull_image(self.image)
            
            # Start container in detached mode
            trusted_image = self.docker_manager.TRUSTED_IMAGES[self.image]
            
            self.container = self.docker_manager.client.containers.run(
                image=trusted_image,
                detach=True,
                ports={f"{self.container_port}/tcp": self.host_port},
                remove=False,  # We'll remove it manually
                name=f"hermes-searxng-{int(time.time())}",
                environment={
                    "SEARXNG_BASE_URL": f"http://localhost:{self.host_port}/",
                },
                # Security settings
                cap_drop=["ALL"],
                security_opt=["no-new-privileges"],
                mem_limit="512m",
                memswap_limit="512m",
            )
            
            self.container_id = self.container.id[:12]
            logger.info(f"Started SearXNG container: {self.container_id}")
            
            # Wait for service to be ready (with timeout)
            max_wait = 30  # seconds
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                try:
                    # Try to connect to the service
                    response = requests.get(
                        f"{self.base_url}/",
                        timeout=2
                    )
                    if response.status_code == 200:
                        logger.info("SearXNG service is ready")
                        self.is_running = True
                        return True
                except requests.exceptions.RequestException:
                    # Service not ready yet
                    time.sleep(1)
                    continue
            
            logger.error("SearXNG service failed to start within timeout")
            self.stop_service()
            return False
            
        except Exception as e:
            logger.error(f"Failed to start SearXNG service: {e}")
            self.stop_service()
            return False

    def stop_service(self) -> bool:
        """
        Stop the SearXNG service.
        
        Returns:
            True if service stopped successfully
        """
        try:
            if self.container:
                logger.info(f"Stopping SearXNG container: {self.container_id}")
                self.container.stop(timeout=5)
                self.container.remove(force=True)
                logger.info("SearXNG container stopped and removed")
                self.container = None
                self.container_id = None
                self.is_running = False
                return True
        except Exception as e:
            logger.warning(f"Failed to stop SearXNG service: {e}")
            return False
        
        return True

    def query_api(self, query: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query the SearXNG API.
        
        Args:
            query: Search query
            config: Configuration options
            
        Returns:
            Parsed search results
        """
        try:
            # SearXNG API endpoint
            search_url = f"{self.base_url}/search"
            
            # Build query parameters
            params = {
                "q": query,
                "format": "json",
                "categories": config.get("categories", "general"),
                "language": config.get("language", "en"),
                "pageno": config.get("page", 1),
            }
            
            # Add time range if specified
            if "time_range" in config:
                params["time_range"] = config["time_range"]
            
            # Make request with timeout
            logger.debug(f"Querying SearXNG: {search_url} with params: {params}")
            response = requests.get(
                search_url,
                params=params,
                timeout=30,
                headers={
                    "User-Agent": "Hermes-OSINT/2.0"
                }
            )
            
            response.raise_for_status()
            
            # Parse JSON response
            data = response.json()
            
            return self.parse_results(data, query)
            
        except requests.exceptions.Timeout:
            logger.error("SearXNG API request timed out")
            return {"error": "Request timed out", "tool": "searxng", "results": []}
        except requests.exceptions.RequestException as e:
            logger.error(f"SearXNG API request failed: {e}")
            return {"error": str(e), "tool": "searxng", "results": []}
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SearXNG JSON response: {e}")
            return {"error": "Invalid JSON response", "tool": "searxng", "results": []}

    def parse_results(self, data: Dict[str, Any], query: str) -> Dict[str, Any]:
        """
        Parse SearXNG API response.
        
        Args:
            data: JSON response from SearXNG API
            query: Original search query
        """
        results = {
            "tool": "searxng",
            "query": query,
            "search_results": [],
            "suggestions": [],
            "number_of_results": 0,
        }
        
        try:
            # Extract search results
            if "results" in data:
                for result in data["results"]:
                    results["search_results"].append({
                        "title": result.get("title", ""),
                        "url": result.get("url", ""),
                        "content": result.get("content", ""),
                        "engine": result.get("engine", "unknown"),
                        "score": result.get("score", 0),
                        "category": result.get("category", "general"),
                    })
            
            # Extract suggestions if available
            if "suggestions" in data:
                results["suggestions"] = data["suggestions"]
            
            # Extract metadata
            results["number_of_results"] = data.get("number_of_results", len(results["search_results"]))
            
            # Limit results to prevent excessive data
            max_results = 100
            if len(results["search_results"]) > max_results:
                logger.info(f"Limiting results from {len(results['search_results'])} to {max_results}")
                results["search_results"] = results["search_results"][:max_results]
            
            results["count"] = len(results["search_results"])
            
        except Exception as e:
            logger.warning(f"Failed to parse SearXNG results: {e}")
            results["error"] = f"Parsing error: {str(e)}"
        
        return results

    def __del__(self):
        """Cleanup: ensure container is stopped when adapter is destroyed."""
        if self.is_running:
            self.stop_service()
