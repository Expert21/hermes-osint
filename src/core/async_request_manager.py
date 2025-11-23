import asyncio
import aiohttp
import logging
import random
import secrets
import os
import ipaddress
import urllib.parse
import hashlib
from typing import Optional, Dict, Any, List, Union
from src.core.url_validator import URLValidator
from src.core.resource_limiter import ResourceLimiter

logger = logging.getLogger("OSINT_Tool")

class AsyncRequestManager:
    """
    Manages async HTTP requests with rate limiting, retries, and proxy rotation.
    """
    
    def __init__(self, proxy_file: Optional[str] = None, auto_fetch_proxies: bool = False):
        self.session: Optional[aiohttp.ClientSession] = None
        self.sem = asyncio.Semaphore(10) 
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"
        ]
        
        # Proxy Management
        self.proxies: List[str] = []
        self.proxy_file = proxy_file
        self.auto_fetch = auto_fetch_proxies
        
        if self.proxy_file:
            self.load_proxies()
            
        if not self.proxies and self.auto_fetch:
            # We can't await here in __init__, so we'll do it lazily or require explicit call
            pass

    def load_proxies(self):
        """Load and validate proxies from file with integrity check."""
        if not self.proxy_file or not os.path.exists(self.proxy_file):
            return
            
        try:
            # Read proxies
            with open(self.proxy_file, 'r') as f:
                content = f.read()
                raw_proxies = [line.strip() for line in content.splitlines() if line.strip()]
            
            # Integrity check
            checksum_file = f"{self.proxy_file}.sha256"
            if os.path.exists(checksum_file):
                with open(checksum_file, 'r') as f:
                    expected_checksum = f.read().strip()
                
                actual_checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
                
                if actual_checksum != expected_checksum:
                    logger.warning("Proxy file integrity check failed! Discarding proxies.")
                    self.proxies = []  # Clear any existing proxies
                    return
                
                logger.info("Proxy file integrity verified.")
            else:
                logger.warning("No checksum file found for proxies. Integrity not verified.")
            
            # Validate each proxy
            valid_proxies = []
            for proxy in raw_proxies:
                if URLValidator.validate_proxy(proxy):
                    valid_proxies.append(proxy)
            
            self.proxies = valid_proxies
            logger.info(f"Loaded {len(self.proxies)} valid proxies from {self.proxy_file}")
        except Exception as e:
            logger.error(f"Failed to load proxies: {e}")

    async def fetch_free_proxies(self):
        """Fetch free proxies with validation."""
        logger.info("Auto-fetching free proxies...")
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all"
        
        # Validate source URL
        if not URLValidator.is_safe_url(url):
            logger.error("Proxy source URL failed security validation")
            return
        
        try:
            # Use a temporary session to avoid circular dependency
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status == 200:
                        text = await response.text()
                        raw_proxies = [line.strip() for line in text.splitlines() if line.strip()]
                        
                        # Validate each proxy
                        validated = []
                        for proxy in raw_proxies[:1000]:  # Limit to 1000
                            if URLValidator.validate_proxy(proxy):
                                validated.append(proxy)
                        
                        self.proxies.extend(validated)
                        # Remove duplicates and limit total
                        self.proxies = list(set(self.proxies))[:1000]
                        logger.info(f"Validated {len(validated)} proxies. Total: {len(self.proxies)}")
                        
                        # Save to file if configured
                        if self.proxy_file:
                            self._save_proxies_securely()
                    else:
                        logger.error(f"Failed to fetch proxies: HTTP {response.status}")
        except Exception as e:
            logger.error(f"Error fetching proxies: {e}")
    
    def _save_proxies_securely(self):
        """Save proxies with secure file permissions and checksum."""
        try:
            # Create parent directory if needed
            if os.path.dirname(self.proxy_file):
                os.makedirs(os.path.dirname(self.proxy_file), exist_ok=True)
            
            content = '\n'.join(self.proxies)
            
            # Write proxies
            with open(self.proxy_file, 'w') as f:
                f.write(content)
            
            # Write checksum
            checksum = hashlib.sha256(content.encode('utf-8')).hexdigest()
            with open(f"{self.proxy_file}.sha256", 'w') as f:
                f.write(checksum)
            
            # Set secure permissions (owner read/write only)
            try:
                os.chmod(self.proxy_file, 0o600)
                os.chmod(f"{self.proxy_file}.sha256", 0o600)
            except Exception:
                pass  # Windows doesn't support chmod
                
        except Exception as e:
            logger.warning(f"Could not save proxies securely: {e}")

    def get_proxy(self) -> Optional[str]:
        """Get a random proxy from the list"""
        if not self.proxies:
            return None
        return f"http://{secrets.choice(self.proxies)}"

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create the ClientSession."""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=30, connect=10)
            self.session = aiohttp.ClientSession(timeout=timeout)
        return self.session

    async def close(self):
        """Close the ClientSession."""
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch(
        self, 
        url: str, 
        method: str = "GET", 
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Any = None,
        json_data: Any = None,
        retries: int = 3,
        delay: float = 1.0
    ) -> Dict[str, Any]:
        """
        Perform an HTTP request with retries, rate limiting, proxy rotation, and security checks.
        """
        # SECURITY: Validate URL to prevent SSRF attacks
        if not URLValidator.is_safe_url(url):
            logger.error(f"Blocked unsafe URL: {url}")
            return {"status": 0, "text": "", "error": "Unsafe URL blocked", "ok": False}
        
        if headers is None:
            headers = {}
            
        if "User-Agent" not in headers:
            headers["User-Agent"] = secrets.choice(self.user_agents)

        session = await self.get_session()
        
        # Auto-fetch proxies if needed and enabled (lazy load)
        if not self.proxies and self.auto_fetch:
            await self.fetch_free_proxies()
            self.auto_fetch = False  # Only try once to avoid loops
        
        async with self.sem:
            for attempt in range(retries):
                proxy = self.get_proxy()
                
                try:
                    await asyncio.sleep(random.uniform(0.1, 0.5))
                    
                    # Manual redirect handling
                    current_url = url
                    redirect_count = 0
                    max_redirects = 5
                    
                    while redirect_count < max_redirects:
                        # Validate current URL before fetching
                        if not URLValidator.is_safe_url(current_url):
                            logger.error(f"Blocked unsafe redirect URL: {current_url}")
                            return {"status": 0, "text": "", "error": "Unsafe redirect blocked", "ok": False}

                        async with session.request(
                            method, 
                            current_url, 
                            headers=headers, 
                            params=params, 
                            data=data, 
                            json=json_data,
                            proxy=proxy,
                            allow_redirects=False
                        ) as response:
                            
                            if response.status in (301, 302, 303, 307, 308):
                                redirect_count += 1
                                location = response.headers.get('Location')
                                if not location:
                                    pass # Treat as final response
                                else:
                                    current_url = urllib.parse.urljoin(current_url, location)
                                    logger.debug(f"Following redirect to {current_url}")
                                    continue
                            
                            # SECURITY: Check content length before downloading
                            if not ResourceLimiter.check_content_length(dict(response.headers)):
                                return {"status": 0, "text": "", "error": "Response too large", "ok": False}
                            
                            if response.status == 429:
                                retry_after = int(response.headers.get("Retry-After", 5))
                                logger.warning(f"Rate limited by {current_url}. Waiting {retry_after}s...")
                                await asyncio.sleep(retry_after)
                                break # Break inner loop to retry outer loop
                            
                            # 403 Forbidden might indicate a bad proxy or bot detection
                            if response.status == 403 and proxy:
                                logger.debug(f"Proxy {proxy} blocked by {current_url}")
                                break # Break inner loop to retry outer loop
                            
                            # HTTP 202 Accepted - retry once with delay
                            if response.status == 202 and attempt < retries - 1:
                                logger.debug(f"HTTP 202 Accepted - retrying after delay")
                                await asyncio.sleep(2)
                                break # Break inner loop to retry outer loop
                            
                            try:
                                # SECURITY: Read with size limit
                                content_bytes = await ResourceLimiter.read_limited(response)
                                text = content_bytes.decode('utf-8', errors='ignore')
                            except ValueError as e:
                                # Size limit exceeded
                                return {"status": 0, "text": "", "error": str(e), "ok": False}
                            except UnicodeDecodeError:
                                # Fallback for binary content
                                text = str(await response.read())
                                
                            return {
                                "status": response.status,
                                "text": text,
                                "headers": dict(response.headers),
                                "url": str(response.url),
                                "ok": response.status < 400
                            }
                            
                    if redirect_count >= max_redirects:
                         return {"status": 0, "text": "", "error": "Too many redirects", "ok": False}
                        
                except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
                    # Proxy errors often manifest as ClientProxyConnectionError, ServerDisconnectedError, etc.
                    logger.debug(f"Request failed ({attempt+1}/{retries}) with proxy {proxy}: {e}")
                    
                    if attempt == retries - 1:
                        logger.error(f"Max retries reached for {url}")
                        return {"status": 0, "text": "", "error": str(e), "ok": False}
                    
                    await asyncio.sleep(delay * (2 ** attempt))
                    
        return {"status": 0, "text": "", "error": "Unknown error", "ok": False}
