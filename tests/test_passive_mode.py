"""
Test script for Passive Mode (Stealth Mode)
Demonstrates complete passive-only OSINT workflow.
"""
import asyncio
import logging
import os
from src.core.scan_logger import ScanLogger, EventType
from src.modules.passive_intelligence import PassiveIntelligenceModule
from src.modules.email_enumeration import run_email_enumeration_async
from src.modules.social_media import run_social_media_checks_async
from src.reporting.html_report import generate_html_report
from src.reporting.markdown_report import generate_markdown_report

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("OSINT_Tool")

async def passive_mode_scan(target: str, target_type: str = "individual", domain: str = None):
    """
    Run a complete OSINT scan in passive mode only.
    No active HTTP requests to the target's infrastructure.
    """
    logger.info("="*60)
    logger.info(f"PASSIVE MODE SCAN: {target} ({target_type})")
    logger.info("="*60)
    
    # Initialize scan logger
    scan_logger = ScanLogger(output_format="json")
    scan_logger.log_event(
        EventType.SCAN_START,
        "passive_mode",
        f"Starting passive scan for {target}",
        {"target": target, "type": target_type}
    )
    
    results = {
        "target": target,
        "target_type": target_type,
        "emails": {},
        "social_media": [],
        "statistics": {}
    }
    
    # Phase 1: Passive Intelligence Gathering
    logger.info("\n[PHASE 1] Passive Intelligence Gathering")
    passive_intel = PassiveIntelligenceModule(scan_logger=scan_logger)
    
    # Email enumeration with passive sources only
    if domain or "@" in target:
        logger.info("  → Email enumeration (passive only)...")
        email_results = await run_email_enumeration_async(
            target_name=target,
            domain=domain,
            verify_mx=False,  # Skip MX checks in passive mode
            passive_only=True
        )
        results["emails"] = email_results
        
        confirmed_count = len(email_results.get("confirmed_emails", []))
        possible_count = len(email_results.get("possible_emails", []))
        logger.info(f"  ✓ Found {confirmed_count} confirmed, {possible_count} possible emails")
    
    # Social media profiling (passive dorking only)
    logger.info("  → Social media discovery (dorks only)...")
    social_results = await run_social_media_checks_async(
        target=target,
        target_type=target_type,
        config={},
        passive_only=True
    )
    results["social_media"] = social_results
    logger.info(f"  ✓ Found {len(social_results)} potential profiles")
    
    # Calculate statistics
    confirmed_count = len(results["emails"].get("confirmed_emails", []))
    possible_email_count = len(results["emails"].get("possible_emails", []))
    social_count = len(results["social_media"])
    
    results["statistics"] = {
        "total_unique": confirmed_count + possible_email_count + social_count,
        "confirmed_count": confirmed_count,
        "possible_count": possible_email_count + social_count
    }
    
    # Log scan completion
    scan_logger.log_event(
        EventType.SCAN_END,
        "passive_mode",
        "Passive scan complete",
        results["statistics"]
    )
    
    # Print summary
    logger.info("\n" + "="*60)
    logger.info("SCAN SUMMARY")
    logger.info("="*60)
    logger.info(f"Total Findings: {results['statistics']['total_unique']}")
    logger.info(f"  - Confirmed: {results['statistics']['confirmed_count']}")
    logger.info(f"  - Possible: {results['statistics']['possible_count']}")
    scan_logger.print_summary()
    
    # Save scan log
    os.makedirs("tests/outputs", exist_ok=True)
    scan_logger.save_log(f"tests/outputs/passive_scan_{target.replace(' ', '_')}.json")
    
    return results

async def main():
    """Main test function"""
    print("\n🔍 Hermes OSINT Tool - Passive Mode Test\n")
    
    # Test 1: Individual with email domain
    print("TEST 1: Individual Target with Domain")
    print("-" * 60)
    results1 = await passive_mode_scan(
        target="Linus Torvalds",
        target_type="individual",
        domain="linux-foundation.org"
    )
    
    # Generate reports
    os.makedirs("tests/outputs", exist_ok=True)
    print("\nGenerating reports...")
    generate_html_report(results1, "tests/outputs/passive_test_individual.html")
    generate_markdown_report(results1, "tests/outputs/passive_test_individual.md")
    print("✓ Reports generated: tests/outputs/passive_test_individual.html/md")
    
    # Test 2: Company target
    print("\n\nTEST 2: Company Target")
    print("-" * 60)
    results2 = await passive_mode_scan(
        target="google",
        target_type="company"
    )
    
    # Generate reports
    generate_html_report(results2, "tests/outputs/passive_test_company.html")
    generate_markdown_report(results2, "tests/outputs/passive_test_company.md")
    print("✓ Reports generated: tests/outputs/passive_test_company.html/md")
    
    print("\n" + "="*60)
    print("✓ PASSIVE MODE TEST COMPLETE")
    print("="*60)
    print("\nKey Benefits of Passive Mode:")
    print("  • Zero risk of detection by target")
    print("  • No rate limiting from target platforms")
    print("  • Fast execution (no direct HTTP requests)")
    print("  • Still provides actionable intelligence\n")

if __name__ == "__main__":
    asyncio.run(main())
