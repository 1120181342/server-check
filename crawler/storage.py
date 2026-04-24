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
import requests
from bs4 import BeautifulSoup

from core import Document, HtmlParser

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
        soup = BeautifulSoup(html, 'lxml')
        
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
                response = requests.get(url, timeout=60, stream=True)
                if response.status_code == 200:
                    with open(save_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
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


class Downloader:
    
    def __init__(
        self,
        config: Dict[str, Any],
        storage: StorageManager
    ):
        self.config = config
        self.storage = storage
        
        request_config = config.get('crawler', {}).get('request', {})
        self.timeout = request_config.get('timeout', 30)
        self.headers = request_config.get('headers', {})
    
    async def download_document(
        self,
        doc: Document,
        session: Optional[aiohttp.ClientSession] = None
    ) -> Document:
        logger.info(f"Downloading document: {doc.title} ({doc.url})")
        
        if doc.url.lower().endswith('.pdf'):
            doc.file_type = 'pdf'
            save_path = self.storage.get_document_path(doc, 'pdf')
            success = await self.storage.download_file(
                doc.url, save_path, session
            )
            if success:
                doc.downloaded = True
                doc.save_path = str(save_path)
            return doc
        
        try:
            if session:
                async with session.get(
                    doc.url,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    if response.status == 200:
                        content = await response.text()
                        doc.content = content
                        
                        soup = HtmlParser.parse(content, doc.url)
                        if not doc.title:
                            doc.title = HtmlParser.extract_title(soup)
                        
                        await self.storage.save_document(doc)
            else:
                response = requests.get(
                    doc.url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                if response.status_code == 200:
                    doc.content = response.text
                    
                    soup = HtmlParser.parse(response.text, doc.url)
                    if not doc.title:
                        doc.title = HtmlParser.extract_title(soup)
                    
                    await self.storage.save_document(doc)
                    
        except Exception as e:
            logger.error(f"Failed to download document {doc.url}: {e}")
        
        return doc
    
    async def download_documents(
        self,
        documents: List[Document],
        max_concurrent: int = 5
    ) -> List[Document]:
        logger.info(f"Starting download of {len(documents)} documents...")
        
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def download_with_semaphore(doc: Document) -> Document:
                async with semaphore:
                    return await self.download_document(doc, session)
            
            tasks = [download_with_semaphore(doc) for doc in documents]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        downloaded_docs = []
        for result in results:
            if isinstance(result, Document):
                downloaded_docs.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Download task failed: {result}")
        
        logger.info(f"Downloaded {len(downloaded_docs)} of {len(documents)} documents")
        
        return downloaded_docs
