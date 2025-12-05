# DEPRECATED: Import from plugin instead
import logging
import warnings

# Use try/except to handle potential import errors during transition
try:
    from src.plugins.sherlock.adapter import SherlockAdapter
except ImportError:
    # Fallback or just let it fail if plugin not found
    pass

logger = logging.getLogger(__name__)
warnings.warn(
    "Importing SherlockAdapter from src.orchestration.adapters is deprecated. Use src.plugins.sherlock.adapter instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["SherlockAdapter"]
