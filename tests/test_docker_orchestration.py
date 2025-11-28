<<<<<<< HEAD
import sys
from unittest.mock import MagicMock, patch

# Mock docker module before importing modules that depend on it
sys.modules["docker"] = MagicMock()
sys.modules["docker.errors"] = MagicMock()

import unittest
from src.orchestration.docker_manager import DockerManager
from src.orchestration.adapters.sherlock_adapter import SherlockAdapter
from src.orchestration.adapters.theharvester_adapter import TheHarvesterAdapter

class TestDockerOrchestration(unittest.TestCase):

    @patch('src.orchestration.docker_manager.docker')
    def test_docker_manager_connection(self, mock_docker):
        # Setup mock
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        
        # Test connection
        manager = DockerManager()
        self.assertTrue(manager.is_available)
        mock_docker.from_env.assert_called_once()
        mock_client.ping.assert_called_once()

    @patch('src.orchestration.docker_manager.docker')
    def test_run_container(self, mock_docker):
        # Setup mock
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Container Output"
        
        # Test run
        manager = DockerManager()
        output = manager.run_container("test/image", "echo hello")
        
        self.assertEqual(output, "Container Output")
        mock_client.containers.run.assert_called_once()
        mock_container.remove.assert_called_once()

    def test_sherlock_adapter_parsing(self):
        # Mock DockerManager
        mock_manager = MagicMock()
        mock_manager.run_container.return_value = """
[*] Checking username johndoe on:
[+] Instagram: https://www.instagram.com/johndoe
[+] Twitter: https://twitter.com/johndoe
[-] Facebook: Not Found
        """
        
        adapter = SherlockAdapter(mock_manager)
        results = adapter.execute("johndoe", {})
        
        self.assertEqual(results['tool'], 'sherlock')
        self.assertEqual(len(results['results']), 2)
        self.assertEqual(results['results'][0]['service'], 'Instagram')
        self.assertEqual(results['results'][0]['url'], 'https://www.instagram.com/johndoe')

    def test_theharvester_adapter_parsing(self):
        # Mock DockerManager
        mock_manager = MagicMock()
        mock_manager.run_container.return_value = """
*******************************************************************
*  _   _                                            _             *
* | |_| |__   ___    H a r v e s t e r    __      __ | |__   ___  *
*******************************************************************
[*] Target: example.com

[+] Emails found:
user1@example.com
user2@example.com

[+] Hosts found:
192.168.1.1: mail.example.com
        """
        
        adapter = TheHarvesterAdapter(mock_manager)
        results = adapter.execute("example.com", {})
        
        self.assertEqual(results['tool'], 'theharvester')
        self.assertEqual(len(results['emails']), 2)
        self.assertIn('user1@example.com', results['emails'])
        self.assertIn('user2@example.com', results['emails'])

if __name__ == '__main__':
    unittest.main()
=======
import sys
from unittest.mock import MagicMock, patch

# Mock docker module before importing modules that depend on it
sys.modules["docker"] = MagicMock()
sys.modules["docker.errors"] = MagicMock()

import unittest
from src.orchestration.docker_manager import DockerManager
from src.orchestration.adapters.sherlock_adapter import SherlockAdapter
from src.orchestration.adapters.theharvester_adapter import TheHarvesterAdapter

class TestDockerOrchestration(unittest.TestCase):

    @patch('src.orchestration.docker_manager.docker')
    def test_docker_manager_connection(self, mock_docker):
        # Setup mock
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        
        # Test connection
        manager = DockerManager()
        self.assertTrue(manager.is_available)
        mock_docker.from_env.assert_called_once()
        mock_client.ping.assert_called_once()

    @patch('src.orchestration.docker_manager.docker')
    def test_run_container(self, mock_docker):
        # Setup mock
        mock_client = MagicMock()
        mock_docker.from_env.return_value = mock_client
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_container.wait.return_value = {'StatusCode': 0}
        mock_container.logs.return_value = b"Container Output"
        
        # Test run
        manager = DockerManager()
        output = manager.run_container("sherlock/sherlock", "echo hello")
        
        self.assertEqual(output, "Container Output")
        mock_client.containers.run.assert_called_once()
        mock_container.remove.assert_called_once()

    def test_sherlock_adapter_parsing(self):
        # Mock DockerManager
        mock_manager = MagicMock()
        mock_manager.run_container.return_value = """
[*] Checking username johndoe on:
[+] Instagram: https://www.instagram.com/johndoe
[+] Twitter: https://twitter.com/johndoe
[-] Facebook: Not Found
        """
        
        adapter = SherlockAdapter(mock_manager)
        results = adapter.execute("johndoe", {})
        
        self.assertEqual(results['tool'], 'sherlock')
        self.assertEqual(len(results['results']), 2)
        self.assertEqual(results['results'][0]['service'], 'Instagram')
        self.assertEqual(results['results'][0]['url'], 'https://www.instagram.com/johndoe')

    def test_theharvester_adapter_parsing(self):
        # Mock DockerManager
        mock_manager = MagicMock()
        mock_manager.run_container.return_value = """
*******************************************************************
*  _   _                                            _             *
* | |_| |__   ___    H a r v e s t e r    __      __ | |__   ___  *
*******************************************************************
[*] Target: example.com

[+] Emails found:
user1@example.com
user2@example.com

[+] Hosts found:
192.168.1.1: mail.example.com
        """
        
        adapter = TheHarvesterAdapter(mock_manager)
        results = adapter.execute("example.com", {})
        
        self.assertEqual(results['tool'], 'theharvester')
        self.assertEqual(len(results['emails']), 2)
        self.assertIn('user1@example.com', results['emails'])
        self.assertIn('user2@example.com', results['emails'])

if __name__ == '__main__':
    unittest.main()
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
