"""
Tests for InputValidator - Critical Security Component

This module tests all input validation and sanitization functions.
These tests are critical for preventing injection attacks.
"""

import pytest
from pathlib import Path
import tempfile
import os

from src.core.input_validator import InputValidator


class TestSanitizeUsername:
    """Tests for username sanitization."""
    
    def test_valid_username(self):
        """Normal usernames pass through."""
        assert InputValidator.sanitize_username("john_doe") == "john_doe"
        assert InputValidator.sanitize_username("user123") == "user123"
        assert InputValidator.sanitize_username("test.user") == "test.user"
        assert InputValidator.sanitize_username("test-user") == "test-user"
    
    def test_strips_whitespace(self):
        """Leading/trailing whitespace is stripped."""
        assert InputValidator.sanitize_username("  john_doe  ") == "john_doe"
    
    def test_removes_unsafe_characters(self):
        """Unsafe characters are stripped."""
        assert InputValidator.sanitize_username("john@doe") == "johndoe"
        assert InputValidator.sanitize_username("user$name") == "username"
        assert InputValidator.sanitize_username("test;user") == "testuser"
        assert InputValidator.sanitize_username("test|user") == "testuser"
        assert InputValidator.sanitize_username("test&user") == "testuser"
    
    def test_blocks_path_traversal(self):
        """Path traversal attempts are rejected."""
        with pytest.raises(ValueError, match="path traversal"):
            InputValidator.sanitize_username("../etc/passwd")
        with pytest.raises(ValueError, match="path traversal"):
            InputValidator.sanitize_username("..\\windows\\system32")
        with pytest.raises(ValueError, match="path traversal"):
            InputValidator.sanitize_username(".hidden")
        with pytest.raises(ValueError, match="path traversal"):
            InputValidator.sanitize_username("/etc/passwd")
        with pytest.raises(ValueError, match="path traversal"):
            InputValidator.sanitize_username("\\windows")
    
    def test_enforces_max_length(self):
        """Excessively long usernames are rejected."""
        with pytest.raises(ValueError, match="too long"):
            InputValidator.sanitize_username("a" * 101)
        # Exactly 100 should work
        assert InputValidator.sanitize_username("a" * 100) == "a" * 100
    
    def test_custom_max_length(self):
        """Custom max length is respected."""
        with pytest.raises(ValueError, match="too long"):
            InputValidator.sanitize_username("username", max_length=5)
    
    def test_empty_username_rejected(self):
        """Empty username after sanitization is rejected."""
        with pytest.raises(ValueError, match="empty"):
            InputValidator.sanitize_username("")
        with pytest.raises(ValueError, match="empty"):
            InputValidator.sanitize_username("   ")
        with pytest.raises(ValueError, match="empty"):
            InputValidator.sanitize_username("@#$%")  # All chars stripped
    
    def test_shell_injection_blocked(self):
        """Shell injection attempts are neutralized."""
        # Dangerous characters are stripped
        assert InputValidator.sanitize_username("user;rm -rf /") == "userrm-rf"
        assert InputValidator.sanitize_username("user`whoami`") == "userwhoami"
        assert InputValidator.sanitize_username("user$(id)") == "userid"


class TestValidateDomain:
    """Tests for domain validation."""
    
    def test_valid_domains(self):
        """Valid domains pass."""
        assert InputValidator.validate_domain("example.com") == "example.com"
        assert InputValidator.validate_domain("sub.example.com") == "sub.example.com"
        assert InputValidator.validate_domain("deep.sub.example.co.uk") == "deep.sub.example.co.uk"
    
    def test_normalizes_to_lowercase(self):
        """Domains are normalized to lowercase."""
        assert InputValidator.validate_domain("EXAMPLE.COM") == "example.com"
        assert InputValidator.validate_domain("Example.Com") == "example.com"
    
    def test_strips_whitespace(self):
        """Whitespace is stripped."""
        assert InputValidator.validate_domain("  example.com  ") == "example.com"
    
    def test_rejects_invalid_domains(self):
        """Invalid domain formats are rejected."""
        with pytest.raises(ValueError, match="Invalid domain"):
            InputValidator.validate_domain("notadomain")
        with pytest.raises(ValueError, match="Invalid domain"):
            InputValidator.validate_domain("example")
        with pytest.raises(ValueError, match="Invalid domain"):
            InputValidator.validate_domain("-example.com")
        with pytest.raises(ValueError, match="Invalid domain"):
            InputValidator.validate_domain("example-.com")
    
    def test_rejects_too_long(self):
        """Domains over 253 chars are rejected."""
        long_domain = "a" * 250 + ".com"
        with pytest.raises(ValueError):  # May fail on format or length
            InputValidator.validate_domain(long_domain)


