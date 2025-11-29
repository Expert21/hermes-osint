# Migration Guide: v1.x to v2.0

Hermes v2.0 introduces significant architectural changes. This guide will help you migrate your existing installation and workflows.

## Key Changes

| Feature | v1.x | v2.0 |
| :--- | :--- | :--- |
| **Execution** | Native Python scripts | Hybrid (Native + Docker) |
| **Configuration** | Command line flags | `.env` + Profiles + CLI |
| **Tooling** | Hardcoded modules | Plugin-based Adapters |
| **Search Engines** | Built-in scraping | External `searxng` container |

## Upgrade Steps

### 1. Update Codebase

```bash
git pull origin main
pip install -r requirements.txt
```

### 2. Install Docker (Recommended)

While v2.0 supports Native mode, Docker mode is recommended for stability and security.
-   **Windows/Mac**: Install Docker Desktop.
-   **Linux**: Install Docker Engine (`apt install docker.io`).

### 3. Update Configuration

The `.env` file format has been updated. It is recommended to regenerate it.

```bash
# Backup existing .env
mv .env .env.bak

# Generate new template
hermes --init-env

# Re-import your keys from .env.bak to .env
# Then import into secure storage
hermes --import-env
```

### 4. Pull Docker Images

If you plan to use Docker or Hybrid mode, pull the required images:

```bash
hermes --pull-images
```

### 5. Update Scripts

If you have automation scripts, update the flags:

-   **Removed**: `--google-dorking` (Use `searxng` directly or via adapter if available)
-   **Changed**: `--tool` now accepts adapter names (e.g., `sherlock`, `theharvester`) instead of internal module names.
-   **New**: `--mode` flag to control execution strategy.

## Troubleshooting

**"Docker is not available" error:**
-   Ensure Docker is running.
-   Or use `--mode native` to force local execution (requires tools to be installed in your PATH).

**"Adapter not found" error:**
-   Check `hermes --help` for the list of supported tools.
-   Ensure you are using the correct tool name.

**Permission errors on Linux:**
-   Ensure your user is in the `docker` group: `sudo usermod -aG docker $USER`.
