# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 存储模块
"""

import asyncio
import hashlib
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import aiofiles
import aiohttp
from bs4 import BeautifulSoup

from core import Document, HtmlParser, RateLimiter, UserAgentRotator

logger = logging.getLogger(__name__)


class StorageManager:
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        storage_config = config.get('crawler', {}).get('storage', {})
        
        self.output_dir = Path(storage_config.get('output_dir', './downloads'))
        self.save_html = storage_config.get('save_html', True)
        self.save_pdf = storage_config.get('save_pdf', True)
        self.create_index = storage_config.get('create_index', True)
        
        self._ensure_directories()
    
    def _ensure_directories(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        (self.output_dir / 'html').mkdir(exist_ok=True)
        (self.output_dir / 'pdf').mkdir(exist_ok=True)
        (self.output_dir / 'metadata').mkdir(exist_ok=True)
    
    def generate_safe_filename(
        self,
        title: str,
        url: str,
        extension: str = '.html'
    ) -> str:
        if title:
            safe_title = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', title)
            safe_title = safe_title[:100]
        else:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            safe_title = f"document_{url_hash}"
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        return f"{safe_title}_{timestamp}{extension}"
    
    def get_document_path(
        self,
        doc: Document,
        file_type: Optional[str] = None
    ) -> Path:
        file_type = file_type or doc.file_type
        
        if file_type == 'pdf':
            subdir = 'pdf'
            ext = '.pdf'
        elif file_type == 'html':
            subdir = 'html'
            ext = '.html'
        else:
            subdir = 'html'
            ext = '.html'
        
        filename = self.generate_safe_filename(doc.title, doc.url, ext)
        
        product_dir = self.output_dir / subdir
        if doc.product:
            safe_product = re.sub(r'[^\w\-_\u4e00-\u9fff]', '_', doc.product)
            product_dir = product_dir / safe_product
        
        product_dir.mkdir(parents=True, exist_ok=True)
        
        return product_dir / filename
    
    async def save_document(
        self,
        doc: Document,
        content: Optional[str] = None
    ) -> str:
        save_path = self.get_document_path(doc)
        
        try:
            content_to_save = content or doc.content
            
            if doc.file_type == 'html' and content_to_save:
                content_to_save = self._clean_html(content_to_save, doc.url)
            
            async with aiofiles.open(save_path, 'w', encoding='utf-8') as f:
                await f.write(content_to_save)
            
            doc.downloaded = True
            doc.save_path = str(save_path)
            
            logger.info(f"Saved document to: {save_path}")
            
            await self._save_metadata(doc)
            
            return str(save_path)
            
        except Exception as e:
            logger.error(f"Failed to save document {doc.url}: {e}")
            raise
    
    def _clean_html(self, html: str, base_url: str) -> str:
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup.find_all('script'):
            script.decompose()
        
        for style in soup.find_all('style'):
            style.decompose()
        
        for nav in soup.find_all('nav'):
            nav.decompose()
        
        for header in soup.find_all('header'):
            header.decompose()
        
        for footer in soup.find_all('footer'):
            footer.decompose()
        
        for aside in soup.find_all('aside'):
            aside.decompose()
        
        title = HtmlParser.extract_title(soup)
        
        body_content = soup.find('body')
        if body_content:
            main_content = body_content.find(['main', 'article', 'div', 'section'])
            if main_content:
                cleaned_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title or 'Document'}</title>
    <base href="{base_url}">
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        h1, h2, h3, h4, h5, h6 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 10px 0; }}
        table, th, td {{ border: 1px solid #ccc; }}
        th, td {{ padding: 8px; text-align: left; }}
        pre {{ background: #f4f4f4; padding: 10px; overflow-x: auto; }}
        code {{ background: #f4f4f4; padding: 2px 4px; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{str(main_content)}
</body>
</html>"""
                return cleaned_html
        
        return html
    
    async def _save_metadata(self, doc: Document):
        metadata_dir = self.output_dir / 'metadata'
        metadata_dir.mkdir(parents=True, exist_ok=True)
        
        url_hash = hashlib.md5(doc.url.encode()).hexdigest()
        metadata_path = metadata_dir / f"{url_hash}.json"
        
        metadata = {
            'url': doc.url,
            'title': doc.title,
            'description': doc.description,
            'doc_type': doc.doc_type,
            'product': doc.product,
            'version': doc.version,
            'file_type': doc.file_type,
            'save_path': doc.save_path,
            'downloaded': doc.downloaded,
            'downloaded_at': datetime.now().isoformat(),
            'links_count': len(doc.links),
            'metadata': doc.metadata
        }
        
        async with aiofiles.open(metadata_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(metadata, ensure_ascii=False, indent=2))
        
        logger.debug(f"Saved metadata to: {metadata_path}")
    
    async def download_file(
        self,
        url: str,
        save_path: Path,
        session: Optional[aiohttp.ClientSession] = None
    ) -> bool:
        try:
            if session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                    if response.status == 200:
                        content = await response.read()
                        async with aiofiles.open(save_path, 'wb') as f:
                            await f.write(content)
                        return True
            else:
                async with aiohttp.ClientSession() as temp_session:
                    async with temp_session.get(url, timeout=aiohttp.ClientTimeout(total=60)) as response:
                        if response.status == 200:
                            content = await response.read()
                            async with aiofiles.open(save_path, 'wb') as f:
                                await f.write(content)
                            return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to download file {url}: {e}")
            return False
    
    async def create_document_index(self, documents: List[Document]):
        if not self.create_index:
            return
        
        index_path = self.output_dir / 'index.json'
        
        index_data = {
            'generated_at': datetime.now().isoformat(),
            'total_documents': len(documents),
            'documents': []
        }
        
        for doc in documents:
            index_data['documents'].append({
                'url': doc.url,
                'title': doc.title,
                'doc_type': doc.doc_type,
                'product': doc.product,
                'version': doc.version,
                'save_path': doc.save_path,
                'downloaded': doc.downloaded
            })
        
        async with aiofiles.open(index_path, 'w', encoding='utf-8') as f:
            await f.write(json.dumps(index_data, ensure_ascii=False, indent=2))
        
        logger.info(f"Created document index at: {index_path}")
        
        await self._create_html_index(documents)
    
    async def _create_html_index(self, documents: List[Document]):
        index_path = self.output_dir / 'index.html'
        
        grouped_docs = {}
        for doc in documents:
            product = doc.product or 'Unknown'
            if product not in grouped_docs:
                grouped_docs[product] = []
            grouped_docs[product].append(doc)
        
        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>华为E8000防火墙文档索引</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
        h1 {{ color: #333; border-bottom: 2px solid #007cba; padding-bottom: 10px; }}
        h2 {{ color: #007cba; margin-top: 30px; }}
        .stats {{ background: #f0f8ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        .doc-list {{ list-style: none; padding: 0; }}
        .doc-item {{ padding: 10px; border-bottom: 1px solid #eee; }}
        .doc-item:hover {{ background: #f9f9f9; }}
        .doc-title {{ font-weight: bold; }}
        .doc-meta {{ color: #666; font-size: 0.9em; margin-top: 5px; }}
        .doc-link {{ color: #007cba; text-decoration: none; }}
        .doc-link:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h1>华为E8000防火墙文档索引</h1>
    
    <div class="stats">
        <strong>生成时间:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
        <strong>文档总数:</strong> {len(documents)}
    </div>
"""
        
        for product, docs in grouped_docs.items():
            html_content += f"""
    <h2>{product} ({len(docs)} 个文档)</h2>
    <ul class="doc-list">
"""
            for doc in docs:
                relative_path = Path(doc.save_path).relative_to(self.output_dir) if doc.save_path else ''
                html_content += f"""
        <li class="doc-item">
            <div class="doc-title">
                <a href="{relative_path}" class="doc-link" target="_blank">{doc.title or '无标题'}</a>
            </div>
            <div class="doc-meta">
                类型: {doc.doc_type or '未知'} | 
                版本: {doc.version or '未知'} | 
                <a href="{doc.url}" target="_blank">原始链接</a>
            </div>
        </li>
"""
            
            html_content += "    </ul>\n"
        
        html_content += """
</body>
</html>
"""
        
        async with aiofiles.open(index_path, 'w', encoding='utf-8') as f:
            await f.write(html_content)
        
        logger.info(f"Created HTML index at: {index_path}")


class ConcurrentDownloader:
    
    def __init__(
        self,
        config: Dict[str, Any],
        storage: StorageManager
    ):
        self.config = config
        self.storage = storage
        
        request_config = config.get('crawler', {}).get('request', {})
        self.timeout = request_config.get('timeout', 30)
        self.base_headers = request_config.get('headers', {})
        
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
        
        self._downloaded_count = 0
        self._downloaded_lock = asyncio.Lock()
        self._failed_urls: List[str] = []
        self._failed_lock = asyncio.Lock()
    
    async def _get_headers(self) -> Dict[str, str]:
        headers = self.base_headers.copy()
        user_agent = await self.ua_rotator.get_user_agent()
        headers['User-Agent'] = user_agent
        return headers
    
    async def download_single_document(
        self,
        doc: Document,
        session: aiohttp.ClientSession
    ) -> Document:
        logger.debug(f"Downloading: {doc.title or 'No Title'} ({doc.url})")
        
        await self.rate_limiter.acquire()
        
        if doc.url.lower().endswith('.pdf'):
            return await self._download_pdf(doc, session)
        
        return await self._download_html(doc, session)
    
    async def _download_pdf(
        self,
        doc: Document,
        session: aiohttp.ClientSession
    ) -> Document:
        doc.file_type = 'pdf'
        save_path = self.storage.get_document_path(doc, 'pdf')
        
        try:
            headers = await self._get_headers()
            async with session.get(
                doc.url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(save_path, 'wb') as f:
                        await f.write(content)
                    
                    doc.downloaded = True
                    doc.save_path = str(save_path)
                    await self._increment_downloaded()
                    logger.info(f"Downloaded PDF: {doc.title}")
                else:
                    logger.warning(f"Failed to download PDF, status: {response.status}")
                    
        except Exception as e:
            logger.error(f"Error downloading PDF {doc.url}: {e}")
            await self._add_failed(doc.url)
        
        return doc
    
    async def _download_html(
        self,
        doc: Document,
        session: aiohttp.ClientSession
    ) -> Document:
        try:
            headers = await self._get_headers()
            async with session.get(
                doc.url,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status == 200:
                    content = await response.text()
                    doc.content = content
                    
                    if not doc.title or not doc.links:
                        soup = HtmlParser.parse(content, doc.url)
                        if not doc.title:
                            doc.title = HtmlParser.extract_title(soup)
                        if not doc.links:
                            doc.links = HtmlParser.extract_links(soup, doc.url)
                    
                    await self.storage.save_document(doc)
                    await self._increment_downloaded()
                    logger.info(f"Downloaded: {doc.title or doc.url}")
                else:
                    logger.warning(f"Failed to download HTML, status: {response.status}")
                    await self._add_failed(doc.url)
                    
        except Exception as e:
            logger.error(f"Error downloading {doc.url}: {e}")
            await self._add_failed(doc.url)
        
        return doc
    
    async def _increment_downloaded(self):
        async with self._downloaded_lock:
            self._downloaded_count += 1
    
    async def _add_failed(self, url: str):
        async with self._failed_lock:
            self._failed_urls.append(url)
    
    async def download_documents(
        self,
        documents: List[Document],
        max_concurrent: Optional[int] = None
    ) -> List[Document]:
        max_concurrent = max_concurrent or self.max_workers
        total = len(documents)
        
        logger.info(f"Starting concurrent download of {total} documents with {max_concurrent} workers...")
        
        self._downloaded_count = 0
        self._failed_urls = []
        
        download_queue = asyncio.Queue()
        for doc in documents:
            await download_queue.put(doc)
        
        results: List[Document] = []
        results_lock = asyncio.Lock()
        
        async def worker(worker_id: int):
            nonlocal results
            while True:
                try:
                    doc = await asyncio.wait_for(download_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    return
                
                try:
                    async with aiohttp.ClientSession() as session:
                        downloaded_doc = await self.download_single_document(doc, session)
                    
                    async with results_lock:
                        results.append(downloaded_doc)
                    
                    if self._downloaded_count % 10 == 0:
                        logger.info(f"Progress: {self._downloaded_count}/{total} downloaded")
                        
                except Exception as e:
                    logger.error(f"Worker {worker_id} error: {e}")
                finally:
                    download_queue.task_done()
        
        workers = [asyncio.create_task(worker(i)) for i in range(max_concurrent)]
        
        await download_queue.join()
        
        for w in workers:
            w.cancel()
        
        await asyncio.gather(*workers, return_exceptions=True)
        
        downloaded_docs = [doc for doc in results if doc.downloaded]
        
        logger.info("=" * 60)
        logger.info("Download Summary:")
        logger.info(f"  Total: {total}")
        logger.info(f"  Downloaded: {len(downloaded_docs)}")
        logger.info(f"  Failed: {len(self._failed_urls)}")
        if self._failed_urls:
            logger.info(f"  Failed URLs: {self._failed_urls[:5]}")
            if len(self._failed_urls) > 5:
                logger.info(f"  ... and {len(self._failed_urls) - 5} more")
        logger.info("=" * 60)
        
        return downloaded_docs


Downloader = ConcurrentDownloader
