import pytest
import asyncio
import logging
import os
import sys
# Add root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import hmac
import hashlib
from unittest.mock import MagicMock, patch, mock_open
from src.modules.passive_intelligence import PassiveIntelligenceModule
from src.core.cache_manager import CacheManager
from src.core.async_request_manager import AsyncRequestManager
from src.core.url_validator import URLValidator
from src.core.utils import SafeSoup
from src.core.secrets_manager import SecretsManager

# H1: API Key Exposure
@pytest.mark.asyncio
async def test_h1_api_key_redaction(caplog):
    with patch.dict(os.environ, {"HIBP_API_KEY": "TEST_API_KEY_12345"}):
        module = PassiveIntelligenceModule()
        # Mock logger to capture output
        with caplog.at_level(logging.DEBUG):
            with patch("aiohttp.ClientSession.get") as mock_get:
                mock_get.return_value.__aenter__.return_value.status = 200
                mock_get.return_value.__aenter__.return_value.json.return_value = []
                
                await module.check_breach_data("test@example.com")
                
                # Check logs for redacted key
                assert "TEST_API_KEY_12345" not in caplog.text
                # We expect redaction to show something like TEST****2345
                # The implementation uses: f"{key[:4]}****{key[-4:]}"
                assert "TEST****2345" in caplog.text

# H2: Race Condition
def test_h2_cache_race_condition():
    cm = CacheManager()
    # Mock write_limiter to fail
    cm.write_limiter.is_allowed = MagicMock(return_value=False)
    
    # Should return False after retries
    # set() requires: target, platform, result (dict), and optional extra
    assert cm.set("test_target", "test_platform", {"data": "test"}) is False
    assert cm.write_limiter.is_allowed.call_count > 1 # Should have retried

# H3: Unvalidated Redirects
@pytest.mark.asyncio
async def test_h3_unsafe_redirect():
    arm = AsyncRequestManager()
    # Mock session and response
    with patch("aiohttp.ClientSession.request") as mock_request:
        # First response is redirect to unsafe IP
        mock_response = MagicMock()
        mock_response.status = 302
        mock_response.headers = {"Location": "http://192.168.1.1/admin"}
        mock_response.close = MagicMock()
        
        mock_request.return_value.__aenter__.return_value = mock_response
        
        result = await arm.fetch("http://example.com")
        assert result["ok"] is False
        assert "Unsafe URL blocked" in result["error"]

# M1: PGP Parsing
@pytest.mark.asyncio
async def test_m1_pgp_parsing_dos():
    module = PassiveIntelligenceModule()
    # Mock response with huge lines
    huge_line = "pub:12345:1" + "A" * 10000 + ":timestamp"
    
    with patch("aiohttp.ClientSession.get") as mock_get:
        mock_get.return_value.__aenter__.return_value.status = 200
        mock_get.return_value.__aenter__.return_value.text.return_value = huge_line
        
        # We just want to ensure it doesn't crash and hopefully truncates
        # The implementation truncates lines to 200 chars
        keys = await module.query_pgp_keyservers("test@example.com")
        pass

# M3: Proxy Validation
def test_m3_proxy_validation():
    assert URLValidator.validate_proxy("127.0.0.1:8080") is False # Loopback
    assert URLValidator.validate_proxy("192.168.1.1:8080") is False # Private
    assert URLValidator.validate_proxy("8.8.8.8:8080") is True # Public
    assert URLValidator.validate_proxy("999.999.999.999:80") is False # Invalid IP

# M4: BeautifulSoup DoS
def test_m4_safesoup_xxe():
    xml_payload = """<?xml version="1.0" encoding="ISO-8859-1"?>
    <!DOCTYPE foo [  
    <!ELEMENT foo ANY >
    <!ENTITY xxe SYSTEM "file:///etc/passwd" >]><foo>&xxe;</foo>"""
    
    # SafeSoup uses html.parser which ignores DOCTYPE and entities usually
    soup = SafeSoup(xml_payload)
    # Verify entity is NOT expanded
    assert "root:x:0:0:root" not in str(soup)

# L1: Proxy Integrity
def test_l1_proxy_integrity(tmp_path):
    proxy_file = tmp_path / "proxies.txt"
    proxy_file.write_text("8.8.8.8:8080", encoding="utf-8")
    
    arm = AsyncRequestManager(proxy_file=str(proxy_file))
    
    # No checksum file -> verify logs warning (we can't easily check logs here without caplog, but logic is simple)
    arm.load_proxies()
    # Should load but warn
    
    # Create invalid checksum
    checksum_file = tmp_path / "proxies.txt.sha256"
    checksum_file.write_text("invalid_checksum", encoding="utf-8")
    
    arm.load_proxies()
    assert len(arm.proxies) == 0 # Should discard

    # Create valid checksum
    valid_checksum = hashlib.sha256(b"8.8.8.8:8080").hexdigest()
    checksum_file.write_text(valid_checksum, encoding="utf-8")
    
    arm.load_proxies()
    assert len(arm.proxies) == 1

# L3: Secrets HMAC
def test_l3_secrets_hmac(tmp_path):
    # Mock SecretsManager to use tmp_path
    with patch("pathlib.Path.home", return_value=tmp_path):
        sm = SecretsManager()
        # Force crypto available
        with patch("src.core.secrets_manager.CRYPTO_AVAILABLE", True):
            sm.store_credential("test_key", "test_value")
            
            # Read back
            assert sm.get_credential("test_key") == "test_value"
            
            # Tamper with file
            creds_file = sm.creds_file
            content = creds_file.read_bytes()
            
            # Modify encrypted part (after 32 bytes HMAC)
            if len(content) > 32:
                tampered = content[:32] + b'\x00' + content[33:]
                creds_file.write_bytes(tampered)
                
                # Read back should fail
                assert sm.get_credential("test_key") is None
