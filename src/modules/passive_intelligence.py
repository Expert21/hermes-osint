import asyncio
import logging
import os
import urllib.parse
from typing import List, Dict, Any, Optional
from src.core.async_request_manager import AsyncRequestManager
from src.modules.search_engines import AsyncSearchEngineManager
from src.core.scan_logger import ScanLogger, EventType

logger = logging.getLogger("OSINT_Tool")

class PassiveIntelligenceModule:
    """
    Gather intelligence from passive sources without directly contacting the target.
    Sources: HIBP (Breaches), PGP Keyservers, Search Engine Dorks.
    """

    def __init__(self, scan_logger: Optional[ScanLogger] = None):
        self.request_manager = AsyncRequestManager()
        self.search_manager = AsyncSearchEngineManager()
        self.hibp_api_key = os.getenv("HIBP_API_KEY")
        self.scan_logger = scan_logger

    def _redact(self, value: str) -> str:
        """Redact sensitive values for logging."""
        if not value or len(value) < 4:
            return "****"
        return f"{value[:4]}****{value[-2:]}"

    async def check_breach_data(self, email: str) -> List[Dict[str, Any]]:
        """
        Check Have I Been Pwned API for breaches.
        Requires HIBP_API_KEY environment variable.
        """
        if not self.hibp_api_key:
            logger.warning("HIBP_API_KEY not found. Skipping breach check.")
            return []

        url = f"https://haveibeenpwned.com/api/v3/breachedaccount/{urllib.parse.quote(email)}?truncateResponse=false"
        
        # Redact API key for logging
        redacted_key = self._redact(self.hibp_api_key)
        logger.debug(f"Using HIBP API Key: {redacted_key}")
        
        headers = {
            "hibp-api-key": redacted_key,
            "user-agent": "Hermes-OSINT-Tool"
        }
        
        try:
            response = await self.request_manager.fetch(url, headers=headers)
            
            if response["status"] == 200:
                try:
                    breaches = json.loads(response["text"])
                    if self.scan_logger:
                        self.scan_logger.log_event(
                            EventType.SUCCESS,
                            "passive_intelligence",
                            f"HIBP check successful for {email}",
                            {"breach_count": len(breaches)}
                        )
                    return breaches
                except json.JSONDecodeError as e:
                    if self.scan_logger:
                        self.scan_logger.log_event(
                            EventType.API_ERROR,
                            "passive_intelligence",
                            "Failed to parse HIBP response",
                            {"email": email},
                            e
                        )
                    logger.error("Failed to parse HIBP response")
                    return []
            elif response["status"] == 404:
                return [] # No breaches found
            elif response["status"] == 429:
                if self.scan_logger:
                    self.scan_logger.log_event(
                        EventType.RATE_LIMIT,
                        "passive_intelligence",
                        "HIBP Rate Limit Exceeded",
                        {"email": email}
                    )
                logger.warning("HIBP Rate Limit Exceeded")
                return []
            else:
                if self.scan_logger:
                    self.scan_logger.log_event(
                        EventType.API_ERROR,
                        "passive_intelligence",
                        f"HIBP API Error: {response['status']}",
                        {"email": email, "status_code": response['status']}
                    )
                logger.error(f"HIBP API Error: {response['status']}")
                return []
        except Exception as e:
            if self.scan_logger:
                self.scan_logger.log_event(
                    EventType.FAILURE,
                    "passive_intelligence",
                    "Error checking breach data",
                    {"email": email},
                    e
                )
            logger.error(f"Error checking breach data: {e}")
            return []

    async def query_pgp_keyservers(self, email: str) -> List[Dict[str, str]]:
        """
        Query public PGP keyservers for email addresses.
        This is a great passive source as it confirms email existence and usage.
        """
        keyservers = [
            f"https://keyserver.ubuntu.com/pks/lookup?search={urllib.parse.quote(email)}&op=index&options=mr",
            # Add more if needed, but Ubuntu's is quite comprehensive
        ]

        results = []
        for url in keyservers:
            try:
                response = await self.request_manager.fetch(url)
                if response["ok"] and "pub:" in response["text"]:
                    # Parse the machine-readable output
                    lines = response["text"].split('\n')
                    
                    # SECURITY: Limit number of lines processed to prevent DoS
                    processed_count = 0
                    max_lines = 100
                    
                    for line in lines:
                        if processed_count >= max_lines:
                            logger.warning(f"PGP response truncated after {max_lines} lines")
                            break
                            
                        if line.startswith("pub:"):
                            processed_count += 1
                            parts = line.split(':')
                            if len(parts) > 1:
                                # SECURITY: Sanitize and limit length of extracted fields
                                key_id = parts[1] if len(parts) > 1 else "Unknown"
                                timestamp = parts[4] if len(parts) > 4 else "Unknown"
                                
                                # Truncate to safe length
                                key_id = key_id[:50]
                                timestamp = timestamp[:50]
                                
                                # Sanitize raw data line
                                safe_line = line[:200]
                                
                                results.append({
                                    "source": "PGP Keyserver",
                                    "key_id": key_id,
                                    "timestamp": timestamp,
                                    "data": safe_line
                                })
            except Exception as e:
                if self.scan_logger:
                    self.scan_logger.log_event(
                        EventType.FAILURE,
                        "passive_intelligence",
                        "PGP Keyserver query failed",
                        {"email": email, "url": url},
                        e
                    )
                logger.error(f"PGP Keyserver error: {e}")
        
        return results

    async def dork_profiles(self, username: str) -> List[Dict[str, str]]:
        """
        Use search engine dorks to find social media profiles passively.
        This avoids sending requests directly to social media platforms.
        """
        platforms = [
            "linkedin.com", "twitter.com", "facebook.com", "instagram.com", 
            "github.com", "reddit.com", "tiktok.com", "youtube.com"
        ]
        
        tasks = []
        for platform in platforms:
            query = f'site:{platform} "{username}"'
            tasks.append(self.search_manager.search_all(query, num_results=3))
            
        results_list = await asyncio.gather(*tasks)
        
        found_profiles = []
        for i, platform_results in enumerate(results_list):
            platform = platforms[i]
            for result in platform_results:
                # Basic validation to ensure the URL actually belongs to the platform
                if platform in result['url']:
                    found_profiles.append({
                        "platform": platform,
                        "url": result['url'],
                        "title": result['title'],
                        "source": "Passive Dork",
                        "confidence": "High" # Dorks are usually reliable for existence
                    })
                    
        return found_profiles

    async def gather_all_passive(self, target: str, target_type: str = "individual") -> Dict[str, Any]:
        """
        Run all passive intelligence gathering methods.
        """
        passive_data = {
            "breaches": [],
            "pgp_keys": [],
            "dork_profiles": []
        }
        
        tasks = []
        
        # If it looks like an email, check breaches and PGP
        if "@" in target:
            tasks.append(self.check_breach_data(target))
            tasks.append(self.query_pgp_keyservers(target))
        else:
            # If it's a username, we can't easily check HIBP/PGP without an email
            # But we can dork for profiles
            tasks.append(asyncio.sleep(0)) # Placeholder
            tasks.append(asyncio.sleep(0)) # Placeholder
            
        # Always dork for profiles using the target name/username
        tasks.append(self.dork_profiles(target))
        
        results = await asyncio.gather(*tasks)
        
        if "@" in target:
            passive_data["breaches"] = results[0]
            passive_data["pgp_keys"] = results[1]
        
        passive_data["dork_profiles"] = results[2]
        
        return passive_data
