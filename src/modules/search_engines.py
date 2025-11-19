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
        self.search_engines_available = ["duckduckgo", "bing"]
    
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
        """Generate realistic headers"""
        return {
            "User-Agent": random.choice(self.user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
    
    def _random_delay(self, min_sec: float = 3.0, max_sec: float = 7.0):
        """Random delay between searches"""
        delay = random.uniform(min_sec, max_sec)
        logger.debug(f"Waiting {delay:.2f}s before next search")
        time.sleep(delay)
    
    def search_duckduckgo(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Search DuckDuckGo using HTML scraping.
        DDG is more lenient with automated queries than Google.
        """
        results = []
        encoded_query = quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
        
        try:
            self._random_delay(2.0, 4.0)
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parse DDG HTML results
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
            else:
                logger.warning(f"DuckDuckGo search failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
        
        return results
    
    def search_bing(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Search Bing using HTML scraping.
        Bing is generally more tolerant of automation than Google.
        """
        results = []
        encoded_query = quote_plus(query)
        url = f"https://www.bing.com/search?q={encoded_query}&count={num_results}"
        
        try:
            self._random_delay(3.0, 6.0)
            response = self.session.get(url, headers=self._get_headers(), timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Parse Bing results
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
            else:
                logger.warning(f"Bing search failed with status {response.status_code}")
                
        except Exception as e:
            logger.error(f"Bing search error: {e}")
        
        return results
    
    def search_with_fallback(self, query: str, num_results: int = 10) -> List[Dict[str, str]]:
        """
        Try multiple search engines with fallback.
        Prioritizes DuckDuckGo (most lenient) then falls back to Bing.
        """
        logger.info(f"Searching for: {query}")
        
        # Try DuckDuckGo first (most automation-friendly)
        results = self.search_duckduckgo(query, num_results)
        
        if results:
            return results
        
        logger.info("DuckDuckGo failed, trying Bing...")
        results = self.search_bing(query, num_results)
        
        if results:
            return results
        
        logger.warning("All search engines failed")
        return []


def run_search_engines(target: str, config: Dict) -> List[Dict[str, str]]:
    """
    Enhanced search engine module with multiple sources and dorking.
    """
    search_manager = SearchEngineManager()
    all_results = []
    
    # Basic search
    logger.info(f"Running basic search for: {target}")
    basic_results = search_manager.search_with_fallback(target, num_results=10)
    all_results.extend(basic_results)
    
    # Google Dorks (adapted for DuckDuckGo/Bing syntax)
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
        dork_results = search_manager.search_with_fallback(dork, num_results=5)
        
        # Mark these as dork results
        for result in dork_results:
            result['query_type'] = 'dork'
            result['dork_query'] = dork
        
        all_results.extend(dork_results)
        
        # Longer delay between dork queries to avoid detection
        time.sleep(random.uniform(5, 10))
    
    logger.info(f"Search complete: {len(all_results)} total results collected")
    return all_results