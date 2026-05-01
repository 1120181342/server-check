# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 文档发现模块
高性能并发版本 - 使用异步队列和Worker模式
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import aiohttp
from bs4 import BeautifulSoup

from core import (
    BaseCrawler,
    ConcurrentCrawler,
    Document,
    HtmlParser,
    LinkExtractor,
)

logger = logging.getLogger(__name__)


@dataclass
class CrawlTask:
    url: str
    depth: int
    task_type: str = "crawl"


class ConcurrentUrlQueue:
    
    def __init__(self, max_workers: int = 20):
        self._queue: asyncio.Queue = asyncio.Queue()
        self._seen_urls: Set[str] = set()
        self._seen_lock = asyncio.Lock()
        self._workers: List[asyncio.Task] = []
        self._max_workers = max_workers
        self._active_workers = 0
        self._workers_lock = asyncio.Lock()
    
    async def add_url(self, url: str, depth: int = 0, task_type: str = "crawl") -> bool:
        async with self._seen_lock:
            if url in self._seen_urls:
                return False
            self._seen_urls.add(url)
        
        await self._queue.put(CrawlTask(url=url, depth=depth, task_type=task_type))
        return True
    
    async def get_task(self) -> Optional[CrawlTask]:
        try:
            return await asyncio.wait_for(self._queue.get(), timeout=0.5)
        except asyncio.TimeoutError:
            return None
    
    def task_done(self):
        self._queue.task_done()
    
    async def join(self):
        await self._queue.join()
    
    def qsize(self) -> int:
        return self._queue.qsize()
    
    def seen_count(self) -> int:
        return len(self._seen_urls)


