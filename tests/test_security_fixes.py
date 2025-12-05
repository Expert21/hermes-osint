
import unittest
import tarfile
import os
import tempfile
import shutil
from unittest.mock import MagicMock, patch
from src.orchestration.docker_manager import DockerManager
from src.orchestration.security_error import SecurityError

class TestSecurityFixes(unittest.TestCase):
    def setUp(self):
        # Mock docker client to avoid connection attempts
        with patch('docker.from_env'):
            self.dm = DockerManager()
            # We don't need a real client for these tests
            self.dm.client = MagicMock()

    def test_zip_slip_prevention(self):
        """Test that _safe_extract prevents Zip Slip attacks."""
        # Create a temporary directory for extraction
        extract_dir = tempfile.mkdtemp()
        try:
            # Create a mock tar member with a malicious path
            malicious_member = tarfile.TarInfo(name="../evil.txt")
            
            # Verify that _safe_extract raises SecurityError
            with self.assertRaises(SecurityError):
                self.dm._safe_extract(MagicMock(), malicious_member, extract_dir)
                
            # Verify valid path works (mocking extract to do nothing)
            valid_member = tarfile.TarInfo(name="good.txt")
            mock_tar = MagicMock()
            self.dm._safe_extract(mock_tar, valid_member, extract_dir)
            mock_tar.extract.assert_called_once()
            
        finally:
            shutil.rmtree(extract_dir)

if __name__ == '__main__':
    unittest.main()
