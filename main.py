# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

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
from src.core.proxy_manager import ProxyManager
from src.core.secrets_manager import SecretsManager
from src.core.task_manager import TaskManager, TaskPriority
from src.core.resource_limiter import ResourceLimiter

# Async Module Imports
from src.modules.social_media import run_social_media_checks_async
from src.modules.email_enumeration import run_email_enumeration_async
from src.reporting.generator import generate_report
from src.core.input_validator import InputValidator

# Priority 2 & 3 imports
from src.modules.username_generator import generate_username_variations
from src.core.cache_manager import get_cache_manager
from src.core.interactive import run_interactive_mode

async def main_async():
    parser = argparse.ArgumentParser(
        description="OSINT Tool - Social Media & Email Enumeration (v2.0 Alpha)",
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
    parser.add_argument("--skip-social", action="store_true", help="Skip social media")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress indicators")
    parser.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent workers (default: 10)")
    
    # Priority 2: Username Variations
    parser.add_argument("--username-variations", action="store_true", help="Try username variations on social media")
    parser.add_argument("--include-leet", action="store_true", help="Include leet speak variations")
    parser.add_argument("--include-suffixes", action="store_true", help="Include number suffixes")
    
    # Priority 2: Cache Management
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached results")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    
    # Priority 3: Interactive Mode
    parser.add_argument("--interactive", "-i", action="store_true", help="Run in interactive wizard mode")
    
    # Proxy Configuration
    parser.add_argument("--proxies", help="Path to proxy list file")
    parser.add_argument("--fetch-proxies", action="store_true", help="Fetch free proxies and save to file")

    # Phase 3: Modes & UX
    parser.add_argument("--mode", choices=["native", "docker", "hybrid"], default="native", help="Execution mode")
    parser.add_argument("--tool", choices=["sherlock", "theharvester", "holehe", "phoneinfoga", "subfinder", "searxng", "photon", "exiftool"], help="Specific tool to run")
    parser.add_argument("--doctor", action="store_true", help="Run system diagnostics")
    parser.add_argument("--pull-images", action="store_true", help="Pull all required Docker images")

    # Environment Management
    parser.add_argument("--import-env", action="store_true", help="Import .env file values into secure encrypted storage")
    
    args = parser.parse_args()
    
    # Setup logger with Rich
    from rich.logging import RichHandler
    logging.basicConfig(
        level="INFO",
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )
    logger = logging.getLogger("hermes")
    
    # Handle Doctor
    if args.doctor:
        from src.core.doctor import HermesDoctor
        doc = HermesDoctor()
        doc.run_diagnostics()
        doc.print_report()
        return 0

    # Handle Pull Images
    if args.pull_images:
        from src.orchestration.docker_manager import DockerManager
        logger.info("Pulling Docker images...")
        dm = DockerManager()
        if not dm.is_available:
            logger.error("Docker is not available.")
            return 1
        for image in dm.TRUSTED_IMAGES:
            dm.pull_image(image)
        logger.info("All images pulled successfully.")
        return 0

    # Handle interactive mode
    if args.interactive:
        wizard_config = run_interactive_mode()
        if not wizard_config:
            return 0
        for key, value in wizard_config.items():
            setattr(args, key, value)
    
    # Handle configuration profile commands
    config_manager = ConfigManager()
    
    # Initialize proxy manager from environment variables
    secrets_manager = SecretsManager()
    proxy_manager = ProxyManager.load_from_env(secrets_manager)
    if proxy_manager.providers:
        logger.info(f"Loaded {len(proxy_manager.providers)} proxy provider(s)")
        await proxy_manager.initialize()
    
    # Handle environment import
    if args.import_env:
        logger.info("Importing .env file into secure storage...")
        secrets_manager.import_from_env_file('.env')
        logger.info("✓ Environment variables imported successfully")
        logger.info("You can now run hermes commands with encrypted credentials")
        return 0
    
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
    
    # Validate required arguments
    if args.tool:
        # Tool execution mode (Single tool)
        logger.info(f"Starting execution for {args.tool} in {args.mode} mode...")
        
        from src.orchestration.execution_strategy import DockerExecutionStrategy, NativeExecutionStrategy, HybridExecutionStrategy
        from src.orchestration.docker_manager import DockerManager
        
        # Initialize Strategy
        strategy = None
        if args.mode == "docker":
            strategy = DockerExecutionStrategy(DockerManager())
        elif args.mode == "native":
            strategy = NativeExecutionStrategy()
        elif args.mode == "hybrid":
            strategy = HybridExecutionStrategy(DockerExecutionStrategy(DockerManager()), NativeExecutionStrategy())
            
        try:
            # We need to map tool names to adapters or just run raw commands?
            # The original code used adapters. Let's stick to adapters but inject the strategy.
            # For now, only Sherlock adapter is updated.
            
            if args.tool == "sherlock":
                from src.orchestration.adapters.sherlock_adapter import SherlockAdapter
                adapter = SherlockAdapter(strategy)
                results = adapter.execute(args.target, {})
                logger.info(f"Results: {results}")
                return 0
            else:
                logger.warning(f"Adapter for {args.tool} not yet updated for new strategy. Running legacy Docker mode if available.")
                # Fallback to legacy logic if needed, or just fail for now as we are in dev
                return 1

        except Exception as e:
            logger.error(f"Execution failed: {e}")
            return 1

    if not args.target or not args.type:
        parser.error("the following arguments are required: --target, --type")
    try:
        args.target = InputValidator.validate_target_name(args.target)
    except ValueError as e:
        parser.error(str(e))
        
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
        "social_media": [],
        "emails": []
    }
    
    
    # Initialize Async Request Manager with Proxy Manager
    request_manager = AsyncRequestManager(proxy_manager=proxy_manager)
    
    # Auto-detect resources
    ResourceLimiter.auto_detect_resources()
    
    # Initialize TaskManager
    task_manager = TaskManager(max_workers=args.workers)
    await task_manager.start()
    
    try:
        tasks = []
        
        # 1. Email Enumeration (Async)
        if args.email_enum and config_dict.get('features', {}).get('email_enumeration', True):
            logger.info("[Email Enumeration] Generating potential email addresses...")
            email_future = await task_manager.submit(run_email_enumeration_async(
                target_name=args.target,
                domain=args.domain,
                custom_domains=args.domains,
                verify_mx=not args.passive,  # Skip MX verification in passive mode
                passive_only=args.passive
            ), priority=TaskPriority.NORMAL)
            tasks.append(("email", email_future))

        # 2. Social Media (Async)
        if not args.skip_social:
            logger.info("[Social Media] Queuing social media modules...")
            
            target_names = [args.target]
            if args.username_variations:
                variations = generate_username_variations(args.target, include_leet=args.include_leet, include_suffixes=args.include_suffixes)
                target_names.extend(variations[:10])
            
            # Run social media checks for all username variations
            for name in target_names:
                social_future = await task_manager.submit(run_social_media_checks_async(
                    name, args.type, config_dict, passive_only=args.passive
                ), priority=TaskPriority.LOW)
                tasks.append(("social", social_future))

        # Wait for all async tasks to complete
        if tasks:
            logger.info(f"Executing {len(tasks)} async task groups...")
            from rich.progress import Progress
            with Progress() as progress:
                task_id = progress.add_task("[cyan]Scanning...", total=len(tasks))
                
                # We need to await tasks but also update progress.
                # Since we used gather, we can't easily update progress per task completion without as_completed
                # For now, let's just await all.
                await asyncio.gather(*[t[1] for t in tasks])
                progress.update(task_id, completed=len(tasks))
            
            # Collect results
            for task_type, task in tasks:
                try:
                    res = task.result()
                    if task_type == "email":
                        results['emails'] = res
                    elif task_type == "social":
                        results['social_media'].extend(res)
                except Exception as e:
                    logger.error(f"Task {task_type} failed: {e}")

    finally:
        # Cleanup
        await task_manager.stop()
        await request_manager.close()

    # Deduplication (Sync)
    if not args.no_dedup and config_dict.get('features', {}).get('deduplication', True):
        logger.info("\n[Deduplication] Processing results...")
        try:
            processed = deduplicate_and_correlate(
                search_results=[],  # No search results anymore
                social_results=results.get('social_media', [])
            )
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
