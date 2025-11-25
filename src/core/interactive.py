from typing import Dict, Any, List
import logging

# Try to import colorama, but handle if not present
try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    class Fore:
        CYAN = ""
        GREEN = ""
        YELLOW = ""
        RED = ""
        BLUE = ""
        MAGENTA = ""
        WHITE = ""
    class Style:
        BRIGHT = ""
        RESET_ALL = ""

logger = logging.getLogger("OSINT_Tool")

class InteractiveWizard:
    """
    CLI Wizard for guided OSINT scans.
    """
    
    def __init__(self):
        self.config = {}
    
    def clear_screen(self):
        print("\033[H\033[J", end="")

    def print_header(self):
        self.clear_screen()
        print(f"{Fore.CYAN}{Style.BRIGHT}" + "="*60)
        print(f"{Fore.CYAN}{Style.BRIGHT}   🕵️  OSINT Tool - Interactive Wizard")
        print(f"{Fore.CYAN}{Style.BRIGHT}" + "="*60 + f"{Style.RESET_ALL}")
        print()

    def get_input(self, prompt: str, default: str = None, required: bool = True) -> str:
        """Get user input with optional default."""
        prompt_text = f"{Fore.GREEN}{prompt}"
        if default:
            prompt_text += f" {Fore.WHITE}[{default}]"
        prompt_text += f": {Style.RESET_ALL}"
        
        while True:
            value = input(prompt_text).strip()
            if not value and default:
                return default
            if not value and required:
                print(f"{Fore.RED}Error: This field is required.{Style.RESET_ALL}")
                continue
            return value

    def select_option(self, prompt: str, options: List[str]) -> str:
        """Present a list of options to the user."""
        print(f"\n{Fore.YELLOW}{prompt}:{Style.RESET_ALL}")
        for i, opt in enumerate(options, 1):
            print(f"  {Fore.CYAN}{i}.{Style.RESET_ALL} {opt}")
        
        while True:
            try:
                choice = int(input(f"\n{Fore.GREEN}Select an option (1-{len(options)}): {Style.RESET_ALL}"))
                if 1 <= choice <= len(options):
                    return options[choice-1]
            except ValueError:
                pass
            print(f"{Fore.RED}Invalid selection. Please try again.{Style.RESET_ALL}")

    def run(self) -> Dict[str, Any]:
        """Run the interactive wizard and return configuration dictionary."""
        self.print_header()
        
        print("Welcome to the guided scan mode. I'll help you configure your scan.\n")
        
        # 1. Target Information
        print(f"{Fore.MAGENTA}--- Target Information ---{Style.RESET_ALL}")
        target_type_display = self.select_option("What type of target are you investigating?", ["Individual", "Company"])
        target_type = target_type_display.lower()
        
        target_name = self.get_input(f"Enter the {target_type} name")
        
        additional_info = {}
        if target_type == "individual":
            if self.get_input("Do you know their employer/company?", "n", required=False).lower().startswith('y'):
                additional_info['company'] = self.get_input("Company name")
            
            if self.get_input("Do you know their location?", "n", required=False).lower().startswith('y'):
                additional_info['location'] = self.get_input("Location")
        
        # 2. Scan Configuration
        print(f"\n{Fore.MAGENTA}--- Scan Configuration ---{Style.RESET_ALL}")
        scan_profile = self.select_option("Select a scan profile", ["Quick Scan (Fast, less detail)", "Default Scan (Balanced)", "Deep Scan (Thorough, slower)"])
        
        profile_map = {
            "Quick Scan (Fast, less detail)": "quick_scan",
            "Default Scan (Balanced)": "default",
            "Deep Scan (Thorough, slower)": "deep_scan"
        }
        config_profile = profile_map[scan_profile]
        
        # 3. Features
        print(f"\n{Fore.MAGENTA}--- Features ---{Style.RESET_ALL}")
        features = {}
        
        features['email_enum'] = self.get_input("Enable Email Enumeration?", "y", required=False).lower().startswith('y')
        if features['email_enum']:
            features['domain'] = self.get_input("Target domain for emails (e.g. company.com)")
            
        features['username_vars'] = False
        if target_type == "individual":
            features['username_vars'] = self.get_input("Try username variations?", "y", required=False).lower().startswith('y')
            
        features['domain_enum'] = False
        if target_type == "company" or features.get('domain'):
            features['domain_enum'] = self.get_input("Run Domain/Subdomain Enumeration?", "y", required=False).lower().startswith('y')
            
        # 4. Output
        print(f"\n{Fore.MAGENTA}--- Output ---{Style.RESET_ALL}")
        output_format = self.select_option("Select report format", ["HTML", "JSON", "Markdown", "PDF", "STIX"])
        output_file = self.get_input("Output filename", f"report.{output_format.lower()}")
        
        # Summary
        print(f"\n{Fore.GREEN}{Style.BRIGHT}--- Scan Summary ---{Style.RESET_ALL}")
        print(f"Target: {target_name} ({target_type})")
        print(f"Profile: {config_profile}")
        print(f"Features: Email Enum={features['email_enum']}, Domain Enum={features['domain_enum']}")
        print(f"Output: {output_file}")
        
        if self.get_input("\nStart scan now?", "y", required=False).lower().startswith('y'):
            # Construct args dictionary similar to argparse
            return {
                "target": target_name,
                "type": target_type,
                "config": config_profile,
                "output": output_file,
                "email_enum": features['email_enum'],
                "domain": features.get('domain'),
                "username_variations": features['username_vars'],
                "domain_enum": features['domain_enum'],
                # Default flags
                "no_verify": False,
                "skip_search": False,
                "skip_social": False,
                "no_progress": False,
                "no_dedup": False,
                # Extras
                "company": additional_info.get('company'),
                "location": additional_info.get('location')
            }
        else:
            print("Scan cancelled.")
            return None

def run_interactive_mode():
    """Entry point for interactive mode."""
    wizard = InteractiveWizard()
    return wizard.run()
