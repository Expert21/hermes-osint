import re
import logging
import asyncio
from typing import List, Dict, Optional, Any
import dns.resolver
from validators import email as validate_email_format
from src.modules.passive_intelligence import PassiveIntelligenceModule

logger = logging.getLogger("OSINT_Tool")

class EmailEnumerator:
    """
    Email enumeration module with tiered intelligence (Passive -> Active).
    """
    
    def __init__(self):
        self.passive_module = PassiveIntelligenceModule()
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
        """Generate potential email addresses"""
        emails = set()
        first = first_name.lower().strip()
        last = last_name.lower().strip() if last_name else ""
        f = first[0] if first else ""
        l = last[0] if last else ""
        
        domains_to_check = []
        if domain:
            domains_to_check.append(domain.lower().strip())
        if custom_domains:
            domains_to_check.extend([d.lower().strip() for d in custom_domains])
        if not domains_to_check:
            domains_to_check = self.common_domains
        
        for pattern in self.common_patterns:
            for dom in domains_to_check:
                try:
                    email = pattern.format(
                        first=first, last=last, f=f, l=l, domain=dom
                    )
                    if self.validate_email_format(email):
                        emails.add(email)
                except (KeyError, IndexError):
                    continue
        
        return sorted(list(emails))
    
    def validate_email_format(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        try:
            return validate_email_format(email) is True
        except:
            return False
    
    def verify_domain_mx_records_sync(self, domain: str) -> bool:
        """Synchronous DNS check (to be run in executor)"""
        try:
            mx_records = dns.resolver.resolve(domain, 'MX')
            if mx_records:
                return True
            return False
        except Exception:
            return False

    async def verify_domain_mx_records(self, domain: str) -> bool:
        """Async wrapper for DNS check"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.verify_domain_mx_records_sync, domain)
    
    async def enumerate_emails(
        self,
        first_name: str,
        last_name: Optional[str] = None,
        domain: Optional[str] = None,
        custom_domains: Optional[List[str]] = None,
        verify_mx: bool = True,
        passive_only: bool = False
    ) -> Dict[str, Any]:
        """
        Async main enumeration function with tiered intelligence.
        """
        logger.info(f"Starting email enumeration for: {first_name} {last_name or ''}")
        
        results = {
            "target_name": f"{first_name} {last_name or ''}".strip(),
            "confirmed_emails": [], # High confidence (Passive confirmed)
            "possible_emails": [],  # Low confidence (Pattern generated)
            "domains_checked": [],
            "domains_with_mx": []
        }
        
        # 1. Generate Patterns
        generated_emails = self.generate_email_patterns(
            first_name=first_name,
            last_name=last_name,
            domain=domain,
            custom_domains=custom_domains
        )
        
        # 2. Passive Intelligence Check (Tier 1)
        logger.info(f"Checking {len(generated_emails)} emails against passive sources...")
        
        # We'll check passive sources for all generated emails
        # To avoid rate limits, we might want to batch this or prioritize
        # For now, let's check PGP for all (it's fast) and HIBP for top candidates if API key exists
        
        confirmed_set = set()
        
        # Check PGP for all generated emails (it's relatively cheap)
        pgp_tasks = [self.passive_module.query_pgp_keyservers(email) for email in generated_emails]
        pgp_results = await asyncio.gather(*pgp_tasks)
        
        for i, res in enumerate(pgp_results):
            if res:
                email = generated_emails[i]
                confirmed_set.add(email)
                results["confirmed_emails"].append({
                    "email": email,
                    "source": "PGP Keyserver",
                    "confidence": 1.0,
                    "details": res
                })

        # Check HIBP for top 5 most likely patterns if not already confirmed
        # (e.g. first.last, firstlast, f.last)
        likely_patterns = generated_emails[:5] 
        hibp_tasks = []
        hibp_emails = []
        
        for email in likely_patterns:
            if email not in confirmed_set:
                hibp_tasks.append(self.passive_module.check_breach_data(email))
                hibp_emails.append(email)
                
        if hibp_tasks:
            hibp_results = await asyncio.gather(*hibp_tasks)
            for i, breaches in enumerate(hibp_results):
                if breaches:
                    email = hibp_emails[i]
                    confirmed_set.add(email)
                    results["confirmed_emails"].append({
                        "email": email,
                        "source": "HIBP Breach Data",
                        "confidence": 1.0,
                        "details": {"breach_count": len(breaches)}
                    })

        # 3. Active Verification (Tier 2) - Skip if passive_only
        if not passive_only:
            # Filter domains for MX check
            domains = set()
            for email in generated_emails:
                domain_part = email.split('@')[1]
                domains.add(domain_part)
            
            results["domains_checked"] = sorted(list(domains))
            
            if verify_mx:
                logger.info(f"Verifying MX records for {len(domains)} domain(s)...")
                tasks = [self.verify_domain_mx_records(dom) for dom in domains]
                mx_results = await asyncio.gather(*tasks)
                
                valid_domains = set()
                for i, has_mx in enumerate(mx_results):
                    if has_mx:
                        valid_domains.add(list(domains)[i])
                        results["domains_with_mx"].append(list(domains)[i])
                
                # Add remaining emails to "possible" if domain has MX
                for email in generated_emails:
                    if email not in confirmed_set:
                        domain_part = email.split('@')[1]
                        if domain_part in valid_domains:
                            results["possible_emails"].append({
                                "email": email,
                                "source": "Pattern Generation",
                                "confidence": 0.5 # Medium confidence if MX exists
                            })
        else:
            # In passive mode, we don't check MX, so remaining are just "possible" with low confidence
            for email in generated_emails:
                if email not in confirmed_set:
                    results["possible_emails"].append({
                        "email": email,
                        "source": "Pattern Generation",
                        "confidence": 0.1 # Low confidence (unchecked)
                    })

        logger.info(f"Email enumeration complete: {len(results['confirmed_emails'])} confirmed, {len(results['possible_emails'])} possible")
        return results


async def run_email_enumeration_async(
    target_name: str,
    domain: Optional[str] = None,
    custom_domains: Optional[List[str]] = None,
    verify_mx: bool = True,
    passive_only: bool = False
) -> Dict[str, Any]:
    """
    Async convenience function.
    """
    enumerator = EmailEnumerator()
    
    name_parts = target_name.strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
    
    return await enumerator.enumerate_emails(
        first_name=first_name,
        last_name=last_name,
        domain=domain,
        custom_domains=custom_domains,
        verify_mx=verify_mx,
        passive_only=passive_only
    )
