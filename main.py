import argparse
import sys
from src.core.logger import setup_logger
from src.core.config import load_config
from src.core.config_manager import ConfigManager
from src.core.progress_tracker import get_progress_tracker
from src.core.deduplication import deduplicate_and_correlate
from src.modules.search_engines import run_search_engines
from src.modules.social_media import run_social_media_checks
from src.modules.email_enumeration import run_email_enumeration
from src.reporting.generator import generate_report
from src.modules.profile_verification import enhanced_social_media_check_with_verification

# Priority 2 & 3 imports
from src.modules.username_generator import generate_username_variations
from src.core.cache_manager import get_cache_manager
from src.modules.domain_enum import run_domain_enumeration
from src.core.interactive import run_interactive_mode

def main():
    parser = argparse.ArgumentParser(
        description="OSINT Tool - Social Media & Web Search with Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  python main.py --target "johndoe" --type individual
  
  # Interactive mode
  python main.py --interactive
  
  # With email enumeration
  python main.py --target "John Doe" --type individual --email-enum --domain company.com
  
  # With username variations
  python main.py --target "johndoe" --type individual --username-variations --include-leet
  
  # Domain enumeration
  python main.py --target "example.com" --type company --domain-enum
  
  # List or create profiles
  python main.py --list-profiles
  python main.py --create-profiles
        """
    )
    
    # Required arguments (but not for utility commands)
    parser.add_argument("--target", help="Target name (individual or company)")
    parser.add_argument("--type", choices=["individual", "company"], help="Type of target")
    parser.add_argument("--output", default="report.json", help="Output report file")
    
    # Configuration arguments
    parser.add_argument("--config", help="Configuration profile to use (e.g., default, quick_scan)")
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
    parser.add_argument("--no-verify", action="store_true", help="Skip profile verification (faster)")
    parser.add_argument("--skip-search", action="store_true", help="Skip search engines")
    parser.add_argument("--skip-social", action="store_true", help="Skip social media")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress indicators")
    parser.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    parser.add_argument("--js-render", action="store_true", help="Enable JavaScript rendering (requires Playwright)")
    
    # Priority 2: Username Variations
    parser.add_argument("--username-variations", action="store_true", help="Try username variations on social media")
    parser.add_argument("--include-leet", action="store_true", help="Include leet speak variations (e.g., j0hnd0e)")
    parser.add_argument("--include-suffixes", action="store_true", help="Include number suffixes (e.g., johndoe123)")
    
    # Priority 2: Cache Management
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached results")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    
    # Priority 3: Interactive Mode & Domain Enumeration
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive wizard mode")
    parser.add_argument("--domain-enum", action="store_true", help="Run domain/subdomain enumeration")
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger()
    
    # Handle interactive mode first (it will gather all args)
    if args.interactive:
        wizard_config = run_interactive_mode()
        if not wizard_config:
            return 0
        # Map wizard config to args namespace
        for key, value in wizard_config.items():
            setattr(args, key, value)
    
    # Handle configuration profile commands (these don't require target/type)
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
    
    # Handle cache management commands
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
        logger.info(f"  Valid Entries: {stats['valid_entries']}")
        logger.info(f"  Expired Entries: {stats['expired_entries']}")
        logger.info(f"  Database Size: {stats['database_size_mb']} MB")
        return 0
    
    # Validate required arguments for scan
    if not args.target or not args.type:
        parser.error("the following arguments are required: --target, --type")
        
    # Load configuration
    if args.config:
        config_dict = config_manager.load_config(args.config)
    else:
        config_dict = config_manager.load_config('default')
    
    # Initialize progress tracker
    use_progress = not args.no_progress and config_dict.get('features', {}).get('progress_indicators', True)
    progress_tracker = get_progress_tracker(use_tqdm=use_progress)
    
    logger.info("=" * 60)
    logger.info(f"Starting OSINT scan for target: {args.target} ({args.type})")
    if args.config:
        logger.info(f"Using configuration profile: {args.config}")
    
    if not args.js_render:
        logger.info("JavaScript Rendering disabled, use --js-render to enable (Requires Playwright)")
    else:
        logger.info("JavaScript Rendering enabled (using Playwright)")
        
    logger.info("=" * 60)
    
    results = {
        "target": args.target,
        "target_type": args.type,
        "search_engines": [],
        "social_media": [],
        "emails": [],
        "domain_data": {}
    }
    
    # Run Domain Enumeration (Priority 3)
    if args.domain_enum or (args.type == 'company' and config_dict.get('features', {}).get('domain_enum', False)):
        logger.info("\n[Domain Enumeration] Running domain analysis...")
        logger.info("-" * 60)
        domain = args.domain if args.domain else args.target
        try:
            domain_results = run_domain_enumeration(domain, bruteforce=False)
            results['domain_data'] = domain_results
            logger.info(f"✓ Found {domain_results['subdomain_count']} subdomains")
            logger.info(f"✓ Retrieved {len(domain_results['dns_records'])} DNS record types")
        except Exception as e:
            logger.error(f"Domain enumeration failed: {e}")
    
    # Run Email Enumeration (if enabled)
    if args.email_enum and config_dict.get('features', {}).get('email_enumeration', True):
        logger.info("\n[Email Enumeration] Generating potential email addresses...")
        logger.info("-" * 60)
        try:
            email_results = run_email_enumeration(
                target_name=args.target,
                domain=args.domain,
                custom_domains=args.domains,
                verify_mx=True
            )
            results['emails'] = email_results
            logger.info(f"✓ Generated {email_results.get('valid_format_count', 0)} potential email addresses")
        except Exception as e:
            logger.error(f"Email enumeration failed: {e}")
            results['emails'] = []
    
    # Run Search Engines
    if not args.skip_search:
        logger.info("\n[Search Engines] Running search engine modules...")
        logger.info("-" * 60)
        try:
            results['search_engines'] = run_search_engines(args.target, config_dict, js_render=args.js_render)
        except Exception as e:
            logger.error(f"Search engine module failed: {e}")
            results['search_engines'] = []
    
    # Run Social Media Checks (with optional username variations)
    if not args.skip_social:
        logger.info("\n[Social Media] Running social media modules...")
        logger.info("-" * 60)
        
        # Generate username variations if requested (Priority 2)
        target_names = [args.target]
        if args.username_variations:
            try:
                variations = generate_username_variations(
                    args.target,
                    include_leet=args.include_leet,
                    include_suffixes=args.include_suffixes,
                    max_variations=20
                )
                target_names.extend(variations[:10])  # Limit to avoid excessive requests
                logger.info(f"Generated {len(variations)} username variations, checking top 10...")
            except Exception as e:
                logger.error(f"Username variation generation failed: {e}")
        
        try:
            if args.no_verify:
                logger.info("Verification disabled (--no-verify)")
                # Check all target name variations
                all_social_results = []
                for name in target_names:
                    social_results = run_social_media_checks(name, args.type, config_dict)
                    all_social_results.extend(social_results)
                results['social_media'] = all_social_results
            else:
                additional_info = {}
                if args.company:
                    additional_info["company"] = args.company
                if args.location:
                    additional_info["location"] = args.location
                if args.email:
                    additional_info["email"] = args.email
                
                # For username variations with verification, check primary name only
                # (verification is expensive, so we don't do it for all variations)
                results['social_media'] = enhanced_social_media_check_with_verification(
                    target=args.target,
                    target_type=args.type,
                    config=config_dict,
                    additional_info=additional_info if additional_info else None
                )
        except Exception as e:
            logger.error(f"Social media module failed: {e}")
            results['social_media'] = []
    
    # Run Deduplication and Correlation
    if not args.no_dedup and config_dict.get('features', {}).get('deduplication', True):
        logger.info("\n[Deduplication] Processing results...")
        logger.info("-" * 60)
        try:
            processed = deduplicate_and_correlate(
                search_results=results.get('search_engines', []),
                social_results=results.get('social_media', [])
            )
            
            results['search_engines'] = processed.get('search_engines', [])
            results['social_media'] = processed.get('social_media', [])
            results['connections'] = processed.get('connections', [])
            results['statistics'] = processed.get('statistics', {})
            
            logger.info("✓ Deduplication complete")
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")
    
    # Generate Report
    logger.info("\n" + "=" * 60)
    logger.info(f"Generating report to {args.output}...")
    try:
        generate_report(results, args.output)
        logger.info("✓ Report saved successfully")
    except Exception as e:
        logger.error(f"Failed to generate report: {e}")
        return 1
    
    # Print summary
    logger.info("\n" + "=" * 60)
    logger.info("Scan complete.")
    logger.info(f"  Search Results: {len(results.get('search_engines', []))}")
    logger.info(f"  Social Profiles: {len(results.get('social_media', []))}")
    if args.email_enum:
        logger.info(f"  Email Addresses: {results.get('emails', {}).get('valid_format_count', 0)}")
    if args.domain_enum and results.get('domain_data'):
        logger.info(f"  Subdomains Found: {results['domain_data'].get('subdomain_count', 0)}")
    if 'statistics' in results:
        stats = results['statistics']
        logger.info(f"  High Quality Results: {stats.get('high_quality_results', 0)}")
        logger.info(f"  Avg Quality Score: {stats.get('avg_quality_score', 0):.1f}/100")
        logger.info(f"  Connections Found: {stats.get('connections_found', 0)}")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())