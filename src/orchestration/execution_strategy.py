from abc import ABC, abstractmethod
from typing import Dict, Any, List, Union, Optional
import shutil
import logging
import subprocess
import os
from src.orchestration.docker_manager import DockerManager

logger = logging.getLogger(__name__)

class ExecutionStrategy(ABC):
    """
    Abstract base class for tool execution strategies.
    """
    
    @abstractmethod
    def is_available(self, tool_name: str) -> bool:
        """Check if the tool is available in this strategy."""
        pass

    @abstractmethod
    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        """
        Execute the tool.
        
        Args:
            tool_name: Name of the tool (e.g., 'sherlock')
            command: Command arguments list
            config: Configuration dictionary (including proxies)
            
        Returns:
            Output string (stdout/stderr)
        """
        pass

class DockerExecutionStrategy(ExecutionStrategy):
    """
    Executes tools using Docker containers.
    """
    
    def __init__(self, docker_manager: DockerManager):
        self.docker_manager = docker_manager
        # Map generic tool names to Docker image names
        self.tool_image_map = {
            "sherlock": "sherlock/sherlock",
            "theharvester": "secsi/theharvester",
            "h8mail": "khast3x/h8mail",
            "holehe": "holehe", # Placeholder, need actual image if different
            "phoneinfoga": "sundowndev/phoneinfoga",
            "sublist3r": "sublist3r", # Placeholder
            "photon": "photon", # Placeholder
            "exiftool": "exiftool" # Placeholder
        }

    def is_available(self, tool_name: str) -> bool:
        return self.docker_manager.is_available and tool_name in self.tool_image_map

    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        if not self.is_available(tool_name):
            raise RuntimeError(f"Tool {tool_name} not available in Docker mode")
            
        image_name = self.tool_image_map[tool_name]
        
        # Construct environment from config if present
        environment = {}
        if "proxy_url" in config:
            # SECURITY: Validate proxy URL to prevent injection
            proxy_url = config["proxy_url"]
            if not self._is_valid_proxy_url(proxy_url):
                logger.warning(f"Invalid proxy URL format: {proxy_url}. Skipping proxy configuration.")
            else:
                environment["HTTP_PROXY"] = proxy_url
                environment["HTTPS_PROXY"] = proxy_url
                environment["ALL_PROXY"] = proxy_url
        
        return self.docker_manager.run_container(
            image_name=image_name,
            command=command,
            environment=environment
        )
    
    def _is_valid_proxy_url(self, url: str) -> bool:
        """
        Validate proxy URL to prevent injection attacks.
        
        SECURITY: Ensures proxy URL is well-formed and uses allowed schemes.
        """
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # Must have a valid scheme
            if parsed.scheme not in ['http', 'https', 'socks4', 'socks5', 'socks4h', 'socks5h']:
                logger.warning(f"Invalid proxy scheme: {parsed.scheme}")
                return False
            
            # Must have a netloc (hostname:port)
            if not parsed.netloc:
                logger.warning("Proxy URL missing hostname")
                return False
            
            # Should not contain path, params, query, or fragment (suspicious)
            if any([parsed.path and parsed.path != '/', parsed.params, parsed.query, parsed.fragment]):
                logger.warning("Proxy URL contains suspicious components")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating proxy URL: {e}")
            return False

