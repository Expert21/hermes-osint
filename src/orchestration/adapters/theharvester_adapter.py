# DEPRECATED: Import from plugin instead
import logging
import warnings

# Use try/except to handle potential import errors during transition
try:
    from src.plugins.theharvester.adapter import TheHarvesterAdapter
except ImportError:
    # Fallback or just let it fail if plugin not found
    pass

logger = logging.getLogger(__name__)
warnings.warn(
    "Importing TheHarvesterAdapter from src.orchestration.adapters is deprecated. Use src.plugins.theharvester.adapter instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["TheHarvesterAdapter"]
