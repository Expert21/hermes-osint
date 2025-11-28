# Changelog

All notable changes to Hermes OSINT Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.5.0] - 2025-11-27

### Added
- Terminal User Interface (TUI) with clean installer-style design
- Docker orchestration framework for running OSINT tools in containers
- Proxy management system with rotation and validation
- Tool adapter interface for external OSINT tools
- Sherlock and TheHarvester adapters
- Security-hardened container execution with resource limits

### Changed
- Major codebase refactoring and formatting improvements
- Enhanced test coverage across modules

## [1.4.1] - 2025-11-25

### Added
- Repository cleanup and configuration refinement
- Enhanced `.gitignore` for better project organization
- Improved documentation structure

### Security
- Proactive log sanitization for PII protection
- URL query parameter masking in logs
- Email address redaction in log output
- API key masking (first 4 and last 2 characters only)
- Response body truncation to prevent log bloat

### Fixed
- Import path corrections in `profile_verification.py`
- Relative import compatibility improvements

## [1.4.0] - 2025-11-25

### Added
- Environment-based configuration via `.env` files
- Encrypted credential storage with Fernet encryption
- Configuration profile system (Default, Quick Scan, Deep Scan)
- `--import-env` command for secure credential import
- `verify_config.py` utility for configuration validation

### Changed
- Migrated from YAML to `.env` configuration format
- Improved configuration management with `ConfigManager`

## [1.3.2] - 2025-11-23

### Security
- Proactive logging sanitization with centralized Sanitizer class
- URL query masking in all logs
- Response truncation to 500 characters
- Email masking in logs
- Enhanced API key redaction

### Fixed
- Import path corrections in `profile_verification.py`

## [1.3.1] - 2025-11-23

### Security
- Enhanced API key redaction in logs (4+2 character format)
- Cache race condition fixes with retry logic
- SSRF protection via redirect validation
- PGP parser DoS prevention with length limits
- Proxy integrity verification with SHA-256 checksums
- Secrets validation with HMAC integrity checking
- XXE vulnerability prevention with SafeSoup wrapper

### Changed
- Removed singleton pattern from `AsyncRequestManager` for better testability

## [1.3.0] - 2025-11-22

### Added
- Three-tier intelligence architecture (Passive → Active → Verification)
- Passive intelligence module (HIBP, PGP keyservers, search dorking)
- Scan logger with structured JSON/CSV output
- `--passive` flag for stealth mode operations
- Confidence scoring system (0.0-1.0)
- Source metadata tags (HIBP, PGP, Dork, Active)

### Changed
- Email enumeration refactored to passive-first approach
- Social media checks now use two-tier verification
- Enhanced error handling with graceful degradation
- Improved reporting with confidence badges

## [1.2.2] - 2025-11-21

### Security
- Input validation for all CLI arguments
- Log sanitization to redact sensitive data
- Hardened Playwright browser security configuration
- Content Security Policy (CSP) headers in HTML reports
- Pinned all dependencies to secure versions

## [1.2.1] - 2025-11-21

### Security
- **CRITICAL:** Fernet encryption for credential storage
- **HIGH:** SSRF and command injection protection
- **HIGH:** YAML path traversal and deserialization fixes
- **MEDIUM:** DoS protection with resource limits
- **MEDIUM:** Proxy validation with IP filtering

## [1.2.0] - 2025-11-21

### Added
- Complete async/await implementation
- Proxy rotation with auto-fetch capability
- JavaScript rendering via Playwright
- Enhanced rate limit evasion

### Performance
- 10x performance improvement through async operations

## [1.1.1] - 2025-11-20

### Added
- Initial public release
- Multi-platform OSINT scanning
- Email enumeration and validation
- Profile verification
- Multiple output formats (HTML, PDF, Markdown, JSON, STIX 2.1)

---

[Unreleased]: https://github.com/Expert21/hermes-osint/compare/v1.4.1...HEAD
[1.4.1]: https://github.com/Expert21/hermes-osint/compare/v1.4.0...v1.4.1
[1.4.0]: https://github.com/Expert21/hermes-osint/compare/v1.3.1...v1.4.0
[1.3.1]: https://github.com/Expert21/hermes-osint/compare/v1.3.0...v1.3.1
[1.3.0]: https://github.com/Expert21/hermes-osint/compare/v1.2.2...v1.3.0
[1.2.2]: https://github.com/Expert21/hermes-osint/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/Expert21/hermes-osint/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/Expert21/hermes-osint/compare/v1.1.1...v1.2.0
[1.1.1]: https://github.com/Expert21/hermes-osint/releases/tag/v1.1.1
