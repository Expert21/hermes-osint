import re
import logging
from typing import List, Dict, Optional, Set
import dns.resolver
from validators import email as validate_email_format

logger = logging.getLogger("OSINT_Tool")


class EmailEnumerator:
    """
    Email enumeration module for generating and validating potential email addresses.
    Focuses on free, pattern-based enumeration without external API dependencies.
    """
    
    def __init__(self):
        self.common_patterns = [
            "{first}.{last}@{domain}",
            "{first}{last}@{domain}",
            "{first}_{last}@{domain}",
            "{first}-{last}@{domain}",
            "{first}@{domain}",
            "{last}@{domain}",
            "{f}{last}@{domain}",
            "{first}{l}@{domain}",
            "{f}.{last}@{domain}",
            "{first}.{l}@{domain}",
            "{last}.{first}@{domain}",
            "{last}{first}@{domain}",
        ]
        
        self.common_domains = [
            "gmail.com",
            "outlook.com",
            "yahoo.com",
            "hotmail.com",
            "protonmail.com",
            "icloud.com"
        ]
    
    def generate_email_patterns(
        self, 
        first_name: str, 
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
        custom_domains: Optional[List[str]] = None
    ) -> List[str]:
        """
        Generate potential email addresses based on name and domain.
        
        Args:
            first_name: First name of the target
            last_name: Last name of the target (optional)
            domain: Specific domain to check (e.g., company.com)
            custom_domains: List of custom domains to check
            
        Returns:
            List of potential email addresses
        """
        emails = set()
        
        # Normalize inputs
        first = first_name.lower().strip()
        last = last_name.lower().strip() if last_name else ""
        f = first[0] if first else ""
        l = last[0] if last else ""
        
        # Determine which domains to use
        domains_to_check = []
        if domain:
            domains_to_check.append(domain.lower().strip())
        if custom_domains:
            domains_to_check.extend([d.lower().strip() for d in custom_domains])
        if not domains_to_check:
            # Use common public domains if no specific domain provided
            domains_to_check = self.common_domains
        
        # Generate patterns
        for pattern in self.common_patterns:
            for dom in domains_to_check:
                try:
                    email = pattern.format(
                        first=first,
                        last=last,
                        f=f,
                        l=l,
                        domain=dom
                    )
                    
                    # Only add if it's a valid format
                    if self.validate_email_format(email):
                        emails.add(email)
                except (KeyError, IndexError):
                    # Skip patterns that don't have all required components
                    continue
        
        return sorted(list(emails))
    
    def validate_email_format(self, email: str) -> bool:
        """
        Validate email format using regex and validators library.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid format, False otherwise
        """
        # Basic regex pattern
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not re.match(pattern, email):
            return False
        
        # Use validators library for additional validation
        try:
            return validate_email_format(email) is True
        except:
            return False
    
    def verify_domain_mx_records(self, domain: str) -> bool:
        """
        Verify that a domain has valid MX (Mail Exchange) records.
        This indicates the domain can receive emails.
        
        Args:
            domain: Domain to check (e.g., company.com)
            
        Returns:
            True if domain has MX records, False otherwise
        """
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                logger.debug(f"✓ Domain {domain} has {len(mx_records)} MX record(s)")
                return True
            return False
        except dns.resolver.NXDOMAIN:
            logger.warning(f"✗ Domain {domain} does not exist")
            return False
        except dns.resolver.NoAnswer:
            logger.warning(f"✗ Domain {domain} has no MX records")
            return False
        except dns.resolver.Timeout:
            logger.warning(f"⚠ DNS timeout checking {domain}")
            return False
        except Exception as e:
            logger.error(f"✗ Error checking MX records for {domain}: {e}")
            return False
    
    def enumerate_emails(
        self,
        first_name: str,
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
        custom_domains: Optional[List[str]] = None,
        verify_mx: bool = True
    ) -> Dict[str, any]:
        """
        Main enumeration function that generates and validates email addresses.
        
        Args:
            first_name: First name of target
            last_name: Last name of target
            domain: Primary domain to check
            custom_domains: Additional domains to check
            verify_mx: Whether to verify MX records for domains
            
        Returns:
            Dictionary with enumeration results
        """
        logger.info(f"Starting email enumeration for: {first_name} {last_name or ''}")
        
        results = {
            "target_name": f"{first_name} {last_name or ''}".strip(),
            "emails_generated": [],
            "valid_format_count": 0,
            "domains_checked": [],
            "domains_with_mx": []
        }
        
        # Generate email patterns
        emails = self.generate_email_patterns(
            first_name=first_name,
            last_name=last_name,
            domain=domain,
            custom_domains=custom_domains
        )
        
        results["emails_generated"] = emails
        results["valid_format_count"] = len(emails)
        
        # Collect unique domains
        domains = set()
        for email in emails:
            domain_part = email.split('@')[1]
            domains.add(domain_part)
        
        results["domains_checked"] = sorted(list(domains))
        
        # Verify MX records if requested
        if verify_mx:
            logger.info(f"Verifying MX records for {len(domains)} domain(s)...")
            for dom in domains:
                if self.verify_domain_mx_records(dom):
                    results["domains_with_mx"].append(dom)
        
        logger.info(f"Email enumeration complete: {len(emails)} potential addresses generated")
        if verify_mx:
            logger.info(f"  {len(results['domains_with_mx'])}/{len(domains)} domains have valid MX records")
        
        return results


def run_email_enumeration(
    target_name: str,
    domain: Optional[str] = None,
    custom_domains: Optional[List[str]] = None,
    verify_mx: bool = True
) -> Dict[str, any]:
    """
    Convenience function to run email enumeration.
    
    Args:
        target_name: Full name of target (will be split into first/last)
        domain: Primary domain to check
        custom_domains: Additional domains to check
        verify_mx: Whether to verify MX records
        
    Returns:
        Dictionary with enumeration results
    """
    enumerator = EmailEnumerator()
    
    # Parse name
    name_parts = target_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
    
    return enumerator.enumerate_emails(
        first_name=first_name,
        last_name=last_name,
        domain=domain,
        custom_domains=custom_domains,
        verify_mx=verify_mx
    )
