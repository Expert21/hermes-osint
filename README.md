# Hermes OSINT 2.0 (Alpha)

🚧 **STATUS: ALPHA RELEASE — NOT READY FOR CASUAL USE** 🚧

Hermes 2.0 is a complete rebuild of the Hermes OSINT framework with a focus on:

* Fully ephemeral execution of OSINT tools
* Docker‑based isolation and security
* Strong output handling and extraction
* A more modular, extensible architecture

This is **not** a stable release. Many features are implemented, but some tools, modules, and workflows are incomplete or partially broken. **Casual users should *not* rely on Hermes 2.0 Alpha for production investigations.**

However — **testers, contributors, and developers are highly encouraged to experiment, break things, and submit issues + PRs.**

---

## 🚀 Current Alpha Goals

Hermes 2.0 Alpha focuses on restructuring the core pipeline:

* Ephemeral container lifecycle with secure teardown
* Trust‑based Docker image verification
* Tool‑specific modules (WIP)
* Enhanced logging and output extraction
* Improved internal architecture for future UI + automation layers

Many components function reliably — others are still being built.

---

## ⚠️ Alpha State (What Works / What’s Broken)

### ✅ **Working / Mostly Working**

* Core DockerManager lifecycle
* Ephemeral execution model
* Tool pulling & hashing (digest validation)
* Config + environment loading
* CLI operations

### ⚠️ **Partially Implemented**

* Tool modules (subfinder, searxng, holehe, etc.)
* Output routing
* Error handling across certain tools
* Image trust lists

### ❌ **Not Implemented / Broken**

* TUI rewrite
* Full automation sequences
* Some tool wrappers that rely on unstable docker images

---

## 🧩 Requirements

Hermes **requires Docker**. It will not function without it.

### **System Requirements**

* Docker Engine (latest recommended)
* Python 3.10+
* Linux/macOS/Windows (WSL recommended for Win)

### **Python Dependencies**

All dependencies are listed in `requirements.txt`.
Install with:

```bash
pip install -r requirements.txt
```

---

## 🐳 Docker Requirements

Hermes pulls and runs OSINT tools *inside isolated ephemeral containers*.

You must have Docker installed and running:

```bash
docker --version
```

### Notes

* Some tools require specific, reliable Docker images
* Hermes uses digest pinning and trust lists (WIP)
* If an image for a tool doesn't exist or is unreliable, Hermes may currently fail silently or with partial errors (Alpha behavior)

---

## 📦 Installation (Alpha)

```bash
git clone https://github.com/Expert21/hermes-osint
cd hermes-osint
pip install -r requirements.txt
```

Run Hermes:

```bash
python3 hermes.py
```

---

## 🧪 Contributing / Testing

Hermes 2.0 Alpha needs testers. If you:

* Encounter a broken module
* Find an unreliable Docker image
* Have ideas for improving the ephemeral architecture
* Want to contribute to tool modules

Please open an issue or submit a PR.

---

## 📝 Roadmap for 2.0

* Stable module system
* Automated docker image generation for tools that currently lack them
* Hardened ephemeral container workflows
* Expanded OSINT tool library
* Plugin ecosystem

---

## ❗ Disclaimer

Hermes 2.0 Alpha is experimental software.
It may:

* Delete containers incorrectly
* Fail to extract output
* Throw non‑critical or confusing errors
* Behave unpredictably as tools update

Use with caution.

---

## ⭐ Credits

Built by **Expert21**

Contributions welcome — Hermes 2.0 is a community‑driven OSINT framework.

