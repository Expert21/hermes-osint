"""
Investigation Exporter for Hermes Agent.

Bridges agent entity data to existing v2.1 report generators.
Supports: Markdown, PDF, HTML, CSV, STIX 2.1
"""

import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.core.entities import Entity, ToolResult

logger = logging.getLogger(__name__)


class AgentExporter:
    """
    Exports agent investigation data to various report formats.
    
    Converts Entity objects from agent sessions into the results
    format expected by v2.1 report generators.
    """
    
    SUPPORTED_FORMATS = {
        '.md': 'markdown',
        '.markdown': 'markdown',
        '.pdf': 'pdf',
        '.html': 'html',
        '.htm': 'html',
        '.csv': 'csv',
        '.json': 'stix',
        '.stix': 'stix',
    }
    
    def __init__(self):
        self.target = "Unknown"
        self.target_type = "unknown"
    
    def export(
        self,
        messages: List[Any],
        filename: str,
        format: Optional[str] = None
    ) -> bool:
        """
        Export investigation to file.
        
        Args:
            messages: Agent message history
            filename: Output file path
            format: Optional format override (md, pdf, html, csv, stix)
            
        Returns:
            True if export successful
        """
        path = Path(filename)
        
        # Determine format
        if format:
            fmt = format.lower()
        else:
            fmt = self.SUPPORTED_FORMATS.get(path.suffix.lower(), 'markdown')
        
        # Extract entities from messages
        entities = self._extract_entities(messages)
        
        # Build results dict for v2.1 generators
        results = self._entities_to_results(messages, entities)
        
        try:
            if fmt == 'markdown':
                return self._export_markdown(results, str(path))
            elif fmt == 'pdf':
                return self._export_pdf(results, str(path))
            elif fmt == 'html':
                return self._export_html(results, str(path))
            elif fmt == 'csv':
                return self._export_csv(results, str(path))
            elif fmt == 'stix':
                return self._export_stix(results, str(path))
            else:
                logger.error(f"Unsupported format: {fmt}")
                return False
        except Exception as e:
            logger.error(f"Export failed: {e}")
            return False
    
    def _extract_entities(self, messages: List[Any]) -> List[Entity]:
        """Extract all entities from conversation messages."""
        entities = []
        
        for msg in messages:
            content = getattr(msg, 'content', str(msg))
            # Look for tool results in message content
            # Entities are typically in tool response messages
            if hasattr(msg, 'role') and msg.role == 'tool':
                # Parse entity indicators from formatted output
                for line in content.split('\n'):
                    if line.strip().startswith('•') or line.strip().startswith('  •'):
                        # Extract type and value from formatted line
                        # Format: "  • [type] value"
                        parts = line.strip('• ').strip()
                        if parts.startswith('[') and ']' in parts:
                            type_end = parts.index(']')
                            entity_type = parts[1:type_end]
                            entity_value = parts[type_end+1:].strip()
                            entities.append(Entity(
                                type=entity_type,
                                value=entity_value,
                                source="agent_export"
                            ))
        
        return entities
    
    def _entities_to_results(
        self,
        messages: List[Any],
        entities: List[Entity]
    ) -> Dict[str, Any]:
        """Convert entities to v2.1 results format."""
        results = {
            'target': self.target,
            'target_type': self.target_type,
            'timestamp': datetime.now().isoformat(),
            'social_media': [],
            'emails': {'emails_generated': []},
            'domains': [],
            'breaches': [],
            'phone_info': {},
            'search_engines': [],
            'raw_output': '',
        }
        
        for entity in entities:
            if entity.type in ('account', 'GitHub', 'Twitter', 'Instagram', 
                              'Facebook', 'Reddit', 'LinkedIn'):
                results['social_media'].append({
                    'platform': entity.type if entity.type != 'account' else 'Unknown',
                    'url': entity.value,
                    'status': 'found',
                })
            elif entity.type == 'email':
                results['emails']['emails_generated'].append(entity.value)
            elif entity.type in ('domain', 'subdomain'):
                results['domains'].append({
                    'domain': entity.value,
                    'source': entity.metadata.get('source', 'unknown'),
                })
            elif entity.type == 'breach':
                results['breaches'].append({
                    'source': entity.value,
                    'data': entity.metadata,
                })
            elif entity.type == 'phone_info':
                results['phone_info'] = entity.metadata
        
        # Extract target from first user message
        for msg in messages:
            if hasattr(msg, 'role') and msg.role == 'user':
                self.target = msg.content[:50]
                break
        results['target'] = self.target
        
        return results
    
    def _export_markdown(self, results: Dict, filename: str) -> bool:
        """Export to Markdown format."""
        try:
            from src.reporting.markdown_report import generate_markdown_report
            generate_markdown_report(results, filename)
            logger.info(f"Exported Markdown report: {filename}")
            return True
        except ImportError:
            # Fallback: simple markdown
            return self._simple_markdown(results, filename)
    
    def _simple_markdown(self, results: Dict, filename: str) -> bool:
        """Simple markdown export fallback."""
        lines = [
            f"# Hermes OSINT Report",
            f"",
            f"**Target:** {results.get('target', 'Unknown')}",
            f"**Generated:** {results.get('timestamp', '')}",
            f"",
            "## Findings",
            "",
        ]
        
        if results.get('social_media'):
            lines.append("### Social Media Accounts")
            for sm in results['social_media']:
                lines.append(f"- [{sm.get('platform')}] {sm.get('url')}")
            lines.append("")
        
        if results.get('emails', {}).get('emails_generated'):
            lines.append("### Email Addresses")
            for email in results['emails']['emails_generated']:
                lines.append(f"- {email}")
            lines.append("")
        
        if results.get('domains'):
            lines.append("### Domains/Subdomains")
            for d in results['domains']:
                lines.append(f"- {d.get('domain')}")
            lines.append("")
        
        with open(filename, 'w') as f:
            f.write('\n'.join(lines))
        
        return True
    
    def _export_pdf(self, results: Dict, filename: str) -> bool:
        """Export to PDF format."""
        try:
            from src.reporting.pdf_report import generate_pdf_report
            generate_pdf_report(results, filename)
            logger.info(f"Exported PDF report: {filename}")
            return True
        except ImportError as e:
            logger.error(f"PDF export requires reportlab: {e}")
            return False
    
    def _export_html(self, results: Dict, filename: str) -> bool:
        """Export to HTML format."""
        try:
            from src.reporting.html_report import generate_html_report
            generate_html_report(results, filename)
            logger.info(f"Exported HTML report: {filename}")
            return True
        except ImportError as e:
            logger.error(f"HTML export failed: {e}")
            return False
    
    def _export_csv(self, results: Dict, filename: str) -> bool:
        """Export to CSV format."""
        try:
            from src.reporting.csv_report import generate_csv_report
            generate_csv_report(results, filename)
            logger.info(f"Exported CSV report: {filename}")
            return True
        except ImportError as e:
            logger.error(f"CSV export failed: {e}")
            return False
    
    def _export_stix(self, results: Dict, filename: str) -> bool:
        """Export to STIX 2.1 format."""
        try:
            from src.reporting.stix_export import generate_stix_report
            generate_stix_report(results, filename)
            logger.info(f"Exported STIX report: {filename}")
            return True
        except ImportError as e:
            logger.error(f"STIX export failed: {e}")
            return False
