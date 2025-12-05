# DEPRECATED: Import from plugin instead
import logging
import warnings

# Use try/except to handle potential import errors during transition
try:
    from src.plugins.h8mail.adapter import H8MailAdapter
except ImportError:
    # Fallback or just let it fail if plugin not found
    pass

logger = logging.getLogger(__name__)
warnings.warn(
    "Importing H8MailAdapter from src.orchestration.adapters is deprecated. Use src.plugins.h8mail.adapter instead.",
    DeprecationWarning,
    stacklevel=2
)

__all__ = ["H8MailAdapter"]
