import sqlite3
import json
import logging
import hashlib
from datetime import datetime, timedelta
import time
from typing import Optional, Dict, Any
from pathlib import Path
from src.core.rate_limiter import RateLimiter

logger = logging.getLogger("OSINT_Tool")


class CacheManager:
    """
    SQLite-based caching system for OSINT results.
    Caches successful checks for 24 hours to avoid redundant requests.
    """
    
    def __init__(self, cache_dir: str = ".osint_cache", cache_duration_hours: int = 24):
        """
        Initialize cache manager.
        
        Args:
            cache_dir: Directory for cache database
            cache_duration_hours: How long to keep cached results
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        self.db_path = self.cache_dir / "osint_cache.db"
        self.cache_duration = timedelta(hours=cache_duration_hours)
        
        # Rate limit: 100 writes per minute to prevent local DoS
        self.write_limiter = RateLimiter(max_calls=50, time_window=60)
        
        self._init_database()
    
    def _init_database(self):
        """Initialize SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create cache table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cache (
                cache_key TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                platform TEXT NOT NULL,
                result_data TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL
            )
        ''')
        
        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_target_platform 
            ON cache(target, platform)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_expires_at 
            ON cache(expires_at)
        ''')
        
        conn.commit()
        conn.close()
        
        logger.debug(f"Cache database initialized at {self.db_path}")
    
    def _generate_cache_key(self, target: str, platform: str, extra: str = "") -> str:
        """
        Generate a unique cache key for a target + platform combination.
        
        Args:
            target: Target name
        
        Args:
            target: Target name
            platform: Platform name
            extra: Additional key data
            
        Returns:
            Cached result dict or None if not found/expired
        """
        cache_key = self._generate_cache_key(target, platform, extra)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT result_data, expires_at 
            FROM cache 
            WHERE cache_key = ?
        ''', (cache_key,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            logger.debug(f"Cache miss: {platform} for {target}")
            return None
        
        result_data, expires_at = row
        expires_at = datetime.fromisoformat(expires_at)
        
        # Check if expired
        if datetime.now() > expires_at:
            logger.debug(f"Cache expired: {platform} for {target}")
            self.delete(target, platform, extra)
            return None
        
        logger.debug(f"Cache hit: {platform} for {target}")
        return json.loads(result_data)
    
    def set(self, target: str, platform: str, result: Dict[str, Any], extra: str = "") -> bool:
        """
        Store result in cache.
        
        Args:
            target: Target name
            platform: Platform name
            result: Result data to cache
            extra: Additional key data
            
        Returns:
            True if successful, False otherwise
        """
        retries = 2
        for attempt in range(retries + 1):
            if self.write_limiter.is_allowed():
                try:
                    cache_key = self._generate_cache_key(target, platform, extra)
                    created_at = datetime.now()
                    expires_at = created_at + self.cache_duration
                    
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        INSERT OR REPLACE INTO cache 
                        (cache_key, target, platform, result_data, created_at, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        cache_key,
                        target,
                        platform,
                        json.dumps(result),
                        created_at.isoformat(),
                        expires_at.isoformat()
                    ))
                    
                    conn.commit()
                    conn.close()
                    
                    logger.debug(f"Cached result: {platform} for {target}")
                    return True
                except Exception as e:
                    logger.error(f"Cache write failed: {e}")
                    return False
            
            if attempt < retries:
                wait_time = 0.5 * (2 ** attempt)
                logger.warning(f"Cache write rate limit exceeded. Retrying in {wait_time}s...")
                time.sleep(wait_time)
        
        logger.error("Cache write failed after retries: Rate limit exceeded")
        return False
    
    def delete(self, target: str, platform: str, extra: str = ""):
        """
        Delete a specific cache entry.
        
        Args:
            target: Target name
            platform: Platform name
            extra: Additional key data
        """
        cache_key = self._generate_cache_key(target, platform, extra)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cache WHERE cache_key = ?', (cache_key,))
        
        conn.commit()
        conn.close()
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired cache entries.
        
        Returns:
            Number of entries deleted
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM cache 
            WHERE expires_at < ?
        ''', (datetime.now().isoformat(),))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired cache entries")
        
        return deleted_count
    
    def clear_all(self):
        """Clear all cache entries."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM cache')
        
        conn.commit()
        conn.close()
        
        logger.info("Cleared all cache entries")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute('SELECT COUNT(*) FROM cache')
        total = cursor.fetchone()[0]
        
        # Expired entries
        cursor.execute('''
            SELECT COUNT(*) FROM cache 
            WHERE expires_at < ?
        ''', (datetime.now().isoformat(),))
        expired = cursor.fetchone()[0]
        
        # Valid entries
        valid = total - expired
        
        # Size of database
        db_size = self.db_path.stat().st_size if self.db_path.exists() else 0
        
        conn.close()
        
        return {
            'total_entries': total,
            'valid_entries': valid,
            'expired_entries': expired,
            'database_size_bytes': db_size,
            'database_size_mb': round(db_size / (1024 * 1024), 2)
        }


# Global cache instance
_cache_instance = None


def get_cache_manager(cache_duration_hours: int = 24) -> CacheManager:
    """
    Get or create the global cache manager instance.
    
    Args:
        cache_duration_hours: Cache duration in hours
        
    Returns:
        CacheManager instance
    """
    global _cache_instance
    
    if _cache_instance is None:
        _cache_instance = CacheManager(cache_duration_hours=cache_duration_hours)
    
    return _cache_instance
