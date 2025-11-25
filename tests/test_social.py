import asyncio
import logging
from src.modules.social_media import run_social_media_checks_async

# Setup logging
logging.basicConfig(level=logging.INFO)

async def test_social():
    print("Testing Social Media Refactor...")
    
    # Test 1: Passive Mode (Should only use dorks)
    print("\n--- Test 1: Passive Mode (google) ---")
    results = await run_social_media_checks_async(
        target="google",
        target_type="company",
        config={},
        passive_only=True
    )
    
    print(f"Found {len(results)} profiles (Passive):")
    for res in results:
        print(f"  - [{res['platform']}] {res['url']} (Source: {res['source']})")

    # Test 2: Active Mode (Should use dorks + direct checks)
    # We'll use a target that might not be found via dorks easily to trigger active checks
    # or just verify that active checks run.
    print("\n--- Test 2: Active Mode (openai) ---")
    results_active = await run_social_media_checks_async(
        target="openai",
        target_type="company",
        config={},
        passive_only=False
    )
    
    print(f"Found {len(results_active)} profiles (Active):")
    for res in results_active:
        print(f"  - [{res['platform']}] {res['url']} (Source: {res['source']})")

if __name__ == "__main__":
    asyncio.run(test_social())
