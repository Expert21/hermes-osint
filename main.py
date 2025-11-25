import argparse
import sys
import asyncio
import logging
from src.core.logger import setup_logger
from src.core.config import load_config
from src.core.config_manager import ConfigManager
from src.core.progress_tracker import get_progress_tracker
from src.core.deduplication import deduplicate_and_correlate
from src.core.async_request_manager import AsyncRequestManager

# Async Module Imports
from src.modules.search_engines import run_search_engines_async
from src.modules.social_media import run_social_media_checks_async
from src.modules.email_enumeration import run_email_enumeration_async
from src.modules.profile_verification import enhanced_social_media_check_with_verification_async
from src.reporting.generator import generate_report

# Priority 2 & 3 imports (Keep sync for now if not critical, or refactor later)
from src.modules.username_generator import generate_username_variations
from src.core.cache_manager import get_cache_manager
from src.modules.domain_enum import run_domain_enumeration # Assuming this is still sync for now
from src.core.interactive import run_interactive_mode

async def main_async():
    parser = argparse.ArgumentParser(
        description="OSINT Tool - Social Media & Web Search with Verification (v1.3.2)",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Required arguments
    parser.add_argument("--target", help="Target name (individual or company)")
    parser.add_argument("--type", choices=["individual", "company"], help="Type of target")
    parser.add_argument("--output", default="report.json", help="Output report file")
    
    # Configuration arguments
    parser.add_argument("--config", help="Configuration profile to use")
    parser.add_argument("--list-profiles", action="store_true", help="List available configuration profiles")
    parser.add_argument("--create-profiles", action="store_true", help="Create default configuration profiles")
    
    # Email Enumeration arguments
    parser.add_argument("--email-enum", action="store_true", help="Enable email enumeration")
    parser.add_argument("--domain", help="Primary domain for email enumeration")
    parser.add_argument("--domains", nargs="+", help="Additional domains for email enumeration")
    
    # Verification arguments
    parser.add_argument("--company", help="Company name for verification context")
    parser.add_argument("--location", help="Location for verification context")
    parser.add_argument("--email", help="Known email for verification context")
    
    # Optional flags
    parser.add_argument("--passive", action="store_true", help="Enable passive mode (stealth mode - no direct target contact)")
    parser.add_argument("--no-verify", action="store_true", help="Skip profile verification (faster)")
    parser.add_argument("--skip-search", action="store_true", help="Skip search engines")
    parser.add_argument("--skip-social", action="store_true", help="Skip social media")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress indicators")
    parser.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    parser.add_argument("--js-render", action="store_true", help="Enable JavaScript rendering (requires Playwright)")
    
    # Priority 2: Username Variations
    parser.add_argument("--username-variations", action="store_true", help="Try username variations on social media")
    parser.add_argument("--include-leet", action="store_true", help="Include leet speak variations")
    parser.add_argument("--include-suffixes", action="store_true", help="Include number suffixes")
    
    # Priority 2: Cache Management
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached results")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    
    # Priority 3: Interactive Mode & Domain Enumeration
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive wizard mode")
    parser.add_argument("--domain-enum", action="store_true", help="Run domain/subdomain enumeration")
    
    # Proxy Configuration
    parser.add_argument("--proxies", help="Path to proxy list file")
    parser.add_argument("--fetch-proxies", action="store_true", help="Fetch free proxies and save to file")
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger()
    
    # Handle interactive mode
    if args.interactive:
        wizard_config = run_interactive_mode()
        if not wizard_config:
            return 0
        for key, value in wizard_config.items():
            setattr(args, key, value)
    
    # Handle configuration profile commands
    config_manager = ConfigManager()
    
    if args.create_profiles:
        config_manager.create_default_profile()
        config_manager.create_quick_scan_profile()
        config_manager.create_deep_scan_profile()
        logger.info("✓ Configuration profiles created successfully")
        return 0
        
    if args.list_profiles:
        profiles = config_manager.list_profiles()
        logger.info("Available configuration profiles:")
        for profile in profiles:
            logger.info(f"  - {profile}")
        return 0
    
    # Handle cache management
    if args.clear_cache:
        cache = get_cache_manager()
        cache.clear_all()
        logger.info("✓ Cache cleared")
        return 0
    
    if args.cache_stats:
        cache = get_cache_manager()
        stats = cache.get_stats()
        logger.info("Cache Statistics:")
        logger.info(f"  Total Entries: {stats['total_entries']}")
        return 0
    
    # Validate required arguments (unless fetching proxies)
    if args.fetch_proxies:
        # Just fetch proxies and exit
        logger.info("Fetching free proxies...")
        manager = AsyncRequestManager(proxy_file=args.proxies or "proxies.txt", auto_fetch_proxies=True)
        await manager.fetch_free_proxies()
        await manager.close()
        return 0

    if not args.target or not args.type:
        parser.error("the following arguments are required: --target, --type")
        
    # Load configuration
    if args.config:
        config_dict = config_manager.load_config(args.config)
    else:
        config_dict = config_manager.load_config('default')
    
    logger.info("=" * 60)
    logger.info(f"Starting ASYNC OSINT scan for target: {args.target} ({args.type})")
    logger.info("=" * 60)
    
    results = {
        "target": args.target,
        "target_type": args.type,
        "search_engines": [],
        "social_media": [],
        "emails": [],
        "domain_data": {}
    }
    
    # Initialize Async Request Manager with Proxy Config
    proxy_file = args.proxies or config_dict.get('proxy', {}).get('file', 'proxies.txt')
    auto_fetch = config_dict.get('proxy', {}).get('auto_fetch', False)
    
    request_manager = AsyncRequestManager(proxy_file=proxy_file, auto_fetch_proxies=auto_fetch)
    
    try:
        tasks = []
        
        # 1. Domain Enumeration (Sync for now, run in executor if needed, or keep sync if fast)
        if args.domain_enum or (args.type == 'company' and config_dict.get('features', {}).get('domain_enum', False)):
            logger.info("[Domain Enumeration] Running domain analysis...")
            domain = args.domain if args.domain else args.target
            try:
                # Running sync function directly for now as it's not refactored yet
                domain_results = run_domain_enumeration(domain, bruteforce=False)
                results['domain_data'] = domain_results
                logger.info(f"✓ Found {domain_results['subdomain_count']} subdomains")
            except Exception as e:
                logger.error(f"Domain enumeration failed: {e}")

        # 2. Email Enumeration (Async)
        if args.email_enum and config_dict.get('features', {}).get('email_enumeration', True):
            logger.info("[Email Enumeration] Generating potential email addresses...")
            email_task = asyncio.create_task(run_email_enumeration_async(
                target_name=args.target,
                domain=args.domain,
                custom_domains=args.domains,
                verify_mx=not args.passive,  # Skip MX verification in passive mode
                passive_only=args.passive
            ))
            tasks.append(("email", email_task))

        # 3. Search Engines (Async)
        if not args.skip_search:
            logger.info("[Search Engines] Queuing search engine modules...")
            search_task = asyncio.create_task(run_search_engines_async(args.target, config_dict, js_render=args.js_render))
            tasks.append(("search", search_task))

        # 4. Social Media (Async)
        if not args.skip_social:
            logger.info("[Social Media] Queuing social media modules...")
            
            target_names = [args.target]
            if args.username_variations:
                variations = generate_username_variations(args.target, include_leet=args.include_leet, include_suffixes=args.include_suffixes)
                target_names.extend(variations[:10])
            
            # In passive mode, use passive-only checks (no direct platform contact)
            if args.passive or args.no_verify:
                # Just check existence (passive dorking in passive mode)
                for name in target_names:
                    social_task = asyncio.create_task(run_social_media_checks_async(
                        name, args.type, config_dict, passive_only=args.passive
                    ))
                    tasks.append(("social", social_task))
            else:
                # Check and Verify
                additional_info = {}
                if args.company: additional_info["company"] = args.company
                if args.location: additional_info["location"] = args.location
                if args.email: additional_info["email"] = args.email
                
                verify_task = asyncio.create_task(enhanced_social_media_check_with_verification_async(
                    target=args.target,
                    target_type=args.type,
                    config=config_dict,
                    additional_info=additional_info
                ))
                tasks.append(("social_verify", verify_task))

        # Wait for all async tasks to complete
        if tasks:
            logger.info(f"Executing {len(tasks)} async task groups...")
            await asyncio.gather(*[t[1] for t in tasks])
            
            # Collect results
            for task_type, task in tasks:
                try:
                    res = task.result()
                    if task_type == "email":
                        results['emails'] = res
                    elif task_type == "search":
                        results['search_engines'] = res
                    elif task_type == "social":
                        results['social_media'].extend(res)
                    elif task_type == "social_verify":
                        results['social_media'] = res
                except Exception as e:
                    logger.error(f"Task {task_type} failed: {e}")

    finally:
        # Cleanup
        await request_manager.close()

    # Deduplication (Sync)
    if not args.no_dedup and config_dict.get('features', {}).get('deduplication', True):
        logger.info("\n[Deduplication] Processing results...")
        try:
            processed = deduplicate_and_correlate(
                search_results=results.get('search_engines', []),
                social_results=results.get('social_media', [])
            )
            results['search_engines'] = processed.get('search_engines', [])
            results['social_media'] = processed.get('social_media', [])
            results['connections'] = processed.get('connections', [])
            results['statistics'] = processed.get('statistics', {})
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")

    # Generate Report (Sync)
    logger.info("\n" + "=" * 60)
    logger.info(f"Generating report to {args.output}...")
    try:
        generate_report(results, args.output)
        logger.info("✓ Report saved successfully")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return 1
        
    return 0

def main():
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
        return 1
    except Exception as e:
        print(f"\nFatal error: {e}")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())