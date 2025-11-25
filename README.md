# Hermes 🕊️

**Advanced OSINT Intelligence Gathering Tool**

Hermes is a powerful, command-line OSINT (Open Source Intelligence) tool designed for comprehensive digital footprint analysis. Named after the Greek messenger god, Hermes swiftly gathers intelligence across multiple platforms and presents it in professional, actionable reports.

![Version](https://img.shields.io/badge/version-1.4-blue)
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

## 📝 Release Notes

### v1.4 - Secure Configuration System (Current Release)

**🔐 Encrypted Configuration Management:**
- **`.env` Template Generation:** New `--init-env` command creates a comprehensive template with 20+ API key placeholders
- **Secure Import:** `--import-env` command encrypts and stores all `.env` values using Fernet encryption
- **Sync Validation:** Automatic `.env` integrity checking prevents running with out-of-sync configuration
- **Comprehensive API Support:** Added support for Bing, Brave, Reddit, BuiltWith, URLScan, and more (20+ total APIs)
- **Type Conversion:** Automatic type inference when applying configuration overrides (strings to bool/int/float)
- **Security Audit:** All API key access now routed through `SecretsManager` - zero direct environment variable access
- **Credential Priority:** Runtime env vars > Encrypted file > YAML config for maximum flexibility

**Key Benefits:**
- 🔒 API keys never stored in plain text
- ✅ Enforced `.env` synchronization prevents configuration drift
- 🚀 Simple setup with `--init-env` template
- 🛡️ SHA-256 hash validation ensures `.env` integrity
- 📦 All customization (timing, features, API keys) through single `.env` file

### v1.3.2 - Proactive Logging Sanitization

**🔒 Enhanced Privacy & Security:**
- **Sanitizer Class:** Centralized proactive sanitization utility for all logging operations
- **URL Query Masking:** All query parameters sanitized in logs (e.g., `?api_key=***`, `?q=***`)
- **Response Truncation:** Long response bodies automatically truncated to 500 chars in logs
- **Email Masking:** Email addresses redacted in logs (e.g., `jo***@example.com`)
- **API Key Redaction:** Enhanced key masking showing only first/last 4 characters
- **Sanitization Coverage:** Updated `AsyncRequestManager`, `search_engines`, and `passive_intelligence` modules
- **Import Fixes:** Corrected relative imports in `profile_verification.py` for better compatibility
- **Test Coverage:** All security implementations verified with comprehensive test suite

**Key Benefits:**
- 🛡️ Prevents PII leakage in log files
- 🔍 Maintains log readability while protecting sensitive data
- 📊 Consistent sanitization rules across entire codebase
- ✅ Proactive security at call-site vs reactive filtering

### v1.3.1 - Security Hardening

**🔒 Enhanced Security Fixes:**
- **API Key Redaction:** Sensitive credentials masked in all log output (4+2 character format)
- **Cache Race Condition:** Retry logic with exponential backoff prevents data loss under rate limiting
- **Redirect Validation:** Manual redirect handling blocks SSRF attacks to private IPs
- **PGP Parser DoS:** Length limits and sanitization prevent denial-of-service attacks
- **Proxy Integrity:** SHA-256 checksum verification for fetched proxy lists
- **Secrets Validation:** HMAC integrity checking for encrypted credentials
- **XXE Prevention:** SafeSoup wrapper eliminates XML entity expansion vulnerabilities
- **Architecture:** Removed singleton pattern from AsyncRequestManager for better testability

**Testing:** All 8 security fixes verified with comprehensive unit tests.

### v1.3.0 - Intelligence Refactor

**🧠 Three-Tier Intelligence Architecture:**
- **Passive Intelligence Module:** New stealth-first data gathering via HIBP breach data, PGP keyservers, and search engine dorking
- **Email Enumeration Refactor:** Passive-first logic checks breaches/PGP before MX validation, reducing noise and rate limits
- **Social Media Refactor:** Two-tier approach (passive dorking → active verification) with exponential backoff rate limiting
- **Tiered Reporting:** Visual confidence scoring with green (confirmed) vs yellow (possible) badges, source metadata tags
- **Scan Logger:** Structured JSON/CSV logging of all scan events, API errors, rate limits, and timeouts
- **Stealth Mode:** `--passive` flag for OPSEC-sensitive investigations (no direct target contact)
- **Enhanced Error Handling:** Graceful degradation with specific handling for rate limits, timeouts, and API errors

**Key Benefits:**
- 🎯 Higher quality results with confidence scoring (0.0-1.0)
- 🚀 Reduced rate limiting through passive-first approach
- 🔍 Better data provenance (HIBP, PGP, Dork, Active Check)
- 📊 Clearer reporting with confirmed vs possible separation

### v1.2.2 - Security Hardening

**🔒 Security Hardening (Medium & Low Severity):**
- **Input Validation:** Integrated `InputValidator` to sanitize all CLI arguments and prevent injection
- **Log Sanitization:** Implemented `SanitizingFormatter` to redact API keys, emails, and IPs from logs
- **Browser Security:** Hardened Playwright launch configuration (no-sandbox, context isolation, anti-fingerprinting)
- **Report Security:** Added CSP, X-Frame-Options, and other security headers to HTML reports
- **Error Handling:** Implemented generic user-facing error messages with secure internal logging
- **Dependencies:** Pinned all dependencies to secure versions

### v1.2.1 - Critical Security Patches

**🛡️ Critical & High Severity Fixes:**
- **Credential Encryption:** Implemented Fernet encryption for secure credential storage
- **SSRF & Injection Protection:** Added comprehensive URL validation and command injection prevention
- **YAML Security:** Fixed path traversal and deserialization vulnerabilities in configuration loading
- **DoS Protection:** Implemented resource limits and proxy validation with IP filtering

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
