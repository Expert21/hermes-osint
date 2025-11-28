<<<<<<< HEAD
import asyncio
from src.core.secrets_manager import SecretsManager
from src.core.proxy_manager import ProxyManager

async def test():
    sm = SecretsManager()
    pm = ProxyManager.load_from_env(sm)
    
    print("Provider count:", len(pm.providers))
    print("Stats:", pm.get_provider_stats())
    
    await pm.initialize()
    
    proxy = await pm.get_proxy()
    print("Proxy URL:", proxy)
    
    # Test if credentials are loaded
    print("\nCredentials check:")
    print("PROXY_PROVIDER:", sm.get_credential('PROXY_PROVIDER'))
    print("BRIGHTDATA_USERNAME:", sm.get_credential('BRIGHTDATA_USERNAME'))
    print("BRIGHTDATA_PASSWORD:", sm.get_credential('BRIGHTDATA_PASSWORD')[:10] + "..." if sm.get_credential('BRIGHTDATA_PASSWORD') else None)

asyncio.run(test())
=======
import asyncio
from src.core.secrets_manager import SecretsManager
from src.core.proxy_manager import ProxyManager

async def test():
    sm = SecretsManager()
    pm = ProxyManager.load_from_env(sm)
    
    print("Provider count:", len(pm.providers))
    print("Stats:", pm.get_provider_stats())
    
    await pm.initialize()
    
    proxy = await pm.get_proxy()
    print("Proxy URL:", proxy)
    
    # Test if credentials are loaded
    print("\nCredentials check:")
    print("PROXY_PROVIDER:", sm.get_credential('PROXY_PROVIDER'))
    print("BRIGHTDATA_USERNAME:", sm.get_credential('BRIGHTDATA_USERNAME'))
    print("BRIGHTDATA_PASSWORD:", sm.get_credential('BRIGHTDATA_PASSWORD')[:10] + "..." if sm.get_credential('BRIGHTDATA_PASSWORD') else None)

asyncio.run(test())
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
