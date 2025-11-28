import dns.resolver
import requests
import time
import logging
from typing import List, Dict, Set, Any

logger = logging.getLogger("OSINT_Tool")

class DomainEnumerator:
    """
    Module for Domain and Subdomain Enumeration.
    Includes DNS record retrieval, Certificate Transparency log analysis,
    and controlled subdomain bruteforcing.
    """

    def __init__(self, domain: str):
        self.domain = domain
        self.results = {
            "dns_records": {},
            "subdomains": set(),
            "ct_logs": []
        }
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 2
        self.resolver.lifetime = 2

    def run_all_checks(self, bruteforce: bool = False, wordlist: List[str] = None) -> Dict[str, Any]:
        """Run all domain enumeration checks."""
        logger.info(f"Starting domain enumeration for: {self.domain}")
        
        self.get_dns_records()
        self.get_ct_logs()
        
        if bruteforce:
            self.bruteforce_subdomains(wordlist)
            
        # Convert sets to lists for JSON serialization
        return {
            "domain": self.domain,
            "dns_records": self.results["dns_records"],
            "subdomains": list(self.results["subdomains"]),
            "subdomain_count": len(self.results["subdomains"])
        }

    def get_dns_records(self) -> Dict[str, List[str]]:
        """Retrieve common DNS records (A, AAAA, MX, TXT, NS, SOA)."""
        record_types = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'SOA', 'CNAME']
        
        logger.info(f"Retrieving DNS records for {self.domain}...")
        
        for r_type in record_types:
            try:
                answers = self.resolver.resolve(self.domain, r_type)
                records = []
                for rdata in answers:
                    records.append(str(rdata))
                self.results["dns_records"][r_type] = records
                logger.debug(f"Found {len(records)} {r_type} records")
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.NoNameservers):
                continue
            except Exception as e:
                logger.debug(f"Error retrieving {r_type} records: {e}")
                
        return self.results["dns_records"]

    def get_ct_logs(self) -> Set[str]:
        """
        Query Certificate Transparency logs via crt.sh to find subdomains.
        """
        logger.info(f"Querying Certificate Transparency logs for {self.domain}...")
        
        url = f"https://crt.sh/?q=%.{self.domain}&output=json"
        
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                count = 0
                for entry in data:
                    name_value = entry.get('name_value', '')
                    # Handle multi-line entries
                    subdomains = name_value.split('\n')
                    for sub in subdomains:
                        sub = sub.strip().lower()
                        # Remove wildcard asterisks
                        if sub.startswith('*.'):
                            sub = sub[2:]
                        
                        if sub.endswith(self.domain) and sub != self.domain:
                            self.results["subdomains"].add(sub)
                            count += 1
                
                logger.info(f"Found {count} subdomains from CT logs")
            else:
                logger.warning(f"crt.sh returned status code {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error querying CT logs: {e}")
            
        return self.results["subdomains"]

    def bruteforce_subdomains(self, wordlist: List[str] = None, delay: float = 0.5) -> Set[str]:
        """
        Active subdomain bruteforcing with rate limiting.
        
        Args:
            wordlist: List of subdomains to try. Defaults to a small common list.
            delay: Delay between requests in seconds to avoid rate limiting.
        """
        if wordlist is None:
            # Small default list of common subdomains
            wordlist = [
                'www', 'mail', 'remote', 'blog', 'webmail', 'server',
                'ns1', 'ns2', 'smtp', 'secure', 'vpn', 'm', 'shop',
                'ftp', 'admin', 'portal', 'dev', 'test', 'api', 'cdn'
            ]
            
        logger.info(f"Starting subdomain bruteforce ({len(wordlist)} attempts)...")
        logger.info(f"Using {delay}s delay between checks")
        
        found_count = 0
        
        for sub in wordlist:
            subdomain = f"{sub}.{self.domain}"
            
            # Skip if already found
            if subdomain in self.results["subdomains"]:
                continue
                
            try:
                # Try to resolve
                dns.resolver.resolve(subdomain, 'A')
                self.results["subdomains"].add(subdomain)
                logger.info(f"Found active subdomain: {subdomain}")
                found_count += 1
            except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer, dns.resolver.NoNameservers, dns.exception.Timeout):
                pass
            
            # Rate limiting delay
            time.sleep(delay)
            
        logger.info(f"Bruteforce complete. Found {found_count} new subdomains.")
        return self.results["subdomains"]

def run_domain_enumeration(domain: str, bruteforce: bool = False) -> Dict[str, Any]:
    """Convenience function to run domain enumeration."""
    enumerator = DomainEnumerator(domain)
    return enumerator.run_all_checks(bruteforce=bruteforce)
