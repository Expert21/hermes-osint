import logging
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
from src.core.async_request_manager import AsyncRequestManager
from src.core.utils import SafeSoup
from difflib import SequenceMatcher
import re
import asyncio


logger = logging.getLogger(__name__)

class AsyncProfileVerifier:
    """
    Async verification system to confirm social media profiles.
    """
    
    def __init__(self):
        self.request_manager = AsyncRequestManager()
        self.confidence_threshold = 0.4
    
    async def verify_profile(
        self, 
        url: str, 
        platform: str, 
        target_name: str,
        additional_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Verify if a profile likely belongs to the target asynchronously.
        """
        verification_result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        try:
            response = await self.request_manager.fetch(url)
            
            if not response["ok"]:
                logger.warning(f"Could not fetch profile for verification: {url}")
                return verification_result
            
            soup = SafeSoup(response["text"])
            content = response["text"].lower()
            
            # Platform-specific verification
            if "twitter" in platform.lower() or "x.com" in url:
                verification_result = self._verify_twitter(soup, content, target_name, additional_info)
            elif "linkedin" in platform.lower():
                verification_result = self._verify_linkedin(soup, content, target_name, additional_info)
            elif "github" in platform.lower():
                verification_result = self._verify_github(soup, content, target_name, additional_info)
            elif "instagram" in platform.lower():
                verification_result = self._verify_instagram(soup, content, target_name, additional_info)
            elif "facebook" in platform.lower():
                verification_result = self._verify_facebook(soup, content, target_name, additional_info)
            else:
                verification_result = self._verify_generic(soup, content, target_name, additional_info)
            
            verification_result["verified"] = (
                verification_result["confidence_score"] >= self.confidence_threshold
            )
            
            return verification_result
            
        except Exception as e:
            logger.error(f"Error during profile verification: {e}")
            return verification_result
    
    def _calculate_name_similarity(self, found_name: str, target_name: str) -> float:
        """Calculate similarity between names (0-1)"""
        found_name = found_name.lower().strip()
        target_name = target_name.lower().strip()
        
        if found_name == target_name:
            return 1.0
        
        found_parts = set(found_name.split())
        target_parts = set(target_name.split())
        
        if found_parts & target_parts:
            overlap_ratio = len(found_parts & target_parts) / len(target_parts)
            return min(overlap_ratio, 0.8)
        
        return SequenceMatcher(None, found_name, target_name).ratio()
    
    def _extract_metadata(self, soup: BeautifulSoup, selectors: List[str]) -> Optional[str]:
        """Extract metadata from HTML using multiple selectors"""
        for selector in selectors:
            elements = soup.select(selector)
            if elements:
                text = elements[0].get_text(strip=True)
                if text:
                    return text
        return None
    
    def _verify_twitter(self, soup: BeautifulSoup, content: str, target_name: str, additional_info: Optional[Dict] = None) -> Dict:
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        name_selectors = ['div[data-testid="UserName"]', 'span.css-901oao.css-16my406', 'meta[property="og:title"]']
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            result["extracted_data"]["display_name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        bio_selectors = ['div[data-testid="UserDescription"]', 'meta[property="og:description"]']
        bio = self._extract_metadata(soup, bio_selectors)
        if bio:
            result["extracted_data"]["bio"] = bio
            if additional_info:
                if additional_info.get("company") and additional_info["company"].lower() in bio.lower():
                    result["confidence_score"] += 0.2
                    result["verification_factors"].append("Company mentioned in bio")
                if additional_info.get("location") and additional_info["location"].lower() in bio.lower():
                    result["confidence_score"] += 0.15
                    result["verification_factors"].append("Location mentioned in bio")
        
        if 'verified' in content or 'blue check' in content:
            result["extracted_data"]["verified_account"] = True
            result["confidence_score"] += 0.15
            result["verification_factors"].append("Verified account")
        
        return result
    
    def _verify_linkedin(self, soup: BeautifulSoup, content: str, target_name: str, additional_info: Optional[Dict] = None) -> Dict:
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        name_selectors = ['h1.text-heading-xlarge', 'meta[property="og:title"]', 'title']
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            found_name = found_name.split('|')[0].strip()
            result["extracted_data"]["name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.6
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        if additional_info and additional_info.get("company"):
            if additional_info["company"].lower() in content:
                result["confidence_score"] += 0.3
                result["verification_factors"].append("Company match")
                result["extracted_data"]["company_found"] = True
        
        if additional_info and additional_info.get("location"):
            if additional_info["location"].lower() in content:
                result["confidence_score"] += 0.1
                result["verification_factors"].append("Location match")
        
        return result
    
    def _verify_github(self, soup: BeautifulSoup, content: str, target_name: str, additional_info: Optional[Dict] = None) -> Dict:
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        name_selectors = ['span[itemprop="name"]', 'meta[property="og:title"]']
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            result["extracted_data"]["name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        bio_selectors = ['div[data-bio-text]', 'meta[property="og:description"]']
        bio = self._extract_metadata(soup, bio_selectors)
        if bio:
            result["extracted_data"]["bio"] = bio
            if additional_info:
                if additional_info.get("company") and additional_info["company"].lower() in bio.lower():
                    result["confidence_score"] += 0.25
                    result["verification_factors"].append("Company in bio")
        
        if 'email' in content or '@' in content:
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
            if emails:
                result["extracted_data"]["emails"] = emails
                result["confidence_score"] += 0.15
                result["verification_factors"].append("Email found")
        
        return result
    
    def _verify_instagram(self, soup: BeautifulSoup, content: str, target_name: str, additional_info: Optional[Dict] = None) -> Dict:
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        name_selectors = ['meta[property="og:title"]']
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            found_name = found_name.split('(')[0].strip()
            result["extracted_data"]["name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        if 'verified' in content:
            result["confidence_score"] += 0.2
            result["verification_factors"].append("Verified account")
        
        return result
    
    def _verify_facebook(self, soup: BeautifulSoup, content: str, target_name: str, additional_info: Optional[Dict] = None) -> Dict:
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        name_selectors = ['meta[property="og:title"]', 'title']
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            result["extracted_data"]["name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        result["confidence_score"] *= 0.8
        return result
    
    def _verify_generic(self, soup: BeautifulSoup, content: str, target_name: str, additional_info: Optional[Dict] = None) -> Dict:
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        if target_name.lower() in content:
            result["confidence_score"] += 0.4
            result["verification_factors"].append("Target name found in content")
        
        return result
    
    def cross_reference_profiles(self, profiles: List[Dict[str, str]]) -> Dict[str, any]:
        """Cross-reference multiple profiles"""
        if len(profiles) < 2:
            return {"cross_reference_score": 0.0, "shared_indicators": []}
        
        shared_indicators = []
        cross_ref_score = 0.0
        
        for profile in profiles:
            platform = profile.get("platform")
            url = profile.get("url")
            
            for other_profile in profiles:
                if other_profile != profile:
                    other_platform = other_profile.get("platform")
                    if other_platform.lower() in url.lower():
                        shared_indicators.append(f"{platform} links to {other_platform}")
                        cross_ref_score += 0.2
        
        return {
            "cross_reference_score": min(cross_ref_score, 1.0),
            "shared_indicators": shared_indicators
        }


async def enhanced_social_media_check_with_verification_async(
    target: str,
    target_type: str,
    config: Dict,
    additional_info: Optional[Dict] = None
) -> List[Dict]:
    """
    Async combined function: check for profiles AND verify them.
    """
    from src.modules.social_media import run_social_media_checks_async
    
    # Phase 1: Discover
    logger.info("Phase 1: Discovering potential profiles...")
    potential_profiles = await run_social_media_checks_async(target, target_type, config)
    
    # Phase 2: Verify
    logger.info("Phase 2: Verifying discovered profiles...")
    verifier = AsyncProfileVerifier()
    verified_profiles = []
    
    tasks = []
    for profile in potential_profiles:
        url = profile.get("url")
        platform = profile.get("platform")
        tasks.append(verifier.verify_profile(url, platform, target, additional_info))
    
    verification_results = await asyncio.gather(*tasks)
    
    for i, verification in enumerate(verification_results):
        profile = potential_profiles[i]
        
        profile["verification"] = verification
        profile["confidence_score"] = verification["confidence_score"]
        profile["verified"] = verification["verified"]
        
        if verification["verified"]:
            verified_profiles.append(profile)
            logger.info(f"✓ {profile['platform']} profile verified (confidence: {verification['confidence_score']:.2f})")
        else:
            logger.warning(f"✗ {profile['platform']} profile verification failed (confidence: {verification['confidence_score']:.2f})")
    
    # Phase 3: Cross-reference
    if len(verified_profiles) > 1:
        logger.info("Phase 3: Cross-referencing verified profiles...")
        cross_ref = verifier.cross_reference_profiles(verified_profiles)
        for profile in verified_profiles:
            profile["cross_reference"] = cross_ref
    
    logger.info(f"Verification complete: {len(verified_profiles)}/{len(potential_profiles)} profiles verified")
    return verified_profiles