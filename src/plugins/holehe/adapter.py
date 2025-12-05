
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator
from src.core.entities import ToolResult, Entity

class HoleheAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "holehe"

    def can_run(self) -> bool:
        """Check if Holehe is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Run Holehe against an email.
        
        Args:
            target: Email address
            config: Configuration dictionary
            
        Returns:
            ToolResult containing the structured findings
            
        STEALTH NOTE: Holehe sends "forgot password" requests to websites
        to check for email registration. Incompatible with stealth mode.
        """
        # STEALTH: Skip in stealth mode - makes direct contact with target websites
        if config.get("stealth_mode", False):
            return ToolResult(
                tool=self.tool_name,
                entities=[],
                raw_output="",
                metadata={"skipped": True, "reason": "Holehe makes direct contact - incompatible with stealth mode"}
            )
        
        # SECURITY: Validate email
        try:
            sanitized_target = InputValidator.validate_email(target)
        except ValueError as e:
            raise ValueError(f"Invalid email: {e}")
        
        # Use list format to prevent shell injection
        # Command format: holehe <email> --only-used --no-color
        command = ["holehe", sanitized_target, "--only-used", "--no-color"]
        
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> ToolResult:
        """
        Parse Holehe output.
        """
        entities = []
        for line in output.splitlines():
            if "[+]" in line:
                # Format: [+] Service
                service = line.replace("[+]", "").strip()
                entities.append(Entity(
                    type="account",
                    value=service, # Value is the service name where the email is used
                    source="holehe",
                    metadata={"status": "used"}
                ))
        
        return ToolResult(
            tool="holehe",
            entities=entities,
            raw_output=output
        )
