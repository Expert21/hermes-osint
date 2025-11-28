<<<<<<< HEAD
import asyncio
import logging
import random
import secrets
from typing import List, Dict, Optional
from src.core.utils import SafeSoup, Sanitizer
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

    def _validate_query(self, query: str) -> str:
        """Validate and truncate query length to prevent DoS."""
        MAX_QUERY_LENGTH = 500
        if len(query) > MAX_QUERY_LENGTH:
            logger.warning(f"Query truncated from {len(query)} to {MAX_QUERY_LENGTH} chars")
            return query[:MAX_QUERY_LENGTH]
        return query

    async def _fetch_content(self, url: str, use_js: bool = False) -> Optional[str]:
        """Fetch content using AsyncRequestManager or Playwright"""
        if use_js:
            if not self._playwright_available:
                if not self._playwright_warning_shown:
                    logger.warning("Playwright not installed. Falling back to standard requests.")
                    self._playwright_warning_shown = True
                use_js = False
            else:
                browser = None
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
                        return content
                except Exception as e:
                    logger.error(f"Playwright error: {e}")
                    use_js = False
                finally:
                    if browser:
                        await browser.close()  # ALWAYS cleanup
        
        # Standard async request
        response = await self.request_manager.fetch(url)
        if response["ok"]:
            return response["text"]
        return None

    async def search_duckduckgo(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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

    async def search_mojeek(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://www.mojeek.com/search?q={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('li', class_='result')
            
            for result in search_results[:num_results]:
                title_elem = result.find('a', class_='title')
                snippet_elem = result.find('p', class_='s')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "Mojeek",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"Mojeek search error: {e}")
        
        return results

    async def search_searxng(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        # Using a public instance for now, ideally configurable
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://searx.be/search?q={encoded_query}&format=json"
        
        try:
            # SearxNG supports JSON output
            response = await self.request_manager.fetch(url)
            if response["ok"]:
                data = response.get("json", {})
                for result in data.get('results', [])[:num_results]:
                    results.append({
                        "source": "SearxNG",
                        "title": result.get('title', ''),
                        "url": result.get('url', ''),
                        "description": result.get('content', '')
                    })
        except Exception as e:
            logger.error(f"SearxNG search error: {e}")
        
        return results

    async def search_publicwww(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://publicwww.com/websites/{encoded_query}/"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('tr')
            
            for result in search_results[:num_results]:
                link_elem = result.find('a')
                if link_elem and 'href' in link_elem.attrs:
                    link = link_elem['href']
                    title = link_elem.get_text(strip=True)
                    snippet_elem = result.find('td', class_='snippet') # Hypothetical class
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else f"Source code match for {query}"
                    
                    results.append({
                        "source": "PublicWWW",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"PublicWWW search error: {e}")
        
        return results

    async def search_wayback(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        # Wayback CDX API
        url = f"http://web.archive.org/cdx/search/cdx?url={query}*&output=json&limit={num_results}&collapse=urlkey"
        
        try:
            response = await self.request_manager.fetch(url)
            if response["ok"]:
                data = response.get("json", [])
                if data and len(data) > 1: # Header is first row
                    for row in data[1:]:
                        # format: urlkey, timestamp, original, mimetype, statuscode, digest, length
                        original_url = row[2]
                        timestamp = row[1]
                        wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                        
                        results.append({
                            "source": "Wayback Machine",
                            "title": f"Snapshot: {timestamp}",
                            "url": wayback_url,
                            "description": f"Archived version of {original_url}"
                        })
        except Exception as e:
            logger.error(f"Wayback Machine search error: {e}")
        
        return results

    async def search_archive_today(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://archive.today/search/?q={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('div', class_='TEXT-BLOCK')
            
            for result in search_results[:num_results]:
                link_elem = result.find('a')
                if link_elem:
                    link = link_elem.get('href', '')
                    title = link_elem.get_text(strip=True)
                    
                    results.append({
                        "source": "Archive.today",
                        "title": title,
                        "url": link,
                        "description": "Archived snapshot"
                    })
        except Exception as e:
            logger.error(f"Archive.today search error: {e}")
        
        return results

    async def search_commoncrawl(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        # Using Common Crawl Index API (latest index)
        # Note: This usually requires a specific index ID, defaulting to a recent one or generic endpoint if available
        # For simplicity/stability, we might skip complex index lookup and use a known index or a different provider
        # Using a public CC search interface or API wrapper is better. 
        # Fallback to a simpler implementation or placeholder if direct API is too complex for this snippet.
        # Let's use the index server directly for a domain search
        
        index_url = "https://index.commoncrawl.org/CC-MAIN-2023-50-index?url={query}/*&output=json&limit={num_results}"
        # NOTE: Index changes. Ideally we fetch the latest index list first.
        
        try:
            # Quick fetch of latest index
            idx_list_resp = await self.request_manager.fetch("https://index.commoncrawl.org/collinfo.json")
            if idx_list_resp["ok"]:
                indexes = idx_list_resp.get("json", [])
                if indexes:
                    latest_idx = indexes[0]['id']
                    url = f"https://index.commoncrawl.org/{latest_idx}-index?url={query}/*&output=json&limit={num_results}"
                    
                    response = await self.request_manager.fetch(url)
                    if response["ok"]:
                        # Response is line-delimited JSON
                        for line in response["text"].strip().split('\n'):
                            if not line: continue
                            try:
                                record = line # It's actually JSON string, need to parse if not auto-parsed
                                import json
                                data = json.loads(line)
                                
                                results.append({
                                    "source": "Common Crawl",
                                    "title": f"Crawl Record: {data.get('timestamp')}",
                                    "url": data.get('url'),
                                    "description": f"Mime: {data.get('mime')}, Status: {data.get('status')}"
                                })
                            except: pass
        except Exception as e:
            logger.error(f"Common Crawl search error: {e}")
            
        return results

    async def search_custom(self, engine_config: Dict, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        try:
            name = engine_config.get('name', 'Custom')
            url_template = engine_config.get('url')
            selectors = engine_config.get('selectors', {})
            
            if not url_template or not selectors:
                return []
                
            query = self._validate_query(query)
            encoded_query = quote_plus(query)
            url = url_template.replace('{query}', encoded_query)
            
            html_content = await self._fetch_content(url, use_js)
            if not html_content:
                return []
                
            soup = SafeSoup(html_content)
            container_sel = selectors.get('container')
            
            if container_sel:
                search_results = soup.select(container_sel)
                for result in search_results[:num_results]:
                    title_sel = selectors.get('title')
                    link_sel = selectors.get('link')
                    snippet_sel = selectors.get('snippet')
                    
                    title = result.select_one(title_sel).get_text(strip=True) if title_sel and result.select_one(title_sel) else "No Title"
                    
                    link = ""
                    if link_sel:
                        link_elem = result.select_one(link_sel)
                        if link_elem:
                            link = link_elem.get('href', '')
                            
                    snippet = result.select_one(snippet_sel).get_text(strip=True) if snippet_sel and result.select_one(snippet_sel) else ""
                    
                    if link:
                        results.append({
                            "source": name,
                            "title": title,
                            "url": link,
                            "description": snippet
                        })
        except Exception as e:
            logger.error(f"Custom engine search error: {e}")
            
        return results

    async def search_all(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Run all search engines concurrently"""
        tasks = [
            self.search_duckduckgo(query, num_results, use_js),
            self.search_bing(query, num_results, use_js),
            self.search_yahoo(query, num_results, use_js),
            self.search_brave(query, num_results, use_js),
            self.search_startpage(query, num_results, use_js),
            self.search_yandex(query, num_results, use_js),
            self.search_mojeek(query, num_results, use_js),
            self.search_searxng(query, num_results, use_js),
            self.search_publicwww(query, num_results, use_js),
            self.search_wayback(query, num_results, use_js),
            self.search_archive_today(query, num_results, use_js),
            self.search_commoncrawl(query, num_results, use_js)
        ]
        
        logger.info(f"Launching async search for: {Sanitizer.truncate(query)}")
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
    logger.info(f"Running basic search for: {Sanitizer.truncate(target)}")
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
=======
import asyncio
import logging
import random
import secrets
from typing import List, Dict, Optional
from src.core.utils import SafeSoup, Sanitizer
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

    def _validate_query(self, query: str) -> str:
        """Validate and truncate query length to prevent DoS."""
        MAX_QUERY_LENGTH = 500
        if len(query) > MAX_QUERY_LENGTH:
            logger.warning(f"Query truncated from {len(query)} to {MAX_QUERY_LENGTH} chars")
            return query[:MAX_QUERY_LENGTH]
        return query

    async def _fetch_content(self, url: str, use_js: bool = False) -> Optional[str]:
        """Fetch content using AsyncRequestManager or Playwright"""
        if use_js:
            if not self._playwright_available:
                if not self._playwright_warning_shown:
                    logger.warning("Playwright not installed. Falling back to standard requests.")
                    self._playwright_warning_shown = True
                use_js = False
            else:
                browser = None
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
                        return content
                except Exception as e:
                    logger.error(f"Playwright error: {e}")
                    use_js = False
                finally:
                    if browser:
                        await browser.close()  # ALWAYS cleanup
        
        # Standard async request
        response = await self.request_manager.fetch(url)
        if response["ok"]:
            return response["text"]
        return None

    async def search_duckduckgo(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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
        query = self._validate_query(query)
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

    async def search_mojeek(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://www.mojeek.com/search?q={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('li', class_='result')
            
            for result in search_results[:num_results]:
                title_elem = result.find('a', class_='title')
                snippet_elem = result.find('p', class_='s')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    link = title_elem.get('href', '')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else ""
                    
                    results.append({
                        "source": "Mojeek",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"Mojeek search error: {e}")
        
        return results

    async def search_searxng(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        # Using a public instance for now, ideally configurable
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://searx.be/search?q={encoded_query}&format=json"
        
        try:
            # SearxNG supports JSON output
            response = await self.request_manager.fetch(url)
            if response["ok"]:
                data = response.get("json", {})
                for result in data.get('results', [])[:num_results]:
                    results.append({
                        "source": "SearxNG",
                        "title": result.get('title', ''),
                        "url": result.get('url', ''),
                        "description": result.get('content', '')
                    })
        except Exception as e:
            logger.error(f"SearxNG search error: {e}")
        
        return results

    async def search_publicwww(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://publicwww.com/websites/{encoded_query}/"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('tr')
            
            for result in search_results[:num_results]:
                link_elem = result.find('a')
                if link_elem and 'href' in link_elem.attrs:
                    link = link_elem['href']
                    title = link_elem.get_text(strip=True)
                    snippet_elem = result.find('td', class_='snippet') # Hypothetical class
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else f"Source code match for {query}"
                    
                    results.append({
                        "source": "PublicWWW",
                        "title": title,
                        "url": link,
                        "description": snippet
                    })
        except Exception as e:
            logger.error(f"PublicWWW search error: {e}")
        
        return results

    async def search_wayback(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        # Wayback CDX API
        url = f"http://web.archive.org/cdx/search/cdx?url={query}*&output=json&limit={num_results}&collapse=urlkey"
        
        try:
            response = await self.request_manager.fetch(url)
            if response["ok"]:
                data = response.get("json", [])
                if data and len(data) > 1: # Header is first row
                    for row in data[1:]:
                        # format: urlkey, timestamp, original, mimetype, statuscode, digest, length
                        original_url = row[2]
                        timestamp = row[1]
                        wayback_url = f"https://web.archive.org/web/{timestamp}/{original_url}"
                        
                        results.append({
                            "source": "Wayback Machine",
                            "title": f"Snapshot: {timestamp}",
                            "url": wayback_url,
                            "description": f"Archived version of {original_url}"
                        })
        except Exception as e:
            logger.error(f"Wayback Machine search error: {e}")
        
        return results

    async def search_archive_today(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        query = self._validate_query(query)
        encoded_query = quote_plus(query)
        url = f"https://archive.today/search/?q={encoded_query}"
        
        html_content = await self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = SafeSoup(html_content)
            search_results = soup.find_all('div', class_='TEXT-BLOCK')
            
            for result in search_results[:num_results]:
                link_elem = result.find('a')
                if link_elem:
                    link = link_elem.get('href', '')
                    title = link_elem.get_text(strip=True)
                    
                    results.append({
                        "source": "Archive.today",
                        "title": title,
                        "url": link,
                        "description": "Archived snapshot"
                    })
        except Exception as e:
            logger.error(f"Archive.today search error: {e}")
        
        return results

    async def search_commoncrawl(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        # Using Common Crawl Index API (latest index)
        # Note: This usually requires a specific index ID, defaulting to a recent one or generic endpoint if available
        # For simplicity/stability, we might skip complex index lookup and use a known index or a different provider
        # Using a public CC search interface or API wrapper is better. 
        # Fallback to a simpler implementation or placeholder if direct API is too complex for this snippet.
        # Let's use the index server directly for a domain search
        
        index_url = "https://index.commoncrawl.org/CC-MAIN-2023-50-index?url={query}/*&output=json&limit={num_results}"
        # NOTE: Index changes. Ideally we fetch the latest index list first.
        
        try:
            # Quick fetch of latest index
            idx_list_resp = await self.request_manager.fetch("https://index.commoncrawl.org/collinfo.json")
            if idx_list_resp["ok"]:
                indexes = idx_list_resp.get("json", [])
                if indexes:
                    latest_idx = indexes[0]['id']
                    url = f"https://index.commoncrawl.org/{latest_idx}-index?url={query}/*&output=json&limit={num_results}"
                    
                    response = await self.request_manager.fetch(url)
                    if response["ok"]:
                        # Response is line-delimited JSON
                        for line in response["text"].strip().split('\n'):
                            if not line: continue
                            try:
                                record = line # It's actually JSON string, need to parse if not auto-parsed
                                import json
                                data = json.loads(line)
                                
                                results.append({
                                    "source": "Common Crawl",
                                    "title": f"Crawl Record: {data.get('timestamp')}",
                                    "url": data.get('url'),
                                    "description": f"Mime: {data.get('mime')}, Status: {data.get('status')}"
                                })
                            except: pass
        except Exception as e:
            logger.error(f"Common Crawl search error: {e}")
            
        return results

    async def search_custom(self, engine_config: Dict, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        results = []
        try:
            name = engine_config.get('name', 'Custom')
            url_template = engine_config.get('url')
            selectors = engine_config.get('selectors', {})
            
            if not url_template or not selectors:
                return []
                
            query = self._validate_query(query)
            encoded_query = quote_plus(query)
            url = url_template.replace('{query}', encoded_query)
            
            html_content = await self._fetch_content(url, use_js)
            if not html_content:
                return []
                
            soup = SafeSoup(html_content)
            container_sel = selectors.get('container')
            
            if container_sel:
                search_results = soup.select(container_sel)
                for result in search_results[:num_results]:
                    title_sel = selectors.get('title')
                    link_sel = selectors.get('link')
                    snippet_sel = selectors.get('snippet')
                    
                    title = result.select_one(title_sel).get_text(strip=True) if title_sel and result.select_one(title_sel) else "No Title"
                    
                    link = ""
                    if link_sel:
                        link_elem = result.select_one(link_sel)
                        if link_elem:
                            link = link_elem.get('href', '')
                            
                    snippet = result.select_one(snippet_sel).get_text(strip=True) if snippet_sel and result.select_one(snippet_sel) else ""
                    
                    if link:
                        results.append({
                            "source": name,
                            "title": title,
                            "url": link,
                            "description": snippet
                        })
        except Exception as e:
            logger.error(f"Custom engine search error: {e}")
            
        return results

    async def search_all(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Run all search engines concurrently"""
        tasks = [
            self.search_duckduckgo(query, num_results, use_js),
            self.search_bing(query, num_results, use_js),
            self.search_yahoo(query, num_results, use_js),
            self.search_brave(query, num_results, use_js),
            self.search_startpage(query, num_results, use_js),
            self.search_yandex(query, num_results, use_js),
            self.search_mojeek(query, num_results, use_js),
            self.search_searxng(query, num_results, use_js),
            self.search_publicwww(query, num_results, use_js),
            self.search_wayback(query, num_results, use_js),
            self.search_archive_today(query, num_results, use_js),
            self.search_commoncrawl(query, num_results, use_js)
        ]
        
        logger.info(f"Launching async search for: {Sanitizer.truncate(query)}")
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
    logger.info(f"Running basic search for: {Sanitizer.truncate(target)}")
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
>>>>>>> 56816638956650b83fc09e9dbac18781295d89c5
    return all_results