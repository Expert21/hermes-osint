import ipaddress
import socket
from urllib.parse import urlparse
import logging

logger = logging.getLogger("OSINT_Tool")


class URLValidator:
    """Validate URLs to prevent SSRF and other attacks."""
    
    # Only allow HTTP and HTTPS schemes
    ALLOWED_SCHEMES = {'http', 'https'}
    
    # Block dangerous ports commonly used for internal services
    BLOCKED_PORTS = {
        22,    # SSH
        23,    # Telnet
        25,    # SMTP
        3306,  # MySQL
        5432,  # PostgreSQL
        6379,  # Redis
        27017, # MongoDB
        445,   # SMB
        143,   # IMAP
        110,   # POP3
        3389,  # RDP
        8080,  # Alternative HTTP (often internal)
    }
    
    @staticmethod
    def is_safe_url(url: str) -> bool:
        """
        Check if URL is safe for fetching.
        
        Prevents SSRF attacks by blocking:
        - Private IP addresses
        - Localhost/loopback addresses
        - Non-HTTP(S) schemes
        - Dangerous ports
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is safe, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Check scheme - only allow HTTP and HTTPS
            if parsed.scheme.lower() not in URLValidator.ALLOWED_SCHEMES:
                logger.warning(f"Blocked unsafe URL scheme: {parsed.scheme}")
                return False
            
            # Get hostname
            hostname = parsed.hostname
            if not hostname:
                logger.warning("URL has no hostname")
                return False
            
            # Check port
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            if port in URLValidator.BLOCKED_PORTS:
                logger.warning(f"Blocked dangerous port: {port} in URL: {url}")
                return False
            
            # Resolve hostname to IP address
            try:
                ip_str = socket.gethostbyname(hostname)
                ip = ipaddress.ip_address(ip_str)
                
                # Block private IP addresses (RFC 1918)
                # 10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16
                if ip.is_private:
                    logger.warning(f"Blocked private IP address: {ip}")
                    return False
                
                # Block loopback addresses (127.0.0.0/8)
                if ip.is_loopback:
                    logger.warning(f"Blocked loopback IP address: {ip}")
                    return False
                
                # Block link-local addresses (169.254.0.0/16)
                if ip.is_link_local:
                    logger.warning(f"Blocked link-local IP address: {ip}")
                    return False
                
                # Block multicast addresses
                if ip.is_multicast:
                    logger.warning(f"Blocked multicast IP address: {ip}")
                    return False
                
                # Block reserved addresses
                if ip.is_reserved:
                    logger.warning(f"Blocked reserved IP address: {ip}")
                    return False

                # Block Cloud Metadata Services (AWS, GCP, Azure, etc.)
                # 169.254.169.254 is the magic IP for instance metadata
                if str(ip) == "169.254.169.254":
                    logger.warning(f"Blocked cloud metadata IP: {ip}")
                    return False
                    
                # Block Shared Address Space (CGNAT) - 100.64.0.0/10
                if ip in ipaddress.ip_network("100.64.0.0/10"):
                    logger.warning(f"Blocked CGNAT IP address: {ip}")
                    return False
                
                # Block Benchmarking - 198.18.0.0/15
                if ip in ipaddress.ip_network("198.18.0.0/15"):
                    logger.warning(f"Blocked benchmarking IP address: {ip}")
                    return False
                
                # Block Test-Net - 192.0.2.0/24, 198.51.100.0/24, 203.0.113.0/24
                test_nets = ["192.0.2.0/24", "198.51.100.0/24", "203.0.113.0/24"]
                for net in test_nets:
                    if ip in ipaddress.ip_network(net):
                        logger.warning(f"Blocked test-net IP address: {ip}")
                        return False
                
                # Block IPv6 Unique Local Addresses (fc00::/7)
                if ip.version == 6 and ip in ipaddress.ip_network("fc00::/7"):
                    logger.warning(f"Blocked IPv6 ULA address: {ip}")
                    return False
                
            except socket.gaierror as e:
                logger.warning(f"Cannot resolve hostname '{hostname}': {e}")
                return False
            except ValueError as e:
                logger.warning(f"Invalid IP address for hostname '{hostname}': {e}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"URL validation error for '{url}': {e}")
            return False
    
    @staticmethod
    def validate_proxy(proxy: str) -> bool:
        """
        Validate proxy address format and IP.
        
        Args:
            proxy: Proxy in format "IP:PORT"
            
        Returns:
            True if proxy is valid and safe, False otherwise
        """
        import re
        
        # Match IP:PORT format with stricter regex
        # 0-255 per octet, 1-65535 for port
        ip_octet = r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
        pattern = r'^(' + ip_octet + r'\.' + ip_octet + r'\.' + ip_octet + r'\.' + ip_octet + r'):(\d{1,5})$'
        match = re.match(pattern, proxy)
        
        if not match:
            return False
        
        ip_str, port_str = match.groups()
        
        # Validate IP address
        try:
            ip = ipaddress.ip_address(ip_str)
            
            # Reject private IP addresses for proxies
            if ip.is_private:
                logger.debug(f"Rejected private IP proxy: {ip}")
                return False
            
            # Reject loopback addresses
            if ip.is_loopback:
                logger.debug(f"Rejected loopback proxy: {ip}")
                return False
            
            # Reject link-local addresses
            if ip.is_link_local:
                logger.debug(f"Rejected link-local proxy: {ip}")
                return False
                
        except ValueError:
            logger.debug(f"Invalid IP address in proxy: {ip_str}")
            return False
        
        # Validate port
        try:
            port = int(port_str)
            if port < 1 or port > 65535:
                logger.debug(f"Invalid port in proxy: {port}")
                return False
        except ValueError:
            return False
        
        return True
