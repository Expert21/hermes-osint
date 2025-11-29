import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from src.core.async_request_manager import AsyncRequestManager

logger = logging.getLogger("OSINT_Tool")

class AsyncSocialMediaChecker:
    """
    Async social media checker for stable platforms only.
    Supports: GitHub, Twitter/X, Instagram
    """
    
    def __init__(self):
        self.request_manager = AsyncRequestManager()
        self.backoff_factor = 1.5
        self.initial_delay = 1.0
    
    async def _check_profile_exists(self, url: str, platform: str, retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Check if a profile exists asynchronously with exponential backoff.
        """
        delay = self.initial_delay
        
        for attempt in range(retries):
            try:
                # Add jitter to delay
                sleep_time = delay + random.uniform(0, 1)
                if attempt > 0:
                    logger.debug(f"Retrying {platform} in {sleep_time:.2f}s...")
                    await asyncio.sleep(sleep_time)
                
                response = await self.request_manager.fetch(url)
                
                if response["status"] == 200:
                    if self._verify_profile_content(response["text"], platform):
                        logger.info(f"✓ Found verified profile on {platform}: {url}")
                        return {
                            "platform": platform,
                            "url": url,
                            "status": "Verified",
                            "status_code": 200,
                            "source": "Direct Check",
                            "confidence": 1.0
                        }
                    else:
                        logger.warning(f"⚠ Profile found but verification failed on {platform}: {url}")
                        return {
                            "platform": platform,
                            "url": url,
                            "status": "Found (Unverified)",
                            "status_code": 200,
                            "source": "Direct Check",
                            "confidence": 0.7
                        }
                elif response["status"] == 404:
                    return None
                elif response["status"] == 429:
                    logger.warning(f"⚠ Rate limited on {platform}. Backing off...")
                    delay *= self.backoff_factor
                    continue
                else:
                    return None
                    
            except Exception as e:
                logger.error(f"✗ Error checking {platform}: {e}")
                return None
        
        return None
    
    def _verify_profile_content(self, content: str, platform: str) -> bool:
        """Verify content markers for supported platforms only"""
        content = content.lower()
        
        # Only verify for our 3 supported platforms
        verification_markers = {
            "twitter": ["profile", "tweets", "following", "followers"],
            "instagram": ["followers", "following", "posts", "instagram"],
            "github": ["repositories", "contributions", "github", "profile"]
        }
        
        platform_key = platform.lower()
        markers = verification_markers.get(platform_key, [])
        
        matches = sum(1 for marker in markers if marker in content)
        
        not_found_markers = ["page not found", "doesn't exist", "isn't available", "suspended"]
        has_not_found = any(marker in content for marker in not_found_markers)
        
        return matches >= 2 and not has_not_found


async def run_social_media_checks_async(
    target: str, 
    target_type: str, 
    config: Dict,
    passive_only: bool = False
) -> List[Dict[str, Any]]:
    """
    Async entry point for social media checks.
    Only checks GitHub, Twitter/X, and Instagram.
    """
    checker = AsyncSocialMediaChecker()
    results = []
    
    logger.info(f"Starting social media enumeration for: {target}")
    
    # Only check our 3 stable platforms
    platforms_config = {
        "Twitter": ["https://twitter.com/{}", "https://x.com/{}"],
        "Instagram": ["https://www.instagram.com/{}"],
        "GitHub": ["https://github.com/{}"]
    }
    
    tasks = []
    
    for platform, url_patterns in platforms_config.items():
        for url_pattern in url_patterns:
            url = url_pattern.format(target)
            tasks.append(checker._check_profile_exists(url, platform))
    
    if tasks:
        logger.info(f"Checking {len(tasks)} social media profiles...")
        active_results = await asyncio.gather(*tasks)
        
        for res in active_results:
            if res:
                results.append(res)
    
    logger.info(f"Completed social media checks: {len(results)} profiles found")
    return results