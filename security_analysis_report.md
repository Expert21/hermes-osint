# Security Analysis Report: Hermes 3.0 Implementations

**Date:** 2026-01-16
**Subject:** Security Review of Agent Loop, TUI, and Tool Registry
**Version:** 3.0-dev

## 1. Executive Summary

A security analysis was performed on the core components of the Hermes 3.0 Agent (Agent Loop, TUI, Tool Registry, and Executors). The codebase generally demonstrates high security maturity with robust protections against common injection attacks (Command Injection, Shell Injection). The architecture correctly isolates tool execution and validates inputs before processing.

One moderate architectural weakness was identified regarding the enforcement of "Stealth Mode," and a few minor recommendations are made to further harden the system.

## 2. Detailed Findings

### 2.1. Command Injection Prevention [SECURE]
The system uses a `NativeExecutionStrategy` that relies on `subprocess.run` with `shell=False` (default behavior) and passes arguments as a list. This effectively mitigates shell injection attacks.
- **Evidence**: `src/plugins/sherlock/adapter.py` constructs commands as lists (`[sanitized_target, ...]`).
- **Validation**: `src/core/input_validator.py` provides strict whitelisting for usernames, domains, and filenames, stripping dangerous characters like `;`, `&`, `|`, and `$`.

### 2.2. Input Validation [SECURE]
The `InputValidator` class implements strict whitelist-based validation.
- `sanitize_username`: Allows only `a-zA-Z0-9._-`. This is safe, though potentially over-aggressive (some platforms allow `@` or `+`).
- `validate_output_path`: Prevents directory traversal (`..`) and blocks writes to sensitive system directories (`/etc`, `/bin`, etc.).

### 2.3. Stealth Mode Enforcement [MODERATE RISK]
The "Stealth Mode" feature (intended to prevent active traffic to targets) is currently enforced at the **Adapter** level, not the **Executor** level.
- **Observation**: `SherlockAdapter.execute` checks `config.get("stealth_mode")`.
- **Risk**: While the current implementation works, it relies on every future tool adapter developer remembering to add this check. If a developer forgets, a "stealth" investigation could accidentally leak traffic.
- **Recommendation**: Move the enforcement to `ToolExecutor.execute`. Check `ToolDefinition.stealth_compatible` against `config["stealth_mode"]` before calling the adapter. This guarantees compliance for all tools.

### 2.4. Tool Registry & JSON Parsing [LOW RISK]
The Agent Loop parses tool arguments using `json.loads`.
- **Observation**: `_act_and_observe` in `AgentLoop` attempts to parse JSON.
- **Recommendation**: Ensure the LLM prompts strict JSON output. While `try-except` blocks exist, invalid JSON from the model will cause tool failures. This is a functional stability issue rather than a security vulnerability.

### 2.5. Proxy Configuration [SECURE]
The `execution_strategy.py` includes a `_is_valid_proxy_url` method that is exceptionally robust.
- It blocks local/private IPs (preventing SSRF via proxy).
- It normalizes hostnames and performs DNS resolution checks.
- This is a high-assurance implementation for preventing proxy-based attacks.

## 3. Recommendations

### 3.1. Centralize Stealth Enforcement
Modify `src/agent/tool_executor.py` to block non-stealth tools when stealth mode is active:

```python
# In ToolExecutor.execute
tool_def = get_tool(tool_name)
if config.get("stealth_mode") and not tool_def.stealth_compatible:
    return ToolCallResult(
        success=False,
        error=f"Tool {tool_name} is not compatible with stealth mode."
    )
```

### 3.2. Hardened Tool Arguments
Consider using Pydantic models for tool arguments instead of raw dictionaries. This would provide automatic validation and type coercion (e.g., ensuring `count` is an integer) before the logic reaches the adapter.

### 3.3. Configurable System Prompt
The `SYSTEM_PROMPT` in `agent_loop.py` is hardcoded. Moving this to a config file or `prompts.py` would allow for easier updates and "persona" switching without code changes.

## 4. Conclusion
The new implementations for Session 1, 2, and 3 are well-architected from a security perspective. The use of strict input validation and safe execution strategies demonstrates a "security-by-design" approach. Implementing the centralized stealth check is the only significant action item recommended before release.
