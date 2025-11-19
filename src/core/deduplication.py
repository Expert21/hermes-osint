import logging
from typing import List, Dict, Set, Tuple
from urllib.parse import urlparse, urlunparse
from difflib import SequenceMatcher

logger = logging.getLogger("OSINT_Tool")


class ResultDeduplicator:
    """
    Deduplication and correlation engine for OSINT results.
    Merges duplicate findings and identifies connections between profiles.
    """
    
    def __init__(self):
        self.similarity_threshold = 0.85  # 85% similarity for URL matching
    
    def normalize_url(self, url: str) -> str:
        """
        Normalize URLs for comparison by removing tracking parameters,
        converting to lowercase, and standardizing format.
        
        Args:
            url: URL to normalize
            
        Returns:
            Normalized URL string
        """
        try:
            parsed = urlparse(url.lower().strip())
            
            # Remove common tracking parameters
            # Keep only the scheme, netloc, and path
            normalized = urlunparse((
                parsed.scheme or 'https',
                parsed.netloc,
                parsed.path.rstrip('/'),
                '',  # params
                '',  # query
                ''   # fragment
            ))
            
            return normalized
        except Exception as e:
            logger.warning(f"Failed to normalize URL {url}: {e}")
            return url.lower().strip()
    
    def calculate_url_similarity(self, url1: str, url2: str) -> float:
        """
        Calculate similarity between two URLs using sequence matching.
        
        Args:
            url1: First URL
            url2: Second URL
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        norm1 = self.normalize_url(url1)
        norm2 = self.normalize_url(url2)
        
        return SequenceMatcher(None, norm1, norm2).ratio()
    
    def deduplicate_results(self, results: List[Dict]) -> List[Dict]:
        """
        Remove duplicate results based on URL similarity.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            Deduplicated list of results
        """
        if not results:
            return []
        
        unique_results = []
        seen_urls = set()
        duplicate_count = 0
        
        for result in results:
            url = result.get('url', '')
            if not url:
                unique_results.append(result)
                continue
            
            normalized_url = self.normalize_url(url)
            
            # Check if we've seen this exact normalized URL
            if normalized_url in seen_urls:
                duplicate_count += 1
                logger.debug(f"Duplicate found: {url}")
                continue
            
            # Check for similar URLs (fuzzy matching)
            is_duplicate = False
            for seen_url in seen_urls:
                similarity = self.calculate_url_similarity(normalized_url, seen_url)
                if similarity >= self.similarity_threshold:
                    duplicate_count += 1
                    logger.debug(f"Similar URL found ({similarity:.2%}): {url}")
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                seen_urls.add(normalized_url)
                unique_results.append(result)
        
        logger.info(f"Deduplication: {len(results)} → {len(unique_results)} results ({duplicate_count} duplicates removed)")
        return unique_results
    
    def calculate_result_quality_score(self, result: Dict) -> int:
        """
        Calculate a quality score (0-100) for a result based on various factors.
        
        Scoring factors:
        - Verification status: +40 points if verified
        - Has description/snippet: +20 points
        - Has title: +15 points
        - Valid URL: +15 points
        - Source credibility: +10 points
        
        Args:
            result: Result dictionary
            
        Returns:
            Quality score between 0 and 100
        """
        score = 0
        
        # Verification status (40 points)
        status = result.get('status', '').lower()
        if 'verified' in status:
            score += 40
        elif 'found' in status:
            score += 20
        
        # Has description or snippet (20 points)
        description = result.get('description', '') or result.get('snippet', '')
        if description and len(description) > 10:
            score += 20
        
        # Has title (15 points)
        title = result.get('title', '')
        if title and len(title) > 3:
            score += 15
        
        # Valid URL (15 points)
        url = result.get('url', '')
        if url and url.startswith(('http://', 'https://')):
            score += 15
        
        # Source credibility (10 points)
        source = result.get('source', '').lower() or result.get('platform', '').lower()
        credible_sources = ['linkedin', 'github', 'twitter', 'facebook', 'instagram']
        if any(cs in source for cs in credible_sources):
            score += 10
        
        return min(score, 100)  # Cap at 100
    
    def identify_connections(self, results: List[Dict]) -> List[Dict[str, any]]:
        """
        Identify potential connections between discovered profiles.
        
        Args:
            results: List of result dictionaries
            
        Returns:
            List of connection dictionaries
        """
        connections = []
        
        # Group results by platform/source
        platforms = {}
        for result in results:
            platform = result.get('platform') or result.get('source', 'unknown')
            if platform not in platforms:
                platforms[platform] = []
            platforms[platform].append(result)
        
        # Identify cross-platform connections
        platform_list = list(platforms.keys())
        for i, platform1 in enumerate(platform_list):
            for platform2 in platform_list[i+1:]:
                if platforms[platform1] and platforms[platform2]:
                    connections.append({
                        'type': 'cross_platform',
                        'platforms': [platform1, platform2],
                        'description': f"Target found on both {platform1} and {platform2}",
                        'confidence': 'medium'
                    })
        
        return connections
    
    def merge_and_score_results(
        self,
        search_results: List[Dict],
        social_results: List[Dict]
    ) -> Dict[str, any]:
        """
        Main function to merge, deduplicate, and score all results.
        
        Args:
            search_results: Results from search engines
            social_results: Results from social media checks
            
        Returns:
            Dictionary with processed results and metadata
        """
        logger.info("Starting result deduplication and correlation...")
        
        # Combine all results
        all_results = search_results + social_results
        
        # Deduplicate
        unique_results = self.deduplicate_results(all_results)
        
        # Calculate quality scores
        for result in unique_results:
            result['quality_score'] = self.calculate_result_quality_score(result)
        
        # Sort by quality score (highest first)
        unique_results.sort(key=lambda x: x.get('quality_score', 0), reverse=True)
        
        # Identify connections
        connections = self.identify_connections(unique_results)
        
        # Separate back into categories
        final_search = [r for r in unique_results if r.get('source') and not r.get('platform')]
        final_social = [r for r in unique_results if r.get('platform')]
        
        # Calculate statistics
        stats = {
            'total_original': len(all_results),
            'total_unique': len(unique_results),
            'duplicates_removed': len(all_results) - len(unique_results),
            'search_results': len(final_search),
            'social_results': len(final_social),
            'connections_found': len(connections),
            'avg_quality_score': sum(r.get('quality_score', 0) for r in unique_results) / len(unique_results) if unique_results else 0,
            'high_quality_results': len([r for r in unique_results if r.get('quality_score', 0) >= 70])
        }
        
        logger.info(f"Deduplication complete:")
        logger.info(f"  Total results: {stats['total_original']} → {stats['total_unique']}")
        logger.info(f"  Average quality score: {stats['avg_quality_score']:.1f}/100")
        logger.info(f"  High quality results (≥70): {stats['high_quality_results']}")
        logger.info(f"  Connections identified: {stats['connections_found']}")
        
        return {
            'search_engines': final_search,
            'social_media': final_social,
            'connections': connections,
            'statistics': stats
        }


def deduplicate_and_correlate(
    search_results: List[Dict],
    social_results: List[Dict]
) -> Dict[str, any]:
    """
    Convenience function to deduplicate and correlate results.
    
    Args:
        search_results: Results from search engines
        social_results: Results from social media
        
    Returns:
        Processed results with deduplication and correlation
    """
    deduplicator = ResultDeduplicator()
    return deduplicator.merge_and_score_results(search_results, social_results)
