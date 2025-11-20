import requests
import logging
import time
import random
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger("OSINT_Tool")

class SearchEngineManager:
    """Manages multiple search engines with fallback capabilities"""
    
    def __init__(self):
        self.session = self._create_session()
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        self.search_engines_available = ["duckduckgo", "bing", "yahoo", "brave", "startpage", "yandex"]
        self._playwright_available = self._check_playwright_available()
        self._playwright_warning_shown = False
    
    def _create_session(self) -> requests.Session:
        """Create session with retry logic"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=2,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session
    
    def _get_headers(self) -> Dict[str, str]:
        """Generate realistic headers with randomized order and referer spoofing"""
        base_headers = {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        
        # Add random Referer
        referers = [
            "https://www.google.com/",
            "https://www.bing.com/",
            "https://duckduckgo.com/",
            "https://twitter.com/",
            "https://www.facebook.com/"
        ]
        base_headers["Referer"] = random.choice(referers)
        
        # Randomize header order (create new dict in random order)
        header_items = list(base_headers.items())
        random.shuffle(header_items)
        return dict(header_items)
    
    def _check_playwright_available(self) -> bool:
        """Check if Playwright is available (check once at init)"""
        try:
            import playwright
            return True
        except ImportError:
            return False
            
    def _random_delay(self, min_sec: float = 3.0, max_sec: float = 7.0):
        """Random delay between searches"""
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"Waiting {delay:.2f}s before next search")
        time.sleep(delay) 

    def _fetch_content(self, url: str, use_js: bool = False) -> Optional[str]:
        """Fetch content using requests or Playwright"""
        if use_js:
            # Check if Playwright is available
            if not self._playwright_available:
                # Show warning only once
                if not self._playwright_warning_shown:
                    logger.warning("Playwright not installed. Falling back to standard requests.")
                    logger.warning("To enable JavaScript rendering, run: pip install playwright && playwright install")
                    self._playwright_warning_shown = True
                # Fall back to regular requests
                use_js = False
            else:
                # Playwright is available, try to use it
                try:
                    from playwright.sync_api import sync_playwright
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=True)
                        context = browser.new_context(
                            user_agent=random.choice(self.user_agents),
                            viewport={'width': 1920, 'height': 1080}
                        )
                        page = context.new_page()
                        page.goto(url, wait_until="networkidle", timeout=30000)
                        content = page.content()
                        browser.close()
                        return content
                except Exception as e:
                    logger.error(f"Playwright error: {e}")
                    logger.info("Falling back to standard requests")
                    # Fall back to regular requests
                    use_js = False
        
        # Use regular requests (either originally requested or fallback)
        if not use_js:
            try:
                self._random_delay(2.0, 4.0)
                response = self.session.get(url, headers=self._get_headers(), timeout=15)
                
                # Handle 202 (Accepted) - retry once after a delay
                if response.status_code == 202:
                    logger.info("Received 202 (Accepted) - content not ready. Retrying after delay...")
                    time.sleep(random.uniform(3.0, 5.0))  # Wait a bit longer for processing
                    response = self.session.get(url, headers=self._get_headers(), timeout=15)
                    
                    if response.status_code == 202:
                        logger.warning("Still received 202 after retry - content not available, moving on")
                        return None
                
                if response.status_code == 200:
                    return response.text
                
                # Provide more context for different status codes
                if response.status_code == 429:
                    logger.warning(f"Rate limited (429) - too many requests")
                elif response.status_code in [401, 403]:
                    logger.warning(f"Access denied ({response.status_code}) - possible bot detection")
                elif response.status_code >= 500:
                    logger.warning(f"Server error ({response.status_code})")
                else:
                    logger.warning(f"Request failed with status {response.status_code}")                    
                return None
            except Exception as e:
                logger.error(f"Request error: {e}")
                return None
    
    def search_duckduckgo(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Search DuckDuckGo"""
        results = []
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        html_content = self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
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
            
            logger.info(f"DuckDuckGo returned {len(results)} results for: {query}")
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        return results
    
    def search_bing(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Search Bing"""
        results = []
        encoded_query = quote_plus(query)
        url = f"https://www.bing.com/search?q={encoded_query}&count={num_results}"
        
        html_content = self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
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
            
            logger.info(f"Bing returned {len(results)} results for: {query}")
                
        except Exception as e:
            logger.error(f"Bing search error: {e}")
        
        return results

    def search_yahoo(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Search Yahoo"""
        results = []
        encoded_query = quote_plus(query)
        url = f"https://search.yahoo.com/search?p={encoded_query}&n={num_results}"
        
        html_content = self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
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
            
            logger.info(f"Yahoo returned {len(results)} results for: {query}")
                
        except Exception as e:
            logger.error(f"Yahoo search error: {e}")
        
        return results

    def search_brave(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Search Brave"""
        results = []
        encoded_query = quote_plus(query)
        url = f"https://search.brave.com/search?q={encoded_query}"
        
        html_content = self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
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
            
            logger.info(f"Brave returned {len(results)} results for: {query}")
                
        except Exception as e:
            logger.error(f"Brave search error: {e}")
        
        return results

    def search_startpage(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Search Startpage"""
        results = []
        encoded_query = quote_plus(query)
        url = f"https://www.startpage.com/do/search?query={encoded_query}"
        
        html_content = self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
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
            
            logger.info(f"Startpage returned {len(results)} results for: {query}")
                
        except Exception as e:
            logger.error(f"Startpage search error: {e}")
        
        return results

    def search_yandex(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """Search Yandex"""
        results = []
        encoded_query = quote_plus(query)
        url = f"https://yandex.com/search/?text={encoded_query}"
        
        html_content = self._fetch_content(url, use_js)
        if not html_content:
            return []

        try:
            soup = BeautifulSoup(html_content, 'html.parser')
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
            
            logger.info(f"Yandex returned {len(results)} results for: {query}")
                
        except Exception as e:
            logger.error(f"Yandex search error: {e}")
        
        return results
    
    def search_with_fallback(self, query: str, num_results: int = 10, use_js: bool = False) -> List[Dict[str, str]]:
        """
        Try multiple search engines with fallback.
        """
        logger.info(f"Searching for: {query}")
        
        # Define search order
        engines = [
            self.search_duckduckgo,
            self.search_bing,
            self.search_yahoo,
            self.search_brave,
            self.search_startpage,
            self.search_yandex
        ]
        
        # Shuffle engines for better evasion (except maybe DDG first?)
        # Let's keep DDG first as it's most reliable for scraping, then shuffle others
        first_engine = engines[0]
        other_engines = engines[1:]
        random.shuffle(other_engines)
        search_order = [first_engine] + other_engines
        
        for engine in search_order:
            engine_name = engine.__name__.replace('search_', '').title()
            logger.debug(f"Trying {engine_name}...")
            
            results = engine(query, num_results, use_js)
            if results:
                return results
            
            logger.debug(f"{engine_name} failed or returned no results")
        
        logger.warning("All search engines failed")
        return []


def run_search_engines(target: str, config: Dict, js_render: bool = False) -> List[Dict[str, str]]:
    """
    Enhanced search engine module with multiple sources and dorking.
    """
    search_manager = SearchEngineManager()
    all_results = []
    
    # Basic search
    logger.info(f"Running basic search for: {target}")
    basic_results = search_manager.search_with_fallback(target, num_results=10, use_js=js_render)
    all_results.extend(basic_results)
    
    # Google Dorks (adapted for general syntax)
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
    
    for dork in dorks:
        logger.info(f"Executing dork: {dork}")
        dork_results = search_manager.search_with_fallback(dork, num_results=5, use_js=js_render)
        
        # Mark these as dork results
        for result in dork_results:
            result['query_type'] = 'dork'
            result['dork_query'] = dork
        
        all_results.extend(dork_results)
        
        # Longer delay between dork queries to avoid detection
        time.sleep(random.uniform(5, 10))
    
    logger.info(f"Search complete: {len(all_results)} total results collected")
    return all_results