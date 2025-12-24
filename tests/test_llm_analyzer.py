"""
Unit tests for LLM analysis module.
Uses mocked Ollama responses to enable testing without a running server.
"""

import unittest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from src.core.entities import Entity, ToolResult
from src.analysis.ollama_client import OllamaClient, OllamaConfig
from src.analysis.llm_analyzer import LLMAnalyzer, AnalysisResult


class TestOllamaClient(unittest.TestCase):
    """Tests for OllamaClient."""
    
    def test_default_config(self):
        """Test client initializes with default config."""
        client = OllamaClient()
        self.assertEqual(client.config.host, "http://localhost:11434")
        self.assertEqual(client.config.model, "llama3.2")
        
    def test_custom_config(self):
        """Test client accepts custom config."""
        config = OllamaConfig(host="http://custom:8000", model="mistral")
        client = OllamaClient(config)
        self.assertEqual(client.config.host, "http://custom:8000")
        self.assertEqual(client.config.model, "mistral")
    
    def test_is_available_caches_result(self):
        """Test availability check is cached."""
        client = OllamaClient()
        client._available = True
        # Should return cached value without making request
        result = asyncio.run(client.is_available())
        self.assertTrue(result)
        
    def test_reset_availability(self):
        """Test availability cache can be reset."""
        client = OllamaClient()
        client._available = True
        client.reset_availability()
        self.assertIsNone(client._available)


class TestOllamaClientMocked(unittest.TestCase):
    """Tests for OllamaClient with mocked Ollama library."""
    
    @patch('src.analysis.ollama_client.OllamaClient._get_client')
    def test_is_available_returns_true_when_server_responds(self, mock_get_client):
        """Test availability check returns True when server responds."""
        mock_client = MagicMock()
        mock_client.list = AsyncMock(return_value={"models": []})
        mock_get_client.return_value = mock_client
        
        client = OllamaClient()
        result = asyncio.run(client.is_available())
        
        self.assertTrue(result)
        
    @patch('src.analysis.ollama_client.OllamaClient._get_client')
    def test_is_available_returns_false_on_error(self, mock_get_client):
        """Test availability check returns False on connection error."""
        mock_client = MagicMock()
        mock_client.list = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client
        
        client = OllamaClient()
        result = asyncio.run(client.is_available())
        
        self.assertFalse(result)
        
    @patch('src.analysis.ollama_client.OllamaClient._get_client')
    def test_generate_returns_response(self, mock_get_client):
        """Test generate returns LLM response."""
        mock_client = MagicMock()
        mock_client.list = AsyncMock(return_value={"models": []})
        mock_client.generate = AsyncMock(return_value={"response": "Test analysis result"})
        mock_get_client.return_value = mock_client
        
        client = OllamaClient()
        result = asyncio.run(client.generate("Analyze this data"))
        
        self.assertEqual(result, "Test analysis result")
        
    @patch('src.analysis.ollama_client.OllamaClient._get_client')
    def test_generate_returns_none_when_unavailable(self, mock_get_client):
        """Test generate returns None when Ollama unavailable."""
        mock_client = MagicMock()
        mock_client.list = AsyncMock(side_effect=Exception("Connection refused"))
        mock_get_client.return_value = mock_client
        
        client = OllamaClient()
        result = asyncio.run(client.generate("Analyze this data"))
        
        self.assertIsNone(result)


class TestLLMAnalyzer(unittest.TestCase):
    """Tests for LLMAnalyzer."""
    
    def _create_sample_results(self) -> dict:
        """Create sample ToolResult data for testing."""
        return {
            "sherlock": ToolResult(
                tool="sherlock",
                entities=[
                    Entity(type="username", value="jdoe", source="twitter"),
                    Entity(type="username", value="jdoe", source="github"),
                    Entity(type="url", value="https://twitter.com/jdoe", source="sherlock")
                ]
            ),
            "theharvester": ToolResult(
                tool="theharvester",
                entities=[
                    Entity(type="email", value="john@example.com", source="theharvester"),
                    Entity(type="domain", value="example.com", source="theharvester")
                ]
            )
        }
    
    def test_analysis_result_to_dict(self):
        """Test AnalysisResult serialization."""
        result = AnalysisResult(
            summary="Test summary",
            patterns="Test patterns",
            available=True
        )
        data = result.to_dict()
        
        self.assertEqual(data["summary"], "Test summary")
        self.assertEqual(data["patterns"], "Test patterns")
        self.assertTrue(data["available"])
        
    @patch.object(OllamaClient, 'is_available', new_callable=AsyncMock)
    def test_analyze_returns_unavailable_when_ollama_down(self, mock_available):
        """Test analyze returns unavailable result when Ollama is down."""
        mock_available.return_value = False
        
        analyzer = LLMAnalyzer()
        results = self._create_sample_results()
        analysis = asyncio.run(analyzer.analyze(results, target="testuser"))
        
        self.assertFalse(analysis.available)
        self.assertEqual(analysis.summary, "")
        
    @patch.object(OllamaClient, 'is_available', new_callable=AsyncMock)
    @patch.object(OllamaClient, 'generate', new_callable=AsyncMock)
    def test_analyze_generates_summary(self, mock_generate, mock_available):
        """Test analyze generates summary when Ollama is available."""
        mock_available.return_value = True
        mock_generate.return_value = "Analysis: Found username jdoe on multiple platforms."
        
        analyzer = LLMAnalyzer()
        results = self._create_sample_results()
        analysis = asyncio.run(analyzer.analyze(results, target="testuser"))
        
        self.assertTrue(analysis.available)
        self.assertIn("jdoe", analysis.summary)
        
    @patch.object(OllamaClient, 'is_available', new_callable=AsyncMock)
    @patch.object(OllamaClient, 'generate', new_callable=AsyncMock)
    def test_analyze_with_all_options(self, mock_generate, mock_available):
        """Test analyze with all analysis options enabled."""
        mock_available.return_value = True
        mock_generate.side_effect = [
            "Summary text",
            "Pattern analysis",
            "Priority list",
            "Full narrative"
        ]
        
        analyzer = LLMAnalyzer()
        results = self._create_sample_results()
        analysis = asyncio.run(analyzer.analyze(
            results,
            target="testuser",
            include_patterns=True,
            include_priorities=True,
            include_narrative=True
        ))
        
        self.assertEqual(analysis.summary, "Summary text")
        self.assertEqual(analysis.patterns, "Pattern analysis")
        self.assertEqual(analysis.prioritized_leads, "Priority list")
        self.assertEqual(analysis.narrative, "Full narrative")
        
    def test_prepare_data_summary_formats_correctly(self):
        """Test data summary preparation."""
        analyzer = LLMAnalyzer()
        results = self._create_sample_results()
        summary = analyzer._prepare_data_summary(results)
        
        self.assertIn("SHERLOCK", summary)
        self.assertIn("THEHARVESTER", summary)
        self.assertIn("jdoe", summary)
        self.assertIn("email", summary)
        
    def test_prepare_entities_summary_groups_by_type(self):
        """Test entity summary groups by entity type."""
        analyzer = LLMAnalyzer()
        entities = [
            Entity(type="username", value="user1", source="source1"),
            Entity(type="username", value="user2", source="source2"),
            Entity(type="email", value="test@test.com", source="source3")
        ]
        summary = analyzer._prepare_entities_summary(entities)
        
        self.assertIn("USERNAME", summary)
        self.assertIn("EMAIL", summary)
        self.assertIn("user1", summary)
        self.assertIn("test@test.com", summary)


if __name__ == '__main__':
    unittest.main()
