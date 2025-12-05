# Hermes OSINT v2.0

**Universal OSINT Orchestration Platform**  
*One Command. Every Tool. Clean Results.*

![Version](https://img.shields.io/badge/version-2.0-blue)
[![License: AGPL-3.0](https://img.shields.io/badge/License-AGPL%203.0-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Docker Required](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

---

## What is Hermes?

Hermes is a **universal OSINT orchestration platform** that integrates best-in-class open-source intelligence tools into one unified workflow. Instead of manually running Sherlock, TheHarvester, Holehe, and others separately, Hermes runs them all, correlates the results, removes duplicates, and delivers professional reports.

---

## Features

### Tool Orchestration
- **7 integrated OSINT tools** - Sherlock, TheHarvester, h8mail, Holehe, PhoneInfoga, Subfinder, Exiftool
- **Plugin architecture** - Add custom tools without modifying core code
- **Security-first design** - Static analysis scanner for plugin validation
- **Docker + Native modes** - Run tools in isolated containers or use local installs

### Performance
- **Parallel execution** - 2x faster than sequential runs
- **Smart resource scaling** - Auto-detects system capabilities
- **Ephemeral containers** - Spin up, execute, destroy with automatic cleanup
- **Configurable workers** - Control concurrency (`--workers`)

### Intelligence
- **Cross-tool correlation** - Identify connections across data sources
- **Duplicate removal** - Fuzzy matching eliminates redundant results
- **Result normalization** - Unified entity schema across all tools
- **Source attribution** - Know where each finding came from

---

## Quick Start

### Prerequisites
- Python 3.10+
- Docker

### Installation

```bash
git clone https://github.com/Expert21/osint-tool.git
cd osint-tool
pip install -r requirements.txt
pip install .
hermes --doctor
```

### Usage

```bash
# Individual investigation (auto-runs Sherlock, Holehe, h8mail, PhoneInfoga, Exiftool)
hermes --target "johndoe" --type individual --email "john@example.com"

# Company investigation (auto-runs TheHarvester, Subfinder)
hermes --target "ExampleCorp" --type company --domain "example.com"

# Run specific tool
hermes --tool sherlock --target "johndoe"
hermes --tool phoneinfoga --phone "+15551234567"
hermes --tool exiftool --file "/path/to/image.jpg"

# Execution modes
hermes --target "johndoe" --mode docker   # Isolated containers
hermes --target "johndoe" --mode native   # Local installs
hermes --target "johndoe" --mode hybrid   # Auto-detect (default)
```

### Tool Management

```bash
hermes --doctor        # System diagnostics
hermes --pull-images   # Download Docker images
hermes --remove-images # Remove Docker images
```

---

## Available Tools

| Tool | Purpose | Target | Status |
|------|---------|--------|--------|
| **Sherlock** | Username enumeration (300+ sites) | Username | ✅ |
| **TheHarvester** | Email/subdomain discovery | Domain | ✅ |
| **h8mail** | Breach data correlation | Email | ✅ |
| **Holehe** | Email account detection | Email | ✅ |
| **PhoneInfoga** | Phone number OSINT | Phone | ✅ |
| **Subfinder** | Subdomain enumeration | Domain | ✅ |
| **Exiftool** | Metadata extraction | File | ✅ |

---

## CLI Arguments

| Argument | Description | Example |
|----------|-------------|---------|
| `--target` | Primary target (username/company) | `"johndoe"` |
| `--type` | Target type: `individual` or `company` | `individual` |
| `--mode` | Execution: `docker`, `native`, `hybrid` | `docker` |
| `--tool` | Run specific tool only | `sherlock` |
| `--email` | Email for Holehe/h8mail | `"john@example.com"` |
| `--phone` | Phone for PhoneInfoga | `"+15551234567"` |
| `--file` | File path for Exiftool | `"/path/to/image.jpg"` |
| `--domain` | Domain for TheHarvester/Subfinder | `"example.com"` |
| `--workers` | Concurrent workers (default: 10) | `8` |
| `--stealth` | Enable stealth mode | |
| `--output` | Output file path | `results.json` |

---

## Architecture

```
User Request → WorkflowManager → PluginLoader → SecurityScanner
                                      ↓
                              ExecutionStrategy
                              (Docker/Native/Hybrid)
                                      ↓
                              Tool Adapters → Results
                                      ↓
                              Deduplication → Report
```

### Key Components
- **PluginLoader** - Discovers and loads plugins from `src/plugins/`
- **SecurityScanner** - Validates plugin code safety via AST analysis
- **ExecutionStrategy** - Manages Docker/Native execution with entrypoint override support
- **DockerManager** - Ephemeral container lifecycle with SHA256 verification
- **ToolAdapter** - Standardized interface for all tools

---

## Security

### Docker Isolation
- SHA256 digest pinning for image verification
- Ephemeral containers destroyed after use
- Resource limits (768MB RAM, 50% CPU)
- Network isolation with proxy support
- Non-root execution (user 65534:65534)

### Plugin Security
- Static analysis detects dangerous patterns (`eval`, `exec`, `os.system`)
- Two-tier trust model (Tool vs Core plugins)
- Capability declarations required

### Input Validation
- Path traversal protection
- Command injection prevention (list-based args)
- Encrypted credential storage via OS keyring

---

## 📊 Output Formats

**HTML** - Responsive design with embedded CSS, statistics dashboard, color-coded quality scores

**PDF** - Professional formatting with executive summary and quality score breakdown

**Markdown** - Clean, GitHub-compatible format with tables and statistics

**JSON** - Structured data for further analysis and automation

**STIX 2.1** - Industry-standard threat intelligence format (TAXII-compatible)

**CSV** - Simple, tabular format for easy import into spreadsheets

---

## License

### Community Edition - AGPL-3.0

Hermes OSINT Tool is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:
- ✅ **Free to use** for personal and commercial purposes
- ✅ **Open source** - you can view, modify, and distribute the code
- ✅ **Copyleft** - modifications must also be open-sourced under AGPL-3.0
- ⚠️ **Network use = Distribution** - If you run Hermes as a service, you must share your code

**Key AGPL-3.0 Requirement:** If you modify Hermes and offer it as a web service or SaaS, you **must** make your modified source code available to users.

See the [LICENSE](LICENSE) file for full details.

---

### Third-Party Tools
Each integrated tool has its own license (Sherlock: MIT, TheHarvester: GPL-2.0, h8mail: BSD-3-Clause, Holehe: GPL-3.0, etc.)

---

## 🎓 Use Cases

- **Security Research** - Investigate potential threats and vulnerabilities
- **Due Diligence** - Background checks for business partnerships
- **Digital Footprint Analysis** - Understand your own online presence
- **Competitive Intelligence** - Research competitors and market landscape
- **Threat Intelligence** - Gather information for security operations
- **Journalism** - Research subjects for investigative reporting

---

## ⚠️ Legal & Ethical Disclaimer
**For legitimate OSINT activities only. Users are responsible for obtaining proper authorization, complying with local laws, and using ethically.**

- ✅ Use only on publicly available information
- ✅ Respect platform Terms of Service
- ✅ Comply with local laws and regulations
- ✅ Obtain proper authorization when required
- ❌ Do not use for harassment or stalking
- ❌ Do not use for unauthorized access attempts
- ❌ Do not violate privacy laws

**The developers are not responsible for misuse of this tool.**

---

## Author

Built by **Isaiah Myles** aka "Expert21" ([@Expert21](https://github.com/Expert21))

- **Issues:** [GitHub Issues](https://github.com/Expert21/osint-tool/issues)
- **Email:** isaiahmyles04@protonmail.com

---

*Hermes v2.0: One Command. Every Tool. Clean Results.* 🚀
