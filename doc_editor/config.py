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
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    # 文件存储配置
    FILE_STORAGE_PATH = basedir / 'storage' / 'files'
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @staticmethod
    def init_app(app):
        # 确保文件存储目录存在
        if not os.path.exists(Config.FILE_STORAGE_PATH):
            os.makedirs(Config.FILE_STORAGE_PATH, exist_ok=True)


class DevelopmentConfig(Config):
    """开发环境配置"""
    
    DEBUG = True
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "doc_editor_dev.db"}'


class TestingConfig(Config):
    """测试环境配置"""
    
    TESTING = True
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "doc_editor_test.db"}'


class ProductionConfig(Config):
    """生产环境配置"""
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "doc_editor_prod.db"}'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/doc_editor.log',
            maxBytes=10240000,
            backupCount=10,
            encoding='utf-8'
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Document Editor Startup')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
