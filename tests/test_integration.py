"""
Integration tests for the Hermes CLI.
These tests verify the main entry points work correctly.
"""
import pytest
import sys
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_doctor_command():
    """Test the --doctor command."""
    with patch('sys.argv', ['hermes', '--doctor']):
        with patch('src.core.doctor.HermesDoctor') as MockDoctor:
            # Import after patching argv
            from main import main_async
            
            mock_doc_instance = MockDoctor.return_value
            
            ret = await main_async()
            assert ret == 0
            mock_doc_instance.run_diagnostics.assert_called_once()
            mock_doc_instance.print_report.assert_called_once()

@pytest.mark.asyncio
async def test_list_profiles_command():
    """Test the --list-profiles command."""
    with patch('sys.argv', ['hermes', '--list-profiles']):
        with patch('src.core.config_manager.ConfigManager') as MockConfigManager:
            with patch('src.core.secrets_manager.SecretsManager'):
                with patch('src.core.proxy_manager.ProxyManager'):
                    # Import after patching
                    from main import main_async
                    
                    mock_cm_instance = MockConfigManager.return_value
                    mock_cm_instance.list_profiles.return_value = ['default', 'test']
                    
                    ret = await main_async()
                    assert ret == 0
                    mock_cm_instance.list_profiles.assert_called_once()

@pytest.mark.asyncio
async def test_create_profiles_command():
    """Test the --create-profiles command."""
    with patch('sys.argv', ['hermes', '--create-profiles']):
        with patch('src.core.config_manager.ConfigManager') as MockConfigManager:
            with patch('src.core.secrets_manager.SecretsManager'):
                with patch('src.core.proxy_manager.ProxyManager'):
                    # Import after patching
                    from main import main_async
                    
                    mock_cm_instance = MockConfigManager.return_value
                    
                    ret = await main_async()
                    assert ret == 0
                    mock_cm_instance.create_default_profile.assert_called_once()
                    mock_cm_instance.create_quick_scan_profile.assert_called_once()
                    mock_cm_instance.create_deep_scan_profile.assert_called_once()

@pytest.mark.asyncio
async def test_cache_stats_command():
    """Test the --cache-stats command."""
    with patch('sys.argv', ['hermes', '--cache-stats']):
        with patch('src.core.cache_manager.get_cache_manager') as mock_get_cache:
            with patch('src.core.secrets_manager.SecretsManager'):
                with patch('src.core.proxy_manager.ProxyManager'):
                    # Import after patching
                    from main import main_async
                    
                    mock_cache = mock_get_cache.return_value
                    mock_cache.get_stats.return_value = {'total_entries': 10}
                    
                    ret = await main_async()
                    assert ret == 0
                    mock_cache.get_stats.assert_called_once()
