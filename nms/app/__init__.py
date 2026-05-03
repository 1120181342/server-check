# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 应用初始化
"""

from flask import Flask, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_cors import CORS

from config import config

db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()


def create_app(config_name='default'):
    """应用工厂函数"""
    
    app = Flask(__name__, static_folder='static', static_url_path='/static')
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    CORS(app, supports_credentials=True)
    
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    
    from app.routes.auth import auth_bp
    from app.routes.users import users_bp
    from app.routes.devices import devices_bp
    from app.routes.alarms import alarms_bp
    from app.routes.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(devices_bp, url_prefix='/api/devices')
    app.register_blueprint(alarms_bp, url_prefix='/api/alarms')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    
    @app.route('/')
    def index():
        return send_from_directory('static', 'index.html')
    
    @app.route('/<path:path>')
    def static_proxy(path):
        return send_from_directory('static', path)
    
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'ok',
            'message': 'Cloud NMS API is running'
        })
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500
    
    return app
