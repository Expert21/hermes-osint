#!/usr/bin/env python3
"""
Hermes CLI - Main Entry Point

The unified command-line interface for Hermes OSINT.

Modes:
    TUI (default): Interactive agentic mode with Ollama
    Headless: Single query mode for scripting
    Legacy: Direct tool execution without LLM

Usage:
    hermes                        # TUI mode (requires Ollama)
    hermes --headless -q "..."    # Single query mode
    hermes sherlock testuser      # Legacy direct tool mode
"""

import asyncio
import argparse
import sys
import os
import logging
from typing import Optional, List

# Version
__version__ = "3.0.0"

logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        prog="hermes",
        description="Hermes - Agentic OSINT Analyst",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
MODES:
  TUI (default)     Interactive conversation with LLM (requires Ollama)
  Headless          Single query for scripting: --headless -q "query"
  Legacy            Direct tool execution: hermes <tool> <target>

EXAMPLES:
  hermes                                    # Start TUI
  hermes --headless -q "find john_doe"      # Single query
  hermes sherlock testuser                  # Direct Sherlock
  hermes --resume my_investigation          # Resume session
  
TUI COMMANDS:
  /help, /status, /tools, /clear
  /save, /load, /sessions, /export
  /exit
"""
    )
    
    # Mode flags
    parser.add_argument(
        "--headless", action="store_true",
        help="Run in headless mode (requires --query)"
    )
    parser.add_argument(
        "-q", "--query",
        help="Query to run in headless mode"
    )
    
    # Session management
    parser.add_argument(
        "--resume",
        help="Resume a saved session"
    )
    parser.add_argument(
        "--export",
        help="Export results to file (format from extension)"
    )
    
    # Configuration
    parser.add_argument(
        "-m", "--model", default="llama3.2",
        help="Ollama model to use (default: llama3.2, recommended: llama3.1:8b)"
    )
    parser.add_argument(
        "--mode", default="hybrid",
        choices=["native", "docker", "hybrid"],
        help="Tool execution mode (default: hybrid)"
    )
    parser.add_argument(
        "--stealth", action="store_true",
        help="Enable stealth mode (passive tools only)"
    )
    
    # Meta
    parser.add_argument(
        "--version", action="store_true",
        help="Show version and exit"
    )
    parser.add_argument(
        "--debug", action="store_true",
        help="Enable debug logging"
    )
    
    # Legacy mode: positional arguments for direct tool use
    parser.add_argument(
        "tool", nargs="?",
        help="Tool to run directly (legacy mode)"
    )
    parser.add_argument(
        "target", nargs="?",
        help="Target for direct tool execution"
    )
    
    return parser.parse_args()


async def check_ollama() -> bool:
    """Check if Ollama is available."""
    try:
        from src.analysis.ollama_client import OllamaClient, OllamaConfig
        client = OllamaClient(OllamaConfig())
        return await client.is_available()
    except Exception:
        return False


async def run_tui(args: argparse.Namespace) -> int:
    """Run the interactive TUI."""
    from src.agent.tui import HermesTUI
    
    tui = HermesTUI(model=args.model, execution_mode=args.mode)
    
    # Handle resume
    if args.resume:
        # Will be handled in TUI initialization
        pass
    
    return await tui.run()


async def run_headless(args: argparse.Namespace) -> int:
    """Run headless single-query mode."""
    from src.agent.agent_loop import AgentLoop
    from src.agent.exporter import AgentExporter
    from src.agent.styles import Colors
    
    # Check Ollama
    if not await check_ollama():
        print(f"Error: Ollama is required for headless mode", file=sys.stderr)
        print(f"Start Ollama with: ollama serve", file=sys.stderr)
        return 1
    
    agent = AgentLoop(model=args.model, execution_mode=args.mode)
    
    config = {"stealth_mode": args.stealth}
    
    try:
        # Run query
        result = await agent.run(args.query, config)
        
        # Check if output should be colored
        if sys.stdout.isatty():
            print(f"\n{Colors.CYAN}Hermes:{Colors.RESET} {result}")
        else:
            # Pipe-friendly: no colors
            print(result)
        
        # Export if requested
        if args.export:
            exporter = AgentExporter()
            if exporter.export(agent.messages, args.export):
                if sys.stdout.isatty():
                    print(f"\n{Colors.GREEN}✓ Exported to {args.export}{Colors.RESET}")
            else:
                print(f"Export failed", file=sys.stderr)
                return 1
        
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


async def run_legacy(args: argparse.Namespace) -> int:
    """Run legacy direct tool mode (no LLM)."""
    from src.agent.tool_executor import ToolExecutor
    from src.agent.tool_registry import TOOL_REGISTRY
    from src.agent.styles import Colors
    
    tool_name = args.tool.lower()
    target = args.target
    
    # Validate tool
    if tool_name not in TOOL_REGISTRY:
        print(f"Error: Unknown tool '{tool_name}'", file=sys.stderr)
        print(f"Available tools: {', '.join(TOOL_REGISTRY.keys())}", file=sys.stderr)
        return 1
    
    if not target:
        print(f"Error: Missing target for {tool_name}", file=sys.stderr)
        print(f"Usage: hermes {tool_name} <target>", file=sys.stderr)
        return 1
    
    # Get expected argument name
    tool_def = TOOL_REGISTRY[tool_name]
    param_name = list(tool_def.parameters.get("properties", {}).keys())[0]
    
    # Execute tool directly
    executor = ToolExecutor(execution_mode=args.mode)
    config = {"stealth_mode": args.stealth}
    
    if sys.stdout.isatty():
        print(f"{Colors.DIM}Running {tool_name} on {target}...{Colors.RESET}")
    
    result = executor.execute(tool_name, {param_name: target}, config)
    
    if not result.success:
        print(f"Error: {result.error}", file=sys.stderr)
        return 1
    
    # Print results
    if sys.stdout.isatty():
        print(f"\n{Colors.GREEN}✓ {tool_name} found {len(result.entities)} results:{Colors.RESET}\n")
        for entity in result.entities:
            print(f"  • [{entity.type}] {entity.value}")
    else:
        # Pipe-friendly output
        for entity in result.entities:
            print(f"{entity.type}\t{entity.value}")
    
    # Export if requested
    if args.export:
        from src.agent.exporter import AgentExporter
        exporter = AgentExporter()
        # Create fake message for export
        if exporter.export([], args.export):
            print(f"\n✓ Exported to {args.export}")
    
    return 0


async def main() -> int:
    """Main entry point."""
    args = parse_args()
    
    # Configure logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Version
    if args.version:
        print(f"Hermes v{__version__}")
        return 0
    
    # Headless mode validation
    if args.headless and not args.query:
        print("Error: Headless mode requires --query", file=sys.stderr)
        print("", file=sys.stderr)
        print("Usage: hermes --headless --query 'find user john_doe'", file=sys.stderr)
        print("       hermes --headless -q 'search example.com' --export report.pdf", file=sys.stderr)
        return 1
    
    # Legacy mode: direct tool invocation
    if args.tool and args.tool.lower() in ['sherlock', 'theharvester', 'h8mail', 
                                            'holehe', 'phoneinfoga', 'subfinder']:
        return await run_legacy(args)
    
    # Headless mode
    if args.headless:
        return await run_headless(args)
    
    # TUI mode (default) - requires Ollama
    if not await check_ollama():
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║  Hermes v3.0 - Agentic OSINT Analyst                         ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        print("")
        print("  ⚠️  Ollama is required for TUI mode")
        print("")
        print("  Install: https://ollama.com/download")
        print("  Start:   ollama serve")
        print("  Model:   ollama pull llama3.2")
        print("")
        print("  For direct tool execution without LLM, use:")
        print("    hermes sherlock <username>")
        print("    hermes theharvester <domain>")
        print("    hermes h8mail <email>")
        print("")
        return 1
    
    return await run_tui(args)


def entry_point():
    """Entry point for console script."""
    sys.exit(asyncio.run(main()))


if __name__ == "__main__":
    entry_point()
