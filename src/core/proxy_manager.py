"""
Multi-provider proxy management system with automatic fallback.

Supports: BrightData, Smartproxy, Oxylabs, Webshare, Custom File, Custom API
"""

import aiohttp
import asyncio
import logging
import secrets
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


class ProxyProvider(Enum):
    """Supported proxy providers"""
    NONE = "none"
    BRIGHTDATA = "brightdata"
    SMARTPROXY = "smartproxy"
    OXYLABS = "oxylabs"
    WEBSHARE = "webshare"
    CUSTOM_FILE = "custom_file"
    CUSTOM_API = "custom_api"


class BaseProxyProvider(ABC):
    """Base class for all proxy providers"""
    
    def __init__(self, config: Dict[str, Any]):
        self.name = config.get('name', 'unnamed')
        self.config = config
        
    @abstractmethod
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        """Get a proxy URL"""
        pass
    
    @abstractmethod
    async def validate(self) -> bool:
        """Validate provider configuration"""
        pass
    
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        try:
            proxy = await self.get_proxy()
            return proxy is not None
        except Exception as e:
            logger.error(f"Health check failed for {self.name}: {e}")
            return False


class BrightDataProvider(BaseProxyProvider):
    """BrightData (formerly Luminati) proxy provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'brd.superproxy.io')
        self.port = config.get('port', '22225')
        self.username = config['username']
        self.password = config['password']
        self.country = config.get('country')
        self.session_type = config.get('session_type', 'rotating')
        
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        username = self.username
        
        if session_id and self.session_type == 'sticky':
            username = f"{username}-session-{session_id}"
        
        if self.country:
            username = f"{username}-country-{self.country}"
        
        return f"http://{username}:{self.password}@{self.host}:{self.port}"
    
    async def validate(self) -> bool:
        return bool(self.username and self.password)


class SmartproxyProvider(BaseProxyProvider):
    """Smartproxy provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'gate.smartproxy.com')
        self.port = config.get('port', '7000')
        self.username = config['username']
        self.password = config['password']
        self.country = config.get('country')
        
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        username = self.username
        
        if session_id:
            username = f"{username}-session-{session_id}"
        
        if self.country:
            username = f"{username}-country-{self.country}"
        
        return f"http://{username}:{self.password}@{self.host}:{self.port}"
    
    async def validate(self) -> bool:
        return bool(self.username and self.password)


