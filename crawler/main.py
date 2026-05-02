# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 主程序入口
"""

import asyncio
import logging
from pathlib import Path
from typing import List, Optional

import click

from config import ConfigManager, setup_logging
from core import Document
from discovery import HuaweiSupportCrawler, SearchEngine
from storage import Downloader, StorageManager

logger = logging.getLogger(__name__)


class HuaweiDocumentCrawler:
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_all()
        
        setup_logging(self.config)
        
        self.storage = StorageManager(self.config)
        self.downloader = Downloader(self.config, self.storage)
        self.search_engine = SearchEngine(self.config)
        
        self.crawler: Optional[HuaweiSupportCrawler] = None
    
    async def run(
        self,
        keywords: Optional[List[str]] = None,
        start_url: Optional[str] = None,
        max_depth: int = 3,
        download: bool = True
    ) -> List[Document]:
        logger.info("=" * 60)
        logger.info("华为E8000防火墙文档爬虫启动")
        logger.info("=" * 60)
        
        errors = self.config_manager.validate()
        if errors:
            for error in errors:
                logger.warning(f"Config warning: {error}")
        
        self.crawler = HuaweiSupportCrawler(self.config)
        
        search_keywords = keywords or self._get_default_keywords()
        logger.info(f"使用搜索关键词: {search_keywords}")
        
        target_url = start_url or self.config.get('target', {}).get('search_url', '')
        
        logger.info(f"开始爬取，起始URL: {target_url}")
        logger.info(f"最大深度: {max_depth}")
        
        documents = await self.crawler.crawl(
            start_url=target_url,
            keywords=search_keywords,
            max_depth=max_depth
        )
        
        logger.info(f"发现 {len(documents)} 个文档")
        
        if download and documents:
            logger.info(f"开始下载 {len(documents)} 个文档...")
            
            max_workers = self.config.get('crawler', {}).get('concurrency', {}).get('max_workers', 5)
            downloaded_docs = await self.downloader.download_documents(
                documents,
                max_concurrent=max_workers
            )
            
            await self.storage.create_document_index(downloaded_docs)
            
            logger.info(f"成功下载 {len(downloaded_docs)} 个文档")
            return downloaded_docs
        
        return documents
    
    def _get_default_keywords(self) -> List[str]:
        keywords = []
        products = self.config.get('target', {}).get('products', [])
        
        for product in products:
            product_keywords = product.get('keywords', [])
            keywords.extend(product_keywords)
        
        if not keywords:
            keywords = [
                'Eudemon 8040',
                'Eudemon 8080',
                'Eudemon 8000',
                'USG6000',
                'USG9000'
            ]
        
        return keywords
    
    def get_statistics(self) -> dict:
        stats = {
            'visited_urls': len(self.crawler.visited_urls) if self.crawler else 0,
            'found_documents': len(self.crawler.found_documents) if self.crawler else 0,
            'output_directory': str(self.storage.output_dir),
        }
        return stats


@click.group()
def cli():
    """华为E8000防火墙文档爬虫工具"""
    pass


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--keyword', '-k', multiple=True, help='搜索关键词（可多次指定）')
@click.option('--url', '-u', help='起始URL')
@click.option('--depth', '-d', default=3, type=int, help='爬取深度（默认3）')
@click.option('--no-download', is_flag=True, help='只发现文档，不下载')
@click.option('--output', '-o', type=click.Path(), help='输出目录')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
def crawl(
    config: Optional[str],
    keyword: tuple,
    url: Optional[str],
    depth: int,
    no_download: bool,
    output: Optional[str],
    verbose: bool
):
    """爬取华为E8000防火墙文档"""
    
    crawler = HuaweiDocumentCrawler(config)
    
    if output:
        crawler.config['crawler']['storage']['output_dir'] = output
    
    if verbose:
        crawler.config['crawler']['logging']['level'] = 'DEBUG'
        setup_logging(crawler.config)
    
    keywords = list(keyword) if keyword else None
    
    loop = asyncio.get_event_loop()
    try:
        documents = loop.run_until_complete(
            crawler.run(
                keywords=keywords,
                start_url=url,
                max_depth=depth,
                download=not no_download
            )
        )
        
        stats = crawler.get_statistics()
        
        click.echo("=" * 60)
        click.echo("爬取完成")
        click.echo("=" * 60)
        click.echo(f"访问URL数: {stats['visited_urls']}")
        click.echo(f"发现文档数: {stats['found_documents']}")
        click.echo(f"输出目录: {stats['output_directory']}")
        
        if documents:
            click.echo(f"\n下载的文档 ({len(documents)}):")
            for doc in documents[:10]:
                click.echo(f"  - {doc.title or '无标题'}")
            if len(documents) > 10:
                click.echo(f"  ... 还有 {len(documents) - 10} 个文档")
                
    except KeyboardInterrupt:
        click.echo("用户中断，正在退出...")
    except Exception as e:
        logger.exception(f"爬取过程中出错: {e}")
        click.echo(f"错误: {e}", err=True)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--url', '-u', required=True, help='要下载的文档URL')
@click.option('--output', '-o', type=click.Path(), help='输出目录')
def download(config: Optional[str], url: str, output: Optional[str]):
    """下载单个文档"""
    
    crawler = HuaweiDocumentCrawler(config)
    
    if output:
        crawler.config['crawler']['storage']['output_dir'] = output
    
    loop = asyncio.get_event_loop()
    try:
        doc = Document(url=url)
        
        click.echo(f"下载文档: {url}")
        
        downloaded_doc = loop.run_until_complete(
            crawler.downloader.download_document(doc)
        )
        
        if downloaded_doc.downloaded:
            click.echo(f"下载成功: {downloaded_doc.save_path}")
        else:
            click.echo("下载失败")
            
    except Exception as e:
        logger.exception(f"下载过程中出错: {e}")
        click.echo(f"错误: {e}", err=True)


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
def info(config: Optional[str]):
    """显示配置信息"""
    
    crawler = HuaweiDocumentCrawler(config)
    
    click.echo("=" * 60)
    click.echo("华为E8000防火墙文档爬虫配置")
    click.echo("=" * 60)
    
    config = crawler.config
    
    click.echo(f"\n爬虫设置:")
    crawler_config = config.get('crawler', {})
    click.echo(f"  名称: {crawler_config.get('name')}")
    click.echo(f"  版本: {crawler_config.get('version')}")
    
    click.echo(f"\n请求设置:")
    request_config = crawler_config.get('request', {})
    click.echo(f"  超时: {request_config.get('timeout')}秒")
    click.echo(f"  最大重试: {request_config.get('max_retries')}次")
    click.echo(f"  User-Agent: {request_config.get('headers', {}).get('User-Agent', '')[:50]}...")
    
    click.echo(f"\n并发设置:")
    concurrency_config = crawler_config.get('concurrency', {})
    click.echo(f"  最大并发: {concurrency_config.get('max_workers')}")
    click.echo(f"  速率限制: {concurrency_config.get('rate_limit')}请求/秒")
    
    click.echo(f"\n存储设置:")
    storage_config = crawler_config.get('storage', {})
    click.echo(f"  输出目录: {storage_config.get('output_dir')}")
    click.echo(f"  保存HTML: {storage_config.get('save_html')}")
    click.echo(f"  保存PDF: {storage_config.get('save_pdf')}")
    click.echo(f"  创建索引: {storage_config.get('create_index')}")
    
    click.echo(f"\n目标产品:")
    target_config = config.get('target', {})
    products = target_config.get('products', [])
    
    for product in products:
        click.echo(f"\n  - {product.get('name')}:")
        keywords = product.get('keywords', [])
        for keyword in keywords:
            click.echo(f"    * {keyword}")
    
    click.echo(f"\n文档类型:")
    doc_types = target_config.get('document_types', [])
    for doc_type in doc_types:
        click.echo(f"  - {doc_type}")
    
    click.echo(f"\n允许的域名:")
    filter_config = config.get('filter', {})
    allowed_domains = filter_config.get('allowed_domains', [])
    for domain in allowed_domains:
        click.echo(f"  - {domain}")


@cli.command()
@click.option('--config', '-c', type=click.Path(exists=True), help='配置文件路径')
@click.option('--output', '-o', type=click.Path(), help='输出目录')
def init(config: Optional[str], output: Optional[str]):
    """初始化爬虫环境"""
    
    output_dir = Path(output or './crawler')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        'crawler': {
            'name': 'Huawei E8000 Firewall Document Crawler',
            'version': '1.0.0',
            'request': {
                'timeout': 30,
                'max_retries': 3,
                'retry_delay': 2,
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                }
            },
            'concurrency': {
                'max_workers': 5,
                'rate_limit': 1.0
            },
            'storage': {
                'output_dir': './downloads',
                'save_html': True,
                'save_pdf': True,
                'create_index': True
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            }
        },
        'target': {
            'base_url': 'https://support.huawei.com',
            'search_url': 'https://support.huawei.com/enterprisesearch/',
            'products': [
                {
                    'name': 'Eudemon 8000系列',
                    'keywords': ['Eudemon 8040', 'Eudemon 8080', 'Eudemon 8000', 'Quidway Eudemon 8040', 'Quidway Eudemon 8080']
                },
                {
                    'name': 'USG系列',
                    'keywords': ['USG6000', 'USG9000', 'USG5000']
                }
            ],
            'document_types': ['产品文档', '配置指南', '安装指南', '操作维护', '故障处理', '版本文档']
        },
        'filter': {
            'allowed_domains': ['support.huawei.com', 'e.huawei.com'],
            'excluded_patterns': ['.*login.*', '.*register.*'],
            'url_patterns': []
        }
    }
    
    import yaml
    config_path = output_dir / 'config.yaml'
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(default_config, f, allow_unicode=True, default_flow_style=False, indent=2)
    
    click.echo(f"配置文件已创建: {config_path}")
    
    requirements = """requests>=2.28.0
beautifulsoup4>=4.11.0
lxml>=4.9.0
aiohttp>=3.8.0
pyyaml>=6.0
python-dotenv>=1.0.0
click>=8.0.0
tqdm>=4.64.0
coloredlogs>=15.0.0
tenacity>=8.2.0
furl>=2.1.0
"""
    
    req_path = output_dir / 'requirements.txt'
    with open(req_path, 'w', encoding='utf-8') as f:
        f.write(requirements)
    
    click.echo(f"依赖文件已创建: {req_path}")
    
    click.echo(f"\n初始化完成！")
    click.echo(f"请运行以下命令安装依赖:")
    click.echo(f"  pip install -r {req_path}")
    click.echo(f"\n然后运行以下命令开始爬取:")
    click.echo(f"  python main.py crawl -c {config_path}")


if __name__ == '__main__':
    cli()