class NativeExecutionStrategy(ExecutionStrategy):
    """
    Executes tools using locally installed binaries.
    """
    
    def __init__(self):
        pass

    def is_available(self, tool_name: str) -> bool:
        """Check if the tool is in the system PATH."""
        return shutil.which(tool_name) is not None

    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        if not self.is_available(tool_name):
            raise RuntimeError(f"Tool {tool_name} not found locally")
            
        # Prepare environment
        env = os.environ.copy()
        if "proxy_url" in config:
            # SECURITY: Validate proxy URL to prevent injection
            proxy_url = config["proxy_url"]
            if not self._is_valid_proxy_url(proxy_url):
                logger.warning(f"Invalid proxy URL format: {proxy_url}. Skipping proxy configuration.")
            else:
                env["HTTP_PROXY"] = proxy_url
                env["HTTPS_PROXY"] = proxy_url
                env["ALL_PROXY"] = proxy_url

        logger.info(f"Executing native command: {tool_name} {' '.join(command)}")
        
        try:
            # Prepend tool name to command if it's not already there?
            # The adapters usually provide the full command args, but not the executable?
            # Let's assume 'command' is just the arguments.
            full_cmd = [tool_name] + command
            
            result = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                env=env,
                check=False # We handle return codes manually if needed
            )
            
            if result.returncode != 0:
                logger.warning(f"Native tool {tool_name} exited with code {result.returncode}")
                
            # Combine stdout and stderr
            return result.stdout + "\n" + result.stderr
            
        except Exception as e:
            logger.error(f"Native execution failed: {e}")
            raise

    def _is_valid_proxy_url(self, url: str, *, allow_onion: bool = False, max_addrs: int = 20) -> bool:
        """
        Hardened proxy URL validation.

        - Whitelists safe schemes.
        - Disallows userinfo (username:password@).
        - Normalizes hostnames via IDNA (punycode) to avoid unicode/homoglyph tricks.
        - If hostname is an IP literal, validates it directly.
        - Resolves ALL addresses (IPv4/IPv6) via getaddrinfo but caps number of returned addrs.
        - Blocks any resolved IP that is private, loopback, link-local, unspecified, or multicast.
        - Blocks explicit "unspecified" hosts like 0.0.0.0, ::, 0 and common localhost name aliases.
        - Rejects path/params/query/fragment except a bare "/" path.
        - Fail-closed on any unexpected error.
        """
        import ipaddress
        import socket
        from urllib.parse import urlparse

        try:
            parsed = urlparse(url)

            # 1) Scheme whitelist (normalized)
            allowed_schemes = {"http", "https", "socks4", "socks5", "socks4h", "socks5h"}
            scheme = (parsed.scheme or "").lower()
            if scheme not in allowed_schemes:
                logger.warning("Invalid proxy scheme: %s", parsed.scheme)
                return False

            # 2) Must have netloc/hostname
            if not parsed.netloc:
                logger.warning("Proxy URL missing hostname/netloc")
                return False

            # 3) Disallow userinfo (username/password)
            # urlparse exposes username/password properties; also check for '@' as a fallback
            if parsed.username or parsed.password or "@" in parsed.netloc:
                logger.warning("Proxy URL contains credentials or userinfo - rejected")
                return False

            # 4) Reject URLs with suspicious components
            if any([parsed.params, parsed.query, parsed.fragment]):
                logger.warning("Proxy URL contains params/query/fragment - rejected")
                return False
            if parsed.path and parsed.path not in ("", "/"):
                logger.warning("Proxy URL contains a non-trivial path - rejected")
                return False

            # 5) Extract host and port info robustly
            host = parsed.hostname  # Note: urlparse already handles bracketed IPv6
            port = parsed.port

            if not host:
                # fallback to raw netloc if parsing failed
                host = parsed.netloc
                # strip possible :port if present
                if ":" in host and host.count(":") == 1 and not host.startswith("["):
                    host, _, maybe_port = host.partition(":")
                    try:
                        port = int(maybe_port)
                    except Exception:
                        port = None

            # 6) Validate port range if given (1-65535)
            if port is not None:
                if not (1 <= port <= 65535):
                    logger.warning("Invalid port %r in proxy URL", port)
                    return False

            # 7) Normalize hostname using IDNA to mitigate unicode tricks / punycode
            try:
                # If it's an IPv6 literal or IPv4 literal, this will not change it.
                # idna.encode will raise for illegal hostnames; decode to str
                normalized_host = host.encode("idna").decode("ascii")
            except Exception:
                # If IDNA fails, reject — safer than attempting to accept weird unicode
                logger.warning("Hostname IDNA normalization failed for host: %r", host)
                return False

            # Lowercase normalized host for comparisons
            normalized_host_lc = normalized_host.lower()

            # 8) Block common localhost and ambiguous hostnames up-front
            blocked_hostnames = {
                "localhost", "localhost.localdomain", "ip6-localhost", "ip6-loopback",
                "broadcasthost", "loopback", "0", "0.0.0.0", "::", "::0"
            }
            if normalized_host_lc in blocked_hostnames:
                logger.warning("Proxy hostname is a blocked local/unspecified name: %s", normalized_host)
                return False

            # 9) Optionally block .onion (Tor) addresses unless explicitly allowed
            if not allow_onion and normalized_host_lc.endswith(".onion"):
                logger.warning("Proxy hostname is an .onion address and .onion is not allowed")
                return False

            # 10) If the host is an IP literal, validate it directly without DNS
            try:
                ip_obj = ipaddress.ip_address(normalized_host_lc)
                # Block private/loopback/link-local/multicast/unspecified
                if (
                    ip_obj.is_private
                    or ip_obj.is_loopback
                    or ip_obj.is_link_local
                    or ip_obj.is_multicast
                    or ip_obj.is_unspecified
                ):
                    logger.warning("Proxy IP literal %s rejected (private/loopback/link-local/multicast/unspecified)", ip_obj)
                    return False
                # Valid public IP literal
                return True
            except ValueError:
                # not an IP literal; proceed to DNS resolution
                pass

            # 11) Resolve the hostname to all addresses (AF_UNSPEC). Limit results to avoid DoS.
            try:
                addrinfo = socket.getaddrinfo(normalized_host, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM)
            except socket.gaierror as e:
                logger.warning("DNS resolution failed for host %s: %s", normalized_host, e)
                return False

            # Extract unique IP strings, preserving a deterministic order
            resolved_ips = []
            seen = set()
            for entry in addrinfo:
                # addrinfo tuple: (family, socktype, proto, canonname, sockaddr)
                sockaddr = entry[4]
                ip_str = sockaddr[0]
                if ip_str not in seen:
                    seen.add(ip_str)
                    resolved_ips.append(ip_str)
                if len(resolved_ips) >= max_addrs:
                    logger.warning("Too many DNS addresses for host %s; limiting to %d", normalized_host, max_addrs)
                    break

            if not resolved_ips:
                logger.warning("No A/AAAA records returned for host %s", normalized_host)
                return False

            # 12) Validate each resolved IP: reject private, loopback, link-local, multicast, unspecified
            for ip_str in resolved_ips:
                try:
                    ip = ipaddress.ip_address(ip_str)
                except ValueError:
                    logger.warning("Invalid IP returned from DNS for host %s: %s", normalized_host, ip_str)
                    return False

                if (
                    ip.is_private
                    or ip.is_loopback
                    or ip.is_link_local
                    or ip.is_multicast
                    or ip.is_unspecified
                ):
                    logger.warning("Resolved IP %s for host %s is private/loopback/link-local/multicast/unspecified; rejected",
                                   ip_str, normalized_host)
                    return False

            # 13) All checks passed
            return True

        except Exception as exc:
            # Fail-closed on unexpected errors
            logger.exception("Unexpected error validating proxy URL: %s", exc)
            return False



class HybridExecutionStrategy(ExecutionStrategy):
    """
    Auto-detects availability: prefers Native, falls back to Docker.
    """
    
    def __init__(self, docker_strategy: DockerExecutionStrategy, native_strategy: NativeExecutionStrategy):
        self.docker = docker_strategy
        self.native = native_strategy

    def is_available(self, tool_name: str) -> bool:
        return self.native.is_available(tool_name) or self.docker.is_available(tool_name)

    def execute(self, tool_name: str, command: List[str], config: Dict[str, Any]) -> str:
        if self.native.is_available(tool_name):
            logger.info(f"Hybrid: Using native {tool_name}")
            return self.native.execute(tool_name, command, config)
        elif self.docker.is_available(tool_name):
            logger.info(f"Hybrid: Falling back to Docker for {tool_name}")
            return self.docker.execute(tool_name, command, config)
        else:
            raise RuntimeError(f"Tool {tool_name} not available natively or in Docker")
