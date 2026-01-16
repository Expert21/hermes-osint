# -----------------------------------------------------------------------------
# Hermes OSINT - Plugin Loader
# -----------------------------------------------------------------------------

import os
import json
import logging
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

from src.core.plugin_manifest import PluginManifest
from src.core.plugin_security_scanner import PluginSecurityScanner
from src.orchestration.execution_strategy import ExecutionStrategy, DockerExecutionStrategy
from src.core.secrets_manager import SecretsManager

logger = logging.getLogger(__name__)

class PluginLoader:
    """
    Discovers, validates, and loads Hermes plugins.
    """

    def __init__(self, execution_strategy: ExecutionStrategy):
        self.execution_strategy = execution_strategy
        self.scanner = PluginSecurityScanner()
        self.secrets_manager = SecretsManager()
        
        # Plugin search paths
        self.plugin_dirs = [
            Path(__file__).parent.parent / "plugins",  # src/plugins/
            Path.home() / ".hermes" / "plugins"        # ~/.hermes/plugins/
        ]

    def discover_plugins(self) -> List[PluginManifest]:
        """
        Scan plugin directories for valid plugins.
        """
        manifests = []
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
                
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    manifest_path = item / "plugin.json"
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                data = json.load(f)
                            manifest = PluginManifest.from_dict(data)
                            manifests.append(manifest)
                        except Exception as e:
                            logger.warning(f"Failed to load manifest from {manifest_path}: {e}")
        return manifests

    def load_all_plugins(self) -> Dict[str, Any]:
        """
        Load all discovered and valid plugins.
        Returns a dictionary of {tool_name: adapter_instance}.
        """
        adapters = {}
        manifests = self.discover_plugins()
        
        for manifest in manifests:
            try:
                adapter = self.load_plugin(manifest)
                if adapter:
                    # Use tool_name as key for tool plugins, or name for core plugins
                    key = manifest.tool_name if manifest.plugin_type == "tool" else manifest.name
                    adapters[key] = adapter
                    logger.info(f"Successfully loaded plugin: {manifest.name} ({manifest.version})")
            except Exception as e:
                logger.error(f"Failed to load plugin {manifest.name}: {e}")
                
        return adapters

    def load_plugin(self, manifest: PluginManifest) -> Optional[Any]:
        """
        Load a specific plugin.
        """
        # 1. Find the plugin directory
        plugin_path = self._find_plugin_path(manifest.name)
        if not plugin_path:
            raise FileNotFoundError(f"Plugin directory for {manifest.name} not found")

        # 2. Security Scan
        adapter_file = plugin_path / "adapter.py"
        if not adapter_file.exists():
             # Try finding it based on class path if not standard
             # But for now assume standard structure or relative path
             pass

        # We need to resolve the file path for the adapter class
        # Assuming adapter_class is like "sherlock.adapter.SherlockAdapter"
        # and the file is at src/plugins/sherlock/adapter.py
        
        # Actually, let's rely on the file system structure.
        # If manifest was found at X/plugin.json, we expect code in X/
        
        # Scan all python files in the plugin directory
        for py_file in plugin_path.glob("**/*.py"):
            scan_result = self.scanner.scan_file(str(py_file), manifest.plugin_type)
            if not scan_result.passed:
                logger.error(f"Plugin {manifest.name} failed security scan in {py_file.name}")
                for error in scan_result.errors:
                    logger.error(f"  [ERROR] {error.message} (Line {error.line_number})")
                return None
            elif scan_result.warnings:
                logger.warning(f"Plugin {manifest.name} passed with warnings in {py_file.name}:")
                for warning in scan_result.warnings:
                    logger.warning(f"  [WARNING] {warning.message}")

        # 3. Register Docker Image (if applicable)
        if manifest.plugin_type == "tool" and manifest.docker_image:
            if isinstance(self.execution_strategy, DockerExecutionStrategy):
                try:
                    self.execution_strategy.register_plugin_image(manifest.tool_name, manifest.docker_image)
                except ValueError as e:
                    logger.warning(f"Could not register image for {manifest.name}: {e}")
            # If Hybrid, we might need to access the docker strategy inside it
            elif hasattr(self.execution_strategy, "docker") and isinstance(self.execution_strategy.docker, DockerExecutionStrategy):
                 try:
                    self.execution_strategy.docker.register_plugin_image(manifest.tool_name, manifest.docker_image)
                 except ValueError as e:
                    logger.warning(f"Could not register image for {manifest.name}: {e}")


        # 4. Import Module using safe file-based loading
        # SECURITY: Use spec_from_file_location to avoid sys.path pollution
        # This prevents module shadowing attacks (e.g., malicious logging.py)
        
        adapter_file = plugin_path / "adapter.py"
        if not adapter_file.exists():
            logger.error(f"Adapter file not found: {adapter_file}")
            return None
        
        try:
            # Generate unique module name to avoid conflicts
            module_name = f"hermes_plugin_{plugin_path.name}_adapter"
            
            # Load module directly from file path (no sys.path modification)
            spec = importlib.util.spec_from_file_location(
                module_name,
                str(adapter_file)
            )
            
            if spec is None or spec.loader is None:
                logger.error(f"Failed to create module spec for {adapter_file}")
                return None
            
            module = importlib.util.module_from_spec(spec)
            
            # Execute the module
            spec.loader.exec_module(module)
            
            # 5. Instantiate Class
            class_name = manifest.adapter_class.split(".")[-1]
            adapter_cls = getattr(module, class_name)
            
            # Standard ToolAdapter expects (execution_strategy)
            adapter_instance = adapter_cls(self.execution_strategy)
            
            return adapter_instance

        except ImportError as e:
            logger.error(f"Failed to import adapter for {manifest.name}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"Adapter class not found for {manifest.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error loading plugin {manifest.name}: {e}")
            return None

    def _find_plugin_path(self, plugin_name: str) -> Optional[Path]:
        for plugin_dir in self.plugin_dirs:
            if not plugin_dir.exists():
                continue
            # Check if directory with plugin name exists
            # Or check inside all dirs for a matching manifest name
            # Let's assume directory name matches plugin name for simplicity, 
            # OR scan all subdirs.
            
            # Scanning all subdirs is safer as dir name might differ
            for item in plugin_dir.iterdir():
                if item.is_dir():
                    manifest_path = item / "plugin.json"
                    if manifest_path.exists():
                        try:
                            with open(manifest_path, 'r') as f:
                                data = json.load(f)
                            if data.get("name") == plugin_name:
                                return item
                        except:
                            pass
        return None