class OxylabsProvider(BaseProxyProvider):
    """Oxylabs proxy provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get('host', 'pr.oxylabs.io')
        self.port = config.get('port', '7777')
        self.username = config['username']
        self.password = config['password']
        self.country = config.get('country')
        
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        username = self.username
        
        params = []
        if self.country:
            params.append(f"cc-{self.country}")
        if session_id:
            params.append(f"sessid-{session_id}")
        
        if params:
            username = f"customer-{username}-{'-'.join(params)}"
        
        return f"http://{username}:{self.password}@{self.host}:{self.port}"
    
    async def validate(self) -> bool:
        return bool(self.username and self.password)


class WebshareProvider(BaseProxyProvider):
    """Webshare.io proxy provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_key = config.get('api_key')
        self.proxy_list: List[Dict] = []
        self.proxy_index = 0
        
    async def _fetch_proxies(self):
        """Fetch proxy list from Webshare API"""
        if not self.api_key:
            return
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = {"Authorization": f"Token {self.api_key}"}
                async with session.get(
                    "https://proxy.webshare.io/api/v2/proxy/list/",
                    headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.proxy_list = data.get('results', [])
                        logger.info(f"Loaded {len(self.proxy_list)} Webshare proxies")
        except Exception as e:
            logger.error(f"Failed to fetch Webshare proxies: {e}")
    
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        if not self.proxy_list:
            await self._fetch_proxies()
        
        if not self.proxy_list:
            return None
        
        proxy = self.proxy_list[self.proxy_index % len(self.proxy_list)]
        self.proxy_index += 1
        
        return f"http://{proxy['username']}:{proxy['password']}@{proxy['proxy_address']}:{proxy['port']}"
    
    async def validate(self) -> bool:
        return bool(self.api_key)


class CustomFileProvider(BaseProxyProvider):
    """Load proxies from a file"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.file_path = config['file_path']
        self.proxies: List[str] = []
        self.format = config.get('format', 'ip:port')
        
    async def _load_proxies(self):
        """Load proxies from file"""
        try:
            with open(self.file_path, 'r') as f:
                lines = [line.strip() for line in f if line.strip()]
                
            for line in lines:
                if self.format == 'ip:port':
                    self.proxies.append(f"http://{line}")
                else:
                    self.proxies.append(f"http://{line}")
                    
            logger.info(f"Loaded {len(self.proxies)} proxies from {self.file_path}")
        except Exception as e:
            logger.error(f"Failed to load proxies from file: {e}")
    
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        if not self.proxies:
            await self._load_proxies()
        
        if not self.proxies:
            return None
        
        return secrets.choice(self.proxies)
    
    async def validate(self) -> bool:
        return bool(self.file_path)


class CustomAPIProvider(BaseProxyProvider):
    """Custom API endpoint for proxies"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.api_url = config['api_url']
        self.headers = config.get('headers', {})
        self.proxy_list: List[str] = []
        self.refresh_interval = config.get('refresh_interval', 300)
        self.last_refresh = 0
        
    async def _fetch_proxies(self):
        """Fetch proxies from custom API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, headers=self.headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.proxy_list = [f"http://{p}" for p in data.get('proxies', [])]
                        logger.info(f"Fetched {len(self.proxy_list)} proxies from custom API")
        except Exception as e:
            logger.error(f"Failed to fetch from custom API: {e}")
    
    async def get_proxy(self, session_id: Optional[str] = None) -> Optional[str]:
        import time
        
        if time.time() - self.last_refresh > self.refresh_interval:
            await self._fetch_proxies()
            self.last_refresh = time.time()
        
        if not self.proxy_list:
            return None
        
        return secrets.choice(self.proxy_list)
    
    async def validate(self) -> bool:
        return bool(self.api_url)


class ProxyManager:
    """Enterprise-grade proxy manager supporting multiple providers with fallback"""
    
    def __init__(self):
        self.providers: List[BaseProxyProvider] = []
        self.provider_health: Dict[str, bool] = {}
        self.current_provider_index = 0
        self.fallback_enabled = True
        
    def add_provider(self, provider_type: ProxyProvider, config: Dict[str, Any]):
        """Add a proxy provider"""
        provider_map = {
            ProxyProvider.BRIGHTDATA: BrightDataProvider,
            ProxyProvider.SMARTPROXY: SmartproxyProvider,
            ProxyProvider.OXYLABS: OxylabsProvider,
            ProxyProvider.WEBSHARE: WebshareProvider,
            ProxyProvider.CUSTOM_FILE: CustomFileProvider,
            ProxyProvider.CUSTOM_API: CustomAPIProvider,
        }
        
        if provider_type == ProxyProvider.NONE:
            logger.info("No proxy configured")
            return
        
        provider_class = provider_map.get(provider_type)
        if not provider_class:
            raise ValueError(f"Unknown provider type: {provider_type}")
        
        provider = provider_class(config)
        self.providers.append(provider)
        logger.info(f"Added proxy provider: {provider.name}")
    
    async def initialize(self):
        """Initialize and validate all providers"""
        for provider in self.providers:
            is_valid = await provider.validate()
            if not is_valid:
                logger.warning(f"Provider {provider.name} failed validation")
            else:
                logger.info(f"Provider {provider.name} validated successfully")
    
    async def health_check_all(self):
        """Run health checks on all providers"""
        for provider in self.providers:
            is_healthy = await provider.health_check()
            self.provider_health[provider.name] = is_healthy
            status = "✓" if is_healthy else "✗"
            logger.info(f"Provider {provider.name}: {status}")
    
    async def get_proxy(self, session_id: Optional[str] = None, preferred_provider: Optional[str] = None) -> Optional[str]:
        """Get a proxy from available providers with automatic fallback"""
        if not self.providers:
            return None
        
        # Try preferred provider first
        if preferred_provider:
            for provider in self.providers:
                if provider.name == preferred_provider:
                    try:
                        proxy = await provider.get_proxy(session_id)
                        if proxy:
                            return proxy
                    except Exception as e:
                        logger.debug(f"Preferred provider {preferred_provider} failed: {e}")
        
        # Try providers in order with fallback
        for i in range(len(self.providers)):
            provider = self.providers[self.current_provider_index % len(self.providers)]
            
            try:
                proxy = await provider.get_proxy(session_id)
                if proxy:
                    logger.debug(f"Using proxy from {provider.name}")
                    return proxy
            except Exception as e:
                logger.warning(f"Provider {provider.name} failed: {e}")
                
                if self.fallback_enabled:
                    self.current_provider_index += 1
                    continue
                else:
                    raise
        
        logger.error("All proxy providers failed")
        return None
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """Get statistics about configured providers"""
        return {
            "total_providers": len(self.providers),
            "providers": [
                {
                    "name": p.name,
                    "type": p.__class__.__name__,
                    "healthy": self.provider_health.get(p.name, False)
                }
                for p in self.providers
            ]
        }

    @staticmethod
    def load_from_config(config: Dict[str, Any]) -> 'ProxyManager':
        """Load proxy configuration from a dictionary"""
        manager = ProxyManager()
        
        providers = config.get('providers', [])
        providers.sort(key=lambda x: x.get('priority', 999))
        
        for provider_config in providers:
            if not provider_config.get('enabled', True):
                continue
            
            try:
                provider_type = ProxyProvider(provider_config['type'])
                provider_settings = provider_config.get('config', {})
                provider_settings['name'] = provider_config.get('name', provider_config['type'])
                
                manager.add_provider(provider_type, provider_settings)
            except ValueError as e:
                logger.warning(f"Skipping invalid proxy provider: {e}")
                
        return manager

    @staticmethod
    def load_from_env(secrets_manager=None) -> 'ProxyManager':
        """Load proxy configuration from environment variables or SecretsManager"""
        import os
        manager = ProxyManager()
        
        # Use SecretsManager if provided, otherwise fall back to os.getenv
        def get_env(key: str, default: str = None) -> str:
            if secrets_manager:
                value = secrets_manager.get_credential(key)
                return value if value else default
            return os.getenv(key, default)
        
        # Check for primary provider configuration
        provider_type_str = get_env('PROXY_PROVIDER', 'none')
        if provider_type_str:
            provider_type_str = provider_type_str.lower()
        else:
            provider_type_str = 'none'
        
        if provider_type_str == 'none':
            return manager
            
        try:
            provider_type = ProxyProvider(provider_type_str)
            
            if provider_type == ProxyProvider.BRIGHTDATA:
                manager.add_provider(ProxyProvider.BRIGHTDATA, {
                    'name': 'brightdata-env',
                    'username': get_env('BRIGHTDATA_USERNAME'),
                    'password': get_env('BRIGHTDATA_PASSWORD'),
                    'country': get_env('BRIGHTDATA_COUNTRY'),
                    'host': get_env('BRIGHTDATA_HOST', 'brd.superproxy.io'),
                    'port': get_env('BRIGHTDATA_PORT', '22225'),
                    'session_type': get_env('BRIGHTDATA_SESSION_TYPE', 'rotating')
                })
            
            elif provider_type == ProxyProvider.SMARTPROXY:
                manager.add_provider(ProxyProvider.SMARTPROXY, {
                    'name': 'smartproxy-env',
                    'username': get_env('SMARTPROXY_USERNAME'),
                    'password': get_env('SMARTPROXY_PASSWORD'),
                    'country': get_env('SMARTPROXY_COUNTRY'),
                    'host': get_env('SMARTPROXY_HOST', 'gate.smartproxy.com'),
                    'port': get_env('SMARTPROXY_PORT', '7000')
                })
                
            elif provider_type == ProxyProvider.OXYLABS:
                manager.add_provider(ProxyProvider.OXYLABS, {
                    'name': 'oxylabs-env',
                    'username': get_env('OXYLABS_USERNAME'),
                    'password': get_env('OXYLABS_PASSWORD'),
                    'country': get_env('OXYLABS_COUNTRY'),
                    'host': get_env('OXYLABS_HOST', 'pr.oxylabs.io'),
                    'port': get_env('OXYLABS_PORT', '7777')
                })
                
            elif provider_type == ProxyProvider.WEBSHARE:
                manager.add_provider(ProxyProvider.WEBSHARE, {
                    'name': 'webshare-env',
                    'api_key': get_env('WEBSHARE_API_KEY')
                })
            
            elif provider_type == ProxyProvider.CUSTOM_FILE:
                manager.add_provider(ProxyProvider.CUSTOM_FILE, {
                    'name': 'file-env',
                    'file_path': get_env('PROXY_FILE_PATH'),
                    'format': get_env('PROXY_FILE_FORMAT', 'ip:port')
                })
                
            elif provider_type == ProxyProvider.CUSTOM_API:
                manager.add_provider(ProxyProvider.CUSTOM_API, {
                    'name': 'api-env',
                    'api_url': get_env('PROXY_API_URL'),
                    'headers': {'Authorization': get_env('PROXY_API_TOKEN', '')} if get_env('PROXY_API_TOKEN') else {}
                })
                
        except ValueError:
            logger.warning(f"Unknown proxy provider in PROXY_PROVIDER: {provider_type_str}")
            
        return manager
