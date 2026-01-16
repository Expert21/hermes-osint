"""
Tool Executor for Hermes Agent.

Bridges agent tool calls to existing adapter infrastructure.
Validates inputs, executes tools, and formats results for agent consumption.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from src.agent.tool_registry import TOOL_REGISTRY, get_tool, ToolDefinition
from src.orchestration.execution_strategy import (
    NativeExecutionStrategy,
    DockerExecutionStrategy,
    HybridExecutionStrategy,
    ExecutionStrategy
)
from src.orchestration.docker_manager import DockerManager
from src.core.entities import Entity, ToolResult
from src.core.input_validator import InputValidator

logger = logging.getLogger(__name__)


@dataclass
class ToolCallResult:
    """Result of a tool execution."""
    success: bool
    tool_name: str
    entities: List[Entity]
    error: Optional[str] = None
    raw_output: str = ""
    
    def to_agent_message(self) -> str:
        """
        Format result for agent context window.
        
        Returns entities as structured text the agent can reason about.
        """
        if not self.success:
            return f"Tool '{self.tool_name}' failed: {self.error}"
        
        if not self.entities:
            return f"Tool '{self.tool_name}' completed but found no results."
        
        lines = [f"Results from {self.tool_name} ({len(self.entities)} findings):"]
        for entity in self.entities[:20]:  # Limit to prevent context overflow
            meta = entity.metadata
            if entity.type == "account":
                platform = meta.get("service", "unknown")
                lines.append(f"• [{platform}] {entity.value}")
            else:
                lines.append(f"• [{entity.type}] {entity.value}")
        
        if len(self.entities) > 20:
            lines.append(f"... and {len(self.entities) - 20} more results")
        
        return "\n".join(lines)


class ToolExecutor:
    """
    Executes tools on behalf of the agent.
    
    Acts as the "hands" of the agent - taking structured tool calls
    and executing them safely via the existing adapter infrastructure.
    """
    
    def __init__(
        self,
        execution_mode: str = "native",
        execution_strategy: Optional[ExecutionStrategy] = None
    ):
        """
        Initialize the tool executor.
        
        Args:
            execution_mode: 'native', 'docker', or 'hybrid'
            execution_strategy: Optional pre-configured strategy
        """
        self.execution_mode = execution_mode
        self.strategy = execution_strategy or self._create_strategy(execution_mode)
        self.adapters: Dict[str, Any] = {}
        self._load_adapters()
    
    def _create_strategy(self, mode: str) -> ExecutionStrategy:
        """Create execution strategy based on mode."""
        if mode == "docker":
            dm = DockerManager()
            return DockerExecutionStrategy(dm)
        elif mode == "native":
            return NativeExecutionStrategy()
        else:  # hybrid
            dm = DockerManager()
            return HybridExecutionStrategy(
                DockerExecutionStrategy(dm),
                NativeExecutionStrategy()
            )
    
    def _load_adapters(self):
        """Load adapter instances for all registered tools."""
        # Import here to avoid circular imports
        from src.plugins.sherlock.adapter import SherlockAdapter
        from src.plugins.theharvester.adapter import TheHarvesterAdapter
        from src.plugins.h8mail.adapter import H8MailAdapter
        from src.plugins.holehe.adapter import HoleheAdapter
        from src.plugins.phoneinfoga.adapter import PhoneInfogaAdapter
        from src.plugins.subfinder.adapter import SubfinderAdapter
        
        # Map tool names to their adapters
        adapter_classes = {
            "sherlock": SherlockAdapter,
            "theharvester": TheHarvesterAdapter,
            "h8mail": H8MailAdapter,
            "holehe": HoleheAdapter,
            "phoneinfoga": PhoneInfogaAdapter,
            "subfinder": SubfinderAdapter,
        }
        
        for tool_name, adapter_class in adapter_classes.items():
            if tool_name in TOOL_REGISTRY:
                try:
                    self.adapters[tool_name] = adapter_class(self.strategy)
                    logger.debug(f"Loaded adapter for {tool_name}")
                except Exception as e:
                    logger.error(f"Failed to load adapter for {tool_name}: {e}")
    
    def get_tool_schemas(self) -> list:
        """
        Get all tool schemas for Ollama function calling.
        
        Returns:
            List of tool definitions in Ollama format
        """
        return [
            tool.to_ollama_schema() 
            for name, tool in TOOL_REGISTRY.items()
            if name in self.adapters  # Only include loaded tools
        ]
    
    def can_execute(self, tool_name: str) -> bool:
        """
        Check if a tool can be executed.
        
        Args:
            tool_name: Name of the tool
            
        Returns:
            True if tool is available and can run
        """
        if tool_name not in self.adapters:
            return False
        return self.adapters[tool_name].can_run()
    
    def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None
    ) -> ToolCallResult:
        """
        Execute a tool with the given arguments.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments from LLM
            config: Optional config (stealth_mode, etc.)
            
        Returns:
            ToolCallResult with entities or error
        """
        config = config or {}
        
        # Validate tool exists
        tool_def = get_tool(tool_name)
        if tool_def is None:
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                entities=[],
                error=f"Unknown tool: {tool_name}. Available: {list(TOOL_REGISTRY.keys())}"
            )
        
        # Check adapter is loaded
        if tool_name not in self.adapters:
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                entities=[],
                error=f"Tool '{tool_name}' adapter not loaded"
            )
        
        adapter = self.adapters[tool_name]
        
        # Check tool can run
        if not adapter.can_run():
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                entities=[],
                error=f"Tool '{tool_name}' is not available in {self.execution_mode} mode"
            )
        
        # Extract target based on tool
        try:
            target = self._extract_target(tool_name, arguments)
        except ValueError as e:
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                entities=[],
                error=str(e)
            )
        
        # Execute
        logger.info(f"Executing {tool_name} with target: {target}")
        try:
            result: ToolResult = adapter.execute(target, config)
            
            if result.error:
                return ToolCallResult(
                    success=False,
                    tool_name=tool_name,
                    entities=[],
                    error=result.error,
                    raw_output=result.raw_output
                )
            
            return ToolCallResult(
                success=True,
                tool_name=tool_name,
                entities=result.entities,
                raw_output=result.raw_output
            )
            
        except Exception as e:
            logger.error(f"Tool execution failed: {e}")
            return ToolCallResult(
                success=False,
                tool_name=tool_name,
                entities=[],
                error=str(e)
            )
    
    def _extract_target(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """
        Extract and validate target from arguments.
        
        Args:
            tool_name: Tool being called
            arguments: LLM-provided arguments
            
        Returns:
            Validated target string
            
        Raises:
            ValueError: If arguments are invalid
        """
        # Sherlock - username
        if tool_name == "sherlock":
            username = arguments.get("username")
            if not username:
                raise ValueError("Missing required argument: username")
            return InputValidator.sanitize_username(username)
        
        # TheHarvester, Subfinder - domain
        if tool_name in ("theharvester", "subfinder"):
            domain = arguments.get("domain")
            if not domain:
                raise ValueError("Missing required argument: domain")
            return InputValidator.validate_domain(domain)
        
        # h8mail, Holehe - email
        if tool_name in ("h8mail", "holehe"):
            email = arguments.get("email")
            if not email:
                raise ValueError("Missing required argument: email")
            return InputValidator.validate_email(email)
        
        # PhoneInfoga - phone
        if tool_name == "phoneinfoga":
            phone = arguments.get("phone")
            if not phone:
                raise ValueError("Missing required argument: phone")
            # Basic validation - adapter does more thorough check
            return str(phone).strip()
        
        # Fallback: look for common target keys
        for key in ["target", "username", "email", "domain", "phone"]:
            if key in arguments:
                return str(arguments[key])
        
        raise ValueError(f"Could not extract target from arguments: {arguments}")
