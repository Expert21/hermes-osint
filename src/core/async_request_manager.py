# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

import asyncio
import aiohttp
import logging
import random
import secrets
import urllib.parse
from typing import Optional, Dict, Any
from src.core.url_validator import URLValidator
from src.core.resource_limiter import ResourceLimiter
from src.core.utils import Sanitizer
from src.core.proxy_manager import ProxyManager

logger = logging.getLogger("OSINT_Tool")

class AsyncRequestManager:
    """
    Manages async HTTP requests with rate limiting, retries, and enterprise proxy support.
    """
    
    def __init__(self, proxy_manager: Optional[ProxyManager] = None):
        self.session: Optional[aiohttp.ClientSession] = None
        self.sem = asyncio.Semaphore(10)
        self.proxy_manager = proxy_manager or ProxyManager()
        
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
        ]

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
            await asyncio.sleep(0.25)

    async def fetch(
        self, 
        url: str, 
        method: str = "GET", 
        headers: Optional[Dict] = None,
        params: Optional[Dict] = None,
        data: Any = None,
        json_data: Any = None,
        retries: int = 3,
        delay: float = 1.0,
        use_session: bool = False,
        session_id: Optional[str] = None,
        preferred_proxy_provider: Optional[str] = None,
        use_proxy: bool = True
    ) -> Dict[str, Any]:
        """
        Perform an HTTP request with retries, rate limiting, and enterprise proxy support.
        
        Args:
            url: Target URL
            method: HTTP method
            headers: Request headers
            params: Query parameters
            data: Request body data
            json_data: JSON request body
            retries: Number of retry attempts
            delay: Base delay between retries
            use_session: Use sticky sessions (same IP)
            session_id: Custom session ID
            preferred_proxy_provider: Preferred proxy provider name
            use_proxy: Whether to use proxy at all
        """
        # SECURITY: Validate URL
        if not URLValidator.is_safe_url(url):
            logger.error(f"Blocked unsafe URL: {Sanitizer.sanitize_url(url)}")
            return {"status": 0, "text": "", "error": "Unsafe URL blocked", "ok": False}
        
        if headers is None:
            headers = {}
            
        if "User-Agent" not in headers:
            headers["User-Agent"] = secrets.choice(self.user_agents)

        session = await self.get_session()
        
        # Generate session ID for sticky sessions
        sticky_session_id = None
        if use_session:
            sticky_session_id = session_id or secrets.token_hex(8)
        
        async with self.sem:
            for attempt in range(retries):
                # Get proxy from manager
                proxy = None
                if use_proxy:
                    proxy = await self.proxy_manager.get_proxy(
                        session_id=sticky_session_id,
                        preferred_provider=preferred_proxy_provider
                    )
                
                try:
                    # Randomized delay to avoid pattern detection
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    current_url = url
                    redirect_count = 0
                    max_redirects = 5
                    
                    while redirect_count < max_redirects:
                        # DNS rebinding protection
                        if not URLValidator.is_safe_url(current_url):
                            logger.error(f"Blocked unsafe URL (DNS rebinding): {Sanitizer.sanitize_url(current_url)}")
                            return {"status": 0, "text": "", "error": "DNS rebinding protection triggered", "ok": False}

                        async with session.request(
                            method, 
                            current_url, 
                            headers=headers, 
                            params=params, 
                            data=data, 
                            json=json_data,
                            proxy=proxy,
                            allow_redirects=False,
                            ssl=True  # Enforce SSL verification
                        ) as response:
                            
                            # Handle redirects manually
                            if response.status in (301, 302, 303, 307, 308):
                                redirect_count += 1
                                location = response.headers.get('Location')
                                if not location:
                                    break
                                else:
                                    current_url = urllib.parse.urljoin(current_url, location)
                                    logger.debug(f"Following redirect to {Sanitizer.sanitize_url(current_url)}")
                                    continue
                            
                            # Check content length
                            if not ResourceLimiter.check_content_length(dict(response.headers)):
                                return {"status": 0, "text": "", "error": "Response too large", "ok": False}
                            
                            # Handle rate limiting
                            if response.status == 429:
                                retry_after = int(response.headers.get("Retry-After", 5))
                                logger.warning(f"Rate limited. Waiting {retry_after}s...")
                                await asyncio.sleep(retry_after)
                                break
                            
                            # Proxy blocked - try next proxy
                            if response.status == 403 and proxy:
                                logger.debug(f"Proxy blocked, trying next provider")
                                break
                            
                            # Retry on 202 Accepted
                            if response.status == 202 and attempt < retries - 1:
                                logger.debug("HTTP 202 - retrying")
                                await asyncio.sleep(2)
                                break
                            
                            # Read response
                            try:
                                content_bytes = await ResourceLimiter.read_limited(response)
                                text = content_bytes.decode('utf-8', errors='ignore')
                            except ValueError as e:
                                return {"status": 0, "text": "", "error": str(e), "ok": False}
                            except UnicodeDecodeError:
                                text = str(await response.read())
                                
                            return {
                                "status": response.status,
                                "text": text,
                                "headers": dict(response.headers),
                                "url": str(response.url),
                                "ok": response.status < 400,
                                "proxy_used": proxy is not None
                            }
                            
                    if redirect_count >= max_redirects:
                         return {"status": 0, "text": "", "error": "Too many redirects", "ok": False}
                        
                except (aiohttp.ClientError, asyncio.TimeoutError, OSError) as e:
                    logger.debug(f"Request failed ({attempt+1}/{retries}): {e}")
                    
                    if attempt == retries - 1:
                        logger.error(f"Max retries reached for {Sanitizer.sanitize_url(url)}")
                        return {"status": 0, "text": "", "error": str(e), "ok": False}
                    
                    # Exponential backoff
                    await asyncio.sleep(delay * (2 ** attempt))
                    
        return {"status": 0, "text": "", "error": "Unknown error", "ok": False}