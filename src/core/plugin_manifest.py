# -----------------------------------------------------------------------------
# Hermes OSINT - Plugin Manifest
# -----------------------------------------------------------------------------

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class PluginManifest:
    """
    Metadata definition for a Hermes plugin.
    """
    name: str
    version: str
    plugin_type: str  # "tool" or "core"
    adapter_class: str
    description: str
    author: str
    tool_name: Optional[str] = None
    docker_image: Optional[str] = None
    requires_credentials: List[str] = field(default_factory=list)
    supported_modes: List[str] = field(default_factory=list)
    capabilities: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate manifest fields."""
        if self.plugin_type not in ["tool", "core"]:
            raise ValueError(f"Invalid plugin_type: {self.plugin_type}. Must be 'tool' or 'core'.")
        
        if self.plugin_type == "tool" and not self.tool_name:
            raise ValueError("Tool plugins must specify 'tool_name'.")

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginManifest':
        """Create a PluginManifest from a dictionary."""
        # Filter out unknown keys to be safe
        known_keys = cls.__annotations__.keys()
        filtered_data = {k: v for k, v in data.items() if k in known_keys}
        return cls(**filtered_data)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "plugin_type": self.plugin_type,
            "adapter_class": self.adapter_class,
            "tool_name": self.tool_name,
            "docker_image": self.docker_image,
            "description": self.description,
            "author": self.author,
            "requires_credentials": self.requires_credentials,
            "supported_modes": self.supported_modes,
            "capabilities": self.capabilities
        }
