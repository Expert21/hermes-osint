"""
Test scan logger functionality with passive intelligence module.
"""
import asyncio
import logging
import os
from src.core.scan_logger import ScanLogger, EventType
from src.modules.passive_intelligence import PassiveIntelligenceModule

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_scan_logger():
    print("Testing Scan Logger Integration...")
    
    # Create scan logger
    scan_logger = ScanLogger(output_format="json")
    
    # Log scan start
    scan_logger.log_event(
        EventType.SCAN_START,
        "test",
        "Starting test scan",
        {"target": "test@example.com"}
    )
    
    # Test with passive intelligence
    print("\n--- Testing Passive Intelligence with Logger ---")
    passive = PassiveIntelligenceModule(scan_logger=scan_logger)
    
    # This should trigger some errors/rate limits depending on API availability
    breach_results = await passive.check_breach_data("test@example.com")
    print(f"Breach results: {len(breach_results)}")
    
    pgp_results = await passive.query_pgp_keyservers("torvalds@linux-foundation.org")
    print(f"PGP results: {len(pgp_results)}")
    
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
