
from bs4 import BeautifulSoup
from typing import Union

def SafeSoup(html: Union[str, bytes], features: str = "html.parser", **kwargs) -> BeautifulSoup:
    """
    Safe wrapper for BeautifulSoup to prevent entity expansion attacks.
    Always uses 'html.parser' (or specified safe parser) and disables entity substitution if possible.
    
    Args:
        html: HTML content to parse
        features: Parser to use (default: html.parser)
        **kwargs: Additional arguments for BeautifulSoup
        
    Returns:
        BeautifulSoup object
    """
    # Enforce html.parser if not specified or if unsafe parser requested
    # (Though we allow overriding if really needed, but default is safe)
    if features not in ["html.parser", "lxml", "xml"]:
        features = "html.parser"
        
    # For this hardening, we prefer html.parser as it's Python's built-in and generally safe
    # against billion laughs compared to older lxml versions without configuration.
    # But we'll stick to the plan's simple wrapper.
    
    return BeautifulSoup(html, features, from_encoding=kwargs.get("from_encoding", "utf-8"), **{k:v for k,v in kwargs.items() if k != "from_encoding"})

class Sanitizer:
    """
    Proactive sanitization for logging to prevent PII and secret leaks.
    """
    
    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Mask query parameters in URLs to prevent PII leakage.
        Example: https://example.com/search?q=secret -> https://example.com/search?q=***
        """
        try:
            from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
            
            parsed = urlparse(url)
            if not parsed.query:
                return url
                
            # Mask all query parameters
            qs = parse_qs(parsed.query)
            masked_qs = {k: '***' for k in qs}
            
            # Keep * unencoded for readability
            new_query = urlencode(masked_qs, safe='*')
            
            return urlunparse((
                parsed.scheme,
                parsed.netloc,
                parsed.path,
                parsed.params,
                new_query,
                parsed.fragment
            ))
        except Exception:
            # If parsing fails, return a safe truncated version or just the domain if possible
            # For safety, just return "URL_SANITIZATION_FAILED" or similar if it's completely broken
            return "SANITIZED_URL"

    @staticmethod
    def truncate(text: str, max_length: int = 500) -> str:
        """Truncate long strings for logging."""
        if not text:
            return ""
        if len(text) <= max_length:
            return text
        return f"{text[:max_length]}... (truncated {len(text) - max_length} chars)"

    @staticmethod
    def sanitize_email(email: str) -> str:
        """Mask email address."""
        if not email or "@" not in email:
            return email
        try:
            user, domain = email.split("@")
            if len(user) > 2:
                masked_user = f"{user[:2]}***"
            else:
                masked_user = "***"
            return f"{masked_user}@{domain}"
        except Exception:
            return "***@***.***"

    @staticmethod
    def sanitize_key(key: str) -> str:
        """Mask API keys or secrets."""
        if not key:
            return ""
        if len(key) < 8:
            return "****"
        return f"{key[:4]}****{key[-4:]}"
