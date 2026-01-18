
import logging
import sys
import re
from colorama import init, Fore, Style

init(autoreset=True)

class ColoredFormatter(logging.Formatter):
    FORMATS = {
        logging.DEBUG: Fore.CYAN + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.INFO: Fore.GREEN + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.WARNING: Fore.YELLOW + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.ERROR: Fore.RED + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL,
        logging.CRITICAL: Fore.RED + Style.BRIGHT + "%(asctime)s - %(levelname)s - %(message)s" + Style.RESET_ALL
    }

    SENSITIVE_PATTERNS = [
        # Generic API Keys / Tokens / Passwords
        (re.compile(r'(api[_-]?key|token|password|secret|auth|access_key)["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.I), r'\1=***REDACTED***'),
        (re.compile(r'([?&])(api[_-]?key|token|password|secret)=([^&]+)', re.I), r'\1\2=***REDACTED***'),
        
        # Bearer Tokens
        (re.compile(r'Authorization:\s*Bearer\s+([a-zA-Z0-9._-]+)', re.I), r'Authorization: Bearer ***REDACTED***'),
        
        # AWS Access Key ID
        (re.compile(r'\b(AKIA|ASIA)[0-9A-Z]{16}\b'), r'***AWS_KEY***'),
        
        # AWS Secret Access Key
        (re.compile(r'\b[0-9a-zA-Z/+]{40}\b'), r'***AWS_SECRET***'),
        
        # Google API Key
        (re.compile(r'\bAIza[0-9A-Za-z-_]{35}\b'), r'***GOOGLE_KEY***'),
        
        # JWT Token (Header.Payload.Signature)
        (re.compile(r'\beyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\b'), r'***JWT***'),
        
        # Private Key Headers
        (re.compile(r'-----BEGIN [A-Z ]+ PRIVATE KEY-----'), r'***PRIVATE_KEY_START***'),
        
        # Slack Token
        (re.compile(r'xox[baprs]-([0-9a-zA-Z]{10,48})'), r'***SLACK_TOKEN***'),
        
        # PII: Email Addresses
        (re.compile(r'\b([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b'), r'***EMAIL***'),
        
        # PII: IP Addresses (IPv4)
        (re.compile(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'), r'***IP***'),
        
        # PII: US Phone Numbers (various formats)
        (re.compile(r'\b(\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'), r'***PHONE***'),
        
        # PII: Social Security Numbers
        (re.compile(r'\b\d{3}-\d{2}-\d{4}\b'), r'***SSN***'),
        
        # PII: Credit Card Numbers (basic pattern)
        (re.compile(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'), r'***CC***'),
    ]

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%H:%M:%S")
        formatted = formatter.format(record)
        
        # Sanitize
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            formatted = pattern.sub(replacement, formatted)
            
        return formatted

def setup_logger():
    """
    Sets up the logger with colored output.
    """
    logger = logging.getLogger("OSINT_Tool")
    logger.setLevel(logging.INFO)
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(ColoredFormatter())
    
    if not logger.handlers:
        logger.addHandler(ch)
        
    return logger
