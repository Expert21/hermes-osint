# Hermes 🕊️

**Advanced OSINT Intelligence Gathering Tool**

Hermes is a powerful, command-line OSINT (Open Source Intelligence) tool designed for comprehensive digital footprint analysis. Named after the Greek messenger god, Hermes swiftly gathers intelligence across multiple platforms and presents it in professional, actionable reports.

![Version](https://img.shields.io/badge/version-1.5-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![License](https://img.shields.io/badge/license-AGPL--3.0-orange)

> **🚧 Development Notice:** Hermes v2.0 is currently in active development with significant improvements and new capabilities. Stay tuned for updates!

---

## 🎯 What is Hermes?

Hermes is a comprehensive OSINT framework that automates the process of gathering publicly available information about individuals and organizations. It combines multiple intelligence-gathering techniques into a single, easy-to-use tool with professional reporting capabilities.

### Key Capabilities

- 🔍 **Multi-Platform Search** - Automated searches across search engines and social media
- 📧 **Email Intelligence** - Generate and validate potential email addresses
- 🌐 **Domain Analysis** - DNS enumeration and subdomain discovery via Certificate Transparency
- 👤 **Profile Verification** - Advanced content-based verification of social media profiles
- 📊 **Professional Reports** - Export findings in HTML, PDF, Markdown, JSON, or STIX 2.1 format
- 🎭 **Username Variations** - Test multiple username patterns including leet speak
- ⚡ **Smart Caching** - Avoid redundant requests with 24-hour intelligent caching
- 🧙 **Interactive Mode** - Guided wizard for easy configuration
- 🐳 **Docker Orchestration** - Securely run external tools in isolated containers

---

## ✨ Features

### Core Intelligence Gathering

**🔎 Search Engines** - DuckDuckGo, Bing, Yahoo, Brave, Startpage, Yandex with dorking capabilities and advanced evasion (header randomization, referrer spoofing, delays)

**📱 Social Media** - LinkedIn, Twitter/X, GitHub, Instagram, Facebook, Reddit, TikTok, YouTube, Medium, Pinterest, Tumblr with profile verification and quality scoring

**📧 Email Enumeration** - Pattern generation (12+ formats), MX validation, multi-domain support

**🌐 Domain Analysis** - DNS records, Certificate Transparency logs, subdomain enumeration

### Advanced Features

**🎯 Data Intelligence** - Deduplication, correlation analysis, quality scoring (0-100), comprehensive statistics

**👥 Username Variations** - Pattern generation, leet speak, separator variations, number suffixes

**💾 Smart Caching** - SQLite storage with 24-hour expiration for faster repeated scans

**📊 Professional Reports** - HTML, PDF, Markdown, JSON, STIX 2.1 formats

**🧙 Interactive Wizard** - Guided configuration with smart defaults

**📝 Configuration Profiles** - Default, Quick Scan, Deep Scan, or custom with YAML-based settings

**⛓️ Sequential Execution** - Chain tools together for complex workflows (e.g., Domain -> Email -> Breach Check)

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Expert21/hermes-osint.git
cd hermes-osint

# Install dependencies
pip install -r requirements.txt

# First-run setup: Create profiles and .env template
hermes --create-profiles
hermes --init-env

# Edit .env with your API keys, then import
hermes --import-env

# Verify installation (test all modules)
python hermes-test.py
```

### Usage Examples

```bash
# Quick start (interactive mode recommended for beginners)
hermes --interactive

# Individual scan
hermes --target "johndoe" --type individual

# Individual with email enumeration
hermes --target "John Doe" --type individual --email-enum --domain company.com

# Company with domain analysis
hermes --target "example.com" --type company --domain-enum

# Generate reports (JSON, HTML, PDF, Markdown, STIX)
hermes --target "johndoe" --type individual --output report.html

# Deep scan with config profile
hermes --target "johndoe" --type individual --config deep_scan

# Username variations with leet speak
hermes --target "johndoe" --type individual --username-variations --include-leet

# Cache management
hermes --cache-stats
hermes --clear-cache
```

---

## 🛠️ Command-Line Reference

### Required Arguments
- `--target` - Target name (individual or company)
- `--type` - Target type: `individual` or `company`

### Output Options
- `--output` - Output file (default: report.json)
  - Supported formats: `.json`, `.html`, `.md`, `.pdf`, `.stix.json`

### Configuration
- `--config` - Use configuration profile (default, quick_scan, deep_scan)
- `--list-profiles` - List available profiles
- `--create-profiles` - Create default profiles

### Intelligence Modules
- `--email-enum` - Enable email enumeration
- `--domain` - Primary domain for email/DNS
- `--domains` - Additional domains (space-separated)
- `--domain-enum` - Run domain/subdomain enumeration

### Advanced Features
- `--username-variations` - Try username variations
- `--include-leet` - Include leet speak (j0hnd0e)
- `--include-suffixes` - Include number suffixes (johndoe123)
- `--js-render` - Enable JavaScript rendering via Playwright (default: off)
- `--interactive`, `-i` - Interactive wizard mode

### Cache Management
- `--cache-stats` - Show cache statistics
- `--clear-cache` - Clear all cached results

### Control Flags
- `--no-verify` - Skip profile verification (faster)
- `--skip-search` - Skip search engines
- `--skip-social` - Skip social media
- `--js-render` - Enable JavaScript rendering (requires Playwright)
- `--no-progress` - Disable progress indicators
- `--no-dedup` - Disable deduplication

---

## 📝 Current Release

### v1.5 - Foundation & Orchestration

**Latest stable release** focusing on core stability and tool orchestration.

**Key Features:**
- **h8mail Integration**: New Docker adapter for email breach hunting and password analysis.
- **Sequential Execution**: `WorkflowManager` enables chaining tools (e.g., `theHarvester` -> `h8mail`).
- **Core Stability**: Resolved merge conflicts in logging, caching, rate limiting, and secrets management.
- **Docker Security**: Enhanced container isolation and whitelist management.
- **TUI Improvements**: Fixed style conflicts for a consistent user interface.

**For complete version history and detailed changelogs, see [CHANGELOG.md](CHANGELOG.md)**

---

## 🔧 Configuration

### v1.4: Environment-Based Configuration

Hermes v1.4 uses `.env` files for configuration. Generate a template and import your settings:

```bash
# Generate .env template with all available options
hermes --init-env

# Edit .env file with your API keys and preferences
# Then import and encrypt the settings
hermes --import-env

# Verify your configuration
python verify_config.py
```

### Configuration Profiles

Hermes provides three built-in scan profiles in `.osint_profiles/`:

**Default Profile** - Balanced scanning with core features enabled
**Quick Scan** - Fast scans with minimal verification (1-2s delays)
**Deep Scan** - Comprehensive scanning with all features enabled (longer delays)

Create profiles with:
```bash
hermes --create-profiles
hermes --list-profiles
```

Use a specific profile:
```bash
hermes --target "johndoe" --type individual --config deep_scan
```

### .env Configuration Example

```bash
# API Keys (encrypted after import)
GOOGLE_API_KEY=your_key_here
TWITTER_BEARER_TOKEN=your_token_here
GITHUB_ACCESS_TOKEN=your_token_here

# Timing Configuration
TIMING_MIN_DELAY=2.0
TIMING_MAX_DELAY=5.0
TIMING_TIMEOUT=15

# Feature Toggles
FEATURES_EMAIL_ENUMERATION=true
FEATURES_VERIFICATION=true
FEATURES_DEDUPLICATION=true

# Platform Toggles
PLATFORMS_SOCIAL_MEDIA_TWITTER=true
PLATFORMS_SOCIAL_MEDIA_GITHUB=true
PLATFORMS_SEARCH_ENGINES_DUCKDUCKGO=true
```

---

## 📊 Output Formats

**HTML** - Responsive design with embedded CSS, statistics dashboard, color-coded quality scores

**PDF** - Professional formatting with executive summary and quality score breakdown

**Markdown** - Clean, GitHub-compatible format with tables and statistics

**JSON** - Structured data for further analysis and automation

**STIX 2.1** - Industry-standard threat intelligence format (TAXII-compatible)

---

## 🎓 Use Cases

- **Security Research** - Investigate potential threats and vulnerabilities
- **Due Diligence** - Background checks for business partnerships
- **Digital Footprint Analysis** - Understand your own online presence
- **Competitive Intelligence** - Research competitors and market landscape
- **Threat Intelligence** - Gather information for security operations
- **Journalism** - Research subjects for investigative reporting

---

## ⚠️ Legal & Ethical Considerations

**IMPORTANT:** Hermes is designed for legitimate OSINT activities only.

- ✅ Use only on publicly available information
- ✅ Respect platform Terms of Service
- ✅ Comply with local laws and regulations
- ✅ Obtain proper authorization when required
- ❌ Do not use for harassment or stalking
- ❌ Do not use for unauthorized access attempts
- ❌ Do not violate privacy laws

**The developers are not responsible for misuse of this tool.**

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

---

## 📝 License

### Community Edition - AGPL-3.0

Hermes OSINT Tool is licensed under the **GNU Affero General Public License v3.0 (AGPL-3.0)**.

This means:
- ✅ **Free to use** for personal and commercial purposes
- ✅ **Open source** - you can view, modify, and distribute the code
- ✅ **Copyleft** - modifications must also be open-sourced under AGPL-3.0
- ⚠️ **Network use = Distribution** - If you run Hermes as a service, you must share your code

**Key AGPL-3.0 Requirement:** If you modify Hermes and offer it as a web service or SaaS, you **must** make your modified source code available to users.

See the [LICENSE](LICENSE) file for full details.

### Enterprise Edition - Commercial License

Need to use Hermes without AGPL restrictions? We offer a **Commercial License** for:
- 🏢 Running as a proprietary service without releasing source code
- 🔒 Keeping your modifications and integrations private
- 📞 Priority support and SLAs
- ⚖️ Legal indemnification and compliance assistance

**Interested in Enterprise?** Contact: isaiahmyles04@gmail.com or see [COMMERCIAL-LICENSE.md](COMMERCIAL-LICENSE.md) for details.

---

### Why AGPL-3.0?

We chose AGPL-3.0 to:
1. Keep the core tool **free and open** for the security community
2. Ensure improvements benefit everyone (unless you buy a commercial license)
3. Prevent proprietary forks without contribution back
4. Enable sustainable development through enterprise licensing

---

## 🙏 Acknowledgments

- Built with Python and love for the OSINT community
- Inspired by the need for accessible intelligence gathering tools
- Named after Hermes, the Greek god of messages and communication

---

## 📞 Support

For questions, issues, or feature requests, please open an issue on GitHub.

---

**Hermes** - *Swift Intelligence, Divine Insights* 🕊️

