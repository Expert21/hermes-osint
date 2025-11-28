import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from src.core.async_request_manager import AsyncRequestManager
from src.modules.passive_intelligence import PassiveIntelligenceModule

logger = logging.getLogger("OSINT_Tool")

class AsyncSocialMediaChecker:
    """
    Async social media checker with passive-first logic and rate limiting.
    """
    
    def __init__(self):
        self.request_manager = AsyncRequestManager()
        self.passive_module = PassiveIntelligenceModule()
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
                            "source": "Active Check",
                            "confidence": 1.0
                        }
                    else:
                        logger.warning(f"⚠ Profile found but verification failed on {platform}: {url}")
                        return {
                            "platform": platform,
                            "url": url,
                            "status": "Found (Unverified)",
                            "status_code": 200,
                            "source": "Active Check",
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
        """Verify content markers"""
        content = content.lower()
        
        verification_markers = {
            "twitter": ["profile", "tweets", "following", "followers"],
            "instagram": ["followers", "following", "posts", "instagram"],
            "facebook": ["facebook", "profile", "friends", "posts"],
            "linkedin": ["linkedin", "experience", "connections", "profile"],
            "github": ["repositories", "contributions", "github", "profile"],
            "pinterest": ["pinterest", "pins", "boards", "followers"],
            "tiktok": ["tiktok", "followers", "following", "likes"]
        }
        
        platform_key = platform.lower().replace(" company", "").replace("linkedin company", "linkedin")
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
    Async entry point for social media checks with tiered intelligence.
    """
    checker = AsyncSocialMediaChecker()
    results = []
    
    logger.info(f"Starting social media enumeration for: {target} (Passive Only: {passive_only})")
    
    # Tier 1: Passive Discovery (Dorking)
    # We use the passive module to find profiles via search engines first
    logger.info("Phase 1: Passive Discovery (Dorking)...")
    passive_results = await checker.passive_module.dork_profiles(target)
    
    found_urls = set()
    for res in passive_results:
        found_urls.add(res['url'])
        results.append({
            "platform": res['platform'],
            "url": res['url'],
            "status": "Found (Passive)",
            "status_code": 200,
            "source": "Search Dork",
            "confidence": 0.9 # High confidence from search engine
        })
    
    logger.info(f"Passive phase found {len(results)} potential profiles.")

    # Tier 2: Active Verification
    if not passive_only:
        logger.info("Phase 2: Active Verification...")
        
        platforms_config = {
            "Twitter": ["https://twitter.com/{}", "https://x.com/{}"],
            "Instagram": ["https://www.instagram.com/{}"],
            "Facebook": ["https://www.facebook.com/{}"],
            "LinkedIn": ["https://www.linkedin.com/in/{}"],
            "LinkedIn Company": ["https://www.linkedin.com/company/{}"],
            "GitHub": ["https://github.com/{}"],
            "Pinterest": ["https://www.pinterest.com/{}"],
            "TikTok": ["https://www.tiktok.com/@{}"]
        }
        
        if target_type == "company":
            platforms_config.pop("LinkedIn", None)
        else:
            platforms_config.pop("LinkedIn Company", None)
            
        tasks = []
        
        # Only check platforms that weren't already found passively?
        # Or check all to be sure? 
        # Strategy: Check all standard usernames on platforms NOT found passively.
        # And verify the ones found passively if we want 100% confirmation (but dork is usually good enough).
        # Let's check standard usernames for any platform where we didn't find a dork result.
        
        for platform, url_patterns in platforms_config.items():
            # Check if we already found a profile for this platform
            already_found = any(r['platform'].lower() in platform.lower() for r in results)
            
            if not already_found:
                for url_pattern in url_patterns:
                    url = url_pattern.format(target)
                    if url not in found_urls:
                        tasks.append(checker._check_profile_exists(url, platform))
        
        if tasks:
            logger.info(f"Checking {len(tasks)} additional direct profiles...")
            active_results = await asyncio.gather(*tasks)
            
            for res in active_results:
                if res:
                    results.append(res)
    
    logger.info(f"Completed social media checks: {len(results)} profiles found")
    return results