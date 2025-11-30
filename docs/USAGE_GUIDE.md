<!--
Hermes OSINT - V2.0 Alpha
This project is currently in an alpha state.
-->

# Hermes OSINT - Usage Guide

## Quick Start

### Prerequisites
- **Docker** installed and running (required for Docker mode)
- **Python 3.10+**
- Dependencies installed: `pip install -r requirements.txt`

### Installation
```bash
git clone https://github.com/Expert21/hermes-osint
cd hermes-osint
pip install -r requirements.txt
```

---

## Basic Commands

### System Diagnostics
Check if your system is properly configured:
```bash
python main.py --doctor
```

This checks:
- Docker availability
- Internet connectivity
- Configuration validity
- Native tool installations (sherlock, theharvester, holehe, etc.)

### Pull Docker Images
Download all required Docker images for tool execution:
```bash
python main.py --pull-images
```

---

## Core Functionality

### 1. Social Media Enumeration

**Basic scan for an individual:**
```bash
python main.py --target "johndoe" --type individual
```

**Basic scan for a company:**
```bash
python main.py --target "Acme Corp" --type company
```

**Supported platforms:** GitHub, Twitter/X, Instagram

**Skip social media checks:**
```bash
python main.py --target "johndoe" --type individual --skip-social
```

### 2. Email Enumeration

**Generate email patterns for a domain:**
```bash
python main.py --target "John Doe" --type individual --email-enum --domain example.com
```

**Multiple domains:**
```bash
python main.py --target "John Doe" --type individual --email-enum --domain company.com --domains gmail.com outlook.com
```

**What it does:**
- Generates common email patterns (first.last@domain, firstlast@domain, etc.)
- Verifies MX records for domains
- Assigns confidence scores based on MX verification

### 3. Username Variations

**Try multiple username formats:**
```bash
python main.py --target "John Doe" --type individual --username-variations
```

**Include leet speak variations (j0hnd03, etc.):**
```bash
python main.py --target "johndoe" --type individual --username-variations --include-leet
```

**Include number suffixes (johndoe123, johndoe2023, etc.):**
```bash
python main.py --target "johndoe" --type individual --username-variations --include-suffixes
```

---

## Execution Modes

Hermes supports three execution modes:

### Native Mode (Default)
Runs tools installed on your system:
```bash
python main.py --mode native --tool sherlock --target johndoe
```

### Docker Mode
Runs tools in isolated Docker containers:
```bash
python main.py --mode docker --tool sherlock --target johndoe
```

### Hybrid Mode
Automatically chooses between Docker and Native based on availability:
```bash
python main.py --mode hybrid --tool sherlock --target johndoe
```

---

## Available Tools

When using `--tool` flag with execution modes:

| Tool | Purpose | Example |
|------|---------|---------|
| `sherlock` | Username search across social networks | `--tool sherlock --target johndoe` |
| `theharvester` | Email/subdomain harvesting | `--tool theharvester --target example.com` |
| `holehe` | Email account enumeration (120+ platforms) | `--tool holehe --target user@example.com` |
| `phoneinfoga` | Phone number OSINT | `--tool phoneinfoga --target +1234567890` |
| `sublist3r` | Subdomain enumeration | `--tool sublist3r --target example.com` |
| `photon` | Web crawler for OSINT | `--tool photon --target https://example.com` |
| `exiftool` | Metadata extraction | `--tool exiftool --target image.jpg` |

---

## Configuration Management

### Configuration Profiles

**List available profiles:**
```bash
python main.py --list-profiles
```

**Create default profiles:**
```bash
python main.py --create-profiles
```

This creates:
- `default` - Balanced settings
- `quick_scan` - Fast, minimal checks
- `deep_scan` - Comprehensive, slower

**Use a specific profile:**
```bash
python main.py --config quick_scan --target "johndoe" --type individual
```

### Environment Variables

**Import .env file into encrypted storage:**
```bash
python main.py --import-env
```

This securely stores API keys and credentials from your `.env` file.