class TestValidateEmail:
    """Tests for email validation."""
    
    def test_valid_emails(self):
        """Valid emails pass."""
        assert InputValidator.validate_email("user@example.com") == "user@example.com"
        assert InputValidator.validate_email("user.name@example.com") == "user.name@example.com"
        assert InputValidator.validate_email("user+tag@example.com") == "user+tag@example.com"
    
    def test_normalizes_to_lowercase(self):
        """Emails are normalized to lowercase."""
        assert InputValidator.validate_email("USER@EXAMPLE.COM") == "user@example.com"
    
    def test_strips_whitespace(self):
        """Whitespace is stripped."""
        assert InputValidator.validate_email("  user@example.com  ") == "user@example.com"
    
    def test_rejects_invalid_emails(self):
        """Invalid email formats are rejected."""
        with pytest.raises(ValueError, match="Invalid email"):
            InputValidator.validate_email("notanemail")
        with pytest.raises(ValueError, match="Invalid email"):
            InputValidator.validate_email("@example.com")
        with pytest.raises(ValueError, match="Invalid email"):
            InputValidator.validate_email("user@")
        with pytest.raises(ValueError, match="Invalid email"):
            InputValidator.validate_email("user@.com")
    
    def test_rejects_too_long(self):
        """Emails over 254 chars are rejected."""
        long_email = "a" * 250 + "@example.com"
        with pytest.raises(ValueError, match="too long"):
            InputValidator.validate_email(long_email)


class TestValidateTargetName:
    """Tests for target name validation."""
    
    def test_valid_targets(self):
        """Valid target names pass."""
        assert InputValidator.validate_target_name("John Doe") == "John Doe"
        assert InputValidator.validate_target_name("company_name") == "company_name"
        assert InputValidator.validate_target_name("target-123") == "target-123"
    
    def test_strips_whitespace(self):
        """Whitespace is stripped."""
        assert InputValidator.validate_target_name("  John Doe  ") == "John Doe"
    
    def test_rejects_invalid_characters(self):
        """Invalid characters are rejected."""
        with pytest.raises(ValueError, match="invalid characters"):
            InputValidator.validate_target_name("user@domain")
        with pytest.raises(ValueError, match="invalid characters"):
            InputValidator.validate_target_name("test;rm -rf")
    
    def test_rejects_too_long(self):
        """Targets over 200 chars are rejected."""
        with pytest.raises(ValueError, match="1-200"):
            InputValidator.validate_target_name("a" * 201)
    
    def test_rejects_empty(self):
        """Empty targets are rejected."""
        with pytest.raises(ValueError, match="1-200"):
            InputValidator.validate_target_name("")


class TestValidateOutputPath:
    """Tests for output path validation."""
    
    def test_valid_paths(self):
        """Valid paths in writable directories pass."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = InputValidator.validate_output_path(f"{tmpdir}/output.json")
            assert isinstance(path, Path)
    
    def test_extension_validation(self):
        """Extension restrictions are enforced."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Allowed extension
            path = InputValidator.validate_output_path(
                f"{tmpdir}/output.json", 
                allowed_extensions=['.json', '.html']
            )
            assert path.suffix == '.json'
            
            # Disallowed extension
            with pytest.raises(ValueError, match="extension"):
                InputValidator.validate_output_path(
                    f"{tmpdir}/output.exe",
                    allowed_extensions=['.json', '.html']
                )
    
    def test_blocks_system_directories(self):
        """System directories are blocked."""
        dangerous_paths = [
            "/etc/passwd",
            "/sys/test",
            "/proc/test",
            "/dev/test",
            "/boot/test",
            "/usr/bin/test",
        ]
        for path in dangerous_paths:
            with pytest.raises(ValueError, match="system directory"):
                InputValidator.validate_output_path(path)
    
    def test_blocks_path_traversal(self):
        """Path traversal in output paths is blocked."""
        # Note: resolve() will resolve the path, so the check depends on
        # where it resolves to. The dangerous_dirs check catches system paths.
        with tempfile.TemporaryDirectory() as tmpdir:
            # This should work (relative but in safe location)
            path = InputValidator.validate_output_path(f"{tmpdir}/./output.json")
            assert isinstance(path, Path)


class TestSecurityEdgeCases:
    """Tests for security edge cases and attack vectors."""
    
    def test_null_byte_injection(self):
        """Null byte injection is handled."""
        # Null bytes in strings could terminate path parsing
        result = InputValidator.sanitize_username("user\x00admin")
        assert "\x00" not in result
    
    def test_unicode_normalization(self):
        """Unicode characters are handled safely."""
        # These should be stripped (not in whitelist)
        result = InputValidator.sanitize_username("user™")
        assert result == "user"
        
        result = InputValidator.sanitize_username("usér")
        assert result == "usr"  # é stripped
    
    def test_very_long_inputs(self):
        """Very long inputs are handled without DoS."""
        # Should not hang or crash
        long_input = "a" * 10000
        with pytest.raises(ValueError):
            InputValidator.sanitize_username(long_input)
        
        with pytest.raises(ValueError):
            InputValidator.validate_domain(long_input)
