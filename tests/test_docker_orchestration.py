
import sys
from unittest.mock import MagicMock, patch

# Mock docker module before importing modules that depend on it
sys.modules["docker"] = MagicMock()
sys.modules["docker.errors"] = MagicMock()

import unittest
from src.orchestration.docker_manager import DockerManager
from src.orchestration.adapters.sherlock_adapter import SherlockAdapter
from src.orchestration.adapters.theharvester_adapter import TheHarvesterAdapter
from src.orchestration.adapters.h8mail_adapter import H8MailAdapter
from src.orchestration.workflow_manager import WorkflowManager

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
        
        # Patch TRUSTED_IMAGES to allow test/image
        with patch.dict('src.orchestration.docker_manager.TRUSTED_IMAGES', {'test/image': 'test/image:latest'}):
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

    def test_h8mail_adapter_parsing(self):
        # Mock DockerManager
        mock_manager = MagicMock()
        # h8mail JSON output example
        mock_manager.run_container.return_value = """
        [INFO] Target: user@example.com
        {"target": "user@example.com", "breach": "Collection1", "email": "user@example.com"}
        {"target": "user@example.com", "breach": "ExploitIn", "email": "user@example.com"}
        """
        
        adapter = H8MailAdapter(mock_manager)
        results = adapter.execute("user@example.com", {})
        
        self.assertEqual(results['tool'], 'h8mail')
        self.assertEqual(len(results['breaches']), 2)
        self.assertEqual(results['breaches'][0]['breach'], 'Collection1')

    @patch('src.orchestration.workflow_manager.DockerManager')
    def test_workflow_manager_domain_intel(self, mock_docker_cls):
        # Setup mocks
        mock_docker = mock_docker_cls.return_value
        
        # Mock theHarvester output
        mock_docker.run_container.side_effect = [
            """
            [+] Emails found:
            user1@example.com
            """,
            """
            {"target": "user1@example.com", "breach": "Breach1"}
            """
        ]
        
        manager = WorkflowManager()
        # Inject mock docker manager into adapters (since they are created in __init__)
        manager.docker_manager = mock_docker
        manager.adapters["theharvester"].docker_manager = mock_docker
        manager.adapters["h8mail"].docker_manager = mock_docker
        
        results = manager.execute_workflow("domain_intel", "example.com")
        
        self.assertEqual(results['workflow'], 'domain_intel')
        self.assertEqual(len(results['steps']), 2)
        
        # Check step 1: theHarvester
        self.assertEqual(results['steps'][0]['tool'], 'theharvester')
        self.assertIn('user1@example.com', results['steps'][0]['emails'])
        
        # Check step 2: h8mail
        self.assertEqual(results['steps'][1]['tool'], 'h8mail_batch')
        self.assertEqual(len(results['steps'][1]['results']), 1)
        self.assertEqual(results['steps'][1]['results'][0]['breaches'][0]['breach'], 'Breach1')

if __name__ == '__main__':
    unittest.main()
