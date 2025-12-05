import unittest
from src.core.entities import Entity
from src.core.correlation import CorrelationEngine

class TestCorrelationEngine(unittest.TestCase):
    def setUp(self):
        self.engine = CorrelationEngine()

    def test_exact_match_correlation(self):
        entities = [
            Entity(type="username", value="jdoe", source="twitter"),
            Entity(type="username", value="jdoe", source="instagram"),
            Entity(type="username", value="other", source="github")
        ]
        
        connections = self.engine.correlate(entities)
        
        # Should find 1 exact match connection (jdoe on twitter <-> jdoe on instagram)
        # Plus potentially a username reuse connection
        
        # Filter for exact_match
        exact_matches = [c for c in connections if c.type == "exact_match"]
        self.assertEqual(len(exact_matches), 1)
        self.assertEqual(exact_matches[0].metadata['value'], "jdoe")
        self.assertEqual(len(exact_matches[0].metadata['sources']), 2)

    def test_username_reuse_correlation(self):
        entities = [
            Entity(type="username", value="hacker123", source="hackforums"),
            Entity(type="username", value="hacker123", source="reddit")
        ]
        
        connections = self.engine.correlate(entities)
        
        # Should find exact match AND username reuse
        reuse = [c for c in connections if c.type == "username_reuse"]
        self.assertEqual(len(reuse), 1)
        self.assertEqual(reuse[0].metadata['username'], "hacker123")

    def test_email_domain_link(self):
        entities = [
            Entity(type="email", value="admin@evilcorp.com", source="theharvester"),
            Entity(type="domain", value="evilcorp.com", source="subfinder")
        ]
        
        connections = self.engine.correlate(entities)
        
        links = [c for c in connections if c.type == "email_domain_link"]
        self.assertEqual(len(links), 1)
        self.assertEqual(links[0].source_entity.value, "admin@evilcorp.com")
        self.assertEqual(links[0].target_entity.value, "evilcorp.com")

    def test_no_correlation(self):
        entities = [
            Entity(type="username", value="user1", source="twitter"),
            Entity(type="username", value="user2", source="instagram")
        ]
        
        connections = self.engine.correlate(entities)
        self.assertEqual(len(connections), 0)

if __name__ == '__main__':
    unittest.main()
