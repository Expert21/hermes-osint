# DEPRECATED: Import from plugin instead
import logging
import warnings

# Use try/except to handle potential import errors during transition
try:
    from src.plugins.exiftool.adapter import ExiftoolAdapter
except ImportError:
    # Fallback or just let it fail if plugin not found
    pass

logger = logging.getLogger(__name__)
warnings.warn(
    "Importing ExiftoolAdapter from src.orchestration.adapters is deprecated. Use src.plugins.exiftool.adapter instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["ExiftoolAdapter"]
