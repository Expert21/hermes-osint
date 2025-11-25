import asyncio
import logging
import os
from src.modules.passive_intelligence import PassiveIntelligenceModule

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_passive():
    print("Initializing Passive Intelligence Module...")
    passive = PassiveIntelligenceModule()
    
    # Test 1: Dorking (No API key needed)
    print("\n--- Testing Dorking for 'johndoe' ---")
    results = await passive.dork_profiles("johndoe")
    print(f"Found {len(results)} profiles:")
    for res in results:
        print(f"  - [{res['platform']}] {res['title']} ({res['url']})")
        
    # Test 2: PGP (No API key needed)
    # Use a known email that likely has a key, e.g., a developer or maintainer
    # We'll use a dummy or common one if possible, or just verify the function runs
    print("\n--- Testing PGP for 'torvalds@linux-foundation.org' ---") 
    pgp_results = await passive.query_pgp_keyservers("torvalds@linux-foundation.org")
    print(f"Found {len(pgp_results)} PGP keys:")
    for key in pgp_results:
        print(f"  - {key['key_id']} ({key['timestamp']})")

    # Test 3: HIBP (Requires API Key)
    api_key = os.getenv("HIBP_API_KEY")
    if api_key:
        print("\n--- Testing HIBP for 'test@example.com' ---")
        breaches = await passive.check_breach_data("test@example.com")
        print(f"Found {len(breaches)} breaches.")
    else:
        print("\n--- Skipping HIBP (No API Key) ---")

if __name__ == "__main__":
    asyncio.run(test_passive())
