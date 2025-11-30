# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator

class PhoneInfogaAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "phoneinfoga"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run PhoneInfoga against a phone number.
        
        Args:
            target: Phone number
            config: Configuration dictionary
            
        Returns:
            Parsed results from PhoneInfoga
        """
        # SECURITY: Validate phone number (basic check)
        # PhoneInfoga handles various formats, but we should ensure no shell chars
        if not re.match(r'^\+?[0-9\-\s]+$', target):
             raise ValueError(f"Invalid phone number format: {target}")
        
        # Use list format to prevent shell injection
        command = ["scan", "-n", target, "--no-ansi"]
        
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse PhoneInfoga output.
        """
        # PhoneInfoga output is complex, we'll extract key info
        # Ideally we'd use JSON output but CLI often outputs text
        results = {}
        
        # Simple text parsing for now
        lines = output.splitlines()
        for line in lines:
            if "Country:" in line:
                results['country'] = line.split("Country:")[1].strip()
            elif "Carrier:" in line:
                results['carrier'] = line.split("Carrier:")[1].strip()
            elif "Line type:" in line:
                results['line_type'] = line.split("Line type:")[1].strip()
                
        return {"tool": "phoneinfoga", "results": results, "raw_output": output}
