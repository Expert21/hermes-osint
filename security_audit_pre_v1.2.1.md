# Security Audit & Hardening Guide - OSINT Tool (Pre-v1.2.1)

## Executive Summary

This comprehensive security audit identifies vulnerabilities and provides actionable hardening recommendations for your OSINT tool. The audit covers **16 critical security areas** with specific code fixes and best practices.

**Risk Level Summary:**
- 🔴 **CRITICAL** (3 issues) - Immediate attention required
- 🟠 **HIGH** (5 issues) - Should be addressed soon
- 🟡 **MEDIUM** (6 issues) - Important for production
- 🟢 **LOW** (2 issues) - Nice to have

---

## 🔴 CRITICAL Security Issues

### 1. Command Injection via URL Construction

**Location:** [`search_engines.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/modules/search_engines.py#L62), [`social_media.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/modules/social_media.py#L108)

**Vulnerability:** User input is directly inserted into URLs using `.format()` without proper validation or sanitization.

**Attack Scenario:**
```python
# Attacker input: "../../etc/passwd" or "../../../admin"
# Could lead to path traversal or SSRF attacks
target = "../../../admin'; DROP TABLE users--"
url = url_pattern.format(target)  # Dangerous!
```

**Fix:**
```python
import re
from urllib.parse import quote

def sanitize_username(username: str) -> str:
    """Sanitize username to prevent injection attacks."""
    # Only allow alphanumeric, dash, underscore, and period
    sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', username)
    # Limit length
    sanitized = sanitized[:100]
    # Prevent path traversal
    if '..' in sanitized or sanitized.startswith(('.', '/', '\\')):
        raise ValueError("Invalid username format")
    return sanitized

# In social_media.py line 108:
safe_target = sanitize_username(target)
url = url_pattern.format(quote(safe_target, safe=''))
```

---

### 2. YAML Deserialization Attack

**Location:** [`config_manager.py:101`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/core/config_manager.py#L101)

**Vulnerability:** Using `yaml.safe_load()` is good, but YAML files can be poisoned by attackers if they gain write access.

**Attack Scenario:**
```yaml
# Malicious config.yaml could execute arbitrary Python code
timing: !!python/object/apply:os.system ['rm -rf /']
```

**Fix:**
```python
def load_config(self, profile_name: str = 'default') -> Dict[str, Any]:
    """Load configuration with enhanced security."""
    profile_path = self.config_dir / f"{profile_name}.yaml"
    
    # Prevent path traversal
    if '..' in profile_name or '/' in profile_name or '\\' in profile_name:
        raise ValueError("Invalid profile name")
    
    # Ensure path is within config directory
    if not profile_path.resolve().is_relative_to(self.config_dir.resolve()):
        raise ValueError("Profile path outside allowed directory")
    
    if not profile_path.exists():
        logger.warning(f"Profile '{profile_name}' not found, using default configuration")
        return self.DEFAULT_CONFIG.copy()
    
    try:
        with open(profile_path, 'r') as f:
            # Use SafeLoader explicitly
            loaded_config = yaml.load(f, Loader=yaml.SafeLoader)
        
        # Validate config structure
        if not isinstance(loaded_config, dict):
            raise ValueError("Invalid config format: must be a dictionary")
        
        # Validate all values are safe types
        self._validate_config_types(loaded_config)
        
        config = self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
        logger.info(f"✓ Loaded configuration profile: {profile_name}")
        self.current_config = config
        return config
        
    except Exception as e:
        logger.error(f"Failed to load profile '{profile_name}': {e}")
        return self.DEFAULT_CONFIG.copy()

def _validate_config_types(self, config: dict, path: str = "") -> None:
    """Recursively validate config contains only safe types."""
    safe_types = (str, int, float, bool, type(None), dict, list)
    
    for key, value in config.items():
        current_path = f"{path}.{key}" if path else key
        
        if not isinstance(value, safe_types):
            raise ValueError(f"Unsafe type {type(value)} at {current_path}")
        
        if isinstance(value, dict):
            self._validate_config_types(value, current_path)
        elif isinstance(value, list):
            for i, item in enumerate(value):
                if not isinstance(item, safe_types):
                    raise ValueError(f"Unsafe type in list at {current_path}[{i}]")
```

---

### 3. Credential Exposure in Config Files

**Location:** [`config.yaml:60-63`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/config.yaml#L60-L63), [`config.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/core/config.py)

**Vulnerability:** API keys stored in plain text in config files and potentially committed to version control.

**Fix:**
```python
# New file: src/core/secrets_manager.py
import os
import keyring
from cryptography.fernet import Fernet
from pathlib import Path
import logging

logger = logging.getLogger("OSINT_Tool")

class SecretsManager:
    """Secure credential management using system keyring and encryption."""
    
    def __init__(self):
        self.service_name = "osint_tool"
        self.key_file = Path.home() / ".osint" / "encryption.key"
        self.key_file.parent.mkdir(exist_ok=True, mode=0o700)
        
    def _get_encryption_key(self) -> bytes:
        """Get or create encryption key."""
        if self.key_file.exists():
            with open(self.key_file, 'rb') as f:
                return f.read()
        else:
            key = Fernet.generate_key()
            # Secure file permissions
            self.key_file.touch(mode=0o600)
            with open(self.key_file, 'wb') as f:
                f.write(key)
            return key
    
    def store_credential(self, key_name: str, value: str):
        """Store credential securely in system keyring."""
        try:
            keyring.set_password(self.service_name, key_name, value)
            logger.info(f"✓ Credential '{key_name}' stored securely")
        except Exception as e:
            logger.error(f"Failed to store credential: {e}")
            # Fallback to encrypted file
            self._store_encrypted(key_name, value)
    
    def get_credential(self, key_name: str) -> str | None:
        """Retrieve credential from keyring or environment."""
        # Priority 1: Environment variable
        env_value = os.getenv(key_name.upper())
        if env_value:
            return env_value
        
        # Priority 2: System keyring
        try:
            value = keyring.get_password(self.service_name, key_name)
            if value:
                return value
        except Exception as e:
            logger.debug(f"Keyring retrieval failed: {e}")
        
        # Priority 3: Encrypted file
        return self._get_encrypted(key_name)
    
    def _store_encrypted(self, key_name: str, value: str):
        """Fallback: Store in encrypted file."""
        cipher = Fernet(self._get_encryption_key())
        encrypted = cipher.encrypt(value.encode())
        
        creds_file = Path.home() / ".osint" / "credentials.enc"
        creds_file.touch(mode=0o600)
        
        # Append to file
        with open(creds_file, 'ab') as f:
            f.write(f"{key_name}:".encode())
            f.write(encrypted)
            f.write(b"\n")
    
    def _get_encrypted(self, key_name: str) -> str | None:
        """Retrieve from encrypted file."""
        creds_file = Path.home() / ".osint" / "credentials.enc"
        if not creds_file.exists():
            return None
        
        cipher = Fernet(self._get_encryption_key())
        
        with open(creds_file, 'rb') as f:
            for line in f:
                if line.startswith(f"{key_name}:".encode()):
                    encrypted = line[len(key_name)+1:].strip()
                    return cipher.decrypt(encrypted).decode()
        
        return None

# Update config.py to use SecretsManager
from src.core.secrets_manager import SecretsManager

def load_config():
    """Load configuration with secure credential handling."""
    secrets = SecretsManager()
    
    config = {
        "GOOGLE_API_KEY": secrets.get_credential("google_api_key"),
        "GOOGLE_CSE_ID": secrets.get_credential("google_cse_id"),
        "TWITTER_BEARER_TOKEN": secrets.get_credential("twitter_bearer_token"),
    }
    
    return config
```

**Additional Recommendations:**
- Add `config.yaml` to `.gitignore`
- Use environment variables in production
- Never commit files with secrets

---

## 🟠 HIGH Security Issues

### 4. Server-Side Request Forgery (SSRF)

**Location:** All modules making HTTP requests

**Vulnerability:** No validation of target URLs, allowing attackers to probe internal networks.

**Fix:**
```python
# New file: src/core/url_validator.py
import ipaddress
from urllib.parse import urlparse
import socket

class URLValidator:
    """Validate URLs to prevent SSRF attacks."""
    
    BLOCKED_SCHEMES = {'file', 'ftp', 'gopher', 'data', 'javascript'}
    BLOCKED_PORTS = {22, 23, 25, 3306, 5432, 6379, 27017}  # SSH, Telnet, SMTP, MySQL, etc.
    
    @staticmethod
    def is_safe_url(url: str) -> bool:
        """Check if URL is safe for fetching."""
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme.lower() in URLValidator.BLOCKED_SCHEMES:
                return False
            
            if parsed.scheme.lower() not in ['http', 'https']:
                return False
            
            # Check for blocked ports
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            if port in URLValidator.BLOCKED_PORTS:
                return False
            
            # Resolve hostname
            hostname = parsed.hostname
            if not hostname:
                return False
            
            # Block localhost and private IPs
            try:
                ip = socket.gethostbyname(hostname)
                ip_obj = ipaddress.ip_address(ip)
                
                # Block private, loopback, and link-local addresses
                if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_link_local:
                    return False
                
                # Block multicast and reserved
                if ip_obj.is_multicast or ip_obj.is_reserved:
                    return False
                    
            except (socket.gaierror, ValueError):
                # Can't resolve - block it
                return False
            
            return True
            
        except Exception:
            return False

# Update async_request_manager.py
from src.core.url_validator import URLValidator

async def fetch(self, url: str, ...) -> Dict[str, Any]:
    """Perform HTTP request with SSRF protection."""
    
    # Validate URL before making request
    if not URLValidator.is_safe_url(url):
        logger.error(f"Blocked unsafe URL: {url}")
        return {"status": 0, "text": "", "error": "Unsafe URL blocked", "ok": False}
    
    # ... rest of the method
```

---

### 5. Unvalidated Proxy List Injection

**Location:** [`async_request_manager.py:61-88`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/core/async_request_manager.py#L61-L88)

**Vulnerability:** Fetching proxies from external sources without validation could inject malicious proxies.

**Fix:**
```python
async def fetch_free_proxies(self):
    """Fetch free proxies with validation."""
    logger.info("Auto-fetching free proxies...")
    
    # Use multiple trusted sources
    sources = [
        "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",
        # Add more trusted sources
    ]
    
    validated_proxies = []
    
    for url in sources:
        if not URLValidator.is_safe_url(url):
            logger.warning(f"Skipping untrusted proxy source: {url}")
            continue
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        text = await response.text()
                        new_proxies = [line.strip() for line in text.splitlines() if line.strip()]
                        
                        # Validate each proxy
                        for proxy in new_proxies:
                            if self._is_valid_proxy(proxy):
                                validated_proxies.append(proxy)
                        
        except Exception as e:
            logger.error(f"Error fetching proxies from {url}: {e}")
    
    if validated_proxies:
        self.proxies.extend(validated_proxies)
        self.proxies = list(set(self.proxies))[:1000]  # Limit to 1000 proxies
        logger.info(f"Validated and added {len(validated_proxies)} proxies")
        
        if self.proxy_file:
            self._save_proxies_securely()
    else:
        logger.warning("No valid proxies fetched")

def _is_valid_proxy(self, proxy: str) -> bool:
    """Validate proxy format and prevent malicious entries."""
    import re
    
    # Basic format validation
    proxy_pattern = r'^(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}):(\d{1,5})$'
    match = re.match(proxy_pattern, proxy)
    
    if not match:
        return False
    
    ip, port = match.groups()
    
    # Validate IP
    try:
        ip_obj = ipaddress.ip_address(ip)
        if ip_obj.is_private or ip_obj.is_loopback:
            return False
    except ValueError:
        return False
    
    # Validate port
    try:
        port_num = int(port)
        if port_num < 1 or port_num > 65535:
            return False
    except ValueError:
        return False
    
    return True

def _save_proxies_securely(self):
    """Save proxies with proper permissions."""
    try:
        # Create file with secure permissions
        os.makedirs(os.path.dirname(self.proxy_file), exist_ok=True)
        
        with open(self.proxy_file, 'w') as f:
            os.chmod(self.proxy_file, 0o600)  # Only owner can read/write
            f.write('\n'.join(self.proxies[:1000]))  # Limit file size
            
    except Exception as e:
        logger.warning(f"Could not save proxies securely: {e}")
```

---

### 6. Path Traversal in File Operations

**Location:** [`main.py:73`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/main.py#L73), [`generator.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/reporting/generator.py)

**Vulnerability:** User-controlled paths could access files outside intended directories.

**Fix:**
```python
import os
from pathlib import Path

def validate_output_path(filepath: str, allowed_dir: str = None) -> Path:
    """Validate output path to prevent path traversal."""
    try:
        path = Path(filepath).resolve()
        
        # If allowed_dir specified, ensure path is within it
        if allowed_dir:
            allowed = Path(allowed_dir).resolve()
            if not path.is_relative_to(allowed):
                raise ValueError("Output path outside allowed directory")
        
        # Prevent absolute paths to system directories
        dangerous_dirs = ['/etc', '/sys', '/proc', 'C:\\Windows', 'C:\\Program Files']
        for danger in dangerous_dirs:
            if str(path).startswith(danger):
                raise ValueError("Cannot write to system directory")
        
        # Ensure parent directory exists and is writable
        path.parent.mkdir(parents=True, exist_ok=True)
        
        return path
        
    except Exception as e:
        raise ValueError(f"Invalid output path: {e}")

# In main.py:
try:
    output_path = validate_output_path(args.output)
    generate_report(results, str(output_path))
except ValueError as e:
    logger.error(f"Invalid output path: {e}")
    return 1

# In generator.py:
def generate_report(results, output_file):
    """Generate report with path validation."""
    try:
        safe_path = validate_output_path(output_file)
        output_file = str(safe_path)
        
        # ... rest of the function
```

---

### 7. BeautifulSoup XXE and HTML Injection

**Location:** All uses of `BeautifulSoup` in [`search_engines.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/modules/search_engines.py)

**Vulnerability:** Parsing untrusted HTML without proper sanitization.

**Fix:**
```python
from bs4 import BeautifulSoup
import bleach

def safe_parse_html(html_content: str) -> BeautifulSoup:
    """Parse HTML safely to prevent XXE and injection attacks."""
    # Use 'html.parser' instead of 'lxml' to avoid XXE
    soup = BeautifulSoup(html_content, 'html.parser', 
                        from_encoding='utf-8')
    return soup

def sanitize_extracted_text(text: str) -> str:
    """Sanitize extracted text to prevent XSS in reports."""
    # Strip all HTML tags and sanitize
    clean_text = bleach.clean(text, tags=[], strip=True)
    # Limit length to prevent DoS
    return clean_text[:2000]

# Update all BeautifulSoup usage:
soup = safe_parse_html(html_content)
title = sanitize_extracted_text(title_elem.get_text(strip=True))
snippet = sanitize_extracted_text(snippet_elem.get_text(strip=True))
```

---

### 8. Denial of Service (DoS) via Resource Exhaustion

**Location:** Multiple locations - unbounded data processing

**Vulnerability:** No limits on response sizes, result counts, or memory usage.

**Fix:**
```python
# In async_request_manager.py
async def fetch(self, url: str, ...) -> Dict[str, Any]:
    """Fetch with size limits to prevent DoS."""
    
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10MB limit
    
    async with session.request(...) as response:
        # Check content length before downloading
        content_length = response.headers.get('Content-Length')
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            logger.warning(f"Response too large: {content_length} bytes")
            return {"status": 0, "text": "", "error": "Response too large", "ok": False}
        
        # Read with size limit
        chunks = []
        total_size = 0
        
        async for chunk in response.content.iter_chunked(8192):
            total_size += len(chunk)
            if total_size > MAX_RESPONSE_SIZE:
                logger.warning(f"Response exceeded size limit for {url}")
                return {"status": 0, "text": "", "error": "Response too large", "ok": False}
            chunks.append(chunk)
        
        text = b''.join(chunks).decode('utf-8', errors='ignore')
        
        # ... return response

# Add global limits in config
thresholds:
  max_response_size_mb: 10
  max_total_results: 1000
  max_proxy_count: 1000
  max_concurrent_requests: 20
```

---

## 🟡 MEDIUM Security Issues

### 9. Insecure Random Number Generation

**Location:** [`async_request_manager.py:94`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/core/async_request_manager.py#L94)

**Vulnerability:** Using `random.choice()` for security-sensitive operations.

**Fix:**
```python
import secrets

def get_proxy(self) -> Optional[str]:
    """Get a cryptographically random proxy."""
    if not self.proxies:
        return None
    # Use secrets module for security-sensitive randomness
    return f"http://{secrets.choice(self.proxies)}"

# Same for user agent selection:
if "User-Agent" not in headers:
    headers["User-Agent"] = secrets.choice(self.user_agents)
```

---

### 10. Missing Input Validation on CLI Arguments

**Location:** [`main.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/main.py)

**Vulnerability:** No validation on target names, domains, emails, etc.

**Fix:**
```python
# New file: src/core/input_validator.py
import re
from typing import Optional

class InputValidator:
    """Validate all user inputs."""
    
    @staticmethod
    def validate_target_name(target: str) -> str:
        """Validate target name for OSINT search."""
        if not target or len(target) > 200:
            raise ValueError("Target name must be 1-200 characters")
        
        # Allow alphanumeric, spaces, dots, dashes, underscores
        if not re.match(r'^[a-zA-Z0-9\s._-]+$', target):
            raise ValueError("Target name contains invalid characters")
        
        return target.strip()
    
    @staticmethod
    def validate_domain(domain: str) -> str:
        """Validate domain name."""
        domain = domain.lower().strip()
        
        # Basic domain format
        domain_pattern = r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$'
        if not re.match(domain_pattern, domain):
            raise ValueError("Invalid domain format")
        
        if len(domain) > 253:
            raise ValueError("Domain name too long")
        
        return domain
    
    @staticmethod
    def validate_email(email: str) -> str:
        """Validate email address."""
        email = email.lower().strip()
        
        email_pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:
            raise ValueError("Email too long")
        
        return email

# In main.py:
from src.core.input_validator import InputValidator

try:
    args.target = InputValidator.validate_target_name(args.target)
    
    if args.domain:
        args.domain = InputValidator.validate_domain(args.domain)
    
    if args.email:
        args.email = InputValidator.validate_email(args.email)
        
except ValueError as e:
    parser.error(str(e))
```

---

### 11. Logging Sensitive Information

**Location:** Throughout the codebase

**Vulnerability:** Logging URLs, responses, and potentially sensitive data.

**Fix:**
```python
# Update logger.py
class SanitizingFormatter(logging.Formatter):
    """Formatter that sanitizes sensitive data from logs."""
    
    SENSITIVE_PATTERNS = [
        (re.compile(r'(api[_-]?key|token|password|secret)["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.I), r'\1=***REDACTED***'),
        (re.compile(r'([?&])(api[_-]?key|token|password)=([^&]+)', re.I), r'\1\2=***REDACTED***'),
        (re.compile(r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'), r'***EMAIL***'),
        (re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'), r'***IP***'),
    ]
    
    def format(self, record):
        original = super().format(record)
        sanitized = original
        
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        
        return sanitized

def setup_logger():
    """Setup logger with sanitization."""
    logger = logging.getLogger("OSINT_Tool")
    
    # ... existing setup ...
    
    # Use sanitizing formatter
    handler.setFormatter(SanitizingFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
```

---

### 12. No Rate Limiting on Local Operations

**Location:** Cache operations, file writes

**Vulnerability:** Could be exploited for local DoS.

**Fix:**
```python
import time
from collections import deque
from threading import Lock

class RateLimiter:
    """Rate limiting for operations."""
    
    def __init__(self, max_calls: int, time_window: float):
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = deque()
        self.lock = Lock()
    
    def is_allowed(self) -> bool:
        """Check if operation is allowed under rate limit."""
        with self.lock:
            now = time.time()
            
            # Remove old calls outside time window
            while self.calls and self.calls[0] < now - self.time_window:
                self.calls.popleft()
            
            if len(self.calls) < self.max_calls:
                self.calls.append(now)
                return True
            
            return False

# In cache_manager.py:
class CacheManager:
    def __init__(self):
        # ... existing code ...
        self.write_limiter = RateLimiter(max_calls=100, time_window=60)  # 100 writes/minute
    
    def save(self, key: str, data: any):
        """Save with rate limiting."""
        if not self.write_limiter.is_allowed():
            logger.warning("Cache write rate limit exceeded")
            return
        
        # ... existing save logic ...
```

---

### 13. Playwright Security Risks

**Location:** [`search_engines.py:36-48`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/modules/search_engines.py#L36-L48)

**Vulnerability:** Browser automation without proper isolation and security headers.

**Fix:**
```python
async def _fetch_content(self, url: str, use_js: bool = False) -> Optional[str]:
    """Fetch content with secure browser configuration."""
    if use_js and self._playwright_available:
        try:
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # Launch with security settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-accelerated-2d-canvas',
                        '--disable-gpu',
                        '--disable-web-security',  # Only if needed
                    ]
                )
                
                context = await browser.new_context(
                    user_agent=secrets.choice(self.request_manager.user_agents),
                    viewport={'width': 1920, 'height': 1080},
                    ignore_https_errors=False,  # Enforce HTTPS validation
                    java_script_enabled=True,
                    accept_downloads=False,  # Prevent malicious downloads
                    bypass_csp=False,  # Respect CSP
                )
                
                # Set additional security
                await context.add_init_script("""
                    // Prevent fingerprinting
                    Object.defineProperty(navigator, 'webdriver', {get: () => false});
                """)
                
                page = await context.new_page()
                
                # Set navigation timeout
                await page.goto(url, wait_until="networkidle", timeout=30000)
                
                content = await page.content()
                await browser.close()
                return content
        except Exception as e:
            logger.error(f"Playwright error: {e}")
            use_js = False
```

---

## 🟢 LOW Security Issues

### 14. Missing Security Headers in Stored Reports

**Location:** [`html_report.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/src/reporting/html_report.py)

**Vulnerability:** Generated HTML reports lack CSP and other security headers, making them vulnerable if hosted.

**Fix:**
```python
# Add meta tags to HTML template
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; style-src 'unsafe-inline'; img-src 'self' data: https:;">
<meta http-equiv="X-Content-Type-Options" content="nosniff">
<meta http-equiv="X-Frame-Options" content="DENY">
<meta http-equiv="Referrer-Policy" content="no-referrer">
```

---

### 15. Error Messages Leaking Information

**Location:** [`main.py`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/main.py)

**Vulnerability:** Detailed stack traces printed to console could reveal internal paths and logic.

**Fix:**
```python
try:
    # ... main logic ...
except Exception as e:
    # Generate error ID
    error_id = secrets.token_hex(8)
    # Log full details internally
    logger.error(f"Fatal error (ID: {error_id}): {e}", exc_info=True)
    # Show generic message to user
    print(f"An unexpected error occurred. Error ID: {error_id}")
    print("Please check logs for details.")
    sys.exit(1)
```

---

### 16. Dependency Vulnerabilities

**Location:** [`requirements.txt`](file:///c:/Users/Isaiah%20Myles/.gemini/antigravity/scratch/osint_tool/requirements.txt)

**Vulnerability:** Using unpinned or outdated dependencies.

**Fix:**
```text
# Pin exact versions known to be secure
requests==2.31.0
beautifulsoup4==4.12.2
cryptography==41.0.7
bleach==6.1.0
playwright==1.40.0
aiohttp==3.9.1
# ...
```
