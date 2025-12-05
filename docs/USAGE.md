# Hermes OSINT - Usage Guide

Hermes is an OSINT (Open Source Intelligence) tool that orchestrates multiple external tools to gather information about individuals and companies.

## Installation

```bash
# Clone the repository
git clone https://github.com/expert21/hermes-osint.git
cd hermes-osint

# Install dependencies
pip install -r requirements.txt

# Install Hermes
pip install .

# Verify installation
hermes --doctor
```

## Quick Start

```bash
# Individual scan (username-focused)
hermes --target johndoe --type individual

# Company scan (domain-focused)
hermes --target example.com --type company

# Generate variations for username search
hermes --target johndoe --type individual --variations
```

---

## Command Line Reference

### Required Arguments

| Argument | Description |
|----------|-------------|
| `--target` | Target name (username or domain) |
| `--type` | Target type: `individual` or `company` |

### Optional Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--output` | Output report file with supported extensions (json, md, html, pdf, csv ) | `report.json` |
| `--domain` | Primary domain for email enumeration | - |
| `--email` | Known email for verification | - |
| `--phone` | Phone number for PhoneInfoga | - |
| `--file` | File path for Exiftool analysis | - |
| `--stealth` | Enable stealth mode (no direct target contact) | Off |
| `--variations` | Try username variations | Off |
| `--workers` | Number of concurrent workers | 10 |
| `--mode` | Execution mode: `native`, `docker`, `hybrid` | `native` |
| `--tool` | Run a specific tool only | - |
| `--config` | Configuration profile to use | `default` |

### System Commands

| Command | Description |
|---------|-------------|
| `--doctor` | Run system diagnostics |
| `--pull-images` | Pull all required Docker images |
| `--remove-images` | Remove all Docker images |
| `--import-env` | Import .env file into secure storage |
| `--list-profiles` | List available configuration profiles |
| `--create-profiles` | Create default configuration profiles |
| `--clear-cache` | Clear all cached results |
| `--cache-stats` | Show cache statistics |

### Plugin Commands

```bash
# List all plugins
hermes plugins list

# Show plugin details
hermes plugins info sherlock

# Security scan a directory
hermes plugins scan /path/to/plugin
```

---

## Execution Modes

### Native Mode (Default)
```bash
hermes --target johndoe --type individual --mode native
```
Runs tools installed locally on your system. Fastest but requires manual tool installation.

### Docker Mode
```bash
hermes --target johndoe --type individual --mode docker
```
Runs tools in Docker containers. More isolated but requires Docker.

### Hybrid Mode
```bash
hermes --target johndoe --type individual --mode hybrid
```
Automatically uses native tools if available, falls back to Docker.

---

## Stealth Mode

Stealth mode prevents direct contact with target systems:

```bash
hermes --target johndoe --type individual --stealth
```

**Behavior in stealth mode:**
- **Skipped**: Sherlock, Holehe, PhoneInfoga (make direct HTTP requests)
- **Restricted**: H8mail (uses local breach compilation only)
- **Unchanged**: TheHarvester, Subfinder (already passive), Exiftool (local files)

---

## Running Specific Tools

Run a single tool instead of the full scan:

```bash
# Sherlock (username enumeration)
hermes --tool sherlock --target johndoe

# TheHarvester (email/subdomain discovery)
hermes --tool theharvester --target example.com

# Holehe (email account check)
hermes --tool holehe --email user@example.com

# PhoneInfoga (phone lookup)
hermes --tool phoneinfoga --phone "+1234567890"

# Subfinder (subdomain discovery)
hermes --tool subfinder --target example.com

# Exiftool (file metadata)
hermes --tool exiftool --file /path/to/image.jpg
```

---

## Configuration Profiles

Create and use configuration profiles:

```bash
# Create default profiles
hermes --create-profiles

# List available profiles
hermes --list-profiles

# Use a specific profile
hermes --target johndoe --type individual --config deep_scan
```

---

## Proxy Support

Configure proxies for anonymization:

```bash
# Use a proxy list file
hermes --target johndoe --type individual --proxies proxies.txt

# Fetch free proxies
hermes --fetch-proxies
```

---

## Output Formats

Reports are generated based on output file extension:

```bash
# JSON report (default)
hermes --target johndoe --type individual --output report.json

# Markdown report
hermes --target johndoe --type individual --output report.md

# HTML report
hermes --target johndoe --type individual --output report.html
```

---

## System Diagnostics

Check your system configuration:

```bash
hermes --doctor
```

This checks:
- Docker availability
- Native tool installations
- Python dependencies
- Configuration files

---

## Username Variations

Generate and scan username variations:

```bash
hermes --target johndoe --type individual --variations
```

This generates variations like:
- `johndoe`, `john_doe`, `john-doe`
- `johndoe123`, `johndoe_`, `_johndoe`
- `j0hnd03` (leetspeak)

---

## Examples

### Full Individual Scan
```bash
hermes --target "John Doe" --type individual \
  --email john.doe@company.com \
  --domain company.com \
  --variations \
  --output john_doe_report.html
```

### Company Reconnaissance
```bash
hermes --target example.com --type company \
  --output example_recon.md
```

### Stealth Scan with Docker
```bash
hermes --target johndoe --type individual \
  --stealth \
  --mode docker \
  --output stealth_report.json
```
