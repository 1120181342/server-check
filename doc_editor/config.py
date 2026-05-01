# -*- coding: utf-8 -*-
"""
文档编辑器 - 配置文件
"""

import os
from datetime import timedelta
from pathlib import Path

basedir = Path(__file__).parent.absolute()


class Config:
    """基础配置类"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'doc-editor-secret-key-2024'
    
    # SQLAlchemy配置
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False  # 生产环境关闭，提升性能
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
    }
    
    # JWT配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    JWT_TOKEN_LOCATION = ['headers']
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
    
    # 文件存储配置
    FILE_STORAGE_PATH = basedir / 'storage' / 'files'
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # CORS配置（默认不启用，生产环境同源部署不需要）
    ENABLE_CORS = os.environ.get('ENABLE_CORS', 'False').lower() == 'true'
    
    # 性能优化配置
    USE_X_SENDFILE = True  # 允许Nginx直接处理文件下载
    SEND_FILE_MAX_AGE_DEFAULT = 86400  # 静态文件缓存1天
    
    @staticmethod
    def init_app(app):
        # 确保文件存储目录存在
        if not os.path.exists(Config.FILE_STORAGE_PATH):
            os.makedirs(Config.FILE_STORAGE_PATH, exist_ok=True)
        
        # 确保instance目录存在
        instance_path = basedir / 'instance'
        if not os.path.exists(instance_path):
            os.makedirs(instance_path, exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    
    DEBUG = True
    TESTING = False
    
    # 开发环境可以启用CORS（前后端分离开发时）
    ENABLE_CORS = os.environ.get('ENABLE_CORS', 'True').lower() == 'true'
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "doc_editor_dev.db"}'
    
    # 开发环境启用查询记录（用于调试）
    SQLALCHEMY_RECORD_QUERIES = True


class TestingConfig(Config):
    """测试环境配置"""
    
    TESTING = True
    DEBUG = False
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "doc_editor_test.db"}'
    
    # 测试环境使用更快的密码哈希
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """生产环境配置"""
    
    DEBUG = False
    TESTING = False
    
    # 生产环境强制不启用CORS（同源部署）
    ENABLE_CORS = False
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "doc_editor_prod.db"}'
    
    # 生产环境安全配置
    SESSION_COOKIE_SECURE = True  # 仅通过HTTPS传输Cookie
    SESSION_COOKIE_HTTPONLY = True  # 防止JavaScript访问Cookie
    SESSION_COOKIE_SAMESITE = 'Lax'  # 防止CSRF攻击
    
    # 生产环境使用更强的JWT配置
    JWT_COOKIE_SECURE = True
    JWT_COOKIE_HTTPONLY = True
    JWT_COOKIE_SAMESITE = 'Lax'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # 生产环境日志配置
        import logging
        from logging.handlers import RotatingFileHandler
        from logging import Formatter
        
        # 确保日志目录存在
        log_dir = basedir / 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # 文件日志处理器
        file_handler = RotatingFileHandler(
            log_dir / 'doc_editor.log',
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        
        # 控制台日志处理器
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(Formatter(
            '%(asctime)s %(levelname)s: %(message)s'
        ))
        console_handler.setLevel(logging.INFO)
        
        # 配置根日志记录器
        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.setLevel(logging.INFO)
        
        # 配置Flask应用日志
        app.logger.addHandler(file_handler)
        app.logger.addHandler(console_handler)
        app.logger.setLevel(logging.INFO)
        
        app.logger.info('=' * 50)
        app.logger.info('文档编辑器生产环境启动')
        app.logger.info(f'数据库: {app.config["SQLALCHEMY_DATABASE_URI"]}')
        app.logger.info(f'CORS启用: {app.config["ENABLE_CORS"]}')
        app.logger.info('=' * 50)


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
