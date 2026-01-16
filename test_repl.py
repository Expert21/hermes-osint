#!/usr/bin/env python3
"""
Hermes v3.0 - Agent Test REPL

A simple interactive REPL for testing the agent loop.
This is a development tool, not production code.

Usage:
    python test_repl.py
    
    # Or with options:
    python test_repl.py --model mistral --mode docker
"""

import asyncio
import argparse
import sys


async def main():
    parser = argparse.ArgumentParser(description="Hermes Agent Test REPL")
    parser.add_argument("--model", default="llama3.2", help="Ollama model to use")
    parser.add_argument("--mode", default="native", choices=["native", "docker", "hybrid"],
                        help="Tool execution mode")
    args = parser.parse_args()
    
    # Import here to avoid issues if dependencies missing
    try:
        from src.agent.agent_loop import AgentLoop
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure you're running from the hermes-osint directory")
        return 1
    
    # Initialize agent
    print("=" * 60)
    print("Hermes v3.0 - Agent Test REPL")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Execution Mode: {args.mode}")
    print("-" * 60)
    
    agent = AgentLoop(model=args.model, execution_mode=args.mode)
    
    # Check availability
    print("Checking Ollama connection...")
    if not await agent.is_available():
        print("ERROR: Ollama is not available!")
        print("Make sure Ollama is running: ollama serve")
        return 1
    
    print("✓ Ollama connected")
    print("-" * 60)
    print("Type 'exit' or 'quit' to exit")
    print("Type 'clear' to clear conversation history")
    print("=" * 60)
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ("exit", "quit"):
                print("\nGoodbye!")
                break
            
            if user_input.lower() == "clear":
                agent.clear_history()
                print("Conversation cleared.\n")
                continue
            
            # Run agent
            print()  # Blank line before response
            response = await agent.run(user_input)
            print(f"Hermes: {response}")
            print()  # Blank line after response
            
        except KeyboardInterrupt:
            print("\n\nInterrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
