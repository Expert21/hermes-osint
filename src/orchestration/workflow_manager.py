# -----------------------------------------------------------------------------
# Hermes OSINT - V2.0 Alpha
# This project is currently in an alpha state.
# -----------------------------------------------------------------------------

from typing import List, Dict, Any
import logging
from src.orchestration.docker_manager import DockerManager
from src.orchestration.execution_strategy import (
    ExecutionStrategy,
    DockerExecutionStrategy,
    NativeExecutionStrategy,
    HybridExecutionStrategy
)
from src.orchestration.adapters.sherlock_adapter import SherlockAdapter
from src.orchestration.adapters.theharvester_adapter import TheHarvesterAdapter
from src.orchestration.adapters.h8mail_adapter import H8MailAdapter
from src.orchestration.adapters.holehe_adapter import HoleheAdapter
from src.orchestration.adapters.phoneinfoga_adapter import PhoneInfogaAdapter
from src.orchestration.adapters.subfinder_adapter import SubfinderAdapter
from src.orchestration.adapters.searxng_adapter import SearxngAdapter
from src.orchestration.adapters.photon_adapter import PhotonAdapter
from src.orchestration.adapters.exiftool_adapter import ExiftoolAdapter

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
        self.adapters = {
            "sherlock": SherlockAdapter(self.execution_strategy),
            "theharvester": TheHarvesterAdapter(self.execution_strategy),
            "h8mail": H8MailAdapter(self.execution_strategy),
            "holehe": HoleheAdapter(self.execution_strategy),
            "phoneinfoga": PhoneInfogaAdapter(self.execution_strategy),
            "subfinder": SubfinderAdapter(self.execution_strategy),
            "searxng": SearxngAdapter(self.docker_manager),  # Service-based, needs DockerManager
            "photon": PhotonAdapter(self.execution_strategy),
            "exiftool": ExiftoolAdapter(self.execution_strategy)
        }

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
        results["steps"].append(harvester_results)
        
        emails = harvester_results.get("emails", [])
        logger.info(f"Found {len(emails)} emails")
        
        # Step 2: h8mail (for each email found)
        # Note: In a real scenario, we might batch this or limit it.
        breach_results = []
        for email in emails:
            logger.info(f"Starting step 2: h8mail for {email}")
            h8_result = self.adapters["h8mail"].execute(email, {})
            breach_results.append(h8_result)
            
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
        results["steps"].append(sherlock_results)
