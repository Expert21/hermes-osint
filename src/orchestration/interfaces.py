
from abc import ABC, abstractmethod
from typing import Dict, Any
from src.core.entities import ToolResult

class ToolAdapter(ABC):
    """
    Abstract base class for all external tool adapters.
    """

    @abstractmethod
    def can_run(self) -> bool:
        """
        Check if the tool can run in the current environment.
        
        Returns:
            True if the tool is available and configured correctly, False otherwise.
        """
        pass

    @abstractmethod
    def execute(self, target: str, config: Dict[str, Any]) -> ToolResult:
        """
        Execute the tool against the target.
        
        Args:
            target: The target identifier (username, domain, etc.)
            config: Configuration dictionary for the tool
            
        Returns:
            ToolResult containing the structured findings
        """
        pass

    @abstractmethod
    def parse_results(self, output: str) -> ToolResult:
        """
        Parse the raw output from the tool into a structured format.
        
        Args:
            output: Raw string output from the tool (stdout/stderr)
            
        Returns:
            ToolResult containing the structured findings
        """
        pass
