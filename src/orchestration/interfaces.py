<<<<<<< HEAD
from abc import ABC, abstractmethod
from typing import Dict, Any

class ToolAdapter(ABC):
    """
    Abstract base class for all external tool adapters.
    """

    @abstractmethod
    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool against the target.
        
        Args:
            target: The target identifier (username, domain, etc.)
            config: Configuration dictionary for the tool
            
        Returns:
            Dict containing the raw results and metadata
        """
        pass

    @abstractmethod
    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse the raw output from the tool into a structured format.
        
        Args:
            output: Raw string output from the tool (stdout/stderr)
            
        Returns:
            Structured dictionary of findings
        """
        pass
=======
from abc import ABC, abstractmethod
from typing import Dict, Any

class ToolAdapter(ABC):
    """
    Abstract base class for all external tool adapters.
    """

    @abstractmethod
    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool against the target.
        
        Args:
            target: The target identifier (username, domain, etc.)
            config: Configuration dictionary for the tool
            
        Returns:
            Dict containing the raw results and metadata
        """
        pass

    @abstractmethod
    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse the raw output from the tool into a structured format.
        
        Args:
            output: Raw string output from the tool (stdout/stderr)
            
        Returns:
            Structured dictionary of findings
        """
        pass
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
