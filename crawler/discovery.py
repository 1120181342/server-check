# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 文档发现模块
"""

import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from bs4 import BeautifulSoup

from core import BaseCrawler, Document, HtmlParser, LinkExtractor

logger = logging.getLogger(__name__)


class HuaweiSupportCrawler(BaseCrawler):
    
    def __init__(
        self,
        config: Dict[str, Any],
        session=None
    ):
        super().__init__(config, session)
        self.link_extractor = LinkExtractor(config)
        self.target_config = config.get('target', {})
        self.base_url = self.target_config.get('base_url', 'https://support.huawei.com')
        self.search_url = self.target_config.get('search_url', 'https://support.huawei.com/enterprisesearch/')
        
        self.products = self.target_config.get('products', [])
        self.document_types = self.target_config.get('document_types', [])
        
        self._found_documents: Dict[str, Document] = {}
    
    @property
    def found_documents(self) -> List[Document]:
        return list(self._found_documents.values())
    
    async def crawl(self, start_url: str, **kwargs) -> List[Document]:
        max_depth = kwargs.get('max_depth', 3)
        keywords = kwargs.get('keywords', [])
        
        logger.info(f"Starting crawl from {start_url} with max depth {max_depth}")
        
        if keywords:
            await self._search_by_keywords(keywords)
        
        if start_url and start_url != self.search_url:
            await self._crawl_url(start_url, depth=0, max_depth=max_depth)
        
        return self.found_documents
    
    async def _search_by_keywords(self, keywords: List[str]):
        logger.info(f"Searching with keywords: {keywords}")
        
        for keyword in keywords:
            search_url = self._build_search_url(keyword)
            logger.info(f"Searching: {search_url}")
            
            result = await self.fetch_url(search_url)
            if result.success and result.document:
                await self._process_search_results(
                    result.document.content,
                    search_url
                )
    
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
    
    async def _process_search_results(self, html: str, base_url: str):
        soup = HtmlParser.parse(html, base_url)
        
        doc_links = self.link_extractor.extract_document_links(soup, base_url)
        logger.info(f"Found {len(doc_links)} document links in search results")
        
        for link in doc_links:
            if not self.has_visited(link) and self._is_document_page(link):
                await self._crawl_document_page(link)
        
        all_links = HtmlParser.extract_links(soup, base_url)
        filtered_links = self.link_extractor.filter_links(all_links, base_url)
        
        for link in filtered_links:
            if not self.has_visited(link) and self._is_product_page(link):
                logger.info(f"Found product page: {link}")
                await self._crawl_url(link, depth=0, max_depth=2)
    
    async def _crawl_url(self, url: str, depth: int, max_depth: int):
        if depth >= max_depth:
            return
        
        logger.info(f"Crawling (depth {depth}): {url}")
        
        result = await self.fetch_url(url)
        if not result.success or not result.document:
            logger.warning(f"Failed to fetch {url}: {result.error}")
            return
        
        soup = HtmlParser.parse(result.document.content, url)
        
        if self._is_document_page(url):
            await self._process_document_page(url, soup)
        
        links = HtmlParser.extract_links(soup, url)
        filtered_links = self.link_extractor.filter_links(links, url)
        
        for link in filtered_links:
            if not self.has_visited(link):
                if self._is_document_page(link):
                    await self._crawl_document_page(link)
                elif self._should_crawl(link):
                    await self._crawl_url(link, depth + 1, max_depth)
    
    async def _crawl_document_page(self, url: str):
        if url in self._found_documents:
            return
        
        logger.info(f"Found document page: {url}")
        
        result = await self.fetch_url(url)
        if not result.success or not result.document:
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
            self._found_documents[url] = doc
            logger.info(f"Added document: {doc.title} ({doc.url})")
    
    async def _process_document_page(self, url: str, soup: BeautifulSoup):
        if url in self._found_documents:
            return
        
        doc = Document(url=url)
        doc.title = HtmlParser.extract_title(soup)
        doc.content = HtmlParser.extract_text(soup)
        doc.links = HtmlParser.extract_links(soup, url)
        
        metadata = HtmlParser.extract_metadata(soup)
        doc.description = metadata.get('description', '')
        
        self._classify_document(doc, soup)
        
        if self._is_target_document(doc):
            self._found_documents[url] = doc
            logger.info(f"Added document: {doc.title}")
    
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
        
        if 'support.huawei.com' not in parsed.netloc:
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
