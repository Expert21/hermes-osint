import pytest
import docker
from src.orchestration.docker_manager import DockerManager

def is_docker_available():
    try:
        client = docker.from_env()
        client.ping()
        return True
    except:
        return False

@pytest.mark.skipif(not is_docker_available(), reason="Docker is not available")
class TestDockerContainers:
    
    @pytest.fixture
    def docker_manager(self):
        return DockerManager()

    def test_hello_world(self, docker_manager):
        """Test running a simple container."""
        # We use a small image that is likely to be present or fast to pull
        # But DockerManager has a whitelist. We might need to bypass it or add a test image.
        # Let's see if we can use one of the trusted images or if we can mock the whitelist for this test.
        
        # In a real scenario, we'd want to test the actual tools.
        # But for this test suite, let's try to run 'python:3.9-slim' if it's in the list, or just mock the list.
        
        # Temporarily allow 'hello-world'
        original_trusted = docker_manager.TRUSTED_IMAGES.copy()
        docker_manager.TRUSTED_IMAGES['hello-world'] = 'hello-world'
        
        try:
            output = docker_manager.run_container("hello-world", "")
            assert "Hello from Docker!" in output
        finally:
            docker_manager.TRUSTED_IMAGES = original_trusted

    def test_container_cleanup(self, docker_manager):
        """Test that containers are removed after execution."""
        client = docker.from_env()
        initial_containers = len(client.containers.list(all=True))
        
        # Run a container
        original_trusted = docker_manager.TRUSTED_IMAGES.copy()
        docker_manager.TRUSTED_IMAGES['alpine'] = 'alpine'
        
        try:
            docker_manager.run_container("alpine", "echo test")
        except Exception:
            pass # Even if it fails, we check cleanup
        finally:
            docker_manager.TRUSTED_IMAGES = original_trusted
            
        final_containers = len(client.containers.list(all=True))
        assert final_containers == initial_containers

    def test_resource_limits(self, docker_manager):
        """Test that resource limits are applied (if possible to verify)."""
        # This is hard to verify from outside without inspecting the container config.
        # We can inspect the container object if we modify run_container to return it or if we mock the client.
        pass
