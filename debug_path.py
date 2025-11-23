import sys
import os
import traceback

# Add root to path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

print(f"Sys Path: {sys.path}")

try:
    import tests.test_security_fixes
    print("tests.test_security_fixes imported successfully")
except Exception:
    traceback.print_exc()
