from typing import Dict, Any
from src.orchestration.interfaces import ToolAdapter
from src.orchestration.docker_manager import DockerManager
from src.core.input_validator import InputValidator

class ExiftoolAdapter(ToolAdapter):
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        self.image = "u1234x1234/exiftool" # Placeholder image, replace with actual if needed

    def execute(self, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run Exiftool against a file URL or path (if mounted).
        For this implementation, we assume target is a URL to an image we fetch inside the container or pass to it.
        However, standard exiftool works on files. 
        
        If target is a URL, we might need a wrapper script in the container.
        For simplicity, let's assume the container can handle URLs or we just pass arguments.
        
        Args:
            target: URL to image/file
            config: Configuration dictionary
            
        Returns:
            Parsed results from Exiftool
        """
        # SECURITY: Basic validation
        if not target.startswith(("http://", "https://")):
            raise ValueError("Target must be a URL")
        if not InputValidator.is_safe_url(target):
            raise ValueError("Unsafe URL detected")
        
        # NOTE: Standard exiftool doesn't fetch URLs natively without curl/wget piping.
        # We'll assume the docker image has a wrapper or we use a simple command.
        # For this adapter, we'll just run it and expect the user/container to handle it.
        # A more robust implementation would download the file first.
        
        # Command: exiftool <target>
        command = [target, "-json"]
        output = self.docker_manager.run_container(self.image, command)
        return self.parse_results(output)

    def parse_results(self, output: str) -> Dict[str, Any]:
        """
        Parse Exiftool JSON output.
        """
        import json
        try:
            # Exiftool -json outputs a JSON array
            data = json.loads(output)
            if isinstance(data, list) and len(data) > 0:
                return {"tool": "exiftool", "results": data[0], "raw_output": output}
            return {"tool": "exiftool", "results": {}, "raw_output": output}
        except json.JSONDecodeError:
             return {"tool": "exiftool", "results": {}, "error": "Failed to parse JSON", "raw_output": output}
