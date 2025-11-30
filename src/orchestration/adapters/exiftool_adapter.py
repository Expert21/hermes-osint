# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

from typing import Dict, Any
import json
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator

class ExiftoolAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "exiftool"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Exiftool against a file.
        
        Args:
            target: Path to file (must be within allowed directories)
            config: Configuration dictionary
            
        Returns:
            Parsed results from Exiftool
        """
        # SECURITY: Validate file path
        # In Docker mode, we need to handle file mounting.
        # For now, we assume the file is available or mounted.
        # The ExecutionStrategy should handle file mounting logic if needed.
        
        # Use list format to prevent shell injection
        command = ["-j", target]  # -j for JSON output
        
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse Exiftool JSON output.
        """
        try:
            # Exiftool -json outputs a JSON array
            data = json.loads(output)
            if isinstance(data, list) and len(data) > 0:
                return {"tool": "exiftool", "results": data[0], "raw_output": output}
            return {"tool": "exiftool", "results": {}, "raw_output": output}
        except json.JSONDecodeError:
            return {"tool": "exiftool", "results": {}, "error": "Failed to parse JSON", "raw_output": output}
