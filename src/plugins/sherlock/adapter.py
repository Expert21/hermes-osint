
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator
from src.core.entities import ToolResult, Entity

class SherlockAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "sherlock"

    def can_run(self) -> bool:
        """Check if Sherlock is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Run Sherlock against a username.
        
        Args:
            target: Username to search (validated for safety)
            config: Configuration dictionary
            
        Returns:
            ToolResult containing the structured findings
            
        STEALTH NOTE: Sherlock makes direct HTTP requests to 300+ websites
        to check for username existence. Incompatible with stealth mode.
        """
        # STEALTH: Skip in stealth mode - makes direct contact with target websites
        if config.get("stealth_mode", False):
            return ToolResult(
                tool=self.tool_name,
                entities=[],
                raw_output="",
                metadata={"skipped": True, "reason": "Sherlock makes direct contact - incompatible with stealth mode"}
            )
        
        # SECURITY: Validate and sanitize username to prevent command injection
        try:
            sanitized_target = InputValidator.sanitize_username(target, max_length=100)
        except ValueError as e:
            raise ValueError(f"Invalid target username: {e}")
        
        # Use list format to prevent shell injection
        command = [sanitized_target, "--print-found"]
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> ToolResult:
        """
        Parse Sherlock output.
        Look for lines starting with '[+]'.
        """
        entities = []
        for line in output.splitlines():
            if "[+]" in line:
                # Format: [+] Service: URL
                parts = line.split(":", 1)
                if len(parts) == 2:
                    service = parts[0].replace("[+]", "").strip()
                    url = parts[1].strip()
                    
                    # Create Entity for each found account
                    entity = Entity(
                        type="account",
                        value=url,
                        source="sherlock",
                        metadata={
                            "service": service,
                            "url": url
                        }
                    )
                    entities.append(entity)
        
        return ToolResult(
            tool="sherlock",
            entities=entities,
            raw_output=output
        )
