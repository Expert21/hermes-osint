# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

from typing import Dict, Any
import json
import logging
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy

logger = logging.getLogger(__name__)

class H8MailAdapter(ToolAdapter):
    """
    Adapter for h8mail (Email Breach Hunting).
    """

    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "h8mail"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute h8mail against the target email.
        
        Args:
            target: Email address to check
            config: Configuration dictionary (e.g., API keys)
            
        Returns:
            Dict containing the raw results and metadata
        """
        # Construct command
        # -t: target
        # -j: json output (if supported, otherwise we parse stdout)
        # --loose: loose search (optional, maybe configurable)
        
        command = ["-t", target, "--json"]
        
        # Add API keys if provided in config
        # h8mail uses a config file usually, but can take some via CLI or env
        # For this MVP, we'll assume basic execution or env vars passed via DockerManager
        
        try:
            logger.info(f"Executing h8mail for {target}")
            output = self.execution_strategy.execute(self.tool_name, command, config)
            
            return self.parse_results(output)
            
        except Exception as e:
            logger.error(f"h8mail execution failed: {e}")
            return {"error": str(e), "tool": "h8mail"}

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse h8mail output.
        """
        results = {
            "tool": "h8mail",
            "breaches": [],
            "raw_output": output
        }
        
        try:
            # h8mail with --json might output multiple JSON objects or a list
            # It often outputs logs mixed with JSON. We need to find the JSON part.
            
            # Simple heuristic: look for lines starting with '{'
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        # Check if it looks like a breach result
                        if "target" in data and "breach" in data:
                             results["breaches"].append(data)
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.warning(f"Failed to parse h8mail output: {e}")
            
        return results
