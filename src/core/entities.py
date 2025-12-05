
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Entity:
    """
    Represents a single piece of intelligence found by a tool.
    """
    type: str  # e.g., "username", "email", "domain", "url", "ip", "phone", "metadata"
    value: str
    source: str
    confidence: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "value": self.value,
            "source": self.source,
            "confidence": self.confidence,
            "metadata": self.metadata
        }

@dataclass
class ToolResult:
    """
    Standardized result object returned by all tool adapters.
    """
    tool: str
    entities: List[Entity] = field(default_factory=list)
    raw_output: str = ""
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tool": self.tool,
            "entities": [e.to_dict() for e in self.entities],
            "raw_output": self.raw_output,
            "error": self.error,
            "metadata": self.metadata
        }

@dataclass
class Connection:
    """
    Represents a relationship between two entities or a group of entities.
    """
    type: str # e.g., "exact_match", "username_reuse", "email_domain_link"
    source_entity: Entity
    target_entity: Entity
    relationship: str
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type,
            "source_entity": self.source_entity.to_dict(),
            "target_entity": self.target_entity.to_dict(),
            "relationship": self.relationship,
            "confidence": self.confidence,
            "metadata": self.metadata
        }
