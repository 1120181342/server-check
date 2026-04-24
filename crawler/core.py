# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 核心模块
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
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


class BaseCrawler(ABC):
    
    def __init__(
        self,
        config: Dict[str, Any],
        session: Optional[aiohttp.ClientSession] = None
    ):
        self.config = config
        self.session = session
        self._visited_urls: Set[str] = set()
        self._request_count: int = 0
        self._last_request_time: float = 0.0
        
        request_config = config.get('crawler', {}).get('request', {})
        self.timeout = request_config.get('timeout', 30)
        self.max_retries = request_config.get('max_retries', 3)
        self.retry_delay = request_config.get('retry_delay', 2)
        self.headers = request_config.get('headers', {})
        
        concurrency_config = config.get('crawler', {}).get('concurrency', {})
        self.max_workers = concurrency_config.get('max_workers', 5)
        self.rate_limit = concurrency_config.get('rate_limit', 1.0)
    
    @property
    def visited_urls(self) -> Set[str]:
        return self._visited_urls.copy()
    
    def has_visited(self, url: str) -> bool:
        normalized_url = self._normalize_url(url)
        return normalized_url in self._visited_urls
    
    def mark_visited(self, url: str):
        normalized_url = self._normalize_url(url)
        self._visited_urls.add(normalized_url)
    
    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if parsed.query:
            normalized += f"?{parsed.query}"
        return normalized.rstrip('/')
    
    async def _rate_limit_wait(self):
        if self.rate_limit <= 0:
            return
        
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        
        if elapsed < self.rate_limit:
            wait_time = self.rate_limit - elapsed
            await asyncio.sleep(wait_time)
        
        self._last_request_time = time.time()
    
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
        
        if self.has_visited(url):
            logger.debug(f"URL already visited: {url}")
            return CrawlResult(
                success=False,
                error="URL already visited",
                response_time=0.0
            )
        
        await self._rate_limit_wait()
        
        try:
            if self.session:
                response = await self._async_fetch(url, method, **kwargs)
            else:
                response = self._sync_fetch(url, method, **kwargs)
            
            self.mark_visited(url)
            self._request_count += 1
            
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
        if not self.session:
            raise RuntimeError("Async session not available")
        
        async with self.session.request(
            method,
            url,
            headers=kwargs.get('headers', self.headers),
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            **kwargs
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
    
    def _sync_fetch(
        self,
        url: str,
        method: str = 'GET',
        **kwargs
    ) -> Dict[str, Any]:
        response = requests.request(
            method,
            url,
            headers=kwargs.get('headers', self.headers),
            timeout=self.timeout,
            **kwargs
        )
        response.raise_for_status()
        
        return {
            'content': response.text,
            'metadata': {
                'status': response.status_code,
                'headers': dict(response.headers),
                'url': response.url
            }
        }
    
    @abstractmethod
    async def crawl(self, start_url: str, **kwargs) -> List[Document]:
        pass


class HtmlParser:
    
    @staticmethod
    def parse(html: str, base_url: str = '') -> BeautifulSoup:
        return BeautifulSoup(html, 'lxml')
    
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
        
        for pattern in self.excluded_patterns:
            import re
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
