
import pytest
from unittest.mock import patch, MagicMock
from src.core.resource_limiter import ResourceLimiter

def test_auto_detect_resources_high_spec():
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value.total = 16 * 1024**3  # 16 GB
        
        ResourceLimiter.auto_detect_resources()
        
        assert ResourceLimiter.MAX_RESPONSE_SIZE == 50 * 1024 * 1024
        assert ResourceLimiter.MAX_RESULTS_TOTAL == 5000

def test_auto_detect_resources_mid_spec():
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value.total = 8 * 1024**3  # 8 GB
        
        ResourceLimiter.auto_detect_resources()
        
        assert ResourceLimiter.MAX_RESPONSE_SIZE == 20 * 1024 * 1024
        assert ResourceLimiter.MAX_RESULTS_TOTAL == 2000

def test_auto_detect_resources_low_spec():
    with patch('psutil.virtual_memory') as mock_mem:
        mock_mem.return_value.total = 4 * 1024**3  # 4 GB
        
        # Reset to defaults first just in case
        ResourceLimiter.MAX_RESPONSE_SIZE = 10 * 1024 * 1024
        ResourceLimiter.MAX_RESULTS_TOTAL = 1000
        
        ResourceLimiter.auto_detect_resources()
        
        assert ResourceLimiter.MAX_RESPONSE_SIZE == 10 * 1024 * 1024
        assert ResourceLimiter.MAX_RESULTS_TOTAL == 1000
