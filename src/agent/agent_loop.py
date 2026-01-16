"""
Agent Loop for Hermes v3.0

Implements the ReAct (Reason + Act) pattern for agentic OSINT investigations.

The agent loop:
1. Receives user input
2. Reasons about what action to take
3. Optionally calls tools via function calling
4. Observes results and synthesizes response
5. Repeats until task is complete
"""

import logging
import json
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

from src.analysis.ollama_client import OllamaClient, OllamaConfig
from src.agent.tool_executor import ToolExecutor, ToolCallResult

logger = logging.getLogger(__name__)


# System prompt that defines the agent's behavior
SYSTEM_PROMPT = """You are Hermes, an OSINT (Open Source Intelligence) analyst assistant.

Your role is to help users investigate targets by:
1. Understanding their investigation goals
2. Choosing appropriate OSINT tools to gather information
3. Analyzing and synthesizing findings
4. Presenting clear, factual results WITH SOURCE CITATIONS

CRITICAL GROUNDING RULES:
- ONLY report information that comes from tool results - NEVER invent or assume data
- ALWAYS cite the source tool when reporting findings (e.g., "Sherlock found...")
- If a tool returns no results, say "No results found" - do not speculate
- If a tool fails, report the error and suggest alternatives
- Ask for clarification if the user's request is ambiguous

RESPONSE FORMAT:
When reporting findings, use this structure:
"[Tool Name] found [N] results:
• [Type] Value
• [Type] Value
..."

Example:
"Sherlock found 3 accounts for 'john_doe':
• [GitHub] github.com/john_doe
• [Twitter] twitter.com/john_doe
• [Reddit] reddit.com/u/john_doe"

You have access to tools for usernames, emails, domains, and phone numbers.
Use the appropriate tool based on the input type."""


@dataclass
class AgentMessage:
    """A message in the conversation."""
    role: str  # "user", "assistant", or "tool"
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    tool_call_id: Optional[str] = None
    name: Optional[str] = None  # Tool name for tool messages
    
    def to_ollama_format(self) -> Dict[str, Any]:
        """Convert to Ollama message format."""
        msg = {"role": self.role, "content": self.content}
        if self.tool_calls:
            msg["tool_calls"] = self.tool_calls
        if self.name:
            msg["name"] = self.name
        return msg


@dataclass
class AgentResponse:
    """Response from a single agent turn."""
    content: str
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)
    has_tool_calls: bool = False
    
    @classmethod
    def from_ollama_response(cls, response: Dict[str, Any]) -> "AgentResponse":
        """Parse Ollama response into AgentResponse."""
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])
        return cls(
            content=message.get("content", ""),
            tool_calls=tool_calls,
            has_tool_calls=len(tool_calls) > 0
        )


class AgentLoop:
    """
    The core agentic loop for Hermes v3.0.
    
    Maintains conversation state and orchestrates the think → act → observe cycle.
    """
    
    def __init__(
        self,
        client: Optional[OllamaClient] = None,
        executor: Optional[ToolExecutor] = None,
        model: str = "llama3.2",
        execution_mode: str = "native"
    ):
        """
        Initialize the agent loop.
        
        Args:
            client: Optional pre-configured Ollama client
            executor: Optional pre-configured tool executor
            model: Ollama model to use
            execution_mode: Tool execution mode (native/docker/hybrid)
        """
        self.client = client or OllamaClient(OllamaConfig(model=model))
        self.executor = executor or ToolExecutor(execution_mode=execution_mode)
        self.model = model
        self.messages: List[AgentMessage] = []
        self.system_prompt = SYSTEM_PROMPT
        
    async def is_available(self) -> bool:
        """Check if the agent can run (Ollama available)."""
        return await self.client.is_available()
    
    async def run(self, user_input: str, config: Optional[Dict[str, Any]] = None) -> str:
        """
        Process a single user input and return agent response.
        
        This is the main entry point for the ReAct loop.
        
        Args:
            user_input: The user's message
            config: Optional config (stealth_mode, etc.)
            
        Returns:
            Agent's response string
        """
        config = config or {}
        
        # Add user message to history
        self.messages.append(AgentMessage(role="user", content=user_input))
        
        # ReAct loop - may iterate if tools are called
        max_iterations = 5  # Prevent infinite loops
        for _ in range(max_iterations):
            # Get agent response
            response = await self._think()
            
            if response is None:
                return "I'm having trouble connecting to my reasoning engine. Please try again."
            
            # Check if agent wants to call tools
            if response.has_tool_calls:
                # Execute tools and collect observations
                await self._act_and_observe(response.tool_calls, config)
                # Continue loop to let agent process observations
            else:
                # No tool calls - agent is ready to respond
                self.messages.append(AgentMessage(
                    role="assistant",
                    content=response.content
                ))
                return response.content
        
        return "I've reached my reasoning limit for this turn. Please try rephrasing your request."
    
    async def _think(self) -> Optional[AgentResponse]:
        """
        Send current context to LLM and get response.
        
        Returns:
            AgentResponse with content and/or tool calls
        """
        # Build messages for Ollama
        ollama_messages = [
            {"role": "system", "content": self.system_prompt},
        ]
        for msg in self.messages:
            ollama_messages.append(msg.to_ollama_format())
        
        # Get tool schemas
        tools = self.executor.get_tool_schemas()
        
        try:
            # Call Ollama with tools
            raw_response = await self._chat_with_tools(ollama_messages, tools)
            if raw_response is None:
                return None
            return AgentResponse.from_ollama_response(raw_response)
        except Exception as e:
            logger.error(f"Agent thinking failed: {e}")
            return None
    
    async def _act_and_observe(
        self,
        tool_calls: List[Dict[str, Any]],
        config: Dict[str, Any]
    ):
        """
        Execute tool calls and add observations to context.
        
        Args:
            tool_calls: List of tool calls from the LLM
            config: Execution config
        """
        for call in tool_calls:
            function = call.get("function", {})
            tool_name = function.get("name", "unknown")
            
            # Parse arguments
            try:
                arguments = json.loads(function.get("arguments", "{}"))
            except json.JSONDecodeError:
                arguments = {}
            
            logger.info(f"Executing tool: {tool_name} with args: {arguments}")
            
            # Execute via tool executor
            result: ToolCallResult = self.executor.execute(
                tool_name=tool_name,
                arguments=arguments,
                config=config
            )
            
            # Add tool result to messages
            observation = result.to_agent_message()
            self.messages.append(AgentMessage(
                role="tool",
                content=observation,
                name=tool_name
            ))
            
            logger.info(f"Tool {tool_name} completed: {len(result.entities)} entities")
    
    async def _chat_with_tools(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Call Ollama chat API with tool definitions.
        
        Args:
            messages: Conversation messages
            tools: Tool definitions
            
        Returns:
            Raw Ollama response dict
        """
        if not await self.client.is_available():
            logger.warning("Ollama not available")
            return None
        
        try:
            client = self.client._get_client()
            response = await client.chat(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
            )
            return response
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return None
    
    def clear_history(self):
        """Clear conversation history."""
        self.messages = []
    
    def get_context_size(self) -> int:
        """
        Estimate current context size in characters.
        
        Returns:
            Approximate character count of context
        """
        total = len(self.system_prompt)
        for msg in self.messages:
            total += len(msg.content)
        return total
