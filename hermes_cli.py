#!/usr/bin/env python3

"""
Hermes CLI entry point
This module is used when running 'hermes' command after installation
"""

def cli():
    """Entry point for the hermes command"""
    import sys
    import os
    
    # Add the installation directory to the path
    install_dir = os.path.dirname(os.path.abspath(__file__))
    if install_dir not in sys.path:
        sys.path.insert(0, install_dir)
    
    # Import and run main
    from main import main
    sys.exit(main())

if __name__ == "__main__":
    cli()
