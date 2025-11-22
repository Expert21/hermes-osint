# Hermes 🕊️

**Advanced OSINT Intelligence Gathering Tool**

Hermes is a powerful, command-line OSINT (Open Source Intelligence) tool designed for comprehensive digital footprint analysis. Named after the Greek messenger god, Hermes swiftly gathers intelligence across multiple platforms and presents it in professional, actionable reports.

![Version](https://img.shields.io/badge/version-1.2.1-blue)
![Python](https://img.shields.io/badge/python-3.7+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

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

---

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Expert21/hermes-osint.git
cd hermes-osint

# Install dependencies
pip install -r requirements.txt

# Create configuration profiles
hermes --create-profiles

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

## 📝 Release Notes

### v1.2.1 - Security Hardening (Current Release)

**🔒 Security Updates:**
- Encrypted credential storage with Fernet
- SSRF protection with URL validation  
- YAML configuration security (path traversal prevention)
- Proxy validation with IP filtering
- DoS protection with resource limits

**🛡️ Vulnerabilities Fixed:**
- ✅ Command injection in URL construction
- ✅ YAML deserialization attacks
- ✅ Credential exposure (encrypted storage)
- ✅ Server-side request forgery (SSRF)
- ✅ Unvalidated proxy injection
- ✅ Resource exhaustion attacks

**📦 New Security Modules:**
- `input_validator.py`, `secrets_manager.py`, `url_validator.py`, `html_sanitizer.py`, `resource_limiter.py`

**Dependencies:** Added `cryptography`, `bleach`

### v1.2.0 - Async Performance

- Complete async/await implementation
- Proxy rotation with auto-fetch
- JavaScript rendering via Playwright
- Enhanced rate limit evasion
- 10x performance improvement

### v1.1.1 - Initial Release

- Multi-platform OSINT scanning
- Email enumeration and validation
- Profile verification
- Multiple output formats

---

## 🔧 Configuration

### Creating Custom Profiles

Edit `config.yaml` or create a new profile in `.osint_profiles/`:

```yaml
timing:
  request_delay: 2.0
  timeout: 10
  
platforms:
  search_engines:
    duckduckgo: true
    bing: true
  social_media:
    linkedin: true
    github: true
    twitter: true

features:
  email_enumeration: true
  deduplication: true
  progress_indicators: true
  domain_enum: false

thresholds:
  quality_score_minimum: 50
  similarity_threshold: 0.85
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

This project is licensed under the MIT License - see the LICENSE file for details.

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
