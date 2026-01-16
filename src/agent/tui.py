#!/usr/bin/env python3
"""
Hermes TUI - Terminal User Interface

A conversational interface for the Hermes OSINT Agent using prompt_toolkit.

Usage:
    python -m src.agent.tui
    python -m src.agent.tui --model mistral --mode docker
"""

import asyncio
import argparse
import os
import sys
import logging
from pathlib import Path
from typing import Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.patch_stdout import patch_stdout
from prompt_toolkit.formatted_text import HTML, FormattedText

from src.agent.agent_loop import AgentLoop
from src.agent.styles import (
    Colors,
    HERMES_STYLE,
    format_agent_response,
    format_error,
    print_header,
    print_help,
    format_status,
)

logger = logging.getLogger(__name__)


class HermesTUI:
    """
    Terminal User Interface for Hermes Agent.
    
    Provides a conversational REPL with:
    - Styled prompts and responses
    - Command history
    - Status bar
    - Slash commands
    """
    
    def __init__(
        self,
        model: str = "llama3.2",
        execution_mode: str = "native",
    ):
        """
        Initialize the TUI.
        
        Args:
            model: Ollama model to use
            execution_mode: Tool execution mode (native/docker/hybrid)
        """
        self.model = model
        self.execution_mode = execution_mode
        self.agent: Optional[AgentLoop] = None
        self.running = False
        self.current_tool: Optional[str] = None
        
        # History file in user's home
        history_path = Path.home() / ".hermes_history"
        self.session = PromptSession(
            history=FileHistory(str(history_path)),
            style=HERMES_STYLE,
        )
    
    def get_prompt(self) -> FormattedText:
        """Get the styled prompt."""
        return FormattedText([
            ('class:prompt', 'You'),
            ('class:prompt-symbol', ': '),
        ])
    
    def get_toolbar(self) -> str:
        """Get the bottom toolbar content."""
        # Connection status
        if self.agent and self.agent.client._available:
            status = f'<status-ok>●</status-ok>'
        else:
            status = f'<status-error>●</status-error>'
        
        # Context size
        context_chars = self.agent.get_context_size() if self.agent else 0
        context_kb = context_chars / 1024
        
        # Current activity
        activity = f'<tool-name>{self.current_tool}</tool-name>' if self.current_tool else 'idle'
        
        return HTML(
            f' {status} <status-key>Model:</status-key> <status-value>{self.model}</status-value> '
            f'│ <status-key>Context:</status-key> <status-value>{context_kb:.1f}kb</status-value> '
            f'│ <status-key>Mode:</status-key> <status-value>{self.execution_mode}</status-value> '
            f'│ {activity}'
        )
    
    async def initialize(self) -> bool:
        """
        Initialize the agent and check availability.
        
        Returns:
            True if initialization successful
        """
        self.agent = AgentLoop(
            model=self.model,
            execution_mode=self.execution_mode
        )
        
        print(f"{Colors.DIM}Connecting to Ollama...{Colors.RESET}")
        
        if not await self.agent.is_available():
            print(format_error("Ollama is not available!"))
            print(f"{Colors.DIM}Make sure Ollama is running: ollama serve{Colors.RESET}")
            return False
        
        print(f"{Colors.GREEN}✓ Connected to Ollama ({self.model}){Colors.RESET}")
        return True
    
    async def handle_command(self, command: str) -> bool:
        """
        Handle slash commands.
        
        Args:
            command: The command string (e.g., "/help")
            
        Returns:
            True to continue, False to exit
        """
        cmd = command.lower().strip()
        
        if cmd in ('/exit', '/quit', '/q'):
            print(f"\n{Colors.CYAN}Goodbye!{Colors.RESET}")
            return False
        
        elif cmd in ('/help', '/h', '/?'):
            print_help()
        
        elif cmd == '/clear':
            if self.agent:
                self.agent.clear_history()
            print(f"{Colors.GREEN}✓ Conversation cleared{Colors.RESET}")
        
        elif cmd == '/status':
            await self.show_status()
        
        elif cmd == '/tools':
            self.show_tools()
        
        else:
            print(format_error(f"Unknown command: {command}"))
            print(f"{Colors.DIM}Type /help for available commands{Colors.RESET}")
        
        return True
    
    async def show_status(self):
        """Show system status."""
        print(f"\n{Colors.BRIGHT_CYAN}System Status{Colors.RESET}")
        print("─" * 40)
        
        # Ollama status
        available = await self.agent.is_available() if self.agent else False
        ollama_status = f"{Colors.GREEN}Connected{Colors.RESET}" if available else f"{Colors.RED}Disconnected{Colors.RESET}"
        print(f"  Ollama:     {ollama_status}")
        print(f"  Model:      {self.model}")
        print(f"  Mode:       {self.execution_mode}")
        
        # Context
        if self.agent:
            context = self.agent.get_context_size()
            messages = len(self.agent.messages)
            print(f"  Context:    {context:,} chars ({messages} messages)")
        
        # Tools
        if self.agent and self.agent.executor:
            tools = list(self.agent.executor.adapters.keys())
            print(f"  Tools:      {', '.join(tools) or 'None loaded'}")
        
        print()
    
    def show_tools(self):
        """Show available tools."""
        print(f"\n{Colors.BRIGHT_CYAN}Available Tools{Colors.RESET}")
        print("─" * 40)
        
        if self.agent and self.agent.executor:
            for name, adapter in self.agent.executor.adapters.items():
                can_run = adapter.can_run()
                status = f"{Colors.GREEN}✓{Colors.RESET}" if can_run else f"{Colors.RED}✗{Colors.RESET}"
                print(f"  {status} {name}")
        else:
            print(f"  {Colors.DIM}No tools loaded{Colors.RESET}")
        
        print()
    
    async def process_input(self, user_input: str):
        """
        Process user input through the agent.
        
        Args:
            user_input: The user's message
        """
        if not self.agent:
            print(format_error("Agent not initialized"))
            return
        
        try:
            # Show thinking indicator
            print(f"{Colors.DIM}Thinking...{Colors.RESET}", end='\r')
            
            # Run the agent
            response = await self.agent.run(user_input)
            
            # Clear thinking indicator and show response
            print(" " * 20, end='\r')  # Clear line
            print(format_agent_response(response))
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Interrupted{Colors.RESET}")
        except Exception as e:
            logger.error(f"Error processing input: {e}")
            print(format_error(str(e)))
    
    async def run(self):
        """Main TUI loop."""
        # Print header
        print_header()
        
        # Initialize
        if not await self.initialize():
            return 1
        
        print(f"{Colors.DIM}Type /help for commands, or just start chatting!{Colors.RESET}\n")
        
        self.running = True
        
        # Main loop
        while self.running:
            try:
                # Get input with styled prompt and toolbar
                with patch_stdout():
                    user_input = await self.session.prompt_async(
                        self.get_prompt(),
                        bottom_toolbar=self.get_toolbar,
                    )
                
                user_input = user_input.strip()
                
                if not user_input:
                    continue
                
                # Handle commands
                if user_input.startswith('/'):
                    should_continue = await self.handle_command(user_input)
                    if not should_continue:
                        self.running = False
                else:
                    # Process through agent
                    await self.process_input(user_input)
                
                print()  # Blank line between exchanges
                
            except KeyboardInterrupt:
                print(f"\n{Colors.DIM}Use /exit to quit{Colors.RESET}")
            except EOFError:
                # Ctrl+D
                print(f"\n{Colors.CYAN}Goodbye!{Colors.RESET}")
                self.running = False
        
        return 0


async def main():
    """Entry point for the TUI."""
    parser = argparse.ArgumentParser(
        description="Hermes OSINT Agent - Terminal Interface"
    )
    parser.add_argument(
        "--model", "-m",
        default="llama3.2",
        help="Ollama model to use (default: llama3.2)"
    )
    parser.add_argument(
        "--mode",
        default="native",
        choices=["native", "docker", "hybrid"],
        help="Tool execution mode (default: native)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    # Run TUI
    tui = HermesTUI(model=args.model, execution_mode=args.mode)
    return await tui.run()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
