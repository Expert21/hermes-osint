# Plugin Development Guide

This guide explains how to create custom plugins for Hermes OSINT.

## Plugin Structure

Each plugin lives in its own directory under `src/plugins/` or `~/.hermes/plugins/`:

```
my_tool/
├── plugin.json      # Manifest file (required)
├── adapter.py       # Tool adapter implementation (required)
└── __init__.py      # Module exports
```

---

## Plugin Types

Hermes supports two types of plugins:

### Tool Plugins (`plugin_type: "tool"`)
Integrate external OSINT tools (like Sherlock, TheHarvester, etc.). These:
- Implement the `ToolAdapter` interface
- Are executed via `ExecutionStrategy` (Docker/Native/Hybrid)
- Must specify `tool_name` in the manifest
- Are subject to stricter security scanning (no `subprocess.call(shell=True)`, etc.)

### Core Plugins (`plugin_type: "core"`)
Extend Hermes core functionality. These can:
- Add new report formats
- Implement custom correlation engines
- Add new data sources or enrichment pipelines
- Integrate with external APIs for data enrichment
- Have more permissive security scanning (network/file access allowed)

**Core Plugin Example Manifest:**
```json
{
    "name": "custom_enricher",
    "version": "1.0.0",
    "plugin_type": "core",
    "adapter_class": "src.plugins.custom_enricher.enricher.CustomEnricher",
    "description": "Enriches entities with additional data from custom API",
    "author": "Your Name",
    "requires_credentials": ["CUSTOM_API_KEY"],
    "supported_modes": ["native"],
    "capabilities": {
        "enrichment": true,
        "entity_types": ["email", "domain"]
    }
}
```

---

## Step 1: Create the Plugin Manifest

Create `plugin.json` with your plugin metadata:

```json
{
    "name": "my_tool",
    "version": "1.0.0",
    "plugin_type": "tool",
    "adapter_class": "src.plugins.my_tool.adapter.MyToolAdapter",
    "tool_name": "my_tool",
    "docker_image": "myorg/my_tool:latest",
    "description": "Description of what my tool does",
    "author": "Your Name",
    "requires_credentials": [],
    "supported_modes": ["docker", "native", "hybrid"],
    "capabilities": {}
}
```

### Manifest Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Unique plugin identifier |
| `version` | Yes | Semantic version string |
| `plugin_type` | Yes | `"tool"` for tool adapters |
| `adapter_class` | Yes | Full Python path to adapter class |
| `tool_name` | Yes | Tool name used in CLI |
| `docker_image` | No | Docker image for Docker mode |
| `description` | Yes | Human-readable description |
| `author` | Yes | Plugin author |
| `requires_credentials` | No | List of required secrets |
| `supported_modes` | Yes | Supported execution modes |
| `capabilities` | No | Additional capability flags |

---

## Step 2: Implement the Adapter

Create `adapter.py` implementing the `ToolAdapter` interface:

```python
from typing import Dict, Any
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.entities import ToolResult, Entity

class MyToolAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "my_tool"

    def can_run(self) -> bool:
        """Check if the tool is available."""
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool against a target.
        
        Args:
            target: The target to scan
            config: Configuration dict (may include stealth_mode, proxy_url, etc.)
        """
        # Handle stealth mode if applicable
        if config.get("stealth_mode", False):
            # Option 1: Skip if tool makes direct contact
            return ToolResult(
                tool=self.tool_name,
                entities=[],
                metadata={"skipped": True, "reason": "Incompatible with stealth mode"}
            )
            # Option 2: Add passive flags to command
            # command.append("--passive")
        
        # Build command arguments
        command = ["--target", target, "--output", "json"]
        
        # Execute via strategy (handles Docker/Native automatically)
        output = self.execution_strategy.execute(self.tool_name, command, config)
        
        return self.parse_results(output)

    def parse_results(self, output: str) -> ToolResult:
        """Parse raw output into structured entities."""
        entities = []
        
        # Parse your tool's output format
        for line in output.splitlines():
            if "FOUND:" in line:
                value = line.split("FOUND:")[1].strip()
                entities.append(Entity(
                    type="account",  # or: email, domain, ip, phone, metadata
                    value=value,
                    source=self.tool_name,
                    confidence=1.0,
                    metadata={"raw_line": line}
                ))
        
        return ToolResult(
            tool=self.tool_name,
            entities=entities,
            raw_output=output
        )
```

