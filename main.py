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

def main():
    parser = argparse.ArgumentParser(
        description="OSINT Tool - Social Media & Web Search with Verification",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic scan
  python main.py --target "johndoe" --type individual
  
  # Use configuration profile
  python main.py --target "johndoe" --type individual --config quick_scan
  
  # With email enumeration
  python main.py --target "John Doe" --type individual --email-enum --domain company.com
  
  # List or create profiles
  python main.py --list-profiles
  python main.py --create-profiles
        """
    )
    
    # Required arguments (but not for utility commands)
    parser.add_argument("--target", help="Target name (individual or company)")
    parser.add_argument("--type", choices=["individual", "company"], help="Type of target")
    parser.add_argument("--output", default="report.json", help="Output report file (.json or .csv)")
    
    # Optional flags
    parser.add_argument("--no-verify", action="store_true", help="Skip profile verification (faster)")
    parser.add_argument("--skip-search", action="store_true", help="Skip search engines")
    parser.add_argument("--skip-social", action="store_true", help="Skip social media")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress indicators")
    parser.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    
    # Configuration
    parser.add_argument("--config", help="Configuration profile name (e.g., 'quick_scan', 'deep_scan')")
    parser.add_argument("--list-profiles", action="store_true", help="List available configuration profiles")
    parser.add_argument("--create-profiles", action="store_true", help="Create default configuration profiles")
    
    # Email enumeration
    parser.add_argument("--email-enum", action="store_true", help="Enable email enumeration")
    parser.add_argument("--domain", help="Domain for email enumeration (e.g., company.com)")
    parser.add_argument("--domains", nargs="+", help="Multiple domains for email enumeration")
    
    # Verification helpers
    parser.add_argument("--company", help="Target's company (helps verification)")
    parser.add_argument("--location", help="Target's location (helps verification)")
    parser.add_argument("--email", help="Known email (helps verification)")
    
    args = parser.parse_args()
    
    # Setup logger
    logger = setup_logger()
    
    # Handle configuration profile commands (these don't require target/type)
    config_manager = ConfigManager()
    
    if args.list_profiles:
        profiles = config_manager.list_profiles()
        logger.info("Available configuration profiles:")
        for profile in profiles:
            logger.info(f"  - {profile}")
        return 0
    
    if args.create_profiles:
        logger.info("Creating default configuration profiles...")
        config_manager.create_default_profile()
        config_manager.create_quick_scan_profile()
        config_manager.create_deep_scan_profile()
        logger.info("✓ Created profiles: default, quick_scan, deep_scan")
        return 0
    
    # Validate required arguments for scan operations
    if not args.target or not args.type:
        parser.error("--target and --type are required for scan operations")
    
    # Load configuration
    if args.config:
        config_dict = config_manager.load_config(args.config)
    else:
        config_dict = config_manager.load_config('default')
    
    config = load_config()  # Load env vars
    
    # Initialize progress tracker
    use_progress = not args.no_progress and config_dict.get('features', {}).get('progress_indicators', True)
    progress_tracker = get_progress_tracker(use_tqdm=use_progress)
    
    logger.info("=" * 60)
    logger.info(f"Starting OSINT scan for target: {args.target} ({args.type})")
    if args.config:
        logger.info(f"Using configuration profile: {args.config}")
    logger.info("=" * 60)
    
    results = {
        "target": args.target,
        "target_type": args.type,
        "search_engines": [],
        "social_media": [],
        "emails": []
    }
    
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
            results['search_engines'] = run_search_engines(args.target, config_dict)
        except Exception as e:
            logger.error(f"Search engine module failed: {e}")
            results['search_engines'] = []
    
    # Run Social Media Checks
    if not args.skip_social:
        logger.info("\n[Social Media] Running social media modules...")
        logger.info("-" * 60)
        
        try:
            if args.no_verify:
                logger.info("Verification disabled (--no-verify)")
                results['social_media'] = run_social_media_checks(args.target, args.type, config_dict)
            else:
                additional_info = {}
                if args.company:
                    additional_info["company"] = args.company
                if args.location:
                    additional_info["location"] = args.location
                if args.email:
                    additional_info["email"] = args.email
                
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
    if 'statistics' in results:
        stats = results['statistics']
        logger.info(f"  High Quality Results: {stats.get('high_quality_results', 0)}")
        logger.info(f"  Avg Quality Score: {stats.get('avg_quality_score', 0):.1f}/100")
        logger.info(f"  Connections Found: {stats.get('connections_found', 0)}")
    logger.info("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())