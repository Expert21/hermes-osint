
"""
Hermes OSINT Tool
Advanced Open Source Intelligence Gathering Framework
"""

__version__ = "3.0"
__author__ = "Expert21"
__description__ = "Advanced OSINT Intelligence Gathering Tool"

# Core modules
from src.core.logger import setup_logger
from src.core.config import load_config

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "setup_logger",
    "load_config",
]
