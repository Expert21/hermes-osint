
"""
Hermes Self-Test Module - Simplified Version
Verifies all components can be imported without performing actual operations
"""
import logging
from colorama import Fore, Style, init

init(autoreset=True)
logger = logging.getLogger("OSINT_Tool")


def run_self_test():
    """Run all self-tests and return results"""
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Hermes Self-Test - Module Verification")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}\n")
    
    results = []
    passed = 0
    failed = 0
    
    # Test all modules
    tests = [
        ("Logger", lambda: __import__('src.core.logger')),
        ("Config Manager", lambda: __import__('src.core.config_manager')),
        ("Progress Tracker", lambda: __import__('src.core.progress_tracker')),
        ("Deduplication", lambda: __import__('src.core.deduplication')),
        ("Cache Manager", lambda: __import__('src.core.cache_manager')),
        ("Email Enumeration", lambda: __import__('src.modules.email_enumeration')),
        ("Username Generator", lambda: __import__('src.modules.username_generator')),
        ("Domain Enumeration", lambda: __import__('src.modules.domain_enum')),
        ("Search Engines", lambda: __import__('src.modules.search_engines')),
        ("Social Media", lambda: __import__('src.modules.social_media')),
        ("Profile Verification", lambda: __import__('src.modules.profile_verification')),
        ("HTML Report", lambda: __import__('src.reporting.html_report')),
        ("Markdown Report", lambda: __import__('src.reporting.markdown_report')),
        ("PDF Report", lambda: __import__('src.reporting.pdf_report')),
        ("STIX Export", lambda: __import__('src.reporting.stix_export')),
        ("Interactive Mode", lambda: __import__('src.core.interactive')),
    ]
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            results.append({"name": name, "status": "PASS", "error": None})
            print(f"{Fore.GREEN}✓ PASS{Style.RESET_ALL} - {name}")
        except Exception as e:
            failed += 1
            results.append({"name": name, "status": "FAIL", "error": str(e)})
            print(f"{Fore.RED}✗ FAIL{Style.RESET_ALL} - {name}")
            print(f"  {Fore.YELLOW}Error: {str(e)}{Style.RESET_ALL}")
    
    # Print summary
    total = len(tests)
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"\n{Fore.CYAN}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.CYAN}{Style.BRIGHT}Test Summary")
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}")
    print(f"Total Tests: {total}")
    print(f"{Fore.GREEN}Passed: {passed}{Style.RESET_ALL}")
    print(f"{Fore.RED}Failed: {failed}{Style.RESET_ALL}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    if failed == 0:
        print(f"\n{Fore.GREEN}{Style.BRIGHT}🎉 All modules are working correctly!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}{Style.BRIGHT}⚠️ Some modules failed. Please review the errors above.{Style.RESET_ALL}")
    
    print(f"{Fore.CYAN}{Style.BRIGHT}{'='*60}{Style.RESET_ALL}\n")
    
    return {
        "total_tests": total,
        "passed": passed,
        "failed": failed,
        "results": results
    }
