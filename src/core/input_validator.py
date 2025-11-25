import re
from pathlib import Path
import logging
import os

logger = logging.getLogger("OSINT_Tool")


class InputValidator:
    """Validate and sanitize all user inputs to prevent injection attacks."""
    
    @staticmethod
    def sanitize_username(username: str, max_length: int = 100) -> str:
        """
        Sanitize username for use in URLs.
        
        Args:
            username: Raw username input
            max_length: Maximum allowed length
            
        Returns:
            Sanitized username
            
        Raises:
            ValueError: If username is invalid or contains dangerous patterns
        """
        # Remove whitespace
        username = username.strip()
        
        # Check for path traversal
        if '..' in username or username.startswith(('.', '/', '\\')):
            raise ValueError("Invalid username: contains path traversal sequences")
        
        # Allow only safe characters: alphanumeric, dots, dashes, underscores
        sanitized = re.sub(r'[^a-zA-Z0-9._-]', '', username)
        
        # Enforce length limit
        if len(sanitized) > max_length:
            raise ValueError(f"Username too long (max {max_length} characters)")
        
        if not sanitized:
            raise ValueError("Username cannot be empty after sanitization")
        
        return sanitized
    
    @staticmethod
    def validate_target_name(target: str) -> str:
        """
        Validate target name for OSINT search.
        
        Args:
            target: Raw target input
            
        Returns:
            Validated and trimmed target name
            
        Raises:
            ValueError: If target is invalid
        """
        if not target or len(target) > 200:
            raise ValueError("Target must be 1-200 characters")
        
        # Allow letters, numbers, spaces, and basic punctuation
        if not re.match(r'^[a-zA-Z0-9\s._-]+$', target):
            raise ValueError("Target contains invalid characters (only letters, numbers, spaces, dots, dashes, underscores allowed)")
        
        return target.strip()
    
    @staticmethod
    def validate_domain(domain: str) -> str:
        """
        Validate domain name format.
        
        Args:
            domain: Raw domain input
            
        Returns:
            Validated lowercase domain
            
        Raises:
            ValueError: If domain format is invalid
        """
        domain = domain.lower().strip()
        
        # Basic domain pattern: subdomain.example.com
        if not re.match(r'^([a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$', domain):
            raise ValueError("Invalid domain format")
        
        if len(domain) > 253:
            raise ValueError("Domain name too long (max 253 characters)")
        
        return domain
    
    @staticmethod
    def validate_email(email: str) -> str:
        """
        Validate email address format.
        
        Args:
            email: Raw email input
            
        Returns:
            Validated lowercase email
            
        Raises:
            ValueError: If email format is invalid
        """
        email = email.lower().strip()
        
        # Basic email pattern
        if not re.match(r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$', email):
            raise ValueError("Invalid email format")
        
        if len(email) > 254:
            raise ValueError("Email address too long")
        
        return email
    
    @staticmethod
    def validate_output_path(filepath: str, allowed_extensions: list = None) -> Path:
        """
        Validate output file path to prevent path traversal.
        
        Args:
            filepath: User-provided file path
            allowed_extensions: List of allowed extensions (e.g., ['.json', '.html'])
            
        Returns:
            Validated Path object
            
        Raises:
            ValueError: If path is invalid or unsafe
        """
        try:
            path = Path(filepath).resolve()
            
            # Check extension if restricted
            if allowed_extensions:
                if path.suffix not in allowed_extensions:
                    raise ValueError(f"File extension must be one of: {', '.join(allowed_extensions)}")
            
            # Block system directories (common dangerous paths)
            dangerous_dirs = [
                '/etc', '/sys', '/proc', '/dev', '/boot', '/root',
                'C:\\Windows', 'C:\\Program Files', 'C:\\Program Files (x86)',
                '/usr/bin', '/bin', '/sbin', '/usr/sbin'
            ]
            
            path_str = str(path)
            for danger in dangerous_dirs:
                if path_str.startswith(danger):
                    raise ValueError(f"Cannot write to system directory: {danger}")
            
            # Ensure parent directory exists and is writable
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if we can write to this location
            if path.exists() and not os.access(path, os.W_OK):
                raise ValueError("Path is not writable")
            
            return path
            
        except Exception as e:
            raise ValueError(f"Invalid output path: {e}")
