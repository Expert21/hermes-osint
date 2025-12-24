"""
Async wrapper for the Ollama Python client.
Provides health checking, error handling, and OSINT-focused defaults.
"""

import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OllamaConfig:
    """Configuration for Ollama client."""
    host: str = "http://localhost:11434"
    model: str = "llama3.2"
    timeout: float = 120.0  # LLM generation can be slow
    temperature: float = 0.7
    

class OllamaClient:
    """
    Async wrapper around the Ollama Python client.
    
    Provides connection health checking and graceful error handling
    for integration with Hermes OSINT.
    """
    
    def __init__(self, config: Optional[OllamaConfig] = None):
        """
        Initialize OllamaClient.
        
        Args:
            config: Optional configuration. Uses defaults if not provided.
        """
        self.config = config or OllamaConfig()
        self._client = None
        self._available: Optional[bool] = None
        
    def _get_client(self):
        """Lazy initialization of the Ollama client."""
        if self._client is None:
            try:
                from ollama import AsyncClient
                self._client = AsyncClient(host=self.config.host)
            except ImportError:
                logger.error("ollama package not installed. Run: pip install ollama")
                raise
        return self._client
    
    async def is_available(self) -> bool:
        """
        Check if Ollama server is running and accessible.
        
        Returns:
            True if Ollama is available, False otherwise.
        """
        if self._available is not None:
            return self._available
            
        try:
            client = self._get_client()
            # List models as a health check
            await client.list()
            self._available = True
            logger.info("Ollama server is available")
        except Exception as e:
            logger.warning(f"Ollama server not available: {e}")
            self._available = False
            
        return self._available
    
    async def list_models(self) -> list:
        """
        List available models on the Ollama server.
        
        Returns:
            List of available model names.
        """
        if not await self.is_available():
            return []
            
        try:
            client = self._get_client()
            response = await client.list()
            return [model.get("name", "") for model in response.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    async def generate(
        self,
        prompt: str,
        model: Optional[str] = None,
        system: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a response from the LLM.
        
        Args:
            prompt: The user prompt.
            model: Model to use (defaults to config model).
            system: Optional system prompt for context.
            
        Returns:
            Generated response text, or None if failed.
        """
        if not await self.is_available():
            logger.warning("Ollama not available, skipping generation")
            return None
            
        try:
            client = self._get_client()
            
            options = {
                "temperature": self.config.temperature,
            }
            
            response = await client.generate(
                model=model or self.config.model,
                prompt=prompt,
                system=system,
                options=options,
            )
            
            return response.get("response", "")
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return None
    
    async def chat(
        self,
        messages: list,
        model: Optional[str] = None
    ) -> Optional[str]:
        """
        Chat-style generation with message history.
        
        Args:
            messages: List of message dicts with 'role' and 'content'.
            model: Model to use (defaults to config model).
            
        Returns:
            Generated response text, or None if failed.
        """
        if not await self.is_available():
            logger.warning("Ollama not available, skipping chat")
            return None
            
        try:
            client = self._get_client()
            
            response = await client.chat(
                model=model or self.config.model,
                messages=messages,
            )
            
            return response.get("message", {}).get("content", "")
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return None
    
    def reset_availability(self):
        """Reset cached availability status to force a new check."""
        self._available = None
