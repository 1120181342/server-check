# -*- coding: utf-8 -*-
"""
文档编辑器 - 应用初始化
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from config import config

db = SQLAlchemy()
jwt = JWTManager()


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__, static_folder='static', template_folder='templates')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    jwt.init_app(app)
    
    # 仅在开发环境需要时启用CORS（前后端分离开发时）
    # 生产环境使用Nginx反向代理，同源部署，不需要CORS
    if app.config.get('ENABLE_CORS', False):
        from flask_cors import CORS
        CORS(app)
    
    # 注册蓝图
    from app.routes.auth import auth_bp
    from app.routes.files import files_bp
    from app.routes.main import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(files_bp, url_prefix='/api/files')
    app.register_blueprint(main_bp)
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
    
    return app
