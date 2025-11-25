#!/usr/bin/env python3
"""
Hermes Self-Test - Standalone Command
Run this to verify all modules are working correctly
"""
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.core.self_test import run_self_test

if __name__ == "__main__":
    results = run_self_test()
    sys.exit(0 if results['failed'] == 0 else 1)
