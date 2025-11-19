# OSINT Tool - Advanced Open Source Intelligence Gathering

A comprehensive, cross-platform command-line OSINT tool for gathering intelligence on individuals and companies through social media platforms, search engines, and email enumeration.

## 🚀 Features

### Core Capabilities
- **Social Media Reconnaissance** - Automated profile discovery across 8+ platforms (Twitter/X, LinkedIn, GitHub, Instagram, Facebook, Pinterest, TikTok)
- **Search Engine Intelligence** - Multi-engine search with Google dorking techniques (DuckDuckGo, Bing)
- **Profile Verification** - Advanced verification system to reduce false positives
- **Rate Limit Evasion** - Smart delays, rotating user agents, and detection avoidance

### 🆕 Priority 1 Enhancements

#### 📧 Email Enumeration
- Generates 12+ common email patterns from names
- Email format validation with regex and validators library
- MX record verification to confirm domains can receive email
- Multi-domain support for comprehensive coverage

#### 🔄 Data Deduplication & Correlation
- Intelligent URL normalization and duplicate removal
- Quality scoring system (0-100) for all results
- Cross-platform connection identification
- Similarity-based fuzzy matching (85% threshold)

#### 📊 Progress Tracking
- Real-time status updates for all operations
- Visual progress bars with ETA calculation
- Module-specific progress indicators
- Configurable (can be disabled)

#### ⚙️ Configuration Management
- YAML-based configuration profiles
- Platform enable/disable toggles
- Customizable timing and thresholds
- Preset profiles: `default`, `quick_scan`, `deep_scan`

## 📦 Installation

### Prerequisites
- Python 3.7+
- pip

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd osint_tool

# Install dependencies
pip install -r requirements.txt

# Create configuration profiles
python main.py --create-profiles
```

### Dependencies
- `requests` - HTTP requests
- `beautifulsoup4` - HTML parsing
- `colorama` - Colored terminal output
- `python-dotenv` - Environment variable management
- `urllib3` - URL handling
- `tqdm` - Progress bars
- `pyyaml` - YAML configuration
- `dnspython` - DNS/MX lookups
- `validators` - Email validation

## 🎯 Usage

### Basic Scan
```bash
# Individual target
python main.py --target "johndoe" --type individual

# Company target
python main.py --target "openai" --type company --output report.csv
```

### Email Enumeration
```bash
# Generate email addresses for a target
python main.py --target "John Doe" --type individual \
  --email-enum --domain company.com

# Multiple domains
python main.py --target "John Doe" --type individual \
  --email-enum --domains company.com example.org
```

### Configuration Profiles
```bash
# List available profiles
python main.py --list-profiles

# Use a specific profile
python main.py --target "johndoe" --type individual --config quick_scan

# Quick scan (minimal verification, faster)
python main.py --target "johndoe" --type individual --config quick_scan

# Deep scan (all features enabled)
python main.py --target "johndoe" --type individual --config deep_scan
```

### Advanced Options
```bash
# Skip specific modules
python main.py --target "johndoe" --type individual --skip-search --skip-social

# Disable verification (faster)
python main.py --target "johndoe" --type individual --no-verify

# Disable progress indicators
python main.py --target "johndoe" --type individual --no-progress

# Disable deduplication
python main.py --target "johndoe" --type individual --no-dedup

# With verification helpers
python main.py --target "johndoe" --type individual \
  --company "Google" --location "San Francisco" --email "john@example.com"
```

### Complete Example
```bash
# Full scan with all Priority 1 features
python main.py \
  --target "John Doe" \
  --type individual \
  --email-enum \
  --domain company.com \
  --company "Tech Corp" \
  --location "San Francisco" \
  --config default \
  --output full_scan.json
```

## 📋 Command-Line Arguments

### Required Arguments
- `--target TARGET` - Target name (individual or company)
- `--type {individual,company}` - Type of target

### Optional Arguments
- `--output OUTPUT` - Output file (.json or .csv, default: report.json)
- `--config PROFILE` - Configuration profile to use
- `--email-enum` - Enable email enumeration
- `--domain DOMAIN` - Domain for email enumeration
- `--domains DOMAIN [DOMAIN ...]` - Multiple domains for email enumeration

### Flags
- `--no-verify` - Skip profile verification (faster)
- `--skip-search` - Skip search engines
- `--skip-social` - Skip social media
- `--no-progress` - Disable progress indicators
- `--no-dedup` - Disable deduplication

### Verification Helpers
- `--company COMPANY` - Target's company (helps verification)
- `--location LOCATION` - Target's location (helps verification)
- `--email EMAIL` - Known email (helps verification)

### Utility Commands
- `--list-profiles` - List available configuration profiles
- `--create-profiles` - Create default configuration profiles

## 📁 Output Formats

### JSON (Default)
```json
{
  "target": "John Doe",
  "target_type": "individual",
  "search_engines": [...],
  "social_media": [...],
  "emails": {
    "emails_generated": [...],
    "valid_format_count": 12,
    "domains_with_mx": [...]
  },
  "connections": [...],
  "statistics": {
    "avg_quality_score": 72.5,
    "high_quality_results": 8,
    "duplicates_removed": 3
  }
}
```

### CSV
```bash
python main.py --target "johndoe" --type individual --output report.csv
```

## ⚙️ Configuration

### Configuration Files
Configuration profiles are stored in `.osint_profiles/` directory as YAML files.

### Default Configuration Structure
```yaml
timing:
  min_delay: 2.0              # Minimum delay between requests
  max_delay: 5.0              # Maximum delay
  timeout: 15                 # Request timeout
  rate_limit_backoff: 30      # Backoff when rate limited

