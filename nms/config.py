# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 配置文件
"""

import os
from datetime import timedelta
from pathlib import Path

basedir = Path(__file__).parent.absolute()


class Config:
    """基础配置类"""
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'cloud-nms-secret-key-2024'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key-2024'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=2)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=7)
    
    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    """开发环境配置"""
    
    DEBUG = True
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "nms_dev.db"}'


class TestingConfig(Config):
    """测试环境配置"""
    
    TESTING = True
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "nms_test.db"}'


class ProductionConfig(Config):
    """生产环境配置"""
    
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        f'sqlite:///{basedir / "instance" / "nms_prod.db"}'
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        import logging
        from logging.handlers import RotatingFileHandler
        
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler(
            'logs/nms.log',
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
        app.logger.info('Cloud NMS Startup')


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