class HuaweiSupportCrawler(ConcurrentCrawler):
    
    def __init__(
        self,
        config: Dict[str, Any],
        session: Optional[aiohttp.ClientSession] = None
    ):
        super().__init__(config, session)
        self.link_extractor = LinkExtractor(config)
        self.target_config = config.get('target', {})
        self.base_url = self.target_config.get('base_url', 'https://support.huawei.com')
        self.search_url = self.target_config.get('search_url', 'https://support.huawei.com/enterprisesearch/')
        
        self.products = self.target_config.get('products', [])
        self.document_types = self.target_config.get('document_types', [])
        
        self._found_documents: Dict[str, Document] = {}
        self._found_lock = asyncio.Lock()
    
    @property
    def found_documents(self) -> List[Document]:
        return list(self._found_documents.values())
    
    async def add_found_document(self, doc: Document):
        async with self._found_lock:
            if doc.url not in self._found_documents:
                self._found_documents[doc.url] = doc
                logger.info(f"Added document: {doc.title or 'No Title'} ({doc.url})")
    
    async def crawl(self, start_url: str, **kwargs) -> List[Document]:
        max_depth = kwargs.get('max_depth', 3)
        keywords = kwargs.get('keywords', [])
        
        logger.info(f"Starting concurrent crawl with max_depth={max_depth}, max_workers={self.max_workers}")
        logger.info(f"Search keywords: {keywords}")
        
        url_queue = ConcurrentUrlQueue(max_workers=self.max_workers)
        
        if keywords:
            for keyword in keywords:
                search_url = self._build_search_url(keyword)
                logger.info(f"Adding search URL: {search_url}")
                await url_queue.add_url(search_url, depth=0, task_type="search")
        
        if start_url and start_url != self.search_url:
            await url_queue.add_url(start_url, depth=0, task_type="crawl")
        
        stop_event = asyncio.Event()
        
        workers = []
        for i in range(self.max_workers):
            worker = asyncio.create_task(
                self._worker_loop(
                    worker_id=i,
                    url_queue=url_queue,
                    max_depth=max_depth,
                    stop_event=stop_event
                )
            )
            workers.append(worker)
        
        logger.info(f"Started {self.max_workers} worker tasks")
        
        await url_queue.join()
        stop_event.set()
        
        logger.info("All tasks completed, waiting for workers to finish...")
        await asyncio.gather(*workers, return_exceptions=True)
        
        logger.info(f"Found {len(self.found_documents)} documents")
        return self.found_documents
    
    async def _worker_loop(
        self,
        worker_id: int,
        url_queue: ConcurrentUrlQueue,
        max_depth: int,
        stop_event: asyncio.Event
    ):
        logger.debug(f"Worker {worker_id} started")
        
        while not stop_event.is_set():
            task = await url_queue.get_task()
            
            if task is None:
                if stop_event.is_set():
                    break
                continue
            
            try:
                if task.depth >= max_depth:
                    logger.debug(f"Worker {worker_id}: Skipping {task.url} (max depth reached)")
                    url_queue.task_done()
                    continue
                
                logger.debug(f"Worker {worker_id}: Processing {task.task_type} - {task.url} (depth={task.depth})")
                
                if task.task_type == "search":
                    await self._process_search_task(task, url_queue, worker_id)
                else:
                    await self._process_crawl_task(task, url_queue, max_depth, worker_id)
                
            except Exception as e:
                logger.error(f"Worker {worker_id} error processing {task.url}: {e}")
            finally:
                url_queue.task_done()
        
        logger.debug(f"Worker {worker_id} stopped")
    
    async def _process_search_task(
        self,
        task: CrawlTask,
        url_queue: ConcurrentUrlQueue,
        worker_id: int
    ):
        result = await self.fetch_url(task.url)
        
        if not result.success or not result.document:
            logger.warning(f"Worker {worker_id}: Failed to fetch search URL: {task.url}")
            return
        
        soup = HtmlParser.parse(result.document.content, task.url)
        
        doc_links = self.link_extractor.extract_document_links(soup, task.url)
        logger.info(f"Worker {worker_id}: Found {len(doc_links)} document links in search results")
        
        for link in doc_links:
            if self._is_document_page(link):
                await self._crawl_document_page(link)
            else:
                await url_queue.add_url(link, depth=task.depth + 1, task_type="crawl")
        
        all_links = HtmlParser.extract_links(soup, task.url)
        filtered_links = self.link_extractor.filter_links(all_links, task.url)
        
        for link in filtered_links:
            if self._is_product_page(link):
                await url_queue.add_url(link, depth=task.depth + 1, task_type="crawl")
    
    async def _process_crawl_task(
        self,
        task: CrawlTask,
        url_queue: ConcurrentUrlQueue,
        max_depth: int,
        worker_id: int
    ):
        if self._is_document_page(task.url):
            await self._crawl_document_page(task.url)
            return
        
        result = await self.fetch_url(task.url)
        
        if not result.success or not result.document:
            logger.debug(f"Worker {worker_id}: Failed to fetch {task.url}: {result.error}")
            return
        
        soup = HtmlParser.parse(result.document.content, task.url)
        
        all_links = HtmlParser.extract_links(soup, task.url)
        filtered_links = self.link_extractor.filter_links(all_links, task.url)
        
        doc_links = [link for link in filtered_links if self._is_document_page(link)]
        other_links = [link for link in filtered_links if link not in doc_links and self._should_crawl(link)]
        
        for doc_link in doc_links:
            await self._crawl_document_page(doc_link)
        
        if task.depth + 1 < max_depth:
            for link in other_links:
                await url_queue.add_url(link, depth=task.depth + 1, task_type="crawl")
    
    def _build_search_url(self, keyword: str) -> str:
        parsed = urlparse(self.search_url)
        query_params = {
            'keyword': keyword,
            'lang': 'zh',
            'searchType': 'searchAll',
            'sortType': 'Relevance',
            'type': 'searchAll'
        }
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query_params),
            parsed.fragment
        ))
    
    async def _crawl_document_page(self, url: str):
        async with self._found_lock:
            if url in self._found_documents:
                return
        
        logger.debug(f"Crawling document page: {url}")
        
        result = await self.fetch_url(url)
        if not result.success or not result.document:
            logger.debug(f"Failed to fetch document page: {url}")
            return
        
        soup = HtmlParser.parse(result.document.content, url)
        
        doc = Document(url=url)
        doc.title = HtmlParser.extract_title(soup)
        doc.content = HtmlParser.extract_text(soup)
        doc.links = HtmlParser.extract_links(soup, url)
        
        metadata = HtmlParser.extract_metadata(soup)
        doc.description = metadata.get('description', '')
        
        self._classify_document(doc, soup)
        
        if self._is_target_document(doc):
            await self.add_found_document(doc)
    
    def _classify_document(self, doc: Document, soup: BeautifulSoup):
        doc_type_patterns = {
            '产品文档': ['产品文档', 'product document', '产品描述'],
            '配置指南': ['配置指南', '配置调测', 'configuration'],
            '安装指南': ['安装指南', '硬件安装', '快速安装', 'installation'],
            '操作维护': ['操作维护', '日常维护', 'maintenance'],
            '故障处理': ['故障处理', 'troubleshooting', 'FAQ'],
            '版本文档': ['版本文档', 'release notes', '版本说明'],
            '技术规范': ['技术规范', '技术参数', 'specification'],
            '命令参考': ['命令参考', 'command reference'],
        }
        
        text_to_check = f"{doc.title} {doc.description} {doc.url}".lower()
        
        for doc_type, patterns in doc_type_patterns.items():
            for pattern in patterns:
                if pattern.lower() in text_to_check:
                    doc.doc_type = doc_type
                    break
            if doc.doc_type:
                break
        
        for product in self.products:
            product_name = product.get('name', '')
            keywords = product.get('keywords', [])
            
            all_keywords = [product_name] + keywords
            for keyword in all_keywords:
                if keyword.lower() in text_to_check:
                    doc.product = product_name
                    break
            if doc.product:
                break
        
        version_match = re.search(
            r'[Vv]\d+[Rr]\d+[Cc]?\d*|[Vv]\d+\.\d+',
            text_to_check
        )
        if version_match:
            doc.version = version_match.group().upper()
    
    def _is_target_document(self, doc: Document) -> bool:
        if not doc.title:
            return False
        
        if not self.products:
            return True
        
        for product in self.products:
            product_name = product.get('name', '')
            keywords = product.get('keywords', [])
            
            all_keywords = [product_name] + keywords
            text_to_check = f"{doc.title} {doc.description} {doc.url}".lower()
            
            for keyword in all_keywords:
                if keyword.lower() in text_to_check:
                    return True
        
        return False
    
    def _is_document_page(self, url: str) -> bool:
        doc_indicators = [
            '/document/',
            '/documents/',
            '/product/',
            '/support/',
            '/zh-cn/',
            'product-document',
            'docId=',
            'col=',
        ]
        
        url_lower = url.lower()
        
        for indicator in doc_indicators:
            if indicator in url_lower:
                return True
        
        return False
    
    def _is_product_page(self, url: str) -> bool:
        product_indicators = [
            '/product/',
            '/products/',
            '/enterprise/network/',
            '/security/',
            '/switch/',
            '/router/',
        ]
        
        url_lower = url.lower()
        
        for indicator in product_indicators:
            if indicator in url_lower:
                return True
        
        return False
    
    def _should_crawl(self, url: str) -> bool:
        parsed = urlparse(url)
        
        if 'support.huawei.com' not in parsed.netloc and 'e.huawei.com' not in parsed.netloc:
            return False
        
        exclude_patterns = [
            '/login',
            '/register',
            '/download?',
            'javascript:',
            'mailto:',
            '#',
        ]
        
        for pattern in exclude_patterns:
            if pattern in url:
                return False
        
        return True


