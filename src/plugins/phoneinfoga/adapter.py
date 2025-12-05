
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator
from src.core.entities import ToolResult, Entity

class PhoneInfogaAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "phoneinfoga"

    def can_run(self) -> bool:
        """Check if PhoneInfoga is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Run PhoneInfoga against a phone number.
        
        Args:
            target: Phone number
            config: Configuration dictionary
            
        Returns:
            ToolResult containing the structured findings
            
        STEALTH NOTE: PhoneInfoga makes API calls to external services
        for phone number lookups. Incompatible with stealth mode.
        """
        # STEALTH: Skip in stealth mode - makes direct API calls
        if config.get("stealth_mode", False):
            return ToolResult(
                tool=self.tool_name,
                entities=[],
                raw_output="",
                metadata={"skipped": True, "reason": "PhoneInfoga makes direct contact - incompatible with stealth mode"}
            )
        
        # SECURITY: Validate phone number (basic check)
        # PhoneInfoga handles various formats, but we should ensure no shell chars
        if not re.match(r'^\+?[0-9\-\s]+$', target):
             raise ValueError(f"Invalid phone number format: {target}")
        
        # Use list format to prevent shell injection
        command = ["scan", "-n", target, "--no-ansi"]
        
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> ToolResult:
        """
        Parse PhoneInfoga output.
        """
        # PhoneInfoga output is complex, we'll extract key info
        # Ideally we'd use JSON output but CLI often outputs text
        entities = []
        metadata = {}
        
        # Simple text parsing for now
        lines = output.splitlines()
        for line in lines:
            if "Country:" in line:
                metadata['country'] = line.split("Country:")[1].strip()
            elif "Carrier:" in line:
                metadata['carrier'] = line.split("Carrier:")[1].strip()
            elif "Line type:" in line:
                metadata['line_type'] = line.split("Line type:")[1].strip()
        
        # Create a single entity for the phone number info
        if metadata:
             # We don't have the target phone number explicitly passed here unless we parse it from output or pass it down.
             # But 'execute' has it. However, parse_results only takes output.
             # We can assume the value is the phone number being scanned, but we don't have it.
             # We'll use "phone_info" as value or just put it in metadata.
             # Let's use a generic value "target_phone" or similar if we can't get it.
             # Actually, the best practice would be to pass the target to parse_results, but the interface doesn't support it.
             # We can just put the metadata in the ToolResult metadata or create a generic entity.
             # Let's create an entity with value "phone_details" and all info in metadata.
             entities.append(Entity(
                 type="phone_info",
                 value="phone_details", 
                 source="phoneinfoga",
                 metadata=metadata
             ))

        return ToolResult(
            tool="phoneinfoga",
            entities=entities,
            raw_output=output
        )