---

## Performance Tuning

### Concurrent Workers
Control how many parallel operations run:
```bash
python main.py --target "johndoe" --type individual --workers 20
```

Default: 10 workers
- Lower values (5-10): Slower but more polite to target sites
- Higher values (20-50): Faster but may trigger rate limits

### Cache Management

**View cache statistics:**
```bash
python main.py --cache-stats
```

**Clear all cached results:**
```bash
python main.py --clear-cache
```

---

## Output Options

### Specify Output File
```bash
python main.py --target "johndoe" --type individual --output results.json
```

Default output format: JSON

### Disable Features

**Disable progress indicators:**
```bash
python main.py --target "johndoe" --type individual --no-progress
```

**Disable deduplication:**
```bash
python main.py --target "johndoe" --type individual --no-dedup
```

---

## Interactive Mode

For beginners, use the interactive wizard:
```bash
python main.py --interactive
```
or
```bash
python main.py -i
```

The wizard will guide you through all options step-by-step.

---

## Complete Examples

### Example 1: Basic Individual Scan
```bash
python main.py \
  --target "Jane Smith" \
  --type individual \
  --output jane_report.json
```

### Example 2: Deep Company Investigation
```bash
python main.py \
  --target "Acme Corp" \
  --type company \
  --email-enum \
  --domain acmecorp.com \
  --domains acme.io acme.net \
  --username-variations \
  --workers 15 \
  --output acme_deep.json
```

### Example 3: Email-Focused Scan
```bash
python main.py \
  --target "John Doe" \
  --type individual \
  --email-enum \
  --domain company.com \
  --skip-social \
  --output emails_only.json
```

### Example 4: Docker Mode Tool Execution
```bash
python main.py \
  --mode docker \
  --tool sherlock \
  --target johndoe
```

### Example 5: Username Variations with Leet Speak
```bash
python main.py \
  --target "hacker" \
  --type individual \
  --username-variations \
  --include-leet \
  --include-suffixes \
  --workers 20
```

---

## Proxy Support

Hermes supports proxy rotation for rate limit evasion.

**Configure proxies via .env file:**
```env
PROXY_PROVIDER_1_TYPE=http
PROXY_PROVIDER_1_HOST=proxy1.example.com
PROXY_PROVIDER_1_PORT=8080
PROXY_PROVIDER_1_USERNAME=user
PROXY_PROVIDER_1_PASSWORD=pass
```

Then import:
```bash
python main.py --import-env
```

---

## Understanding Results

### Confidence Scores
- **1.0**: Verified profile with content validation
- **0.7**: Profile found but verification failed
- **0.5**: Email pattern with valid MX records
- **0.1**: Email pattern without MX verification

### Source Attribution
Results include source metadata showing which tool/method discovered each piece of intelligence:
- `Direct Check` - Direct HTTP verification
- `Pattern Generation` - Email pattern algorithm
- `MX Verified` - Domain has valid mail servers

---

## Troubleshooting

### Docker Not Available
```bash
python main.py --doctor
```
Ensure Docker Desktop is running.

### Rate Limiting
- Reduce `--workers` value
- Configure proxy rotation
- Use `--username-variations` sparingly

### No Results Found
- Try `--username-variations` for different formats
- Verify target name spelling
- Check if platforms are accessible from your network

---

## Important Notes

⚠️ **Alpha Software**: Hermes 2.0 is in alpha. Expect bugs and incomplete features.

🐳 **Docker Required**: Many tools require Docker to be installed and running.

🔒 **Privacy**: Always respect privacy laws and terms of service.

📊 **Results**: All results are saved as JSON by default. Use reporting tools to convert to other formats.

🚫 **Deprecated Flags**: The `--passive` flag is deprecated and no longer has any effect.

---

## Getting Help

- Run `python main.py --help` for all available options
- Check `docs/TOOL_ADAPTER_GUIDE.md` for developer documentation
- Open issues on GitHub for bugs or feature requests
