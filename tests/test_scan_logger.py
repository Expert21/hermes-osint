"""
Test scan logger functionality.
"""
import asyncio
import logging
import os
from src.core.scan_logger import ScanLogger, EventType

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_scan_logger():
    print("Testing Scan Logger...")
    
    # Create scan logger
    scan_logger = ScanLogger(output_format="json")
    
    # Log scan start
    scan_logger.log_event(
        EventType.SCAN_START,
        "test",
        "Starting test scan",
        {"target": "test@example.com"}
    )
    
    # Log some test events
    print("\n--- Testing Logger Events ---")
    scan_logger.log_event(
        EventType.MODULE_START,
        "social_media",
        "Checking social media profiles",
        {"platforms": ["GitHub", "Twitter", "Instagram"]}
    )
    
    scan_logger.log_event(
        EventType.RESULT_FOUND,
        "social_media",
        "Found GitHub profile",
        {"url": "https://github.com/testuser"}
    )
    
    # Log scan end
    scan_logger.log_event(
        EventType.SCAN_END,
        "test",
        "Test scan complete",
        {}
    )
    
    # Print summary
    scan_logger.print_summary()
    
    # Save log
    os.makedirs("tests/outputs", exist_ok=True)
    scan_logger.save_log("tests/outputs/test_scan_log.json")
    
    print("\n✓ Scan logger test complete")

if __name__ == "__main__":
    asyncio.run(test_scan_logger())
