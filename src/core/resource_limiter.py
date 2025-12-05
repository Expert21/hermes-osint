
import logging

logger = logging.getLogger("OSINT_Tool")


class ResourceLimiter:
    """Manage resource limits to prevent DoS attacks."""
    
    # Default limits (configurable)
    MAX_RESPONSE_SIZE = 10 * 1024 * 1024  # 10 MB
    MAX_RESULTS_TOTAL = 1000
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 MB
    MAX_CHUNK_SIZE = 8192  # 8 KB chunks
    
    @staticmethod
    def auto_detect_resources():
        """
        Auto-detect system resources and adjust limits accordingly.
        """
        try:
            import psutil
            
            # Memory check
            mem = psutil.virtual_memory()
            total_ram_gb = mem.total / (1024**3)
            
            if total_ram_gb >= 16:
                ResourceLimiter.MAX_RESPONSE_SIZE = 50 * 1024 * 1024  # 50 MB
                ResourceLimiter.MAX_CONTENT_LENGTH = 200 * 1024 * 1024  # 200 MB
                ResourceLimiter.MAX_RESULTS_TOTAL = 5000
                logger.info(f"High-spec system detected ({total_ram_gb:.1f} GB RAM). Increased limits.")
            elif total_ram_gb >= 8:
                ResourceLimiter.MAX_RESPONSE_SIZE = 20 * 1024 * 1024  # 20 MB
                ResourceLimiter.MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100 MB
                ResourceLimiter.MAX_RESULTS_TOTAL = 2000
                logger.info(f"Mid-spec system detected ({total_ram_gb:.1f} GB RAM). Adjusted limits.")
            else:
                logger.info(f"Standard system detected ({total_ram_gb:.1f} GB RAM). Using default limits.")
                
        except ImportError:
            logger.warning("psutil not found. Using default resource limits.")
        except Exception as e:
            logger.warning(f"Resource auto-detection failed: {e}")

    
    @staticmethod
    def check_content_length(headers: dict) -> bool:
        """
        Check if Content-Length header is within acceptable limits.
        
        Args:
            headers: HTTP response headers dict
            
        Returns:
            True if content length is acceptable, False if too large
        """
        content_length = headers.get('Content-Length')
        
        if content_length:
            try:
                size = int(content_length)
                if size > ResourceLimiter.MAX_CONTENT_LENGTH:
                    logger.warning(f"Content-Length {size:,} bytes exceeds limit of {ResourceLimiter.MAX_CONTENT_LENGTH:,}")
                    return False
                logger.debug(f"Content-Length: {size:,} bytes (within limit)")
            except ValueError:
                logger.warning(f"Invalid Content-Length header: {content_length}")
        
        return True
    
    @staticmethod
    async def read_limited(response, max_size: int = None) -> bytes:
        """
        Read response with size limit to prevent memory exhaustion.
        
        Args:
            response: aiohttp response object
            max_size: Maximum bytes to read (default: MAX_RESPONSE_SIZE)
            
        Returns:
            Response content as bytes
            
        Raises:
            ValueError: If response exceeds size limit
        """
        if max_size is None:
            max_size = ResourceLimiter.MAX_RESPONSE_SIZE
        
        chunks = []
        total_size = 0
        
        async for chunk in response.content.iter_chunked(ResourceLimiter.MAX_CHUNK_SIZE):
            total_size += len(chunk)
            
            if total_size > max_size:
                logger.warning(f"Response exceeded {max_size:,} bytes limit (got {total_size:,})")
                raise ValueError(f"Response too large (>{max_size:,} bytes)")
            
            chunks.append(chunk)
        
        logger.debug(f"Read {total_size:,} bytes from response")
        return b''.join(chunks)
    
    @staticmethod
    def limit_results(results: list, max_count: int = None) -> list:
        """
        Limit number of results to prevent excessive memory usage.
        
        Args:
            results: List of results
            max_count: Maximum number of results to return
            
        Returns:
            Truncated list
        """
        if max_count is None:
            max_count = ResourceLimiter.MAX_RESULTS_TOTAL
        
        if len(results) > max_count:
            logger.warning(f"Limiting results from {len(results)} to {max_count}")
            return results[:max_count]
        
        return results
