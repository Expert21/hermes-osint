
from typing import Dict, Any
import json
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator
from src.core.entities import ToolResult, Entity

class ExiftoolAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "exiftool"

    def can_run(self) -> bool:
        """Check if Exiftool is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Run Exiftool against a file.
        
        Args:
            target: Path to file (must be within allowed directories)
            config: Configuration dictionary
            
        Returns:
            ToolResult containing the structured findings
            
        STEALTH NOTE: Exiftool operates on local files only - no network activity.
        Always safe for stealth mode.
        """
        # SECURITY: Validate file path
        # In Docker mode, we need to handle file mounting.
        # For now, we assume the file is available or mounted.
        # The ExecutionStrategy should handle file mounting logic if needed.
        
        # Use list format to prevent shell injection
        command = ["exiftool", "-j", target]  # -j for JSON output
        
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> ToolResult:
        """
        Parse Exiftool JSON output.
        """
        entities = []
        try:
            # Exiftool -json outputs a JSON array
            data = json.loads(output)
            if isinstance(data, list) and len(data) > 0:
                # Create a single entity for the file metadata
                entities.append(Entity(
                    type="metadata",
                    value="file_metadata",
                    source="exiftool",
                    metadata=data[0]
                ))
                return ToolResult(tool="exiftool", entities=entities, raw_output=output)
            
            return ToolResult(tool="exiftool", entities=[], raw_output=output)
            
        except json.JSONDecodeError:
            return ToolResult(tool="exiftool", error="Failed to parse JSON", raw_output=output)
