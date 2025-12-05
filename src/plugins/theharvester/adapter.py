
from typing import Dict, Any
import re
import logging
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator
from src.core.entities import ToolResult, Entity

logger = logging.getLogger(__name__)

class TheHarvesterAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "theharvester"

    def can_run(self) -> bool:
        """Check if TheHarvester is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Run TheHarvester against a domain.
        
        Args:
            target: Domain to search (validated for safety)
            config: Configuration dictionary
            
        Returns:
            ToolResult containing the structured findings
            
        STEALTH NOTE: TheHarvester is passive by design - it queries search engines
        (Google, Bing, etc.) rather than the target domain directly. Safe for stealth mode.
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
        
        # Override entrypoint to run CLI instead of API server
        config["entrypoint"] = ["python", "theHarvester.py"]
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> ToolResult:
        """
        Parse TheHarvester output.
        
        SECURITY: Protects against ReDoS by limiting output size before regex processing.
        """
        entities = []
        
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
            found_emails = list(set([match.group() for match in email_matches]))[:1000]  # Limit to 1000 emails
            
            for email in found_emails:
                entities.append(Entity(
                    type="email",
                    value=email,
                    source="theharvester"
                ))
                
        except Exception as e:
            logger.error(f"Error parsing emails: {e}")
        
        # Basic host parsing (this might need refinement based on actual output)
        # TheHarvester output varies by source, but often lists "IP: Host" or just hosts
        
        return ToolResult(
            tool="theharvester",
            entities=entities,
            raw_output=output[:10000]  # Only include first 10KB of raw output in results
        )
