import asyncio
import logging
import random
import secrets
from typing import List, Dict, Optional
from src.core.utils import SafeSoup
from urllib.parse import quote_plus
from src.core.async_request_manager import AsyncRequestManager

logger = logging.getLogger("OSINT_Tool")

class AsyncSearchEngineManager:
    """Manages multiple search engines with async execution"""
    
    def __init__(self):
        self.request_manager = AsyncRequestManager()
        self._playwright_available = self._check_playwright_available()
        self._playwright_warning_shown = False
    
    def _check_playwright_available(self) -> bool:
        """Check if Playwright is available"""
        try:
            import playwright
            return True
        except ImportError:
            return False

    async def _fetch_content(self, url: str, use_js: bool = False) -> Optional[str]:
        """Fetch content using AsyncRequestManager or Playwright"""
        if use_js:
            if not self._playwright_available:
                if not self._playwright_warning_shown:
                    logger.warning("Playwright not installed. Falling back to standard requests.")
                    self._playwright_warning_shown = True
                use_js = False
            else:
                try:
                    from playwright.async_api import async_playwright
                    async with async_playwright() as p:
                        # Launch with security settings
                        # SECURITY: Add timeout to prevent hanging
                        browser = await asyncio.wait_for(
                            p.chromium.launch(
                                headless=True,
                                args=[
                                    '--no-sandbox',
                                    '--disable-setuid-sandbox',
                                    '--disable-dev-shm-usage',
                                    '--disable-accelerated-2d-canvas',
                                    '--disable-gpu',
                                    '--disable-web-security',  # Only if needed for some OSINT targets
                                ]
                            ),
                            timeout=30.0
                        )
                        
                        context = await browser.new_context(
                            user_agent=secrets.choice(self.request_manager.user_agents),
                            viewport={'width': 1920, 'height': 1080},
                            ignore_https_errors=False,  # Enforce HTTPS validation
                            java_script_enabled=True,
                            accept_downloads=False,  # Prevent malicious downloads
                            bypass_csp=False,  # Respect CSP
                        )
                        
                        # Set additional security and anti-fingerprinting
                        await context.add_init_script("""
                            // Prevent fingerprinting
                            Object.defineProperty(navigator, 'webdriver', {get: () => false});
                        """)
                        
                        page = await context.new_page()
                        await page.goto(url, wait_until="networkidle", timeout=30000)
                        content = await page.content()
                        await browser.close()
                        return content
                except Exception as e:
                    logger.error(f"Playwright error: {e}")
                    use_js = False
        
        # Standard async request
        response = await self.request_manager.fetch(url)
        if response["ok"]:
            return response["text"]
        return None

    async def search_duckduckgo(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('div', class_='result')
            
            for result in search_results[:num_results]:
                title_elem = result.find('a', class_='result__a')
                snippet_elem = result.find('a', class_='result__snippet')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "DuckDuckGo",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        return results

    async def search_bing(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        encoded_query = quote_plus(query)
        url = f"https://www.bing.com/search?q={encoded_query}&count={num_results}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('li', class_='b_algo')
            
            for result in search_results[:num_results]:
                title_elem = result.find('h2')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('p')
                
                if link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "Bing",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"Bing search error: {e}")
        
        return results

    async def search_yahoo(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        encoded_query = quote_plus(query)
        url = f"https://search.yahoo.com/search?p={encoded_query}&n={num_results}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('div', class_='algo')
            
            for result in search_results[:num_results]:
                title_elem = result.find('h3', class_='title')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('div', class_='compText')
                
                if link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "Yahoo",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"Yahoo search error: {e}")
        
        return results

    async def search_brave(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        encoded_query = quote_plus(query)
        url = f"https://search.brave.com/search?q={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('div', class_='snippet')
            
            for result in search_results[:num_results]:
                title_elem = result.find('span', class_='snippet-title')
                link_elem = result.find('a', class_='result-header')
                snippet_elem = result.find('div', class_='snippet-description')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "Brave",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"Brave search error: {e}")
        
        return results

    async def search_startpage(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        encoded_query = quote_plus(query)
        url = f"https://www.startpage.com/do/search?query={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('div', class_='w-gl__result')
            
            for result in search_results[:num_results]:
                title_elem = result.find('a', class_='w-gl__result-title')
                snippet_elem = result.find('p', class_='w-gl__description')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "Startpage",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"Startpage search error: {e}")
        
        return results

    async def search_yandex(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        encoded_query = quote_plus(query)
        url = f"https://yandex.com/search/?text={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('li', class_='serp-item')
            
            for result in search_results[:num_results]:
                title_elem = result.find('h2', class_='organic__title-wrapper')
                link_elem = title_elem.find('a') if title_elem else None
                snippet_elem = result.find('div', class_='organic__text')
                
                if link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "Yandex",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"Yandex search error: {e}")
        
        return results

    async def search_all(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Run all search engines concurrently"""
        tasks = [
            self.search_duckduckgo(query, num_results, use_js),
            self.search_bing(query, num_results, use_js),
            self.search_yahoo(query, num_results, use_js),
            self.search_brave(query, num_results, use_js),
            self.search_startpage(query, num_results, use_js),
            self.search_yandex(query, num_results, use_js)
        ]
        
        logger.info(f"Launching async search for: {query}")
        results_list = await asyncio.gather(*tasks)
        
        # Flatten results
        all_results = []
        for engine_results in results_list:
            all_results.extend(engine_results)
            
        return all_results


async def run_search_engines_async(target: str, config: Dict, js_render: bool = False) -> List[Dict[str, str]]:
    """
    Async entry point for search engines.
    """
    search_manager = AsyncSearchEngineManager()
    all_results = []
    
    # Basic search
    logger.info(f"Running basic search for: {target}")
    basic_results = await search_manager.search_all(target, num_results=10, use_js=js_render)
    all_results.extend(basic_results)
    
    # Google Dorks
    dorks = [
        f'site:linkedin.com "{target}"',
        f'site:twitter.com "{target}"',
        f'site:facebook.com "{target}"',
        f'site:github.com "{target}"',
        f'site:instagram.com "{target}"',
        f'filetype:pdf "{target}"',
        f'inurl:about "{target}"',
        f'"{target}" email',
        f'"{target}" phone'
    ]
    
    logger.info(f"Running {len(dorks)} targeted dork queries...")
    
    # Run dorks in batches to avoid overwhelming the request manager
    batch_size = 3
    for i in range(0, len(dorks), batch_size):
        batch = dorks[i:i+batch_size]
        tasks = [search_manager.search_all(dork, num_results=5, use_js=js_render) for dork in batch]
        
        batch_results_list = await asyncio.gather(*tasks)
        
        for j, dork_results in enumerate(batch_results_list):
            # Add dork metadata
            for result in dork_results:
                result['query_type'] = 'dork'
                result['dork_query'] = batch[j]
            all_results.extend(dork_results)
            
        # Small delay between batches
        await asyncio.sleep(2)
    
    logger.info(f"Search complete: {len(all_results)} total results collected")
    return all_results