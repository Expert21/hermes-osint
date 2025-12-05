# Hermes Internal API Documentation

Technical reference for Hermes OSINT internal modules and classes.

---

## Core Entities

### `src/core/entities.py`

#### Entity
Represents a single piece of discovered intelligence.

```python
@dataclass
class Entity:
    type: str           # Entity type (see Entity Types below)
    value: str          # The discovered value
    source: str         # Tool that found this entity
    confidence: float   # Confidence score (0.0 to 1.0)
    metadata: Dict      # Additional context
```

**Entity Types:**
- `account` - Social media account
- `email` - Email address  
- `domain` - Domain or subdomain
- `url` - Full URL
- `ip` - IP address
- `phone` - Phone number
- `metadata` - File/document metadata
- `breach` - Breach record
- `phone_info` - Phone carrier/location info

#### ToolResult
Standardized result returned by all tool adapters.

```python
@dataclass
class ToolResult:
    tool: str                    # Tool name
    entities: List[Entity]       # Discovered entities
    raw_output: str              # Raw stdout/stderr
    error: Optional[str]         # Error message if failed
    metadata: Dict               # Additional context
```

#### Connection
Represents a relationship between entities.

```python
@dataclass
class Connection:
    type: str               # Connection type
    source_entity: Entity   # First entity
    target_entity: Entity   # Second entity
    relationship: str       # Relationship description
    confidence: float       # Confidence score
    metadata: Dict          # Additional context
```

**Connection Types:**
- `exact_match` - Same value from different sources
- `username_reuse` - Same username across platforms
- `email_domain_link` - Email belongs to domain

---

## Tool Adapter Interface

### `src/orchestration/interfaces.py`

```python
class ToolAdapter(ABC):
    @abstractmethod
    def can_run(self) -> bool:
        """Check if tool is available in current environment."""
        pass

    @abstractmethod
    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """Execute tool against target. Returns ToolResult."""
        pass

    @abstractmethod
    def parse_results(self, output: str) -> ToolResult:
        """Parse raw output into structured ToolResult."""
        pass
```

---

## Execution Strategies

### `src/orchestration/execution_strategy.py`

#### ExecutionStrategy (Abstract)

```python
class ExecutionStrategy(ABC):
    @abstractmethod
    def is_available(self, tool_name: str) -> bool:
        """Check if tool is available in this strategy."""
        pass

    @abstractmethod
    def execute(self, tool_name: str, command: List[str], config: Dict) -> str:
        """Execute tool and return output string."""
        pass
```

#### DockerExecutionStrategy

Executes tools in Docker containers.

```python
class DockerExecutionStrategy(ExecutionStrategy):
    def __init__(self, docker_manager: DockerManager)
    
    def register_plugin_image(self, tool_name: str, image_name: str)
        """Register a third-party plugin Docker image."""
    
    def is_available(self, tool_name: str) -> bool
        """Returns True if Docker is available and tool image exists."""
    
    def execute(self, tool_name: str, command: List[str], config: Dict) -> str
        """Run container and return logs."""
```

**Config options:**
- `proxy_url` - HTTP/SOCKS proxy URL
- `entrypoint` - Override container entrypoint

#### NativeExecutionStrategy

Executes tools installed locally.

```python
class NativeExecutionStrategy(ExecutionStrategy):
    def is_available(self, tool_name: str) -> bool
        """Returns True if tool is in system PATH."""
    
    def execute(self, tool_name: str, command: List[str], config: Dict) -> str
        """Run subprocess and return stdout+stderr."""
```

#### HybridExecutionStrategy

Auto-detects: prefers native, falls back to Docker.

```python
class HybridExecutionStrategy(ExecutionStrategy):
    def __init__(self, docker_strategy, native_strategy)
    
    def is_available(self, tool_name: str) -> bool
        """True if available in either strategy."""
    
    def execute(self, tool_name: str, command: List[str], config: Dict) -> str
        """Prefers native, falls back to Docker."""
```

---

## Plugin System

### `src/core/plugin_manifest.py`

```python
@dataclass
class PluginManifest:
    name: str                           # Unique identifier
    version: str                        # Semantic version
    plugin_type: str                    # "tool" or "core"
    adapter_class: str                  # Full Python path
    description: str                    # Human description
    author: str                         # Author name
    tool_name: Optional[str]            # CLI tool name (required for type="tool")
    docker_image: Optional[str]         # Docker image name
    requires_credentials: List[str]     # Required secrets
    supported_modes: List[str]          # ["native", "docker", "hybrid"]
    capabilities: Dict                  # Capability flags
    
    @classmethod
    def from_dict(cls, data: Dict) -> PluginManifest
    
    def to_dict(self) -> Dict
```

