<<<<<<< HEAD
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.docker_manager import DockerManager
from src.core.input_validator import InputValidator

class SherlockAdapter(ToolAdapter):
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.image = "sherlock/sherlock"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Sherlock against a username.
        
        Args:
            target: Username to search (validated for safety)
            config: Configuration dictionary
            
        Returns:
            Parsed results from Sherlock
        """
        # SECURITY: Validate and sanitize username to prevent command injection
        try:
            sanitized_target = InputValidator.sanitize_username(target, max_length=100)
        except ValueError as e:
            raise ValueError(f"Invalid target username: {e}")
        
        # Use list format to prevent shell injection
        command = [sanitized_target, "--print-found"]
        output = self.docker_manager.run_container(self.image, command)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse Sherlock output.
        Look for lines starting with '[+]'.
        """
        results = []
        for line in output.splitlines():
            if "[+]" in line:
                # Format: [+] Service: URL
                parts = line.split(":", 1)
                if len(parts) == 2:
                    service = parts[0].replace("[+]", "").strip()
                    url = parts[1].strip()
                    results.append({"service": service, "url": url})
        
        return {"tool": "sherlock", "results": results, "raw_output": output}
=======
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.docker_manager import DockerManager
from src.core.input_validator import InputValidator

class SherlockAdapter(ToolAdapter):
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.image = "sherlock/sherlock"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Sherlock against a username.
        
        Args:
            target: Username to search (validated for safety)
            config: Configuration dictionary
            
        Returns:
            Parsed results from Sherlock
        """
        # SECURITY: Validate and sanitize username to prevent command injection
        try:
            sanitized_target = InputValidator.sanitize_username(target, max_length=100)
        except ValueError as e:
            raise ValueError(f"Invalid target username: {e}")
        
        # Use list format to prevent shell injection
        command = [sanitized_target, "--print-found"]
        output = self.docker_manager.run_container(self.image, command)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse Sherlock output.
        Look for lines starting with '[+]'.
        """
        results = []
        for line in output.splitlines():
            if "[+]" in line:
                # Format: [+] Service: URL
                parts = line.split(":", 1)
                if len(parts) == 2:
                    service = parts[0].replace("[+]", "").strip()
                    url = parts[1].strip()
                    results.append({"service": service, "url": url})
        
        return {"tool": "sherlock", "results": results, "raw_output": output}
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
