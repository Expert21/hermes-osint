# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

from typing import Dict, Any
import logging
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator

logger = logging.getLogger(__name__)

class SubfinderAdapter(ToolAdapter):
    """
    Adapter for Subfinder (Subdomain Discovery).
    ProjectDiscovery's fast passive subdomain enumeration tool.
    """

    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "subfinder"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Subfinder against a domain.
        
        Args:
            target: Domain name to enumerate subdomains for
            config: Configuration dictionary
            
        Returns:
            Parsed results from Subfinder
        """
        # SECURITY: Validate domain
        try:
            sanitized_target = InputValidator.validate_domain(target)
        except ValueError as e:
            raise ValueError(f"Invalid domain: {e}")
        
        # Subfinder command structure:
        # subfinder -d <domain> -silent -json
        # -silent: only output subdomains
        # -json: output in JSON format for easier parsing
        command = ["-d", sanitized_target, "-silent"]
        
        # Add JSON output if we want structured data
        if config.get("json_output", True):
            command.append("-json")
        
        # Add recursive enumeration if configured
        if config.get("recursive", False):
            command.append("-recursive")
        
        # Add all sources flag
        if config.get("all_sources", False):
            command.append("-all")
        
        try:
            logger.info(f"Executing subfinder for domain: {sanitized_target}")
            output = self.execution_strategy.execute(self.tool_name, command, config)
            return self.parse_results(output, config.get("json_output", True))
        except Exception as e:
            logger.error(f"Subfinder execution failed: {e}")
            return {"error": str(e), "tool": "subfinder"}

    def parse_results(self, output: str, json_output: bool = True) -> Dict[str, Any]:
        """
        Parse Subfinder output.
        
        Args:
            output: Raw output from subfinder
            json_output: Whether output is in JSON format
        """
        results = {
            "tool": "subfinder",
            "subdomains": [],
            "raw_output": output[:10000]  # Limit raw output to 10KB
        }
        
        try:
            if json_output:
                # Parse JSON output (one JSON object per line)
                import json
                for line in output.splitlines():
                    line = line.strip()
                    if line.startswith("{") and line.endswith("}"):
                        try:
                            data = json.loads(line)
                            # Subfinder JSON format: {"host": "subdomain.example.com", "source": "..."}
                            if "host" in data:
                                results["subdomains"].append({
                                    "subdomain": data["host"],
                                    "source": data.get("source", "unknown")
                                })
                        except json.JSONDecodeError:
                            continue
            else:
                # Parse plain text output (one subdomain per line)
                for line in output.splitlines():
                    line = line.strip()
                    # Filter out empty lines and potential error messages
                    if line and not line.startswith("[") and "." in line:
                        results["subdomains"].append({
                            "subdomain": line,
                            "source": "unknown"
                        })
            
            # Deduplicate subdomains
            seen = set()
            unique_subdomains = []
            for item in results["subdomains"]:
                subdomain = item["subdomain"]
                if subdomain not in seen:
                    seen.add(subdomain)
                    unique_subdomains.append(item)
            
            results["subdomains"] = unique_subdomains
            results["count"] = len(unique_subdomains)
            
        except Exception as e:
            logger.warning(f"Failed to parse subfinder output: {e}")
        
        return results
