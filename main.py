import argparse
import sys
from src.core.logger import setup_logger
from src.core.config import load_config
from src.modules.search_engines import run_search_engines
from src.modules.social_media import run_social_media_checks
from src.reporting.generator import generate_report
from src.modules.verification import enhanced_social_media_check_with_verification

def main():
    parser = argparse.ArgumentParser(description="OSINT Tool - Social Media & Web Search")
    parser.add_argument("--target", required=True, help="Target name (individual or company)")
    parser.add_argument("--type", choices=["individual", "company"], required=True, help="Type of target")
    parser.add_argument("--output", default="report.json", help="Output report file")
    
    args = parser.parse_args()
    
    logger = setup_logger()
    config = load_config()
    
    logger.info(f"Starting OSINT scan for target: {args.target} ({args.type})")
    
    results = {}
    
    # Run Search Engines
    logger.info("Running search engine modules...")
    results['search_engines'] = run_search_engines(args.target, config)
    
    # Run Social Media Checks
    results['social_media'] = enhanced_social_media_check_with_verification(
        target=args.target,
        target_type=args.type,
        config=config,
        additional_info={
            "company": "Optional Company Name",
            "location": "Optional Location",
        # Add any other known info about target
        }
    )
    # Generate Report
    logger.info(f"Generating report to {args.output}...")
    generate_report(results, args.output)
    
    logger.info("Scan complete.")

if __name__ == "__main__":
    main()
