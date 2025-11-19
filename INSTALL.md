# Hermes Installation Guide

## Quick Install (Recommended)

Install Hermes globally so you can run it from anywhere:

```bash
# Navigate to the hermes directory
cd hermes

# Install in development mode (editable)
pip install -e .

# Or install normally
pip install .
```

After installation, you can use `hermes` from anywhere:

```bash
hermes --help
hermes --target "johndoe" --type individual
hermes --interactive
```

## Manual Installation

If you prefer not to install globally:

```bash
# Install dependencies only
pip install -r requirements.txt

# Run from the project directory
python main.py --target "johndoe" --type individual
```

## Windows-Specific Setup

### Option 1: Using pip install (Recommended)
```powershell
# Install Hermes
pip install -e .

# Verify installation
hermes --help
```

### Option 2: Add to PATH manually
```powershell
# Add the hermes directory to your PATH
$env:PATH += ";C:\path\to\hermes"

# Make it permanent
[Environment]::SetEnvironmentVariable("PATH", $env:PATH, "User")
```

## Linux/Mac Setup

### Option 1: Using pip install (Recommended)
```bash
# Install Hermes
pip install -e .

# Verify installation
hermes --help
```

### Option 2: Create symlink
```bash
# Make the script executable
chmod +x hermes

# Create symlink in /usr/local/bin
sudo ln -s $(pwd)/hermes /usr/local/bin/hermes

# Verify
hermes --help
```

## Verification

After installation, verify Hermes is working:

```bash
# Check version and help
hermes --help

# List configuration profiles
hermes --list-profiles

# Create default profiles
hermes --create-profiles
```

## Uninstallation

```bash
# If installed with pip
pip uninstall hermes-osint

# If using symlink (Linux/Mac)
sudo rm /usr/local/bin/hermes
```

## Troubleshooting

### "hermes: command not found"
- Make sure you ran `pip install -e .`
- Check that your Python Scripts directory is in PATH
- Try closing and reopening your terminal

### Permission errors on Linux/Mac
- Use `sudo pip install -e .` or
- Install in user mode: `pip install --user -e .`

### Import errors
- Make sure all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (requires 3.7+)
