
from typing import Dict, Any
import logging
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.input_validator import InputValidator
from src.core.entities import ToolResult, Entity

logger = logging.getLogger(__name__)

class SubfinderAdapter(ToolAdapter):
    """
    Adapter for Subfinder (Subdomain Discovery).
    ProjectDiscovery's fast passive subdomain enumeration tool.
    """

    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "subfinder"

    def can_run(self) -> bool:
        """Check if Subfinder is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Run Subfinder against a domain.
        
        Args:
            target: Domain name to enumerate subdomains for
            config: Configuration dictionary
            
        Returns:
            ToolResult containing the structured findings
            
        STEALTH NOTE: Subfinder is passive by design - it queries passive DNS sources
        (certificate transparency, OSINT APIs) rather than the target domain. Safe for stealth mode.
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
            return self.parse_results(output) # json_output is handled inside parse_results logic or we assume True
        except Exception as e:
            logger.error(f"Subfinder execution failed: {e}")
            return ToolResult(tool="subfinder", error=str(e))

    def parse_results(self, output: str) -> ToolResult:
        """
        Parse Subfinder output.
        
        Args:
            output: Raw output from subfinder
        """
        entities = []
        
        try:
            # Try parsing as JSON first (default)
            # Parse JSON output (one JSON object per line)
            import json
            for line in output.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        data = json.loads(line)
                        # Subfinder JSON format: {"host": "subdomain.example.com", "source": "..."}
                        if "host" in data:
                            entities.append(Entity(
                                type="domain",
                                value=data["host"],
                                source="subfinder",
                                metadata={"source": data.get("source", "unknown")}
                            ))
                    except json.JSONDecodeError:
                        continue
            
            # If no entities found, try parsing as plain text (fallback)
            if not entities:
                 for line in output.splitlines():
                    line = line.strip()
                    # Filter out empty lines and potential error messages
                    if line and not line.startswith("[") and "." in line and not line.startswith("{"):
                        entities.append(Entity(
                            type="domain",
                            value=line,
                            source="subfinder",
                            metadata={"source": "unknown"}
                        ))
            
            # Deduplicate entities based on value
            seen = set()
            unique_entities = []
            for entity in entities:
                if entity.value not in seen:
                    seen.add(entity.value)
                    unique_entities.append(entity)
            
            entities = unique_entities
            
        except Exception as e:
            logger.warning(f"Failed to parse subfinder output: {e}")
        
        return ToolResult(
            tool="subfinder",
            entities=entities,
            raw_output=output[:10000]  # Limit raw output to 10KB
        )
