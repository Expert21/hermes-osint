
from typing import List, Dict, Any
import logging
from src.orchestration.docker_manager import DockerManager
from src.orchestration.execution_strategy import (
    ExecutionStrategy,
    DockerExecutionStrategy,
    NativeExecutionStrategy,
    HybridExecutionStrategy
)
# Adapters are now loaded dynamically via PluginLoader
from src.core.entities import ToolResult, Entity

logger = logging.getLogger(__name__)

class WorkflowManager:
    """
    Manages sequential execution of OSINT tools.
    """

    def __init__(self, cleanup_images: bool = False, execution_mode: str = "docker"):
        """
        Initialize WorkflowManager.
        
        Args:
            cleanup_images: If True, remove Docker images after execution (OPSEC mode)
            execution_mode: Execution mode - "docker", "native", or "hybrid"
        """
        self.docker_manager = DockerManager()
        self.cleanup_images = cleanup_images
        
        # Initialize execution strategy based on mode
        if execution_mode == "docker":
            self.execution_strategy = DockerExecutionStrategy(self.docker_manager)
        elif execution_mode == "native":
            self.execution_strategy = NativeExecutionStrategy()
        elif execution_mode == "hybrid":
            docker_strategy = DockerExecutionStrategy(self.docker_manager)
            native_strategy = NativeExecutionStrategy()
            self.execution_strategy = HybridExecutionStrategy(docker_strategy, native_strategy)
        else:
            raise ValueError(f"Invalid execution mode: {execution_mode}")
        
        # Initialize all adapters with the execution strategy
        # Initialize PluginLoader and load adapters
        from src.core.plugin_loader import PluginLoader
        
        self.plugin_loader = PluginLoader(self.execution_strategy)
        self.adapters = self.plugin_loader.load_all_plugins()
        
        logger.info(f"Loaded {len(self.adapters)} tool adapters: {list(self.adapters.keys())}")

    def execute_workflow(self, workflow_name: str, target: str) -> Dict[str, Any]:
        """
        Execute a predefined workflow.
        
        Args:
            workflow_name: Name of the workflow (e.g., 'domain_intel')
            target: Initial target (domain or username)
            
        Returns:
            Aggregated results
        """
        results = {
            "workflow": workflow_name,
            "target": target,
            "steps": []
        }
        
        if workflow_name == "domain_intel":
            self._run_domain_intel(target, results)
        elif workflow_name == "username_check":
            self._run_username_check(target, results)
        else:
            raise ValueError(f"Unknown workflow: {workflow_name}")
            
        return results

    def _run_domain_intel(self, target: str, results: Dict[str, Any]):
        """
        Workflow: theHarvester -> h8mail
        1. Find emails associated with domain.
        2. Check found emails for breaches.
        """
        # Step 1: theHarvester
        logger.info(f"Starting step 1: theHarvester for {target}")
        harvester_results = self.adapters["theharvester"].execute(target, {})
        results["steps"].append(harvester_results.to_dict())
        
        # Extract emails from entities
        emails = [e.value for e in harvester_results.entities if e.type == "email"]
        logger.info(f"Found {len(emails)} emails")
        
        # Step 2: h8mail (for each email found)
        # Note: In a real scenario, we might batch this or limit it.
        breach_results = []
        for email in emails:
            logger.info(f"Starting step 2: h8mail for {email}")
            h8_result = self.adapters["h8mail"].execute(email, {})
            breach_results.append(h8_result.to_dict())
            
        results["steps"].append({
            "tool": "h8mail_batch",
            "results": breach_results
        })

    def _run_username_check(self, target: str, results: Dict[str, Any]):
        """
        Workflow: Sherlock
        1. Check username across platforms.
        """
        # Step 1: Sherlock
        logger.info(f"Starting step 1: Sherlock for {target}")
        sherlock_results = self.adapters["sherlock"].execute(target, {})
        results["steps"].append(sherlock_results.to_dict())

    def _run_tool(self, tool_name: str, target: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Helper to run a tool with pre-flight checks and error handling.
        """
        if tool_name not in self.adapters:
            logger.warning(f"Tool {tool_name} not found in adapters.")
            return {"error": "Tool not found"}
            
        adapter = self.adapters[tool_name]
        
        if not adapter.can_run():
            logger.warning(f"Skipping {tool_name}: Tool not available (check installation/docker)")
            return {"skipped": True, "reason": "Not available"}
            
        try:
            logger.info(f"Running {tool_name} for {target}...")
            result = adapter.execute(target, config)
            return result.to_dict()
        except Exception as e:
            logger.error(f"{tool_name} failed: {e}")
            return {"error": str(e)}

    def run_all_tools(
        self, 
        target: str, 
        target_type: str, 
        domain: str = None, 
        email: str = None, 
        phone: str = None,
        file: str = None,
        stealth_mode: bool = False,
        username_variations: List[str] = None
    ) -> Dict[str, Any]:
        """
        Run all applicable tools based on target type and provided inputs.
        Implements "Smart Default" behavior by checking tool availability.
        """
        results = {
            "target": target,
            "target_type": target_type,
            "tool_results": {}
        }
        
        from src.core.input_validator import InputValidator

        # Common config for all adapters
        tool_config = {
            "stealth_mode": stealth_mode
        }

        # Define tool lists
        # Tuples of (tool_name, dependency_value)
        # If dependency_value is None, it runs on the main target
        individual_tools = [
            ("sherlock", None),
            ("holehe", email),
            ("h8mail", email),
            ("phoneinfoga", phone),
            ("exiftool", file)
        ]
        
        company_tools = [
            ("theharvester", "domain"),
            ("subfinder", "domain")
        ]

        # Determine domain for company tools
        target_domain = domain
        if target_type == "company" and not target_domain:
            try:
                InputValidator.validate_domain(target)
                target_domain = target
            except ValueError:
                pass

        # Select tools based on type
        tools_to_run = []
        if target_type == "individual":
            tools_to_run = individual_tools
        elif target_type == "company":
            tools_to_run = company_tools

        # Execute tools
        for tool_name, dependency in tools_to_run:
            # Determine execution target
            exec_target = target
            
            # Handle dependencies
            if dependency == "domain":
                if not target_domain:
                    continue # Skip if no domain
                exec_target = target_domain
            elif dependency is not None:
                if not dependency:
                    continue # Skip if dependency (email/phone) is missing
                exec_target = dependency

            # Special handling for Sherlock variations
            if tool_name == "sherlock" and username_variations:
                self._run_sherlock_with_variations(exec_target, tool_config, username_variations, results)
            else:
                # Standard execution
                results["tool_results"][tool_name] = self._run_tool(tool_name, exec_target, tool_config)

        return results

    def _run_sherlock_with_variations(self, target: str, config: Dict[str, Any], variations: List[str], results: Dict[str, Any]):
        """Helper to run Sherlock with variations."""
        if "sherlock" not in self.adapters:
            return

        adapter = self.adapters["sherlock"]
        if not adapter.can_run():
            results["tool_results"]["sherlock"] = {"skipped": True, "reason": "Not available"}
            return

        try:
            logger.info(f"Running Sherlock for {target}...")
            sherlock_res = adapter.execute(target, config)
            sherlock_res_dict = sherlock_res.to_dict()
            
            # Variations check
            if variations:
                logger.info(f"Running Sherlock for {len(variations)} variations...")
                sherlock_res_dict["variations"] = []
                for variant in variations:
                    try:
                        var_res = adapter.execute(variant, config)
                        # Check if entities exist
                        if var_res.entities:
                            sherlock_res_dict["variations"].append({
                                "variant": variant,
                                "results": var_res.to_dict()
                            })
                    except Exception as e:
                        logger.warning(f"Sherlock variation {variant} failed: {e}")
            
            results["tool_results"]["sherlock"] = sherlock_res_dict
        except Exception as e:
            logger.error(f"Sherlock failed: {e}")
            results["tool_results"]["sherlock"] = {"error": str(e)}