---

## Step 3: Create Module Init

Create `__init__.py`:

```python
from .adapter import MyToolAdapter
```

---

## Core Interfaces

### ToolAdapter (Abstract Base Class)

```python
class ToolAdapter(ABC):
    @abstractmethod
    def can_run(self) -> bool:
        """Check if tool is available in current environment."""
        pass

    @abstractmethod
    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """Execute the tool and return structured results."""
        pass

    @abstractmethod
    def parse_results(self, output: str) -> ToolResult:
        """Parse raw output into ToolResult."""
        pass
```

### Entity

```python
@dataclass
class Entity:
    type: str           # "account", "email", "domain", "ip", "phone", "metadata"
    value: str          # The actual value found
    source: str         # Tool that found it
    confidence: float   # 0.0 to 1.0
    metadata: Dict      # Additional context
```

### ToolResult

```python
@dataclass
class ToolResult:
    tool: str                    # Tool name
    entities: List[Entity]       # Discovered entities
    raw_output: str              # Raw tool output
    error: Optional[str]         # Error message if failed
    metadata: Dict               # Additional context (skipped, reason, etc.)
```

---

## Execution Strategies

Your adapter receives an `ExecutionStrategy` that handles tool execution:

```python
# Check availability
if self.execution_strategy.is_available(self.tool_name):
    # Execute command
    output = self.execution_strategy.execute(
        tool_name="my_tool",
        command=["--target", target],
        config={"proxy_url": "http://proxy:8080"}
    )
```

**Strategy Types:**
- `NativeExecutionStrategy` - Uses locally installed tools
- `DockerExecutionStrategy` - Runs tools in Docker containers
- `HybridExecutionStrategy` - Prefers native, falls back to Docker

---

## Handling Stealth Mode

Check `config.get("stealth_mode", False)` in your `execute()` method:

```python
def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
    if config.get("stealth_mode", False):
        # Option A: Skip entirely
        return ToolResult(
            tool=self.tool_name,
            entities=[],
            metadata={"skipped": True, "reason": "Makes direct contact"}
        )
        
        # Option B: Use passive mode flag
        command.append("--passive")
```

---

## Security Scanner

Plugins are automatically scanned for security issues:

**Blocked patterns (tool plugins):**
- `subprocess.call` with `shell=True`
- `os.system()` calls
- `eval()`, `exec()` usage
- Arbitrary file operations outside workspace

**Allowed (core plugins only):**
- Network operations
- File system access
- Subprocess calls

Run manual security scan:
```bash
hermes plugins scan /path/to/my_plugin
```

---

## Testing Your Plugin

```python
# test_my_tool.py
from src.plugins.my_tool.adapter import MyToolAdapter
from src.orchestration.execution_strategy import NativeExecutionStrategy

def test_my_tool():
    strategy = NativeExecutionStrategy()
    adapter = MyToolAdapter(strategy)
    
    if adapter.can_run():
        result = adapter.execute("test_target", {})
        assert result.tool == "my_tool"
        assert result.error is None
```

---

## Plugin Locations

Plugins are discovered from:

1. **Built-in**: `src/plugins/` (shipped with Hermes)
2. **User plugins**: `~/.hermes/plugins/` (custom plugins)

---

## Example: Complete Plugin

```python
# src/plugins/nmap_lite/adapter.py
from typing import Dict, Any
import re
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.execution_strategy import ExecutionStrategy
from src.core.entities import ToolResult, Entity

class NmapLiteAdapter(ToolAdapter):
    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.tool_name = "nmap"

    def can_run(self) -> bool:
        return self.execution_strategy.is_available(self.tool_name)

    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        # Stealth: nmap has passive mode via -sn (no port scan)
        if config.get("stealth_mode", False):
            command = ["-sn", target]  # Ping scan only
        else:
            command = ["-F", target]   # Fast scan
        
        output = self.execution_strategy.execute(self.tool_name, command, config)
        return self.parse_results(output)

    def parse_results(self, output: str) -> ToolResult:
        entities = []
        
        # Parse open ports
        for match in re.finditer(r'(\d+)/tcp\s+open\s+(\w+)', output):
            port, service = match.groups()
            entities.append(Entity(
                type="port",
                value=f"{port}/{service}",
                source="nmap",
                metadata={"port": int(port), "service": service}
            ))
        
        return ToolResult(tool="nmap", entities=entities, raw_output=output)
```
