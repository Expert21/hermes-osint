"""
Tool Registry for Hermes Agent.

Defines tool schemas for LLM function calling and maps them to adapters.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Type, Optional
import logging

from src.orchestration.interfaces import ToolAdapter

logger = logging.getLogger(__name__)


@dataclass
class ToolDefinition:
    """
    Definition of a tool available to the agent.
    
    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description for the LLM
        parameters: JSON Schema defining the tool's parameters
        adapter_class: The ToolAdapter class to instantiate
        execution_mode: Preferred execution mode (native, docker, hybrid)
        stealth_compatible: Whether tool works in stealth mode
        makes_external_requests: Whether tool contacts external services
    """
    name: str
    description: str
    parameters: Dict[str, Any]
    adapter_class: Optional[Type[ToolAdapter]] = None
    execution_mode: str = "native"
    stealth_compatible: bool = False
    makes_external_requests: bool = True
    
    def to_ollama_schema(self) -> Dict[str, Any]:
        """
        Convert to Ollama function calling format.
        
        Returns:
            Dict compatible with Ollama's tools parameter
        """
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


def _get_sherlock_adapter():
    """Lazy import to avoid circular dependencies."""
    from src.plugins.sherlock.adapter import SherlockAdapter
    return SherlockAdapter


# Tool Registry - Single source of truth for available tools
TOOL_REGISTRY: Dict[str, ToolDefinition] = {
    "sherlock": ToolDefinition(
        name="sherlock",
        description=(
            "Search for a username across 300+ social media platforms and websites. "
            "Use this when you need to find social media accounts, profiles, or online "
            "presence for a given username."
        ),
        parameters={
            "type": "object",
            "properties": {
                "username": {
                    "type": "string",
                    "description": "The username to search for across platforms"
                }
            },
            "required": ["username"]
        },
        stealth_compatible=False,
        makes_external_requests=True
    ),
    
    "theharvester": ToolDefinition(
        name="theharvester",
        description=(
            "Discover emails and subdomains for a domain using search engines and public sources. "
            "This is a passive reconnaissance tool - it queries Google, Bing, etc. without "
            "directly contacting the target. Use for company/domain investigations."
        ),
        parameters={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "The domain to search (e.g., example.com)"
                }
            },
            "required": ["domain"]
        },
        stealth_compatible=True,  # Passive - queries search engines only
        makes_external_requests=True
    ),
    
    "h8mail": ToolDefinition(
        name="h8mail",
        description=(
            "Check if an email address has been involved in data breaches. "
            "Searches breach databases for exposed credentials. Use when you have "
            "an email and want to find associated breaches or leaked data."
        ),
        parameters={
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The email address to check for breaches"
                }
            },
            "required": ["email"]
        },
        stealth_compatible=True,  # Local breach DB option
        makes_external_requests=True
    ),
    
    "holehe": ToolDefinition(
        name="holehe",
        description=(
            "Check if an email is registered on various websites by sending password reset requests. "
            "Discovers which services an email is signed up for. WARNING: This makes direct "
            "contact with target websites - not suitable for stealth investigations."
        ),
        parameters={
            "type": "object",
            "properties": {
                "email": {
                    "type": "string",
                    "description": "The email address to check for registrations"
                }
            },
            "required": ["email"]
        },
        stealth_compatible=False,  # Makes direct requests to services
        makes_external_requests=True
    ),
    
    "phoneinfoga": ToolDefinition(
        name="phoneinfoga",
        description=(
            "Look up information about a phone number including carrier, location, and line type. "
            "Use when you have a phone number and need to gather intelligence about it."
        ),
        parameters={
            "type": "object",
            "properties": {
                "phone": {
                    "type": "string",
                    "description": "The phone number to lookup (include country code, e.g., +1234567890)"
                }
            },
            "required": ["phone"]
        },
        stealth_compatible=False,  # Makes API calls
        makes_external_requests=True
    ),
    
    "subfinder": ToolDefinition(
        name="subfinder",
        description=(
            "Enumerate subdomains for a domain using passive sources like certificate transparency "
            "and DNS databases. Fast and thorough subdomain discovery without touching the target. "
            "Use for mapping a target's infrastructure."
        ),
        parameters={
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "The domain to enumerate subdomains for (e.g., example.com)"
                }
            },
            "required": ["domain"]
        },
        stealth_compatible=True,  # Passive - uses public sources
        makes_external_requests=True
    ),
}


def get_tool_schemas() -> list:
    """
    Get all tool schemas in Ollama-compatible format.
    
    Returns:
        List of tool definitions for Ollama function calling
    """
    return [tool.to_ollama_schema() for tool in TOOL_REGISTRY.values()]


def get_tool(name: str) -> Optional[ToolDefinition]:
    """
    Get a tool definition by name.
    
    Args:
        name: Tool name to look up
        
    Returns:
        ToolDefinition or None if not found
    """
    return TOOL_REGISTRY.get(name)


def list_tools() -> list:
    """
    List all available tool names.
    
    Returns:
        List of tool names
    """
    return list(TOOL_REGISTRY.keys())
