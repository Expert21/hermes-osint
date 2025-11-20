import requests
import logging
from typing import Dict, List, Optional, Set
from bs4 import BeautifulSoup
import re
from difflib import SequenceMatcher

logger = logging.getLogger("OSINT_Tool")

class ProfileVerifier:
    """
    Advanced verification system to confirm social media profiles
    belong to the actual target through cross-referencing and content analysis.
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.confidence_threshold = 0.4  # Confidence score threshold (0-1)
    
    def verify_profile(
        self, 
        url: str, 
        platform: str, 
        target_name: str,
        additional_info: Optional[Dict[str, str]] = None
    ) -> Dict[str, any]:
        """
        Verify if a profile likely belongs to the target.
        Returns verification result with confidence score.
        
        Args:
            url: Profile URL
            platform: Platform name (Twitter, LinkedIn, etc.)
            target_name: Target's name
            additional_info: Additional info about target (location, company, etc.)
        """
        verification_result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        try:
            # Fetch profile content
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Could not fetch profile for verification: {url}")
                return verification_result
            
            soup = BeautifulSoup(response.text, 'html.parser')
            content = response.text.lower()
            
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
                # Generic verification
                verification_result = self._verify_generic(soup, content, target_name, additional_info)
            
            # Determine if verified based on confidence threshold
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
        
        # Direct match
        if found_name == target_name:
            return 1.0
        
        # Partial match (first name, last name)
        found_parts = set(found_name.split())
        target_parts = set(target_name.split())
        
        if found_parts & target_parts:  # Any overlap
            overlap_ratio = len(found_parts & target_parts) / len(target_parts)
            return min(overlap_ratio, 0.8)  # Cap partial matches at 0.8
        
        # Fuzzy string matching
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
    
    def _verify_twitter(
        self, 
        soup: BeautifulSoup, 
        content: str, 
        target_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Twitter-specific verification"""
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        # Extract profile name
        name_selectors = [
            'div[data-testid="UserName"]',
            'span.css-901oao.css-16my406',
            'meta[property="og:title"]'
        ]
        
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            result["extracted_data"]["display_name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        # Extract bio
        bio_selectors = [
            'div[data-testid="UserDescription"]',
            'meta[property="og:description"]'
        ]
        bio = self._extract_metadata(soup, bio_selectors)
        if bio:
            result["extracted_data"]["bio"] = bio
            
            # Check for additional info in bio
            if additional_info:
                if additional_info.get("company") and additional_info["company"].lower() in bio.lower():
                    result["confidence_score"] += 0.2
                    result["verification_factors"].append("Company mentioned in bio")
                
                if additional_info.get("location") and additional_info["location"].lower() in bio.lower():
                    result["confidence_score"] += 0.15
                    result["verification_factors"].append("Location mentioned in bio")
        
        # Check verification badge
        if 'verified' in content or 'blue check' in content:
            result["extracted_data"]["verified_account"] = True
            result["confidence_score"] += 0.15
            result["verification_factors"].append("Verified account")
        
        return result
    
    def _verify_linkedin(
        self, 
        soup: BeautifulSoup, 
        content: str, 
        target_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """LinkedIn-specific verification"""
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        # Extract name
        name_selectors = [
            'h1.text-heading-xlarge',
            'meta[property="og:title"]',
            'title'
        ]
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            # Clean LinkedIn title format ("Name | LinkedIn")
            found_name = found_name.split('|')[0].strip()
            result["extracted_data"]["name"] = found_name
            
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.6
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        # Extract current position/company
        if additional_info and additional_info.get("company"):
            company = additional_info["company"].lower()
            if company in content:
                result["confidence_score"] += 0.3
                result["verification_factors"].append("Company match")
                result["extracted_data"]["company_found"] = True
        
        # Extract location
        if additional_info and additional_info.get("location"):
            location = additional_info["location"].lower()
            if location in content:
                result["confidence_score"] += 0.1
                result["verification_factors"].append("Location match")
        
        return result
    
    def _verify_github(
        self, 
        soup: BeautifulSoup, 
        content: str, 
        target_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """GitHub-specific verification"""
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        # Extract name
        name_selectors = [
            'span[itemprop="name"]',
            'meta[property="og:title"]'
        ]
        found_name = self._extract_metadata(soup, name_selectors)
        if found_name:
            result["extracted_data"]["name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        # Extract bio
        bio_selectors = ['div[data-bio-text]', 'meta[property="og:description"]']
        bio = self._extract_metadata(soup, bio_selectors)
        if bio:
            result["extracted_data"]["bio"] = bio
            
            if additional_info:
                # Check for company/location in bio
                if additional_info.get("company") and additional_info["company"].lower() in bio.lower():
                    result["confidence_score"] += 0.25
                    result["verification_factors"].append("Company in bio")
        
        # Check for email in profile
        if 'email' in content or '@' in content:
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
            if emails:
                result["extracted_data"]["emails"] = emails
                result["confidence_score"] += 0.15
                result["verification_factors"].append("Email found")
        
        return result
    
    def _verify_instagram(
        self, 
        soup: BeautifulSoup, 
        content: str, 
        target_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Instagram-specific verification"""
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        # Instagram is heavily JS-rendered, metadata is key
        name_selectors = ['meta[property="og:title"]']
        found_name = self._extract_metadata(soup, name_selectors)
        
        if found_name:
            # Clean Instagram format
            found_name = found_name.split('(')[0].strip()
            result["extracted_data"]["name"] = found_name
            
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        # Check for verification badge
        if 'verified' in content:
            result["confidence_score"] += 0.2
            result["verification_factors"].append("Verified account")
        
        return result
    
    def _verify_facebook(
        self, 
        soup: BeautifulSoup, 
        content: str, 
        target_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Facebook-specific verification"""
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        # Extract from meta tags
        name_selectors = ['meta[property="og:title"]', 'title']
        found_name = self._extract_metadata(soup, name_selectors)
        
        if found_name:
            result["extracted_data"]["name"] = found_name
            name_score = self._calculate_name_similarity(found_name, target_name)
            if name_score > 0.7:
                result["confidence_score"] += name_score * 0.5
                result["verification_factors"].append(f"Name match: {name_score:.2f}")
        
        # Facebook provides limited public info, lower confidence by default
        result["confidence_score"] *= 0.8
        
        return result
    
    def _verify_generic(
        self, 
        soup: BeautifulSoup, 
        content: str, 
        target_name: str,
        additional_info: Optional[Dict] = None
    ) -> Dict:
        """Generic verification for unknown platforms"""
        result = {
            "verified": False,
            "confidence_score": 0.0,
            "verification_factors": [],
            "extracted_data": {}
        }
        
        # Check if target name appears prominently
        if target_name.lower() in content:
            result["confidence_score"] += 0.4
            result["verification_factors"].append("Target name found in content")
        
        return result
    
    def cross_reference_profiles(
        self, 
        profiles: List[Dict[str, str]]
    ) -> Dict[str, any]:
        """
        Cross-reference multiple profiles to increase confidence.
        Looks for consistent information across platforms.
        """
        if len(profiles) < 2:
            return {"cross_reference_score": 0.0, "shared_indicators": []}
        
        shared_indicators = []
        cross_ref_score = 0.0
        
        # Extract all linked accounts/URLs from each profile
        linked_accounts = {}
        for profile in profiles:
            platform = profile.get("platform")
            url = profile.get("url")
            
            # Check if other profiles are mentioned
            for other_profile in profiles:
                if other_profile != profile:
                    other_platform = other_profile.get("platform")
                    if other_platform.lower() in url.lower():
                        shared_indicators.append(
                            f"{platform} links to {other_platform}"
                        )
                        cross_ref_score += 0.2
        
        return {
            "cross_reference_score": min(cross_ref_score, 1.0),
            "shared_indicators": shared_indicators
        }


def enhanced_social_media_check_with_verification(
    target: str,
    target_type: str,
    config: Dict,
    additional_info: Optional[Dict] = None
) -> List[Dict]:
    """
    Combined function: check for profiles AND verify them.
    
    Args:
        target: Target username/name
        target_type: "individual" or "company"
        config: Configuration dict
        additional_info: Dict with keys like "company", "location", etc.
    """
    from src.modules.social_media import run_social_media_checks
    
    # First, find potential profiles
    logger.info("Phase 1: Discovering potential profiles...")
    potential_profiles = run_social_media_checks(target, target_type, config)
    
    # Then, verify each one
    logger.info("Phase 2: Verifying discovered profiles...")
    verifier = ProfileVerifier()
    verified_profiles = []
    
    for profile in potential_profiles:
        url = profile.get("url")
        platform = profile.get("platform")
        
        logger.info(f"Verifying {platform} profile...")
        verification = verifier.verify_profile(url, platform, target, additional_info)
        
        # Combine profile data with verification results
        profile["verification"] = verification
        profile["confidence_score"] = verification["confidence_score"]
        profile["verified"] = verification["verified"]
        
        if verification["verified"]:
            verified_profiles.append(profile)
            logger.info(f"✓ {platform} profile verified (confidence: {verification['confidence_score']:.2f})")
        else:
            logger.warning(f"✗ {platform} profile verification failed (confidence: {verification['confidence_score']:.2f})")
    
    # Cross-reference all verified profiles
    if len(verified_profiles) > 1:
        logger.info("Phase 3: Cross-referencing verified profiles...")
        cross_ref = verifier.cross_reference_profiles(verified_profiles)
        
        # Add cross-reference data to results
        for profile in verified_profiles:
            profile["cross_reference"] = cross_ref
    
    logger.info(f"Verification complete: {len(verified_profiles)}/{len(potential_profiles)} profiles verified")
    
    return verified_profiles