# Hermes OSINT v2.0 🏛️⚡

> **Universal OSINT Orchestration Platform**  
> One command. Every tool. Clean results. 💪✨

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/Expert21/hermes-osint/releases)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker Required](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

---

## Overview 🎯

Hermes is a **universal OSINT orchestration platform** that unifies best-in-class open-source intelligence tools into a single, streamlined workflow. Instead of manually running Sherlock, TheHarvester, Holehe, and other tools separately—**wasting precious investigation time** ⏰—Hermes orchestrates them all in parallel, correlates results across sources, eliminates duplicates, and delivers professional reports. 📊

**What makes Hermes different:** 🌟
- 🔒 **Security-first plugin architecture** with static code analysis—because trust is earned, not assumed
- 🐳 **Docker isolation** for zero-trust tool execution—sandbox everything, compromise nothing
- ⚡ **Parallel processing** with intelligent resource management—2x faster than sequential runs
- 🧩 **Cross-tool correlation engine** for relationship mapping—connect the dots automatically
- 🔧 **Extensible design**—add new tools without touching core code (seriously, it's that clean!)

---

## Features 💎

### Tool Orchestration 🎼
- **7 integrated OSINT tools** out of the box (Sherlock, TheHarvester, h8mail, Holehe, PhoneInfoga, Subfinder, Exiftool) 🛠️
- **Plugin architecture** for seamless third-party tool integration 🔌
- **Static security scanner** validates plugin code before execution—no surprises! 🛡️
- **Multi-mode execution**: Docker containers, native binaries, or hybrid auto-detection 🎭

### Performance 🚀
- **Parallel execution** delivers **2x speed improvement** over sequential runs—because time matters ⚡
- **Smart resource scaling** auto-detects CPU cores and memory—works on your laptop AND your server farm 💻
- **Ephemeral containers** spin up, execute, and destroy automatically—zero cleanup required! 🌪️
- **Configurable workers** via `--workers` flag for fine-tuned concurrency control 🎛️

### Intelligence 🧠
- **Cross-tool correlation** identifies connections between disparate data sources—the detective work happens automatically 🔍
- **Fuzzy deduplication** eliminates redundant findings intelligently—no more duplicate noise! 🎯
- **Unified entity schema** normalizes output across all tools—consistent structure, every time 📐
- **Source attribution** tracks which tool discovered each piece of intelligence—full transparency 📝
- **Confidence scoring** quantifies reliability of findings—know what you can trust ⭐

---

## Quick Start 🏃‍♂️💨

### Prerequisites ✅
- Python 3.10 or higher 🐍
- Docker (for containerized tool execution) 🐳

### Installation 📦

```bash
git clone https://github.com/Expert21/hermes-osint.git
cd hermes-osint
pip install -r requirements.txt
pip install .
hermes --doctor  # Health check - make sure everything's ready! 🏥
```

### Basic Usage 🎮

```bash
# Individual investigation (auto-runs Sherlock, Holehe, h8mail, PhoneInfoga, Exiftool)
hermes --target "johndoe" --type individual --email "john@example.com" --phone "+15551234567"

# Company investigation (auto-runs TheHarvester, Subfinder)
hermes --target "ExampleCorp" --type company --domain "example.com"

# Run specific tool - surgical precision! 🎯
hermes --tool sherlock --target "johndoe"
hermes --tool phoneinfoga --phone "+15551234567"
hermes --tool exiftool --file "/path/to/image.jpg"

# Execution modes - you choose the strategy! 🎲
hermes --target "johndoe" --mode docker   # 🔒 Isolated containers (most secure)
hermes --target "johndoe" --mode native   # ⚡ Local binaries (fastest)
hermes --target "johndoe" --mode hybrid   # 🧠 Auto-detect with fallback (default)
```

### Tool Management 🔧

```bash
hermes --doctor          # 🏥 System diagnostics - is everything healthy?
hermes --pull-images     # 📥 Download all Docker images - prep your toolkit!
hermes --remove-images   # 🧹 Clean up Docker images - free up space!
```

---

## Available Tools 🛠️

| Tool | Purpose | Input Type | Status |
|------|---------|------------|--------|
| **Sherlock** 🕵️ | Username enumeration across 300+ sites | Username | ✅ |
| **TheHarvester** 🌾 | Email/subdomain discovery from OSINT sources | Domain | ✅ |
| **h8mail** 📧 | Breach data correlation and lookup | Email | ✅ |
| **Holehe** 🔍 | Email account detection across 120+ platforms | Email | ✅ |
| **PhoneInfoga** 📱 | Phone number OSINT and carrier lookup | Phone | ✅ |
| **Subfinder** 🗺️ | Passive subdomain enumeration | Domain | ✅ |
| **Exiftool** 📸 | Metadata extraction from images/documents | File Path | ✅ |

---

## Command Reference 📚

### Core Arguments 💪

| Argument | Description | Example |
|----------|-------------|---------|
| `--target` | Primary target identifier | `"johndoe"` |
| `--type` | Target classification | `individual` or `company` |
| `--mode` | Execution strategy | `docker`, `native`, `hybrid` |
| `--tool` | Run single tool only | `sherlock` |

### Target-Specific Arguments 🎯

| Argument | Description | Example |
|----------|-------------|---------|
| `--email` | Email for Holehe/h8mail | `"user@example.com"` |
| `--phone` | Phone for PhoneInfoga | `"+15551234567"` |
| `--file` | File path for Exiftool | `"/path/to/image.jpg"` |
| `--domain` | Domain for TheHarvester/Subfinder | `"example.com"` |

### Performance & Configuration ⚙️

| Argument | Description | Default |
|----------|-------------|---------|
| `--workers` | Concurrent worker threads | `10` |
| `--stealth` | Enable passive-only mode 🥷 | `false` |
| `--output` | Output file path | `results.json` |

---

## Architecture 🏗️

```
┌─────────────┐
│ User Input  │ 👤
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ WorkflowManager │ 🎯 (The Conductor)
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌──────────────┐   ┌──────────────┐
│ PluginLoader │🔌 │SecurityScanner│🛡️
└──────┬───────┘   └──────────────┘
       │
       ▼
┌──────────────────────┐
│ ExecutionStrategy    │ 🎭
│ (Docker/Native/Hybrid)│
└──────────┬───────────┘
           │
           ▼
    ┌──────────────┐
    │ Tool Adapters│ 🔧
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
                         └─────────────┘
```

### Key Components 🔑
- **PluginLoader** 🔌: Discovers and validates plugins from `src/plugins/` and `~/.hermes/plugins/`
- **SecurityScanner** 🛡️: AST-based static analysis detects dangerous code patterns—no malicious plugins allowed!
- **ExecutionStrategy** 🎭: Manages Docker/native execution with automatic fallback—smart decisions, zero intervention
- **DockerManager** 🐳: Ephemeral container lifecycle with SHA256 image verification—security baked in
- **ToolAdapter** 🔧: Standardized interface for all integrated tools—plug and play!

---

## Security 🔐

### Container Isolation 🐳🔒
- **SHA256 digest pinning** prevents image tampering—trust, but verify! ✅
- **Ephemeral lifecycle** destroys containers immediately after execution—no trace left behind 🌪️
- **Resource limits** (768MB RAM, 50% CPU, 64 PIDs)—prevent runaway processes 🚦
- **Network isolation** with configurable DNS and proxy support—control the blast radius 🌐
- **Non-root execution** (UID/GID 65534:65534)—privilege separation by default 👥

### Plugin Security 🛡️
- **Static analysis** detects `eval()`, `exec()`, `os.system()`, and shell injection patterns—we catch the bad stuff BEFORE it runs! 🚨
- **Two-tier trust model** separates Tool plugins from Core plugins—clear boundaries 🏛️
- **Capability declarations** explicitly define required permissions—no surprises, only transparency 📋

### Input Validation ✅
- **Path traversal protection** for file operations—can't escape the sandbox! 🚫
- **Command injection prevention** via list-based subprocess arguments—shellshock-proof 💪
- **Encrypted credential storage** using OS-native keyring—your secrets stay secret 🔐

---

## Output Formats 📄

Hermes generates reports in multiple formats based on file extension—**your data, your way!** 🎨

📦 **JSON** - Structured data for programmatic consumption and automation

📝 **Markdown** - Clean, GitHub-compatible format with embedded tables

🌐 **HTML** - Responsive design with embedded CSS and interactive statistics dashboard

📄 **PDF** - Professional formatting with executive summary and quality metrics

📊 **CSV** - Simple tabular format for spreadsheet import

🔒 **STIX 2.1** - Industry-standard threat intelligence format (TAXII-compatible)

---

## License ⚖️

### AGPL-3.0 (Community Edition) 🆓

Hermes OSINT is licensed under the **GNU Affero General Public License v3.0**.

**What this means:** 💡
- ✅ Free to use for personal and commercial purposes
- ✅ Open source—view, modify, and distribute the code
- ✅ Copyleft—modifications must also be open-sourced under AGPL-3.0
- ⚠️ **Network use = Distribution**—if you run Hermes as a service, you **must** share your source code

**Critical requirement:** ⚠️ If you modify Hermes and offer it as a web service or SaaS, you **must** make your modified source code available to users.

See the [LICENSE](LICENSE) file for complete terms.

**Third-party tools:** 🛠️ Each integrated tool maintains its own license (Sherlock: MIT, TheHarvester: GPL-2.0, h8mail: BSD-3-Clause, Holehe: GPL-3.0, etc.)

---

## Use Cases 💼

🔍 **Security Research** - Investigate potential threats and attack surface enumeration

🤝 **Due Diligence** - Background verification for business partnerships and hiring

👣 **Digital Footprint Analysis** - Understand your organization's public exposure

📈 **Competitive Intelligence** - Research competitors and market landscape

🎯 **Threat Intelligence** - Collect indicators for security operations centers

📰 **Investigative Journalism** - Research subjects for investigative reporting

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

**Hermes v2.0** 🏛️⚡  
*One Command. Every Tool. Clean Results.*

---

**Built with precision. Deployed with confidence. Trusted by investigators worldwide.** 🌍🔍

Made with 💪 and ☕ by someone who believes OSINT should be **fast, secure, and accessible**.

</div>