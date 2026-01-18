# Hermes OSINT v3.0 🏛️🧠

> **The Agentic OSINT Analyst**  
> Conversational AI-driven investigations. Natural language. Expert results. 🤖✨

[![Version](https://img.shields.io/badge/version-3.0.0-blue.svg)](https://github.com/Expert21/hermes-osint/releases)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker Required](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)
[![Ollama Powered](https://img.shields.io/badge/ollama-powered-green.svg)](https://ollama.ai/)

---

## What's New in v3.0 🎉

**Hermes 3.0** represents a complete paradigm shift from pipeline-based tool orchestration to a **conversational AI-driven investigation platform**. Powered by local LLMs via Ollama, Hermes now understands natural language queries, autonomously selects and executes tools, and synthesizes findings into coherent intelligence reports.

### 🧠 Agentic Intelligence
- **Natural Language Interface** - Ask questions like "Find everything about @johndoe" instead of memorizing CLI flags
- **ReAct Pattern** - Think → Act → Observe cycle for intelligent, iterative investigations
- **Autonomous Tool Selection** - LLM decides which tools to run based on context
- **Citation-Based Reporting** - Every finding is attributed to its source tool

### 💬 Interactive TUI
- **Conversational REPL** - Chat with Hermes in a pentester-themed terminal interface
- **Session Persistence** - Save and resume investigations with `/save` and `/load`
- **Context Management** - Automatic summarization prevents token overflow in long sessions
- **Real-time Status Bar** - Model, context usage, and stealth mode at a glance

### 🔄 Flexible Execution Modes
- **TUI Mode** (default) - Full conversational experience with Ollama
- **Headless Mode** - `--headless --query "..."` for scripting and automation
- **Legacy Mode** - `hermes sherlock <user>` for direct tool access without LLM

---

## Overview 🎯

Hermes is a **universal OSINT orchestration platform** that unifies best-in-class open-source intelligence tools into a single, AI-powered workflow. Instead of manually running Sherlock, TheHarvester, Holehe, and other tools separately—**wasting precious investigation time** ⏰—Hermes's agentic core understands your intent, orchestrates tools intelligently, correlates results across sources, and delivers professional reports. 📊

**What makes Hermes different:** 🌟
- 🧠 **Agentic AI** with ReAct pattern—let the LLM drive your investigation
- 💬 **Natural language queries**—no flags to memorize, just describe what you need
- 🔒 **Security-first plugin architecture** with static code analysis—trust is earned
- 🐳 **Docker isolation** for zero-trust tool execution—sandbox everything
- ⚡ **Parallel processing** with intelligent resource management—2x faster than sequential
- 🧩 **Cross-tool correlation engine** for relationship mapping—connect the dots automatically
- 🔧 **Extensible design**—add new tools without touching core code

---

## Features 💎

### Agentic Core 🤖
- **ReAct Agent Loop** with Think → Act → Observe cycle
- **Ollama Integration** for local LLM inference (Llama 3, Mistral, etc.)
- **Tool Registry** with JSON Schema definitions for function calling
- **Context Manager** with rolling summaries (24k char limit for 8B models)
- **Session Store** for saving/loading investigation state

### Interactive TUI 💻
- **prompt_toolkit REPL** with persistent history (`~/.hermes_history`)
- **Pentester-themed styling** with green/cyan/orange accents
- **Dynamic status bar** showing model, context %, and mode
- **Slash commands**: `/help`, `/tools`, `/status`, `/save`, `/load`, `/export`, `/clear`, `/exit`

### Tool Orchestration 🎼
- **6 integrated OSINT tools** out of the box (Sherlock, TheHarvester, h8mail, Holehe, PhoneInfoga, Subfinder) 🛠️
- **Plugin architecture** for seamless third-party tool integration 🔌
- **Static security scanner** validates plugin code before execution—no surprises! 🛡️
- **Multi-mode execution**: Docker containers, native binaries, or hybrid auto-detection 🎭
- **Stealth mode enforcement** - blocks active probing tools when enabled 🥷

### Performance 🚀
- **Parallel execution** delivers **2x speed improvement** over sequential runs ⚡
- **Smart resource scaling** auto-detects CPU cores and memory 💻
- **Ephemeral containers** spin up, execute, and destroy automatically 🌪️
- **Configurable workers** via `--workers` flag for fine-tuned concurrency 🎛️

### Intelligence 🧠
- **Cross-tool correlation** identifies connections between disparate data sources 🔍
- **Fuzzy deduplication** eliminates redundant findings intelligently 🎯
- **Unified entity schema** normalizes output across all tools 📐
- **Source attribution** tracks which tool discovered each finding 📝
- **Confidence scoring** quantifies reliability of findings ⭐

---

## Quick Start 🏃‍♂️💨

### Prerequisites ✅
- Python 3.10 or higher 🐍
- Docker (for containerized tool execution) 🐳
- Ollama with a model installed (for TUI/agentic mode) 🧠

### Installation 📦

```bash
# Clone and install
git clone https://github.com/Expert21/hermes-osint.git
cd hermes-osint
pip install -r requirements.txt
pip install .

# Install Ollama and pull a model
curl -fsSL https://ollama.com/install.sh | sh
ollama pull llama3.1:8b

# Health check
hermes --doctor  # 🏥 Make sure everything's ready!
```

### Basic Usage 🎮

```bash
# 🧠 TUI Mode (default) - Conversational AI interface
hermes
# Then chat naturally: "Find social accounts for johndoe"

# 📜 Headless Mode - For scripting and automation
hermes --headless --query "Investigate the domain example.com"

# 🔧 Legacy Mode - Direct tool access (no LLM required)
hermes sherlock johndoe
hermes theharvester example.com
hermes holehe user@example.com
```

### TUI Commands 💬

```bash
/help          # Show all commands
/tools         # List available investigation tools
/status        # Show current session status
/save          # Save session to file
/load          # Load a previous session
/sessions      # List all saved sessions
/export FILE   # Export report (md, pdf, html, csv, stix)
/stealth       # Toggle stealth mode
/clear         # Clear conversation
/exit          # Exit Hermes
```

### Advanced Usage 🎯

```bash
# Stealth mode - passive tools only
hermes --stealth
# Blocks: sherlock, holehe, phoneinfoga
# Allows: theharvester, subfinder, h8mail

# Specific model selection
hermes --model mistral:7b

# Headless with output
hermes --headless --query "Find subdomains for target.com" --output report.md
```

---

## Available Tools 🛠️

| Tool | Purpose | Input Type | Stealth | Status |
|------|---------|------------|---------|--------|
| **Sherlock** 🕵️ | Username enumeration across 300+ sites | Username | ❌ | ✅ |
| **TheHarvester** 🌾 | Email/subdomain discovery from OSINT sources | Domain | ✅ | ✅ |
| **h8mail** 📧 | Breach data correlation and lookup | Email | ✅ | ✅ |
| **Holehe** 🔍 | Email account detection across 120+ platforms | Email | ❌ | ✅ |
| **PhoneInfoga** 📱 | Phone number OSINT and carrier lookup | Phone | ❌ | ✅ |
| **Subfinder** 🗺️ | Passive subdomain enumeration | Domain | ✅ | ✅ |

---

## Architecture 🏗️

### v3.0 Agentic Architecture

```
User Input → CLI (cli.py)
                ├── TUI Mode → AgentLoop → Ollama → ToolExecutor → Adapters
                ├── Headless → AgentLoop → Single Query → Report
                └── Legacy → ToolExecutor Direct (no LLM)
```

### Component Flow

```
┌─────────────┐
│ User Query  │ 💬 "Find info about johndoe"
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│   AgentLoop     │ 🧠 ReAct: Think → Act → Observe
│  (agent_loop.py)│
└────────┬────────┘
         │
         ├──────────────────┬────────────────┐
         ▼                  ▼                ▼
┌──────────────┐   ┌───────────────┐  ┌─────────────┐
│ ToolRegistry │   │ContextManager │  │ SessionStore│
│(tool_registry)│  │(context_mgr.py)│ │(session_store)│
└──────┬───────┘   └───────────────┘  └─────────────┘
       │
       ▼
┌──────────────────────┐
│   ToolExecutor       │ 🔧 Validates + Executes
│  (tool_executor.py)  │
└──────────┬───────────┘
           │
           ▼
┌─────────────────────────┐
│ ExecutionStrategy       │ 🎭 Docker/Native/Hybrid
│ (execution_strategy.py) │
└──────────┬──────────────┘
           │
           ▼
    ┌──────────────┐
    │ Tool Adapters│ 🔌 Sherlock, TheHarvester, etc.
    └──────┬───────┘
           │
           ▼
    ┌─────────────┐      ┌──────────────┐
    │ Raw Results │─────▶│Deduplication │ ✨
    └─────────────┘      └──────┬───────┘
                                │
                                ▼
                         ┌─────────────┐
                         │   Report    │ 📊
                         │ (exporter)  │
                         └─────────────┘
```

### Key Components 🔑

#### Agent Layer (`src/agent/`)
- **AgentLoop** 🧠: ReAct pattern with Ollama function calling
- **ToolRegistry** 📋: JSON Schema definitions for LLM tool use
- **ToolExecutor** 🔧: Validates inputs, enforces stealth, bridges to adapters
- **ContextManager** 📊: Rolling summaries, prevents token overflow
- **SessionStore** 💾: JSON persistence for save/load functionality
- **TUI** 💻: prompt_toolkit REPL with pentester styling

#### Orchestration Layer (`src/orchestration/`)
- **ExecutionStrategy** 🎭: Docker/Native/Hybrid mode selection
- **DockerManager** 🐳: Ephemeral containers with SHA256 verification
- **TaskManager** ⚡: Parallel execution with resource limits

#### Security Layer (`src/security/`)
- **PluginSecurityScanner** 🛡️: AST-based static analysis
- **InputValidator** ✅: Injection prevention, path traversal protection
- **SecretsManager** 🔐: Encrypted credential storage

---

## Security 🔐

### Agent Safety 🛡️
- **Grounding rules** prevent LLM speculation—cite sources or stay silent
- **Stealth mode enforcement** blocks active probing tools when enabled
- **Input validation** on all tool parameters before execution
- **Context limits** prevent prompt injection via token overflow

### Container Isolation 🐳🔒
- **SHA256 digest pinning** prevents image tampering ✅
- **Ephemeral lifecycle** destroys containers immediately after execution 🌪️
- **Resource limits** (768MB RAM, 50% CPU, 64 PIDs) 🚦
- **Network isolation** with configurable DNS and proxy support 🌐
- **Non-root execution** (UID/GID 65534:65534) 👥

### Plugin Security 🛡️
- **Static analysis** detects `eval()`, `exec()`, `os.system()`, and shell injection 🚨
- **Two-tier trust model** separates Tool plugins from Core plugins 🏛️
- **Capability declarations** explicitly define required permissions 📋

---

## Output Formats 📄

Hermes generates reports in multiple formats via `/export`—**your data, your way!** 🎨

📦 **JSON** - Structured data for programmatic consumption

📝 **Markdown** - Clean, GitHub-compatible format with tables

🌐 **HTML** - Responsive design with embedded CSS and statistics

📄 **PDF** - Professional formatting with executive summary

📊 **CSV** - Simple tabular format for spreadsheet import

🔒 **STIX 2.1** - Industry-standard threat intelligence format

---

## License ⚖️

### AGPL-3.0 (Community Edition) 🆓

Hermes OSINT is licensed under the **GNU Affero General Public License v3.0**.

**What this means:** 💡
- ✅ Free to use for personal and commercial purposes
- ✅ Open source—view, modify, and distribute the code
- ✅ Copyleft—modifications must also be open-sourced under AGPL-3.0
- ⚠️ **Network use = Distribution**—if you run Hermes as a service, you **must** share your source code

See the [LICENSE](LICENSE) file for complete terms.

---

## Use Cases 💼

🔍 **Security Research** - Investigate threats with natural language queries

🤝 **Due Diligence** - "Tell me everything about this person/company"

👣 **Digital Footprint Analysis** - Understand your organization's exposure

📈 **Competitive Intelligence** - Research competitors conversationally

🎯 **Threat Intelligence** - Collect indicators with AI-driven triage

📰 **Investigative Journalism** - Let Hermes connect the dots

---

## Legal & Ethical Disclaimer ⚖️

**For authorized OSINT activities only.** ⚠️ Users are solely responsible for obtaining proper authorization, complying with applicable laws, and using this tool ethically.

**Permitted uses:** ✅
- Publicly available information gathering
- Authorized security assessments
- Personal digital footprint analysis
- Compliance with local laws and regulations

**Prohibited uses:** 🚫
- Harassment, stalking, or intimidation
- Unauthorized access attempts
- Privacy law violations
- Platform Terms of Service violations

**The developers assume no liability for misuse of this tool.** 🙅‍♂️

---

## Contributing 🤝

Contributions are welcome! 🎉 Please see [PLUGIN_DEVELOPMENT.md](PLUGIN_DEVELOPMENT.md) for plugin creation guidelines and [USAGE.md](USAGE.md) for detailed usage documentation.

**Got ideas? Found bugs? Want to add a tool?** Open an issue or submit a PR! 💪

---

## Author ✍️

**Isaiah Myles** ([@Expert21](https://github.com/Expert21)) 

*Emerging cybersecurity professional | Pentester mindset | Builder of tools that matter* 🛠️⚡

- 🐛 **Issues**: [GitHub Issues](https://github.com/Expert21/hermes-osint/issues)
- 📧 **Email**: isaiahmyles04@protonmail.com

---

<div align="center">

**Hermes v3.0** 🏛️🧠  
*The Agentic OSINT Analyst*

---

**Conversational AI. Expert Tools. Unified Intelligence.**

Made with 💪 and ☕ by someone who believes OSINT should be **intelligent, secure, and accessible**.

</div>