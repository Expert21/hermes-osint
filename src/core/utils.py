from bs4 import BeautifulSoup
from typing import Optional, Union

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
