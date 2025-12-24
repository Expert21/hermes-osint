
import argparse
import sys
import asyncio
import logging
from src.core.logger import setup_logger
from src.core.config import load_config
from src.core.config_manager import ConfigManager
from src.core.progress_tracker import get_progress_tracker
from src.core.deduplication import deduplicate_and_correlate
from src.core.proxy_manager import ProxyManager
from src.core.secrets_manager import SecretsManager
from src.core.task_manager import TaskManager, TaskPriority
from src.core.resource_limiter import ResourceLimiter
from src.orchestration.workflow_manager import WorkflowManager

# Async Module Imports
from src.reporting.generator import generate_report
from src.core.input_validator import InputValidator

# Priority 2 & 3 imports
from src.modules.username_generator import generate_username_variations
from src.core.cache_manager import get_cache_manager

# LLM Analysis (optional)
from src.analysis import LLMAnalyzer


async def main_async():
    parser = argparse.ArgumentParser(
        description="OSINT Tool - Social Media & Email Enumeration (v2.0)",
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
    parser.add_argument("--domain", help="Primary domain for email enumeration")
    parser.add_argument("--domains", nargs="+", help="Additional domains for email enumeration")
    
    # Verification arguments
    parser.add_argument("--company", help="Company name for verification context")
    parser.add_argument("--location", help="Location for verification context")
    parser.add_argument("--email", help="Known email for verification context")
    parser.add_argument("--phone", help="Phone number for PhoneInfoga")
    parser.add_argument("--file", help="File path for Exiftool analysis")
    
    # Optional flags
    parser.add_argument("--stealth", action="store_true", help="Enable stealth mode (no direct target contact)")
    parser.add_argument("--no-progress", action="store_true", help="Disable progress indicators")
    parser.add_argument("--no-dedup", action="store_true", help="Disable deduplication")
    parser.add_argument("--workers", type=int, default=10, help="Number of concurrent workers (default: 10)")
    
    # LLM Analysis
    parser.add_argument("--analyze", action="store_true", help="Enable AI-powered analysis of results (requires Ollama)")
    parser.add_argument("--model", default="llama3.2", help="Ollama model for analysis (default: llama3.2)")
    
    # Priority 2: Username Variations
    parser.add_argument("--variations", action="store_true", help="Try username variations on social media")
    
    # Priority 2: Cache Management
    parser.add_argument("--clear-cache", action="store_true", help="Clear all cached results")
    parser.add_argument("--cache-stats", action="store_true", help="Show cache statistics")
    
    # Setup & Configuration
    parser.add_argument("--setup", action="store_true", help="Run interactive tool setup")
    parser.add_argument("--import-env", action="store_true", help="Import .env file values into secure encrypted storage")

    
    # Proxy Configuration
    parser.add_argument("--proxies", help="Path to proxy list file")
    parser.add_argument("--fetch-proxies", action="store_true", help="Fetch free proxies and save to file")

    # Phase 3: Modes & UX
    parser.add_argument("--mode", choices=["native", "docker", "hybrid"], default="native", help="Execution mode")
    parser.add_argument("--tool", choices=["sherlock", "theharvester", "holehe", "phoneinfoga", "subfinder", "ghunt"], help="Specific tool to run")
    parser.add_argument("--doctor", action="store_true", help="Run system diagnostics")
    parser.add_argument("--pull-images", action="store_true", help="Pull all required Docker images")
    parser.add_argument("--remove-images", action="store_true", help="Remove all trusted Docker images")


    
    # Plugin Management
    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")
    
    plugins_parser = subparsers.add_parser("plugins", help="Manage plugins")
    plugins_subparsers = plugins_parser.add_subparsers(dest="plugin_command", help="Plugin commands")
    
    # plugins list
    plugins_subparsers.add_parser("list", help="List all plugins")
    
    # plugins info <name>
    info_parser = plugins_subparsers.add_parser("info", help="Show plugin details")
    info_parser.add_argument("plugin_name", help="Name of the plugin")
    
    # plugins scan <path>
    scan_parser = plugins_subparsers.add_parser("scan", help="Scan a directory for security issues")
    scan_parser.add_argument("path", help="Path to scan")
    
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
    
    # Handle Setup
    if args.setup:
        from src.orchestration.setup_manager import SetupManager
        setup_mgr = SetupManager()
        setup_mgr.run_setup()
        return 0
        
    # Handle Environment Import
    if args.import_env:
        secrets_manager = SecretsManager()
        logger.info("Importing .env file into secure storage...")
        secrets_manager.import_from_env_file('.env')
        logger.info("✓ Environment variables imported successfully")
        logger.info("You can now run hermes commands with encrypted credentials")
        return 0
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
            try:
                dm.pull_image(image)
            except Exception as e:
                logger.error(f"Failed to pull {image}: {e}")
                continue
        logger.info("Image pull process completed.")
        return 0

    # Handle Remove Images
    if args.remove_images:
        from src.orchestration.docker_manager import DockerManager
        logger.info("Removing Docker images...")
        dm = DockerManager()
        if not dm.is_available:
            logger.error("Docker is not available.")
            return 1
        for image in dm.TRUSTED_IMAGES:
            try:
                dm.remove_image(image, force=True)
            except Exception as e:
                logger.warning(f"Failed to remove {image}: {e}")
        logger.info("All trusted images removed successfully.")
        return 0

    # Handle Plugins Command
    if args.command == "plugins":
        from src.core.plugin_loader import PluginLoader
        from src.orchestration.execution_strategy import NativeExecutionStrategy
        from src.core.plugin_security_scanner import PluginSecurityScanner
        
        # Initialize loader with dummy strategy (we just need discovery/metadata)
        loader = PluginLoader(NativeExecutionStrategy())
        
        if args.plugin_command == "list":
            manifests = loader.discover_plugins()
            logger.info(f"Found {len(manifests)} plugins:")
            for m in manifests:
                status = "Tool" if m.plugin_type == "tool" else "Core"
                logger.info(f"  - {m.name} v{m.version} ({status}) by {m.author}")
                
        elif args.plugin_command == "info":
            manifests = loader.discover_plugins()
            target = next((m for m in manifests if m.name == args.plugin_name), None)
            if target:
                logger.info(f"Plugin: {target.name}")
                logger.info(f"Version: {target.version}")
                logger.info(f"Type: {target.plugin_type}")
                logger.info(f"Description: {target.description}")
                logger.info(f"Author: {target.author}")
                logger.info(f"Adapter: {target.adapter_class}")
                if target.tool_name:
                    logger.info(f"Tool Name: {target.tool_name}")
                if target.docker_image:
                    logger.info(f"Docker Image: {target.docker_image}")
                logger.info(f"Capabilities: {target.capabilities}")
            else:
                logger.error(f"Plugin '{args.plugin_name}' not found.")
                
        elif args.plugin_command == "scan":
            scanner = PluginSecurityScanner()
            # Scan directory
            import os
            path = args.path
            if not os.path.exists(path):
                logger.error(f"Path not found: {path}")
                return 1
                
            logger.info(f"Scanning {path}...")
            has_issues = False
            for root, _, files in os.walk(path):
                for file in files:
                    if file.endswith(".py"):
                        full_path = os.path.join(root, file)
                        result = scanner.scan_file(full_path)
                        if not result.passed or result.warnings:
                            has_issues = True
                            logger.info(f"\nFile: {file}")
                            logger.info(f"Passed: {result.passed} (Confidence: {result.confidence:.2f})")
                            for err in result.errors:
                                logger.error(f"  [ERROR] {err.message} (Line {err.line_number})")
                            for warn in result.warnings:
                                logger.warning(f"  [WARNING] {warn.message}")
            
            if not has_issues:
                logger.info("✓ No security issues found.")
            else:
                logger.warning("\nSecurity scan completed with issues.")
                
        return 0


    
    # Handle configuration profile commands
    config_manager = ConfigManager()
    
    # Initialize proxy manager from environment variables
    secrets_manager = SecretsManager()
    proxy_manager = ProxyManager.load_from_env(secrets_manager)
    if proxy_manager.providers:
        logger.info(f"Loaded {len(proxy_manager.providers)} proxy provider(s)")
        await proxy_manager.initialize()
    
    # Handle environment import (handled earlier, but kept for flow if moved)
    # if args.import_env: ...
    
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
        
        
        # Initialize WorkflowManager with the specified mode
        workflow_manager = WorkflowManager(execution_mode=args.mode)
        
        # Check if tool exists in loaded adapters
        if args.tool not in workflow_manager.adapters:
            logger.error(f"Tool '{args.tool}' not found. Available tools: {list(workflow_manager.adapters.keys())}")
            return 1
        
        # Get the adapter for the requested tool
        adapter = workflow_manager.adapters[args.tool]
        
        # Check if tool can run
        if not adapter.can_run():
            logger.error(f"Tool '{args.tool}' cannot run in {args.mode} mode. Try --mode hybrid or --mode docker")
            return 1
        
        try:
            # Prepare target based on tool type and arguments
            # Use email for email tools, phone for phoneinfoga, file for exiftool, otherwise use target
            if args.email and args.tool in ["holehe", "h8mail", "ghunt"]:
                target = args.email
            elif args.phone and args.tool == "phoneinfoga":
                target = args.phone
            else:
                target = args.target
            
            logger.info(f"Executing {args.tool} with target: {target}")
            result = adapter.execute(target, {})
            
            # Display results
            if result.error:
                logger.error(f"{args.tool} failed: {result.error}")
                return 1
            else:
                logger.info(f"✓ {args.tool} completed successfully")
                logger.info(f"Found {len(result.entities)} results")
                
                # Print entities
                for entity in result.entities:
                    logger.info(f"  - {entity.type}: {entity.value}")
                
                return 0
                
        except Exception as e:
            logger.error(f"Execution failed: {e}")
            import traceback
            traceback.print_exc()
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
        "tool_results": {}
    }
    

    # Auto-detect resources
    ResourceLimiter.auto_detect_resources()
    
    # Initialize TaskManager
    task_manager = TaskManager(max_workers=args.workers)
    await task_manager.start()
    
    # Initialize WorkflowManager for tool execution
    workflow_manager = WorkflowManager(execution_mode=args.mode)
    
    try:
        # Generate username variations if requested
        username_variations = []
        if args.variations and args.type == "individual":
            logger.info("Generating username variations...")
            # Default to including leet and suffixes if variations flag is on, as per user request "Default, all on"
            username_variations = generate_username_variations(
                args.target, 
                include_leet=True, 
                include_suffixes=True
            )
            logger.info(f"Generated {len(username_variations)} variations.")

        # Run External Tools (via WorkflowManager)
        # This runs tools in parallel using ThreadPoolExecutor
        logger.info(f"Running external tools in {args.mode} mode (parallel)...")
        
        # Pass stealth mode, variations, and max workers from CLI
        tool_results = await workflow_manager.run_all_tools(
            target=args.target,
            target_type=args.type,
            domain=args.domain,
            email=args.email,
            phone=args.phone,
            file=args.file,
            stealth_mode=args.stealth,
            username_variations=username_variations,
            max_workers=args.workers
        )
        results['tool_results'] = tool_results.get('tool_results', {})
        
    finally:
        # Cleanup
        await task_manager.stop()

    # Deduplication (Sync)
    if not args.no_dedup and config_dict.get('features', {}).get('deduplication', True):
        logger.info("\n[Deduplication] Processing results...")
        try:
            # Extract social results from tool outputs for deduplication
            social_results = []
            search_results = []
            
            # Iterate over all tool results
            for tool_name, tool_result in results['tool_results'].items():
                # Handle variations (Sherlock)
                if 'variations' in tool_result:
                    for variation in tool_result['variations']:
                        if 'results' in variation and 'entities' in variation['results']:
                             for entity in variation['results']['entities']:
                                if entity['type'] == 'account':
                                    social_results.append({
                                        'platform': entity['metadata'].get('service', tool_name),
                                        'username': variation['variant'],
                                        'url': entity['value'],
                                        'status': 'found',
                                        'source': entity['source']
                                    })

                # Handle standard results
                if 'entities' in tool_result:
                    for entity in tool_result['entities']:
                        if entity['type'] == 'account':
                            social_results.append({
                                'platform': entity['metadata'].get('service', tool_name),
                                'username': args.target, # Best guess for username
                                'url': entity['value'],
                                'status': 'found',
                                'source': entity['source']
                            })
                        elif entity['type'] in ['url', 'domain']:
                            # Map to search result format
                            search_results.append({
                                'source': entity['source'],
                                'title': entity['metadata'].get('title', entity['value']),
                                'url': entity['value'],
                                'description': entity['metadata'].get('content', '') or entity['metadata'].get('source', '')
                            })
            
            processed = deduplicate_and_correlate(
                search_results=search_results,
                social_results=social_results
            )
            results['social_media'] = processed.get('social_media', [])
            results['search_engines'] = processed.get('search_engines', [])
            results['connections'] = processed.get('connections', [])
            results['statistics'] = processed.get('statistics', {})
        except Exception as e:
            logger.error(f"Deduplication failed: {e}")

    # LLM Analysis (optional)
    if args.analyze:
        logger.info("\n[AI Analysis] Analyzing findings with Ollama...")
        try:
            from src.analysis.ollama_client import OllamaConfig
            from src.core.entities import ToolResult as TR, Entity as E
            
            # Convert dict results back to ToolResult objects
            tool_result_objects = {}
            for tool_name, result_dict in results.get('tool_results', {}).items():
                if isinstance(result_dict, dict) and 'entities' in result_dict:
                    entities = [
                        E(
                            type=e.get('type', 'unknown'),
                            value=e.get('value', ''),
                            source=e.get('source', tool_name),
                            confidence=e.get('confidence', 1.0),
                            metadata=e.get('metadata', {})
                        )
                        for e in result_dict.get('entities', [])
                    ]
                    tool_result_objects[tool_name] = TR(
                        tool=tool_name,
                        entities=entities,
                        error=result_dict.get('error')
                    )
            
            config = OllamaConfig(model=args.model)
            analyzer = LLMAnalyzer(config=config)
            analysis = await analyzer.analyze(
                tool_result_objects,
                target=args.target,
                include_patterns=True,
                include_priorities=True
            )
            
            if analysis.available:
                results['ai_analysis'] = analysis.to_dict()
                logger.info("✓ AI analysis complete")
                if analysis.summary:
                    logger.info("\n--- AI Summary ---")
                    logger.info(analysis.summary)
            else:
                logger.warning("Ollama not available - skipping AI analysis")
                logger.info("Install Ollama: https://ollama.ai/download")
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")

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
