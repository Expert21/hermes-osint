import pytest
import os
import time
try:
    import psutil
except ImportError:
    psutil = None

@pytest.mark.skipif(psutil is None, reason="psutil not installed")
def test_memory_usage():
    """Monitor memory usage during a simulated load."""
    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB
    
    # Simulate load
    data = ["x" * 1024 * 1024 for _ in range(10)] # Allocate 10MB
    
    peak_memory = process.memory_info().rss / 1024 / 1024 # MB
    
    # Cleanup
    del data
    
    final_memory = process.memory_info().rss / 1024 / 1024 # MB
    
    print(f"\nInitial Memory: {initial_memory:.2f} MB")
    print(f"Peak Memory: {peak_memory:.2f} MB")
    print(f"Final Memory: {final_memory:.2f} MB")
    
    # Just a sanity check that we didn't explode
    assert peak_memory > initial_memory
    # We can't strictly assert final memory because of GC behavior, but it shouldn't be huge.

