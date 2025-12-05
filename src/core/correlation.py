
import logging
from typing import List, Dict, Any, Set
from collections import defaultdict
from src.core.entities import Entity, Connection

logger = logging.getLogger("OSINT_Tool")

class CorrelationEngine:
    """
    Identifies and links related entities across different tool results.
    """

    def __init__(self):
        self.confidence_threshold = 0.7

    def correlate(self, entities: List[Entity]) -> List[Connection]:
        """
        Analyze a list of entities to find connections.

        Args:
            entities: List of all discovered entities from all tools.

        Returns:
            List of Connection objects representing identified relationships.
        """
        connections: List[Connection] = []
        
        # 1. Group by Value (Exact Matches)
        # Identifies the same entity found by multiple tools/sources
        value_groups = defaultdict(list)
        for entity in entities:
            value_groups[entity.value].append(entity)
            
        for value, group in value_groups.items():
            if len(group) > 1:
                # Create a connection for this group
                sources = sorted(list(set(e.source for e in group)))
                if len(sources) > 1:
                    connections.append(Connection(
                        type="exact_match",
                        source_entity=group[0], # Representative
                        target_entity=group[1], # Representative
                        relationship="same_entity",
                        confidence=1.0,
                        metadata={
                            "value": value,
                            "sources": sources,
                            "count": len(group),
                            "description": f"Entity '{value}' found in {len(sources)} different sources: {', '.join(sources)}"
                        }
                    ))

        # 2. Username Reuse (Cross-Platform)
        # Specifically for username entities
        usernames = [e for e in entities if e.type == "username"]
        username_groups = defaultdict(list)
        for u in usernames:
            username_groups[u.value].append(u)
            
        for username, group in username_groups.items():
            sources = sorted(list(set(e.source for e in group)))
            if len(sources) > 1:
                # We already caught exact matches above, but we can add a specific "username_reuse" connection
                # if we want to highlight it specifically for profiles.
                # To avoid duplicates with "exact_match", we can check if we want to enrich the metadata
                # or create a distinct high-value connection.
                
                # Let's create a specific one because it's high value for OSINT
                connections.append(Connection(
                    type="username_reuse",
                    source_entity=group[0],
                    target_entity=group[1], # Just linking two for the graph, or we could link all to a central node
                    relationship="cross_platform_identity",
                    confidence=0.9,
                    metadata={
                        "username": username,
                        "platforms": sources,
                        "description": f"Username '{username}' reused across {len(sources)} platforms"
                    }
                ))

        # 3. Domain Relationships (Email -> Domain)
        emails = [e for e in entities if e.type == "email"]
        domains = [e for e in entities if e.type == "domain"]
        
        for email in emails:
            if "@" in email.value:
                domain_part = email.value.split("@")[1]
                
                # Check if we have this domain in our results
                for domain in domains:
                    if domain.value == domain_part:
                        connections.append(Connection(
                            type="email_domain_link",
                            source_entity=email,
                            target_entity=domain,
                            relationship="belongs_to_domain",
                            confidence=1.0,
                            metadata={
                                "description": f"Email {email.value} belongs to domain {domain.value}"
                            }
                        ))

        logger.info(f"Correlation complete. Found {len(connections)} connections.")
        return connections