platforms:
  social_media:
    twitter: true
    instagram: true
    facebook: true
    linkedin: true
    github: true
    pinterest: true
    tiktok: true
  search_engines:
    duckduckgo: true
    bing: true

features:
  email_enumeration: true
  verification: true
  deduplication: true
  progress_indicators: true

thresholds:
  similarity_threshold: 0.85   # URL deduplication threshold
  quality_score_minimum: 0     # Minimum quality score
  max_results_per_search: 10   # Results per search query
```

### Customizing Profiles
Edit YAML files in `.osint_profiles/` to customize:
- Timing and delays
- Platform selection
- Feature toggles
- Quality thresholds

## 🎨 Features Breakdown

### Email Enumeration
Generates common email patterns:
- `firstname.lastname@domain.com`
- `firstname_lastname@domain.com`
- `firstname-lastname@domain.com`
- `firstnamelastname@domain.com`
- `f.lastname@domain.com`
- `firstname.l@domain.com`
- And more...

### Quality Scoring System
Each result receives a score (0-100) based on:
- **Verification Status** (40 points) - Profile verified as authentic
- **Description/Content** (20 points) - Has meaningful description
- **Title** (15 points) - Has proper title
- **Valid URL** (15 points) - Properly formatted URL
- **Source Credibility** (10 points) - From trusted platform

### Deduplication
- Normalizes URLs (removes tracking parameters)
- Fuzzy matching with 85% similarity threshold
- Merges duplicate findings across modules
- Preserves highest quality version

## 🏗️ Project Structure

```
osint_tool/
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
├── config.yaml               # Default configuration template
├── .osint_profiles/          # Configuration profiles
│   ├── default.yaml
│   ├── quick_scan.yaml
│   └── deep_scan.yaml
├── src/
│   ├── core/
│   │   ├── logger.py         # Logging configuration
│   │   ├── config.py         # Environment config loader
│   │   ├── config_manager.py # YAML configuration manager
│   │   ├── progress_tracker.py # Progress bars and ETA
│   │   └── deduplication.py  # Deduplication engine
│   ├── modules/
│   │   ├── search_engines.py # Search engine module
│   │   ├── social_media.py   # Social media checker
│   │   ├── email_enumeration.py # Email pattern generator
│   │   └── profile_verification.py # Profile verification
│   └── reporting/
│       └── generator.py      # Report generation
└── README.md
```

## 🔒 Privacy & Ethics

**Important**: This tool is for educational and authorized security research purposes only.

- Always obtain proper authorization before scanning targets
- Respect rate limits and terms of service
- Do not use for harassment, stalking, or malicious purposes
- Be aware of local laws regarding data collection
- Use responsibly and ethically

## 🛠️ Troubleshooting

### Rate Limiting
If you encounter rate limiting:
- Increase delays in configuration: `timing.min_delay` and `timing.max_delay`
- Use `--config quick_scan` for fewer queries
- Enable longer backoff: `timing.rate_limit_backoff`

### DNS/MX Lookup Failures
- Ensure you have internet connectivity
- Check firewall settings for DNS queries
- Some domains may not have MX records (normal)

### Missing Dependencies
```bash
pip install -r requirements.txt --upgrade
```

## 📊 Example Output

```
============================================================
Starting OSINT scan for target: John Doe (individual)
Using configuration profile: default
============================================================

[Email Enumeration] Generating potential email addresses...
------------------------------------------------------------
✓ Generated 12 potential email addresses

[Search Engines] Running search engine modules...
------------------------------------------------------------
DuckDuckGo returned 10 results for: John Doe
✓ Search complete: 10 total results collected

[Social Media] Running social media modules...
------------------------------------------------------------
✓ Found verified profile on LinkedIn: https://linkedin.com/in/johndoe
✓ Found verified profile on GitHub: https://github.com/johndoe
Completed social media checks: 2 profiles found

[Deduplication] Processing results...
------------------------------------------------------------
Deduplication: 12 → 11 results (1 duplicates removed)
✓ Deduplication complete

============================================================
Generating report to report.json...
✓ Report saved successfully

============================================================
Scan complete.
  Search Results: 10
  Social Profiles: 2
  Email Addresses: 12
  High Quality Results: 8
  Avg Quality Score: 72.5/100
  Connections Found: 1
============================================================
```

## 🚧 Roadmap

### ✅ Priority 1 - Complete
- [x] Email Enumeration Module
- [x] Data Deduplication & Correlation
- [x] Progress Indicators
- [x] Configuration File System

### 🔜 Priority 2 - Coming Soon
- [ ] Enhanced Reporting (HTML, PDF, Markdown, STIX)
- [ ] Resume/Caching System
- [ ] Username Variation Generator
- [ ] Additional Export Formats

### 💡 Priority 3 - Future
- [ ] Domain/Subdomain Enumeration
- [ ] Interactive Mode
- [ ] Certificate Transparency Logs

## 📝 License

[Your License Here]

## 🤝 Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for bugs and feature requests.

## ⚠️ Disclaimer

This tool is provided for educational and research purposes only. The authors are not responsible for any misuse or damage caused by this tool. Always ensure you have permission to gather information about your targets and comply with all applicable laws and regulations.
