# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 核心模块
高性能并发版本
"""

import asyncio
import logging
import random
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


@dataclass
class Document:
    url: str
    title: str = ""
    description: str = ""
    doc_type: str = ""
    product: str = ""
    version: str = ""
    file_type: str = "html"
    content: str = ""
    links: List[str] = field(default_factory=list)
    downloaded: bool = False
    save_path: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CrawlResult:
    success: bool
    document: Optional[Document] = None
    error: Optional[str] = None
    response_time: float = 0.0


class RateLimiter:
    
    def __init__(
        self,
        rate_limit: float = 0.1,
        min_delay: float = 0.05,
        max_delay: float = 0.2,
        enable_random_delay: bool = True
    ):
        self.rate_limit = rate_limit
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.enable_random_delay = enable_random_delay
        
        self._lock = asyncio.Lock()
        self._last_request_time = 0.0
        self._request_count = 0
        self._window_start_time = time.time()
        self._window_requests = 0
        self._max_per_second = int(1.0 / rate_limit) if rate_limit > 0 else 100
    
    async def acquire(self):
        async with self._lock:
            current_time = time.time()
            
            elapsed_in_window = current_time - self._window_start_time
            if elapsed_in_window >= 1.0:
                self._window_start_time = current_time
                self._window_requests = 0
            
            if self._window_requests >= self._max_per_second:
                wait_time = 1.0 - elapsed_in_window
                await asyncio.sleep(wait_time)
                current_time = time.time()
                self._window_start_time = current_time
                self._window_requests = 0
            
            elapsed = current_time - self._last_request_time
            base_delay = max(0, self.rate_limit - elapsed)
            
            if self.enable_random_delay:
                random_delay = random.uniform(self.min_delay, self.max_delay)
                total_delay = base_delay + random_delay
            else:
                total_delay = base_delay
            
            if total_delay > 0:
                await asyncio.sleep(total_delay)
            
            self._last_request_time = time.time()
            self._request_count += 1
            self._window_requests += 1


class UserAgentRotator:
    
    def __init__(
        self,
        user_agents: List[str],
        enable_rotation: bool = True
    ):
        self.user_agents = user_agents or self._get_default_user_agents()
        self.enable_rotation = enable_rotation
        self._index = 0
        self._lock = asyncio.Lock()
    
    def _get_default_user_agents(self) -> List[str]:
        return [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
    
    async def get_user_agent(self) -> str:
        if not self.enable_rotation:
            return self.user_agents[0]
        
        async with self._lock:
            ua = self.user_agents[self._index]
            self._index = (self._index + 1) % len(self.user_agents)
            return ua


class BaseCrawler(ABC):
    
    def __init__(
        self,
        config: Dict[str, Any],
        session: Optional[aiohttp.ClientSession] = None
    ):
        self.config = config
        self.session = session
        self._visited_urls: Set[str] = set()
        self._visited_lock = asyncio.Lock()
        self._request_count: int = 0
        self._request_lock = asyncio.Lock()
        
        request_config = config.get('crawler', {}).get('request', {})
        self.timeout = request_config.get('timeout', 30)
        self.max_retries = request_config.get('max_retries', 3)
        self.retry_delay = request_config.get('retry_delay', 2)
        self.headers = request_config.get('headers', {})
        
        user_agents = request_config.get('user_agents', [])
        enable_ua_rotation = request_config.get('enable_ua_rotation', True)
        self.ua_rotator = UserAgentRotator(user_agents, enable_ua_rotation)
        
        concurrency_config = config.get('crawler', {}).get('concurrency', {})
        self.max_workers = concurrency_config.get('max_workers', 20)
        self.rate_limit = concurrency_config.get('rate_limit', 0.1)
        self.min_delay = concurrency_config.get('min_delay', 0.05)
        self.max_delay = concurrency_config.get('max_delay', 0.2)
        self.enable_random_delay = concurrency_config.get('enable_random_delay', True)
        
        self.rate_limiter = RateLimiter(
            rate_limit=self.rate_limit,
            min_delay=self.min_delay,
            max_delay=self.max_delay,
            enable_random_delay=self.enable_random_delay
        )
    
    @property
    def visited_urls(self) -> Set[str]:
        return self._visited_urls.copy()
    
    async def has_visited(self, url: str) -> bool:
        normalized_url = self._normalize_url(url)
        async with self._visited_lock:
            return normalized_url in self._visited_urls
    
    async def mark_visited(self, url: str):
        normalized_url = self._normalize_url(url)
        async with self._visited_lock:
            self._visited_urls.add(normalized_url)
    
    async def increment_request_count(self):
        async with self._request_lock:
            self._request_count += 1
    
    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip('/')
    
    async def _get_headers(self) -> Dict[str, str]:
        headers = self.headers.copy()
        user_agent = await self.ua_rotator.get_user_agent()
        headers['User-Agent'] = user_agent
        return headers
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def fetch_url(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> CrawlResult:
        start_time = time.time()
        
        if await self.has_visited(url):
            logger.debug(f"URL already visited: {url}")
            return CrawlResult(
                success=False,
                error="URL already visited",
                response_time=0.0
            )
        
        await self.rate_limiter.acquire()
        
        try:
            headers = await self._get_headers()
            all_headers = {**headers, **kwargs.get('headers', {})}
            
            response = await self._async_fetch(url, method, headers=all_headers, **kwargs)
            
            await self.mark_visited(url)
            await self.increment_request_count()
            
            response_time = time.time() - start_time
            
            return CrawlResult(
                success=True,
                response_time=response_time,
                document=Document(
                    url=url,
                    content=response.get('content', ''),
                    metadata=response.get('metadata', {})
                )
            )
            
        except Exception as e:
            logger.error(f"Error fetching {url}: {e}")
            return CrawlResult(
                success=False,
                error=str(e),
                response_time=time.time() - start_time
            )
    
    async def _async_fetch(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> Dict[str, Any]:
        headers = kwargs.get('headers', self.headers)
        
        if self.session:
            async with self.session.request(
                method,
                url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                **{k: v for k, v in kwargs.items() if k not in ['headers']}
            ) as response:
                content = await response.text()
                return {
                    'content': content,
                    'metadata': {
                        'status': response.status,
                        'headers': dict(response.headers),
                        'url': str(response.url)
                    }
                }
        else:
            async with aiohttp.ClientSession() as temp_session:
                async with temp_session.request(
                    method,
                    url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout),
                    **{k: v for k, v in kwargs.items() if k not in ['headers']}
                ) as response:
                    content = await response.text()
                    return {
                        'content': content,
                        'metadata': {
                            'status': response.status,
                            'headers': dict(response.headers),
                            'url': str(response.url)
                        }
                    }
    
    @abstractmethod
    async def crawl(self, start_url: str, **kwargs) -> List[Document]:
        pass


class ConcurrentCrawler(BaseCrawler):
    
    def __init__(
        self,
        config: Dict[str, Any],
        session: Optional[aiohttp.ClientSession] = None
    ):
        super().__init__(config, session)
        self._results: List[Document] = []
        self._results_lock = asyncio.Lock()
        self._crawl_tasks: Set[asyncio.Task] = set()
    
    async def add_result(self, doc: Document):
        async with self._results_lock:
            if doc.url not in [d.url for d in self._results]:
                self._results.append(doc)
    
    async def get_results(self) -> List[Document]:
        async with self._results_lock:
            return self._results.copy()
    
    async def run_concurrent_tasks(
        self,
        urls: List[str],
        worker_func: Callable[[str], Any],
        max_workers: Optional[int] = None
    ) -> List[Any]:
        max_workers = max_workers or self.max_workers
        semaphore = asyncio.Semaphore(max_workers)
        
        async def bounded_worker(url: str) -> Any:
            async with semaphore:
                return await worker_func(url)
        
        tasks = [bounded_worker(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Task failed: {result}")
            else:
                valid_results.append(result)
        
        return valid_results


class HtmlParser:
    
    @staticmethod
    def parse(html: str, base_url: str = '') -> BeautifulSoup:
        return BeautifulSoup(html, 'html.parser')
    
    @staticmethod
    def extract_links(soup: BeautifulSoup, base_url: str) -> List[str]:
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('#') or href.startswith('javascript:'):
                continue
            
            absolute_url = urljoin(base_url, href)
            links.append(absolute_url)
        
        return links
    
    @staticmethod
    def extract_text(soup: BeautifulSoup) -> str:
        for script in soup(["script", "style"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        return text
    
    @staticmethod
    def extract_title(soup: BeautifulSoup) -> str:
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text(strip=True)
        
        return ""
    
    @staticmethod
    def extract_metadata(soup: BeautifulSoup) -> Dict[str, str]:
        metadata = {}
        
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name == 'description' or property_attr == 'og:description':
                metadata['description'] = content
            elif name == 'keywords' or property_attr == 'og:keywords':
                metadata['keywords'] = content
            elif name == 'author':
                metadata['author'] = content
        
        return metadata


class LinkExtractor:
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.filter_config = config.get('filter', {})
        self.allowed_domains = set(
            self.filter_config.get('allowed_domains', [])
        )
        self.excluded_patterns = set(
            self.filter_config.get('excluded_patterns', [])
        )
        self.url_patterns = set(
            self.filter_config.get('url_patterns', [])
        )
    
    def is_valid_url(self, url: str) -> bool:
        if not url or not url.startswith(('http://', 'https://')):
            return False
        
        parsed = urlparse(url)
        
        if self.allowed_domains:
            domain = parsed.netloc
            if not any(d in domain for d in self.allowed_domains):
                return False
        
        import re
        for pattern in self.excluded_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return False
        
        return True
    
    def filter_links(self, links: List[str], base_url: str = '') -> List[str]:
        filtered_links = []
        
        for link in links:
            if self.is_valid_url(link):
                filtered_links.append(link)
        
        return list(set(filtered_links))
    
    def extract_document_links(
        self,
        soup: BeautifulSoup,
        base_url: str
    ) -> List[str]:
        document_links = []
        
        doc_selectors = [
            'a[href*="document"]',
            'a[href*="product"]',
            'a[href*="support"]',
            'a[href*="download"]',
            'a[href*="pdf"]',
            'a[href*="zh-cn"]',
        ]
        
        for selector in doc_selectors:
            for element in soup.select(selector):
                href = element.get('href', '')
                if href:
                    absolute_url = urljoin(base_url, href)
                    document_links.append(absolute_url)
        
        return self.filter_links(document_links, base_url)
