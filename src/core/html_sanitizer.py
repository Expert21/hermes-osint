import logging

try:
    import bleach
    BLEACH_AVAILABLE = True
except ImportError:
    BLEACH_AVAILABLE = False
    logging.warning("bleach module not available - HTML sanitization limited")

logger = logging.getLogger("OSINT_Tool")


class HTMLSanitizer:
    """Sanitize HTML content to prevent injection attacks."""
    
    @staticmethod
    def sanitize_text(text: str, max_length: int = 2000) -> str:
        """
        Remove all HTML tags and limit length.
        
        Args:
            text: Raw text that may contain HTML
            max_length: Maximum allowed length
            
        Returns:
            Sanitized plain text
        """
        if not text:
            return ""
        
        # Use bleach if available for thorough sanitization
        if BLEACH_AVAILABLE:
            # Strip all HTML tags
            clean = bleach.clean(text, tags=[], strip=True)
        else:
            # Fallback: basic HTML entity replacement
            clean = text.replace('<', '&lt;').replace('>', '&gt;')
            clean = clean.replace('"', '&quot;').replace("'", '&#x27;')
        
        # Limit length to prevent DoS
        if len(clean) > max_length:
            clean = clean[:max_length] + "..."
        
        return clean.strip()
    
    @staticmethod
    def safe_parse_html(html_content: str):
        """
        Parse HTML safely using html.parser to avoid XXE attacks.
        
        Args:
            html_content: HTML string to parse
            
        Returns:
            BeautifulSoup object
            
        Note:
            Uses 'html.parser' instead of 'lxml' to prevent XML External Entity (XXE) attacks
        """
        from src.core.utils import SafeSoup
        
        # Use SafeSoup wrapper
        soup = SafeSoup(html_content)
        return soup
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Sanitize URL for safe display.
        
        Args:
            url: Raw URL
            
        Returns:
            Sanitized URL
        """
        if not url:
            return ""
        
        # Remove javascript: and data: URIs
        url_lower = url.lower().strip()
        if url_lower.startswith(('javascript:', 'data:', 'vbscript:')):
            logger.warning(f"Blocked potentially malicious URL scheme: {url[:50]}")
            return ""
        
        # Basic length limit
        if len(url) > 2000:
            url = url[:2000] + "..."
        
        return url.strip()
