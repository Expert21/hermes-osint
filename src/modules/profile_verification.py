import requests
import logging
import time
import random
from typing import Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("OSINT_Tool")

class SocialMediaChecker:
    """Enhanced social media checker with detection avoidance"""
    
    def __init__(self):
        self.session = self._create_session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
    def _create_session(self) -> requests.Session:
        """Create a session with retry logic and connection pooling"""
        session = requests.Session()
        
        # Configure retry strategy for transient failures
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "HEAD"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def _get_random_headers(self) -> Dict[str, str]:
        """Generate randomized headers to mimic real browser"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    
    def _random_delay(self, min_seconds: float = 2.0, max_seconds: float = 5.0):
        """Add random delay between requests to appear more human"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"Waiting {delay:.2f}s before next request")
        time.sleep(delay)
    
    def _check_profile_exists(self, url: str, platform: str) -> Optional[Dict[str, str]]:
        """
        Check if a profile exists with detection avoidance.
        Returns None if not found or error, dict with details if found.
        """
        try:
            self._random_delay(2.0, 5.0)  # Random delay before each request
            
            headers = self._get_random_headers()
            
            # Set appropriate timeout
            response = self.session.get(
                url, 
                headers=headers, 
                timeout=15,
                allow_redirects=True
            )
            
            # Check for various success indicators
            if response.status_code == 200:
                # Additional verification based on platform
                if self._verify_profile_content(response, platform):
                    logger.info(f"✓ Found verified profile on {platform}: {url}")
                    return {
                        "platform": platform,
                        "url": url,
                        "status": "Verified",
                        "status_code": response.status_code
                    }
                else:
                    logger.warning(f"⚠ Profile found but verification failed on {platform}: {url}")
                    return {
                        "platform": platform,
                        "url": url,
                        "status": "Found (Unverified)",
                        "status_code": response.status_code
                    }
            elif response.status_code == 404:
                logger.debug(f"✗ No profile found on {platform}")
                return None
            elif response.status_code == 403:
                logger.warning(f"⚠ Access forbidden on {platform} (possible blocking)")
                return None
            elif response.status_code == 429:
                logger.error(f"⚠ Rate limited on {platform} - backing off")
                time.sleep(30)  # Long backoff for rate limiting
                return None
            else:
                logger.warning(f"? Unexpected status {response.status_code} on {platform}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error(f"✗ Timeout checking {platform}")
            return None
        except requests.exceptions.ConnectionError:
            logger.error(f"✗ Connection error checking {platform}")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"✗ Error checking {platform}: {e}")
            return None
    
    def _verify_profile_content(self, response: requests.Response, platform: str) -> bool:
        """
        Verify that the response actually contains a valid profile.
        This helps reduce false positives from landing pages or error pages.
        """
        content = response.text.lower()
        
        # Platform-specific verification markers
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
        
        # Check if at least 2 markers are present
        matches = sum(1 for marker in markers if marker in content)
        
        # Also check for common "not found" indicators
        not_found_markers = ["page not found", "doesn't exist", "isn't available", "suspended"]
        has_not_found = any(marker in content for marker in not_found_markers)
        
        return matches >= 2 and not has_not_found


def run_social_media_checks(target: str, target_type: str, config: Dict) -> List[Dict[str, str]]:
    """
    Enhanced social media checking with verification and evasion.
    """
    checker = SocialMediaChecker()
    results = []
    
    # Define platforms with multiple possible URL patterns
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
    
    # Filter platforms based on target type
    if target_type == "company":
        platforms_config.pop("LinkedIn", None)
    else:
        platforms_config.pop("LinkedIn Company", None)
    
    logger.info(f"Checking {len(platforms_config)} platforms for: {target}")
    logger.info("Using detection avoidance measures (this will take time)...")
    
    for platform, url_patterns in platforms_config.items():
        # Try each URL pattern for the platform
        for url_pattern in url_patterns:
            url = url_pattern.format(target)
            result = checker._check_profile_exists(url, platform)
            
            if result:
                results.append(result)
                break  # Found valid profile, no need to try other patterns
    
    logger.info(f"Completed social media checks: {len(results)} profiles found")
    return results