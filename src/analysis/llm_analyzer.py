"""
High-level LLM analyzer for OSINT data aggregation and analysis.
"""

import logging
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field

from src.core.entities import Entity, ToolResult, Connection
from src.analysis.ollama_client import OllamaClient, OllamaConfig
from src.analysis import prompts

logger = logging.getLogger(__name__)


@dataclass
class AnalysisResult:
    """Result of LLM analysis on OSINT data."""
    summary: str = ""
    patterns: str = ""
    prioritized_leads: str = ""
    narrative: str = ""
    available: bool = True  # False if Ollama was unavailable
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary,
            "patterns": self.patterns,
            "prioritized_leads": self.prioritized_leads,
            "narrative": self.narrative,
            "available": self.available,
            "metadata": self.metadata
        }


class LLMAnalyzer:
    """
    Orchestrates LLM-powered analysis of OSINT results.
    
    Takes aggregated tool results and uses Ollama to:
    - Summarize findings
    - Identify patterns
    - Prioritize leads
    - Generate report narratives
    """
    
    def __init__(self, client: Optional[OllamaClient] = None, config: Optional[OllamaConfig] = None):
        """
        Initialize LLMAnalyzer.
        
        Args:
            client: Optional pre-configured OllamaClient.
            config: Optional OllamaConfig (used if client not provided).
        """
        self.client = client or OllamaClient(config)
    
    async def analyze(
        self,
        results: Dict[str, ToolResult],
        target: str = "unknown",
        include_patterns: bool = True,
        include_priorities: bool = True,
        include_narrative: bool = False
    ) -> AnalysisResult:
        """
        Perform comprehensive analysis on OSINT results.
        
        Args:
            results: Dictionary of tool name -> ToolResult.
            target: The original investigation target.
            include_patterns: Whether to run pattern analysis.
            include_priorities: Whether to run lead prioritization.
            include_narrative: Whether to generate full narrative.
            
        Returns:
            AnalysisResult containing all requested analysis.
        """
        if not await self.client.is_available():
            logger.warning("Ollama not available, returning empty analysis")
            return AnalysisResult(
                available=False,
                metadata={"error": "Ollama server not available"}
            )
        
        # Extract all entities from results
        all_entities = []
        for tool_name, result in results.items():
            if result and result.entities:
                all_entities.extend(result.entities)
        
        # Prepare data for prompts
        data_summary = self._prepare_data_summary(results)
        entities_summary = self._prepare_entities_summary(all_entities)
        
        analysis = AnalysisResult(metadata={"target": target, "entity_count": len(all_entities)})
        
        # Always generate summary
        analysis.summary = await self.summarize_findings(data_summary) or ""
        
        # Optional analyses
        if include_patterns and all_entities:
            analysis.patterns = await self.identify_patterns(entities_summary) or ""
            
        if include_priorities and all_entities:
            analysis.prioritized_leads = await self.prioritize_leads(data_summary) or ""
            
        if include_narrative:
            analysis.narrative = await self.generate_narrative(target, data_summary) or ""
        
        return analysis
    
    async def summarize_findings(self, data: str) -> Optional[str]:
        """
        Generate a concise summary of OSINT findings.
        
        Args:
            data: Formatted string representation of findings.
            
        Returns:
            Summary text or None if failed.
        """
        prompt = prompts.format_prompt(prompts.SUMMARIZE_FINDINGS, data=data)
        return await self.client.generate(prompt, system=prompts.SYSTEM_PROMPT)
    
    async def identify_patterns(self, entities: str) -> Optional[str]:
        """
        Identify patterns and connections in discovered entities.
        
        Args:
            entities: Formatted string representation of entities.
            
        Returns:
            Pattern analysis or None if failed.
        """
        prompt = prompts.format_prompt(prompts.IDENTIFY_PATTERNS, entities=entities)
        return await self.client.generate(prompt, system=prompts.SYSTEM_PROMPT)
    
    async def prioritize_leads(self, findings: str) -> Optional[str]:
        """
        Rank and prioritize leads by investigative value.
        
        Args:
            findings: Formatted string representation of findings.
            
        Returns:
            Prioritized leads or None if failed.
        """
        prompt = prompts.format_prompt(prompts.PRIORITIZE_LEADS, findings=findings)
        return await self.client.generate(prompt, system=prompts.SYSTEM_PROMPT)
    
    async def generate_narrative(self, target: str, data: str) -> Optional[str]:
        """
        Generate a professional report narrative.
        
        Args:
            target: Investigation target.
            data: Formatted findings data.
            
        Returns:
            Report narrative or None if failed.
        """
        prompt = prompts.format_prompt(prompts.GENERATE_NARRATIVE, target=target, data=data)
        return await self.client.generate(prompt, system=prompts.SYSTEM_PROMPT)
    
    def _prepare_data_summary(self, results: Dict[str, ToolResult]) -> str:
        """Format tool results for LLM consumption."""
        lines = []
        for tool_name, result in results.items():
            if result is None:
                continue
            lines.append(f"\n## {tool_name.upper()}")
            if result.error:
                lines.append(f"Error: {result.error}")
            elif result.entities:
                for entity in result.entities[:20]:  # Limit to avoid token overflow
                    lines.append(f"- [{entity.type}] {entity.value} (source: {entity.source})")
                if len(result.entities) > 20:
                    lines.append(f"... and {len(result.entities) - 20} more entities")
            else:
                lines.append("No entities found.")
        return "\n".join(lines)
    
    def _prepare_entities_summary(self, entities: List[Entity]) -> str:
        """Format entity list for LLM consumption."""
        if not entities:
            return "No entities found."
            
        # Group by type
        by_type: Dict[str, List[Entity]] = {}
        for entity in entities:
            by_type.setdefault(entity.type, []).append(entity)
        
        lines = []
        for entity_type, type_entities in by_type.items():
            lines.append(f"\n### {entity_type.upper()}")
            for entity in type_entities[:15]:  # Limit per type
                lines.append(f"- {entity.value} (from {entity.source})")
            if len(type_entities) > 15:
                lines.append(f"... and {len(type_entities) - 15} more")
                
        return "\n".join(lines)
