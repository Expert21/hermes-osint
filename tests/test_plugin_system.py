import pytest
import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.core.plugin_manifest import PluginManifest
from src.core.plugin_loader import PluginLoader
from src.core.plugin_security_scanner import PluginSecurityScanner, ScanResult, SecurityViolation
from src.orchestration.execution_strategy import NativeExecutionStrategy, DockerExecutionStrategy

# Test Data
VALID_MANIFEST = {
    "name": "test_plugin",
    "version": "1.0.0",
    "plugin_type": "tool",
    "adapter_class": "test_plugin.adapter.TestAdapter",
    "tool_name": "test_tool",
    "description": "A test plugin",
    "author": "Tester",
    "supported_modes": ["native"]
}

@pytest.fixture
def mock_strategy():
    return MagicMock(spec=NativeExecutionStrategy)

@pytest.fixture
def loader(mock_strategy):
    return PluginLoader(mock_strategy)

def test_manifest_validation():
    # Valid
    m = PluginManifest.from_dict(VALID_MANIFEST)
    assert m.name == "test_plugin"
    
    # Invalid Type
    invalid = VALID_MANIFEST.copy()
    invalid["plugin_type"] = "invalid"
    with pytest.raises(ValueError):
        PluginManifest.from_dict(invalid)
        
    # Missing Tool Name for Tool Plugin
    invalid = VALID_MANIFEST.copy()
    del invalid["tool_name"]
    with pytest.raises(ValueError):
        PluginManifest.from_dict(invalid)

def test_security_scanner_pass(tmp_path):
    scanner = PluginSecurityScanner()
    
    # Safe code
    safe_code = """
class TestAdapter:
    def execute(self, target):
        return "safe"
"""
    p = tmp_path / "safe.py"
    p.write_text(safe_code, encoding='utf-8')
    
    result = scanner.scan_file(str(p), "tool")
    assert result.passed
    assert result.confidence == 1.0
    assert not result.errors

def test_security_scanner_fail(tmp_path):
    scanner = PluginSecurityScanner()
    
    # Unsafe code
    unsafe_code = """
import os
class TestAdapter:
    def execute(self, target):
        os.system("rm -rf /")
"""
    p = tmp_path / "unsafe.py"
    p.write_text(unsafe_code, encoding='utf-8')
    
    result = scanner.scan_file(str(p), "tool")
    assert not result.passed
    assert len(result.errors) > 0
    assert result.errors[0].rule == "Command Injection"

def test_plugin_discovery(loader, tmp_path):
    # Mock plugin directory
    plugin_dir = tmp_path / "plugins" / "test_plugin"
    plugin_dir.mkdir(parents=True)
    
    (plugin_dir / "plugin.json").write_text(json.dumps(VALID_MANIFEST))
    
    # Patch loader's plugin_dirs
    loader.plugin_dirs = [tmp_path / "plugins"]
    
    manifests = loader.discover_plugins()
    assert len(manifests) == 1
    assert manifests[0].name == "test_plugin"

def test_plugin_loading_security_check(loader, tmp_path):
    # Mock plugin
    plugin_dir = tmp_path / "plugins" / "unsafe_plugin"
    plugin_dir.mkdir(parents=True)
    
    manifest_data = VALID_MANIFEST.copy()
    manifest_data["name"] = "unsafe_plugin"
    (plugin_dir / "plugin.json").write_text(json.dumps(manifest_data))
    
    # Unsafe code
    (plugin_dir / "adapter.py").write_text("import os\nos.system('ls')", encoding='utf-8')
    
    loader.plugin_dirs = [tmp_path / "plugins"]
    
    # Should fail to load
    manifest = PluginManifest.from_dict(manifest_data)
    adapter = loader.load_plugin(manifest)
    assert adapter is None

def test_docker_image_registration():
    docker_manager = MagicMock()
    docker_manager.is_available = True
    strategy = DockerExecutionStrategy(docker_manager)
    
    # Register new image
    strategy.register_plugin_image("new_tool", "new/image")
    assert strategy.is_available("new_tool")
    assert strategy.plugin_image_map["new_tool"] == "new/image"
    
    # Try to override trusted
    with pytest.raises(ValueError):
        strategy.register_plugin_image("sherlock", "hacker/sherlock")
