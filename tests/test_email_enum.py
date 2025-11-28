import asyncio
import logging
from src.modules.email_enumeration import run_email_enumeration_async

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_email_enum():
    print("Testing Email Enumeration Refactor...")
    
    # Test 1: Passive Mode (Should only return "Possible" or "Confirmed" from PGP/HIBP)
    print("\n--- Test 1: Passive Mode (Linus Torvalds) ---")
    results = await run_email_enumeration_async(
        target_name="Linus Torvalds",
        domain="linux-foundation.org",
        passive_only=True
    )
    
    print(f"Confirmed Emails: {len(results['confirmed_emails'])}")
    for email in results['confirmed_emails']:
        print(f"  - {email['email']} (Source: {email['source']}, Conf: {email['confidence']})")
        
    print(f"Possible Emails: {len(results['possible_emails'])}")
    # Just print first 3 possible to avoid spam
    for email in results['possible_emails'][:3]:
        print(f"  - {email['email']} (Source: {email['source']}, Conf: {email['confidence']})")

    # Test 2: Active Mode (Should check MX)
    print("\n--- Test 2: Active Mode (John Doe - gmail.com) ---")
    results_active = await run_email_enumeration_async(
        target_name="John Doe",
        domain="gmail.com",
        verify_mx=True,
        passive_only=False
    )
    
    print(f"Domains with MX: {results_active['domains_with_mx']}")
    print(f"Possible Emails (MX Verified): {len(results_active['possible_emails'])}")

if __name__ == "__main__":
    asyncio.run(test_email_enum())