class SearchEngine:
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.target_config = config.get('target', {})
        self.base_url = self.target_config.get('base_url', 'https://support.huawei.com')
        self.search_url = self.target_config.get('search_url', 'https://support.huawei.com/enterprisesearch/')
    
    def build_search_query(
        self,
        keywords: List[str],
        lang: str = 'zh',
        search_type: str = 'searchAll'
    ) -> str:
        keyword_str = ' '.join(keywords)
        
        parsed = urlparse(self.search_url)
        query_params = {
            'keyword': keyword_str,
            'lang': lang,
            'searchType': search_type,
            'sortType': 'Relevance',
            'type': search_type
        }
        
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            urlencode(query_params),
            parsed.fragment
        ))
    
    def extract_search_results(self, html: str, base_url: str) -> List[Dict[str, str]]:
        soup = HtmlParser.parse(html, base_url)
        results = []
        
        result_selectors = [
            'div.result-item',
            'li.search-result',
            'div.document-item',
            '.search-result-item',
        ]
        
        for selector in result_selectors:
            items = soup.select(selector)
            for item in items:
                result = self._parse_search_result(item, base_url)
                if result:
                    results.append(result)
        
        if not results:
            all_links = HtmlParser.extract_links(soup, base_url)
            for link in all_links:
                if self._is_document_link(link):
                    results.append({
                        'url': link,
                        'title': '',
                        'description': ''
                    })
        
        return results
    
    def _parse_search_result(
        self,
        item: BeautifulSoup,
        base_url: str
    ) -> Optional[Dict[str, str]]:
        result = {}
        
        link_elem = item.find('a', href=True)
        if link_elem:
            href = link_elem.get('href', '')
            result['url'] = self._normalize_link(href, base_url)
            result['title'] = link_elem.get_text(strip=True)
        
        desc_elem = item.find(['p', 'div', 'span'], class_=re.compile(r'description|summary|content'))
        if desc_elem:
            result['description'] = desc_elem.get_text(strip=True)
        
        if 'url' in result:
            return result
        
        return None
    
    def _normalize_link(self, href: str, base_url: str) -> str:
        from urllib.parse import urljoin
        
        if href.startswith('//'):
            return 'https:' + href
        elif not href.startswith(('http://', 'https://')):
            return urljoin(base_url, href)
        
        return href
    
    def _is_document_link(self, url: str) -> bool:
        doc_indicators = [
            '/document/',
            '/product/',
            '/support/',
            'docId=',
            'col=',
            'product-document',
        ]
        
        url_lower = url.lower()
        
        for indicator in doc_indicators:
            if indicator in url_lower:
                return True
        
        return False
