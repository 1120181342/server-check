# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 使用示例
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import ConfigManager, setup_logging
from core import Document
from discovery import HuaweiSupportCrawler, SearchEngine
from storage import Downloader, StorageManager


async def example_basic_usage():
    """
    基础使用示例：使用默认配置爬取文档
    """
    print("=" * 60)
    print("示例1: 基础使用 - 使用默认配置爬取文档")
    print("=" * 60)
    
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    setup_logging(config)
    
    storage = StorageManager(config)
    downloader = Downloader(config, storage)
    crawler = HuaweiSupportCrawler(config)
    
    keywords = [
        'Eudemon 8040',
        'Eudemon 8080',
        'Eudemon 8000',
    ]
    
    print(f"\n使用关键词: {keywords}")
    print("开始发现文档...")
    
    documents = await crawler.crawl(
        start_url=config.get('target', {}).get('search_url', ''),
        keywords=keywords,
        max_depth=2
    )
    
    print(f"\n发现 {len(documents)} 个文档")
    
    if documents:
        print(f"\n开始下载 {len(documents)} 个文档...")
        
        downloaded = await downloader.download_documents(
            documents,
            max_concurrent=3
        )
        
        await storage.create_document_index(downloaded)
        
        print(f"\n成功下载 {len(downloaded)} 个文档")
        print(f"输出目录: {storage.output_dir}")
        
        for doc in downloaded[:5]:
            print(f"  - {doc.title or '无标题'}: {doc.save_path}")


async def example_with_custom_config():
    """
    使用自定义配置示例
    """
    print("\n" + "=" * 60)
    print("示例2: 使用自定义配置")
    print("=" * 60)
    
    custom_config = {
        'crawler': {
            'request': {
                'timeout': 60,
                'max_retries': 5,
            },
            'concurrency': {
                'max_workers': 10,
                'rate_limit': 0.5,
            },
            'storage': {
                'output_dir': './custom_downloads',
            }
        },
        'target': {
            'base_url': 'https://support.huawei.com',
            'search_url': 'https://support.huawei.com/enterprisesearch/',
            'products': [
                {
                    'name': 'USG系列防火墙',
                    'keywords': ['USG6000', 'USG9000', 'USG5000']
                }
            ]
        }
    }
    
    config_manager = ConfigManager()
    config_manager.update(custom_config)
    config = config_manager.get_all()
    
    setup_logging(config)
    
    storage = StorageManager(config)
    downloader = Downloader(config, storage)
    crawler = HuaweiSupportCrawler(config)
    
    products = config.get('target', {}).get('products', [])
    keywords = []
    for product in products:
        keywords.extend(product.get('keywords', []))
    
    print(f"\n使用关键词: {keywords}")
    
    documents = await crawler.crawl(
        start_url=config.get('target', {}).get('search_url', ''),
        keywords=keywords,
        max_depth=1
    )
    
    print(f"\n发现 {len(documents)} 个文档")


async def example_single_document_download():
    """
    下载单个文档示例
    """
    print("\n" + "=" * 60)
    print("示例3: 下载单个文档")
    print("=" * 60)
    
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    setup_logging(config)
    
    storage = StorageManager(config)
    downloader = Downloader(config, storage)
    
    example_url = "https://support.huawei.com/enterprise/zh/doc/EDOC1000178159"
    
    print(f"\n下载文档: {example_url}")
    
    doc = Document(url=example_url)
    downloaded_doc = await downloader.download_document(doc)
    
    if downloaded_doc.downloaded:
        print(f"下载成功!")
        print(f"  标题: {downloaded_doc.title}")
        print(f"  保存路径: {downloaded_doc.save_path}")
    else:
        print("下载失败")


async def example_search_only():
    """
    仅搜索不下载示例
    """
    print("\n" + "=" * 60)
    print("示例4: 仅搜索文档（不下载）")
    print("=" * 60)
    
    config_manager = ConfigManager()
    config = config_manager.get_all()
    
    setup_logging(config)
    
    crawler = HuaweiSupportCrawler(config)
    
    keywords = ['Eudemon 8000', 'USG6000']
    
    print(f"\n搜索关键词: {keywords}")
    
    documents = await crawler.crawl(
        start_url=config.get('target', {}).get('search_url', ''),
        keywords=keywords,
        max_depth=2
    )
    
    print(f"\n发现 {len(documents)} 个文档:")
    for i, doc in enumerate(documents[:10], 1):
        print(f"  {i}. {doc.title or '无标题'}")
        print(f"     URL: {doc.url}")
        print(f"     类型: {doc.doc_type or '未知'}")
        print(f"     产品: {doc.product or '未知'}")
        print()
    
    if len(documents) > 10:
        print(f"... 还有 {len(documents) - 10} 个文档")


async def main():
    """
    运行所有示例
    """
    print("\n" + "#" * 60)
    print("# 华为E8000防火墙文档爬虫 - 使用示例")
    print("#" * 60)
    
    try:
        await example_basic_usage()
    except Exception as e:
        print(f"示例1执行出错: {e}")
    
    try:
        await example_with_custom_config()
    except Exception as e:
        print(f"示例2执行出错: {e}")
    
    try:
        await example_search_only()
    except Exception as e:
        print(f"示例4执行出错: {e}")
    
    print("\n" + "#" * 60)
    print("# 示例执行完成")
    print("#" * 60)


if __name__ == '__main__':
    asyncio.run(main())
