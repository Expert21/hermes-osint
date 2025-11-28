<<<<<<< HEAD
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.docker_manager import DockerManager
from src.core.input_validator import InputValidator

class TheHarvesterAdapter(ToolAdapter):
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.image = "secsi/theharvester"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run TheHarvester against a domain.
        
        Args:
            target: Domain to search (validated for safety)
            config: Configuration dictionary
            
        Returns:
            Parsed results from TheHarvester
        """
        # SECURITY: Validate domain to prevent command injection
        try:
            sanitized_target = InputValidator.validate_domain(target)
        except ValueError as e:
            raise ValueError(f"Invalid target domain: {e}")
        
        # Validate sources parameter
        sources = config.get("sources", "all")
        if not re.match(r'^[a-z,]+$', sources):
            sources = "all"  # Fallback to safe default
        
        # Use list format to prevent shell injection
        command = ["-d", sanitized_target, "-b", sources]
        
        output = self.docker_manager.run_container(self.image, command)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse TheHarvester output.
        
        SECURITY: Protects against ReDoS by limiting output size before regex processing.
        """
        emails = []
        hosts = []
        
        # SECURITY: Limit output size to prevent ReDoS attacks
        MAX_OUTPUT_SIZE = 1 * 1024 * 1024  # 1MB
        if len(output) > MAX_OUTPUT_SIZE:
            logger.warning(f"Output truncated from {len(output)} to {MAX_OUTPUT_SIZE} bytes for parsing")
            output = output[:MAX_OUTPUT_SIZE]
        
        # Simple regex for emails (safe pattern, no catastrophic backtracking)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        try:
            # Use finditer with limit to prevent excessive memory usage
            email_matches = re.finditer(email_pattern, output)
            emails = list(set([match.group() for match in email_matches]))[:1000]  # Limit to 1000 emails
        except Exception as e:
            logger.error(f"Error parsing emails: {e}")
            emails = []
        
        # Basic host parsing (this might need refinement based on actual output)
        # TheHarvester output varies by source, but often lists "IP: Host" or just hosts
        
        return {
            "tool": "theharvester", 
            "emails": emails, 
            "hosts": hosts,  # Placeholder for better host parsing
            "raw_output": output[:10000]  # Only include first 10KB of raw output in results
        }
=======
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.docker_manager import DockerManager
from src.core.input_validator import InputValidator

class TheHarvesterAdapter(ToolAdapter):
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.image = "secsi/theharvester"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run TheHarvester against a domain.
        
        Args:
            target: Domain to search (validated for safety)
            config: Configuration dictionary
            
        Returns:
            Parsed results from TheHarvester
        """
        # SECURITY: Validate domain to prevent command injection
        try:
            sanitized_target = InputValidator.validate_domain(target)
        except ValueError as e:
            raise ValueError(f"Invalid target domain: {e}")
        
        # Validate sources parameter
        sources = config.get("sources", "all")
        if not re.match(r'^[a-z,]+$', sources):
            sources = "all"  # Fallback to safe default
        
        # Use list format to prevent shell injection
        command = ["-d", sanitized_target, "-b", sources]
        
        output = self.docker_manager.run_container(self.image, command)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse TheHarvester output.
        
        SECURITY: Protects against ReDoS by limiting output size before regex processing.
        """
        emails = []
        hosts = []
        
        # SECURITY: Limit output size to prevent ReDoS attacks
        MAX_OUTPUT_SIZE = 1 * 1024 * 1024  # 1MB
        if len(output) > MAX_OUTPUT_SIZE:
            logger.warning(f"Output truncated from {len(output)} to {MAX_OUTPUT_SIZE} bytes for parsing")
            output = output[:MAX_OUTPUT_SIZE]
        
        # Simple regex for emails (safe pattern, no catastrophic backtracking)
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        try:
            # Use finditer with limit to prevent excessive memory usage
            email_matches = re.finditer(email_pattern, output)
            emails = list(set([match.group() for match in email_matches]))[:1000]  # Limit to 1000 emails
        except Exception as e:
            logger.error(f"Error parsing emails: {e}")
            emails = []
        
        # Basic host parsing (this might need refinement based on actual output)
        # TheHarvester output varies by source, but often lists "IP: Host" or just hosts
        
        return {
            "tool": "theharvester", 
            "emails": emails, 
            "hosts": hosts,  # Placeholder for better host parsing
            "raw_output": output[:10000]  # Only include first 10KB of raw output in results
        }
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