### `src/core/plugin_loader.py`

```python
class PluginLoader:
    def __init__(self, execution_strategy: ExecutionStrategy)
    
    # Plugin search paths:
    # - src/plugins/
    # - ~/.hermes/plugins/
    
    def discover_plugins(self) -> List[PluginManifest]
        """Scan plugin directories for valid plugins."""
    
    def load_all_plugins(self) -> Dict[str, ToolAdapter]
        """Load all plugins, return {tool_name: adapter_instance}."""
    
    def load_plugin(self, manifest: PluginManifest) -> Optional[ToolAdapter]
        """Load a specific plugin after security scan."""
```

### `src/core/plugin_security_scanner.py`

```python
class PluginSecurityScanner:
    def scan_file(self, file_path: str, plugin_type: str = "tool") -> ScanResult
        """Scan Python file for security issues."""

@dataclass
class ScanResult:
    passed: bool
    confidence: float
    errors: List[SecurityIssue]
    warnings: List[SecurityIssue]
```

**Blocked patterns (tool plugins):**
- `subprocess.call(..., shell=True)`
- `os.system()`
- `eval()`, `exec()`

---

## Workflow Management

### `src/orchestration/workflow_manager.py`

```python
class WorkflowManager:
    def __init__(self, cleanup_images: bool = False, execution_mode: str = "docker")
    
    # Attributes:
    # - adapters: Dict[str, ToolAdapter]  # Loaded tool adapters
    # - execution_strategy: ExecutionStrategy
    
    def run_all_tools(
        self,
        target: str,
        target_type: str,           # "individual" or "company"
        domain: str = None,
        email: str = None,
        phone: str = None,
        file: str = None,
        stealth_mode: bool = False,
        username_variations: List[str] = None
    ) -> Dict[str, Any]
        """Run all applicable tools based on target type."""
```

**Tool selection by target type:**
- `individual`: sherlock, holehe, h8mail, phoneinfoga, exiftool
- `company`: theharvester, subfinder

---

## Docker Management

### `src/orchestration/docker_manager.py`

```python
class DockerManager:
    TRUSTED_IMAGES = [...]  # Whitelisted Docker images
    
    @property
    def is_available(self) -> bool
        """Check if Docker daemon is accessible."""
    
    def pull_image(self, image_name: str) -> bool
        """Pull a Docker image."""
    
    def remove_image(self, image_name: str, force: bool = False)
        """Remove a Docker image."""
    
    def run_container(
        self,
        image_name: str,
        command: List[str],
        environment: Dict[str, str] = None,
        entrypoint: List[str] = None,
        allow_network: bool = True
    ) -> Dict[str, Any]
        """Run container and return {logs, exit_code, metadata}."""
```

---

## Core Utilities

### Input Validation (`src/core/input_validator.py`)

```python
class InputValidator:
    @staticmethod
    def validate_target_name(name: str) -> str
    
    @staticmethod
    def validate_domain(domain: str) -> str
    
    @staticmethod
    def validate_email(email: str) -> str
    
    @staticmethod
    def sanitize_username(username: str, max_length: int = 50) -> str
```

### Task Manager (`src/core/task_manager.py`)

```python
class TaskManager:
    def __init__(self, max_workers: int = 10)
    
    async def start(self)
    async def stop(self)
    
    async def submit(
        self,
        coro: Coroutine,
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 300.0
    ) -> Any
```

### Resource Limiter (`src/core/resource_limiter.py`)

```python
class ResourceLimiter:
    @staticmethod
    def auto_detect_resources()
        """Auto-detect CPU/memory and set limits."""
    
    @staticmethod
    def get_recommended_workers() -> int
```

### Secrets Manager (`src/core/secrets_manager.py`)

```python
class SecretsManager:
    def get_secret(self, key: str) -> Optional[str]
    def set_secret(self, key: str, value: str)
    def import_from_env_file(self, path: str)
```

---

## Reporting

### `src/reporting/generator.py`

```python
def generate_report(results: Dict, output_path: str)
    """Generate report based on file extension (.json, .md, .html)."""
```

### Report Modules
- `src/reporting/markdown_report.py` - Markdown generation
- `src/reporting/html_report.py` - HTML generation
- `src/reporting/pdf_report.py` - PDF generation

---

## Correlation Engine

### `src/core/correlation.py`

```python
class CorrelationEngine:
    def correlate(self, entities: List[Entity]) -> List[Connection]
        """Find relationships between entities."""
```

### `src/core/deduplication.py`

```python
def deduplicate_and_correlate(
    search_results: List[Dict],
    social_results: List[Dict]
) -> Dict
    """Deduplicate results and find connections."""
```
