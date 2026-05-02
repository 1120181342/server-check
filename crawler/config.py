# -*- coding: utf-8 -*-
"""
华为E8000防火墙文档爬虫 - 配置管理模块
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


class ConfigManager:
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        env_file: Optional[str] = None
    ):
        self.config_path = config_path or self._get_default_config_path()
        self.env_file = env_file
        
        if self.env_file:
            load_dotenv(self.env_file)
        else:
            load_dotenv()
        
        self.config: Dict[str, Any] = {}
        self._load_config()
    
    def _get_default_config_path(self) -> str:
        current_dir = Path(__file__).parent
        config_path = current_dir / 'config.yaml'
        return str(config_path)
    
    def _load_config(self):
        config_file = Path(self.config_path)
        
        if config_file.exists():
            logger.info(f"Loading config from: {config_file}")
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f) or {}
        else:
            logger.warning(f"Config file not found: {config_file}, using defaults")
            self.config = self._get_default_config()
        
        self._override_with_env_vars()
    
    def _get_default_config(self) -> Dict[str, Any]:
        return {
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
                        'keywords': ['Eudemon 8040', 'Eudemon 8080', 'Eudemon 8000']
                    }
                ],
                'document_types': ['产品文档', '配置指南', '安装指南', '操作维护', '故障处理']
            },
            'filter': {
                'allowed_domains': ['support.huawei.com', 'e.huawei.com'],
                'excluded_patterns': [],
                'url_patterns': []
            }
        }
    
    def _override_with_env_vars(self):
        env_mappings = {
            'CRAWLER_TIMEOUT': ('crawler', 'request', 'timeout'),
            'CRAWLER_MAX_RETRIES': ('crawler', 'request', 'max_retries'),
            'CRAWLER_MAX_WORKERS': ('crawler', 'concurrency', 'max_workers'),
            'CRAWLER_RATE_LIMIT': ('crawler', 'concurrency', 'rate_limit'),
            'CRAWLER_OUTPUT_DIR': ('crawler', 'storage', 'output_dir'),
            'CRAWLER_LOG_LEVEL': ('crawler', 'logging', 'level'),
            'TARGET_BASE_URL': ('target', 'base_url'),
            'TARGET_SEARCH_URL': ('target', 'search_url'),
        }
        
        for env_var, config_path in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                self._set_nested_config(config_path, value)
    
    def _set_nested_config(self, path: tuple, value: Any):
        current = self.config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[path[-1]] = self._parse_value(value)
    
    def _parse_value(self, value: str) -> Any:
        if value.lower() in ('true', 'yes', '1'):
            return True
        if value.lower() in ('false', 'no', '0'):
            return False
        if value.isdigit():
            return int(value)
        try:
            return float(value)
        except ValueError:
            return value
    
    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_all(self) -> Dict[str, Any]:
        return self.config.copy()
    
    def update(self, updates: Dict[str, Any]):
        from deepmerge import always_merger
        always_merger.merge(self.config, updates)
    
    def validate(self) -> List[str]:
        errors = []
        
        required_keys = [
            'crawler.request.timeout',
            'crawler.concurrency.max_workers',
            'target.base_url',
        ]
        
        for key in required_keys:
            if self.get(key) is None:
                errors.append(f"Missing required config: {key}")
        
        if self.get('crawler.concurrency.max_workers', 0) <= 0:
            errors.append("max_workers must be greater than 0")
        
        if self.get('crawler.request.timeout', 0) <= 0:
            errors.append("timeout must be greater than 0")
        
        return errors


def setup_logging(config: Dict[str, Any]):
    logging_config = config.get('crawler', {}).get('logging', {})
    
    level_name = logging_config.get('level', 'INFO')
    level = getattr(logging, level_name.upper(), logging.INFO)
    
    format_str = logging_config.get(
        'format',
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logging.basicConfig(
        level=level,
        format=format_str,
        handlers=[
            logging.StreamHandler()
        ]
    )
    
    log_file = logging_config.get('file')
    if log_file:
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(logging.Formatter(format_str))
        logging.getLogger().addHandler(file_handler)
    
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('aiohttp').setLevel(logging.WARNING)
    
    logger.info(f"Logging configured with level: {level_name}")
