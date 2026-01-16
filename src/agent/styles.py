"""
Hermes TUI Styles

Defines colors and formatting for the Terminal User Interface.
Uses a pentesting/hacker aesthetic with green, cyan, and orange accents.
"""

from prompt_toolkit.styles import Style

# Main color scheme
HERMES_STYLE = Style.from_dict({
    # Prompts
    'prompt': '#00ff00 bold',           # Bright green
    'prompt-symbol': '#00aa00',         # Darker green for symbols
    
    # User input
    'user-input': '#ffffff',            # White
    
    # Agent responses
    'agent-name': '#00ffff bold',       # Cyan bold for "Hermes:"
    'agent-text': '#e0e0e0',            # Light gray for response text
    
    # Tool execution
    'tool-name': '#ff8800 bold',        # Orange for tool names
    'tool-running': '#ffff00',          # Yellow for "running..."
    'tool-result': '#88ff88',           # Light green for results
    
    # Status and info
    'status-bar': 'bg:#1a1a1a #888888', # Dark bg, gray text
    'status-key': '#00ffff',            # Cyan for key names
    'status-value': '#ffffff',          # White for values
    'status-ok': '#00ff00',             # Green for good status
    'status-warn': '#ffff00',           # Yellow for warnings
    'status-error': '#ff0000',          # Red for errors
    
    # Errors
    'error': '#ff0000 bold',            # Red bold
    'error-detail': '#ff6666',          # Lighter red
    
    # Commands
    'command': '#ff00ff',               # Magenta for slash commands
    'command-help': '#aaaaaa',          # Gray for help text
    
    # Misc
    'dim': '#666666',                   # Dimmed text
    'highlight': '#ffff00 bold',        # Yellow highlight
})


# ANSI color codes for simple print statements
class Colors:
    """ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Bright foreground
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_MAGENTA = '\033[95m'
    
    # Background
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'


def format_agent_response(text: str) -> str:
    """Format agent response with colors."""
    return f"{Colors.BRIGHT_CYAN}Hermes:{Colors.RESET} {text}"


def format_error(text: str) -> str:
    """Format error message."""
    return f"{Colors.BRIGHT_RED}Error:{Colors.RESET} {text}"


def format_tool_execution(tool_name: str) -> str:
    """Format tool execution message."""
    return f"{Colors.YELLOW}[{tool_name}]{Colors.RESET} Running..."


def format_tool_result(tool_name: str, count: int) -> str:
    """Format tool result summary."""
    return f"{Colors.GREEN}[{tool_name}]{Colors.RESET} Found {count} results"


def format_status(label: str, value: str, ok: bool = True) -> str:
    """Format a status item."""
    color = Colors.GREEN if ok else Colors.YELLOW
    return f"{Colors.CYAN}{label}:{Colors.RESET} {color}{value}{Colors.RESET}"


def print_header():
    """Print the Hermes header/banner."""
    banner = f"""
{Colors.BRIGHT_CYAN}╔══════════════════════════════════════════════════════════════╗
║  {Colors.BRIGHT_GREEN}HERMES v3.0{Colors.BRIGHT_CYAN} - Agentic OSINT Analyst                        ║
╚══════════════════════════════════════════════════════════════╝{Colors.RESET}
"""
    print(banner)


def print_help():
    """Print help message."""
    help_text = f"""
{Colors.BRIGHT_CYAN}Commands:{Colors.RESET}
  {Colors.MAGENTA}/help{Colors.RESET}         - Show this help message
  {Colors.MAGENTA}/status{Colors.RESET}       - Show system status
  {Colors.MAGENTA}/tools{Colors.RESET}        - List available tools
  {Colors.MAGENTA}/clear{Colors.RESET}        - Clear conversation history
  
{Colors.BRIGHT_CYAN}Sessions:{Colors.RESET}
  {Colors.MAGENTA}/save{Colors.RESET} [name]  - Save current session
  {Colors.MAGENTA}/load{Colors.RESET} [name]  - Load a saved session  
  {Colors.MAGENTA}/sessions{Colors.RESET}     - List saved sessions

{Colors.BRIGHT_CYAN}Export:{Colors.RESET}
  {Colors.MAGENTA}/export{Colors.RESET} FILE  - Export report (md/pdf/html/csv/stix)

  {Colors.MAGENTA}/exit{Colors.RESET}         - Exit Hermes

{Colors.BRIGHT_CYAN}Tips:{Colors.RESET}
  • Just type naturally to investigate targets
  • Use {Colors.GREEN}Ctrl+C{Colors.RESET} to interrupt
  • Press {Colors.GREEN}↑/↓{Colors.RESET} for history
"""
    print(help_text)
