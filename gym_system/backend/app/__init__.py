from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from config import config

db = SQLAlchemy()
jwt = JWTManager()

def create_app(config_name='default'):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config.get('CORS_ORIGINS', "*"),
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    db.init_app(app)
    jwt.init_app(app)
    
    @jwt.unauthorized_loader
    def unauthorized_callback(error):
        return jsonify({
            'code': 401,
            'message': '未授权访问，请先登录',
            'data': None
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'code': 401,
            'message': '无效的Token',
            'data': None
        }), 401
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'code': 401,
            'message': 'Token已过期，请重新登录',
            'data': None
        }), 401
    
    @app.before_request
    def handle_options():
        if request.method == 'OPTIONS':
            response = jsonify({'message': 'OK'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
            response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
            return response
    
    from routes.auth import auth_bp
    from routes.coach import coach_bp
    from routes.student import student_bp
    from routes.admin import admin_bp
    from routes.common import common_bp
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(coach_bp, url_prefix='/api/coach')
    app.register_blueprint(student_bp, url_prefix='/api/student')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(common_bp, url_prefix='/api/common')
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'code': 404,
            'message': '资源不存在',
            'data': None
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({
            'code': 500,
            'message': '服务器内部错误',
            'data': None
        }), 500
    
    return app
