# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator

class HoleheAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "holehe"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Holehe against an email.
        
        Args:
            target: Email address
            config: Configuration dictionary
            
        Returns:
            Parsed results from Holehe
        """
        # SECURITY: Validate email
        try:
            sanitized_target = InputValidator.validate_email(target)
        except ValueError as e:
            raise ValueError(f"Invalid email: {e}")
        
        # Use list format to prevent shell injection
        command = [sanitized_target, "--only-used", "--no-color"]
        
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse Holehe output.
        """
        results = []
        for line in output.splitlines():
            if "[+]" in line:
                # Format: [+] Service
                service = line.replace("[+]", "").strip()
                results.append({"service": service, "status": "used"})
        
        return {"tool": "holehe", "results": results, "raw_output": output}
