# Tool Adapter Developer Guide

Hermes v2.0 introduces a standardized `ToolAdapter` interface that allows developers to easily add support for new OSINT tools. This guide explains how to create, test, and register a new adapter.

## Overview

A Tool Adapter is a Python class that bridges Hermes with an external tool. It handles:
1.  **Command Construction**: Building the command line arguments for the tool.
2.  **Execution**: Running the tool via the configured strategy (Docker, Native, or Hybrid).
3.  **Parsing**: Converting the tool's raw output (text, JSON, etc.) into a normalized Hermes format.

## The `ToolAdapter` Interface

All adapters must inherit from `src.orchestration.interfaces.ToolAdapter`.

```python
from src.orchestration.interfaces import ToolAdapter
from typing import Dict, Any

class MyNewToolAdapter(ToolAdapter):
    
    def __init__(self, execution_strategy):
        super().__init__(execution_strategy)
        self.tool_name = "my_new_tool"

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool against the target.
        """
        # 1. Construct command
        command = f"--target {target} --json"
        
        # 2. Run using the execution strategy
        # The strategy handles whether it runs in Docker or Native
        output = self.execution_strategy.run_tool(
            tool_name=self.tool_name,
            command_args=command
        )
        
        # 3. Parse and return results
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse raw output into normalized dictionary.
        """
        # Implement parsing logic here
        return {
            "tool": self.tool_name,
            "results": [] 
        }
```

## Step-by-Step Implementation

### 1. Create the Adapter Class

Create a new file in `src/orchestration/adapters/` named `my_tool_adapter.py`. Implement the class as shown above.

### 2. Define Docker Image (If applicable)

If your tool runs in Docker, ensure the image is added to the trusted list in `src/orchestration/docker_manager.py`.

```python
TRUSTED_IMAGES = {
    # ... existing images ...
    "my_new_tool": "maintainer/my-tool:latest"
}
```

### 3. Implement Parsing Logic

Parsing is critical. Hermes expects a standardized output format.

**Standard Output Format:**
```json
{
    "tool": "tool_name",
    "timestamp": "2023-10-27T10:00:00Z",
    "results": [
        {
            "type": "username|email|phone|etc",
            "value": "found_value",
            "source": "platform_name",
            "url": "https://example.com/profile",
            "metadata": {}
        }
    ]
}
```

### 4. Register the Adapter

Update `src/orchestration/factory.py` (or wherever the factory logic resides) to include your new adapter in the mapping.

### 5. Testing

Create a test file in `tests/` to verify your adapter.

```python
def test_my_adapter_parsing():
    adapter = MyNewToolAdapter(MockStrategy())
    raw_output = "..." # Sample output
    result = adapter.parse_results(raw_output)
    assert result['tool'] == "my_new_tool"
    assert len(result['results']) > 0
```

## Best Practices

-   **Error Handling**: Wrap execution in try/except blocks and return a standardized error structure if something fails.
-   **Dependencies**: If your tool requires specific Python libraries, add them to `requirements.txt` only if they are essential for the *adapter* (not the tool itself, if running in Docker).
-   **Logging**: Use the Hermes logger (`logging.getLogger("hermes")`) for debug and info messages.
