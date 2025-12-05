
from typing import Dict, Any
import json
import logging
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.entities import ToolResult, Entity

logger = logging.getLogger(__name__)

class H8MailAdapter(ToolAdapter):
    """
    Adapter for h8mail (Email Breach Hunting).
    """

    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "h8mail"

    def can_run(self) -> bool:
        """Check if h8mail is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Execute h8mail against the target email.
        
        Args:
            target: Email address to check
            config: Configuration dictionary (e.g., API keys)
            
        Returns:
            ToolResult containing the structured findings
        """
        # Construct command
        # -t: target
        # -j: json output (if supported, otherwise we parse stdout)
        # --loose: loose search (optional, maybe configurable)
        
        command = ["-t", target, "--json"]
        
        # STEALTH: Use local breach compilation only, no external API calls
        if config.get("stealth_mode", False):
            command.append("--local")
        
        # Add API keys if provided in config
        # h8mail uses a config file usually, but can take some via CLI or env
        # For this MVP, we'll assume basic execution or env vars passed via DockerManager
        
        try:
            logger.info(f"Executing h8mail for {target}")
            output = self.execution_strategy.execute(self.tool_name, command, config)
            
            return self.parse_results(output)
            
        except Exception as e:
            logger.error(f"h8mail execution failed: {e}")
            return ToolResult(tool="h8mail", error=str(e))

    def parse_results(self, output: str) -> ToolResult:
        """
        Parse h8mail output.
        """
        entities = []
        
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
                             # data["breach"] can be a list or string depending on h8mail version/plugin
                             # Assuming it's a list of breach names or objects
                             breaches = data.get("breach", [])
                             if isinstance(breaches, list):
                                 for breach in breaches:
                                     entities.append(Entity(
                                         type="breach",
                                         value=str(breach),
                                         source="h8mail",
                                         metadata=data
                                     ))
                             else:
                                 entities.append(Entity(
                                     type="breach",
                                     value=str(breaches),
                                     source="h8mail",
                                     metadata=data
                                 ))

                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            logger.warning(f"Failed to parse h8mail output: {e}")
            
        return ToolResult(
            tool="h8mail",
            entities=entities,
            raw_output=output
        )
