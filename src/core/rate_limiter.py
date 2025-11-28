<<<<<<< HEAD
import time
import sqlite3
from pathlib import Path
from threading import Lock
import logging

logger = logging.getLogger("OSINT_Tool")

class RateLimiter:
    """
    Persistent, thread-safe rate limiter using SQLite.
    Persists state across tool restarts to prevent abuse.
    """
    
    def __init__(self, max_calls: int, time_window: float, resource_id: str = "default"):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of allowed calls within the time window.
            time_window: Time window in seconds.
            resource_id: Unique identifier for the resource being limited (e.g., 'hibp_api', 'twitter_search')
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.resource_id = resource_id
        self.lock = Lock()
        
        # Setup persistent DB
        self.db_path = Path.home() / ".osint_cache" / "rate_limits.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for rate limits."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Table to store timestamps of calls
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        resource_id TEXT,
                        timestamp REAL
                    )
                ''')
                
                # Index for performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_resource_timestamp 
                    ON rate_limits(resource_id, timestamp)
                ''')
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to initialize rate limit DB: {e}")

    def is_allowed(self) -> bool:
        """
        Check if an operation is allowed under the current rate limit.
        Records the call if allowed.
        
        Returns:
            True if allowed, False otherwise.
        """
        with self.lock:
            try:
                now = time.time()
                cutoff = now - self.time_window
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 1. Cleanup old entries (lazy expiration)
                cursor.execute('''
                    DELETE FROM rate_limits 
                    WHERE resource_id = ? AND timestamp < ?
                ''', (self.resource_id, cutoff))
                
                # 2. Count current calls in window
                cursor.execute('''
                    SELECT COUNT(*) FROM rate_limits 
                    WHERE resource_id = ?
                ''', (self.resource_id,))
                
                current_count = cursor.fetchone()[0]
                
                if current_count < self.max_calls:
                    # Allowed: Record new call
                    cursor.execute('''
                        INSERT INTO rate_limits (resource_id, timestamp)
                        VALUES (?, ?)
                    ''', (self.resource_id, now))
                    conn.commit()
                    conn.close()
                    return True
                
                conn.commit()
                conn.close()
                return False
                
            except Exception as e:
                logger.error(f"Rate limiter error: {e}")
                # Fail open or closed? 
                # Fail closed for security/safety
                return False
=======
import time
import sqlite3
from pathlib import Path
from threading import Lock
import logging

logger = logging.getLogger("OSINT_Tool")

class RateLimiter:
    """
    Persistent, thread-safe rate limiter using SQLite.
    Persists state across tool restarts to prevent abuse.
    """
    
    def __init__(self, max_calls: int, time_window: float, resource_id: str = "default"):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of allowed calls within the time window.
            time_window: Time window in seconds.
            resource_id: Unique identifier for the resource being limited (e.g., 'hibp_api', 'twitter_search')
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.resource_id = resource_id
        self.lock = Lock()
        
        # Setup persistent DB
        self.db_path = Path.home() / ".osint_cache" / "rate_limits.db"
        self.db_path.parent.mkdir(exist_ok=True)
        self._init_db()

    def _init_db(self):
        """Initialize SQLite database for rate limits."""
        with self.lock:
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Table to store timestamps of calls
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rate_limits (
                        resource_id TEXT,
                        timestamp REAL
                    )
                ''')
                
                # Index for performance
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_resource_timestamp 
                    ON rate_limits(resource_id, timestamp)
                ''')
                
                conn.commit()
                conn.close()
            except Exception as e:
                logger.error(f"Failed to initialize rate limit DB: {e}")

    def is_allowed(self) -> bool:
        """
        Check if an operation is allowed under the current rate limit.
        Records the call if allowed.
        
        Returns:
            True if allowed, False otherwise.
        """
        with self.lock:
            try:
                now = time.time()
                cutoff = now - self.time_window
                
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # 1. Cleanup old entries (lazy expiration)
                cursor.execute('''
                    DELETE FROM rate_limits 
                    WHERE resource_id = ? AND timestamp < ?
                ''', (self.resource_id, cutoff))
                
                # 2. Count current calls in window
                cursor.execute('''
                    SELECT COUNT(*) FROM rate_limits 
                    WHERE resource_id = ?
                ''', (self.resource_id,))
                
                current_count = cursor.fetchone()[0]
                
                if current_count < self.max_calls:
                    # Allowed: Record new call
                    cursor.execute('''
                        INSERT INTO rate_limits (resource_id, timestamp)
                        VALUES (?, ?)
                    ''', (self.resource_id, now))
                    conn.commit()
                    conn.close()
                    return True
                
                conn.commit()
                conn.close()
                return False
                
            except Exception as e:
                logger.error(f"Rate limiter error: {e}")
                # Fail open or closed? 
                # Fail closed for security/safety
                return False
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
