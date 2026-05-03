# -*- coding: utf-8 -*-
"""
文档编辑器 - 认证路由
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity,
    get_jwt
)
from app import db
from app.models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({
            'error': 'Bad Request',
            'message': '用户名和密码不能为空'
        }), 400
    
    # 检查用户名是否已存在
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({
            'error': 'Conflict',
            'message': '用户名已存在'
        }), 409
    
    # 检查邮箱是否已存在（如果提供）
    if data.get('email'):
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({
                'error': 'Conflict',
                'message': '邮箱已被使用'
            }), 409
    
    # 创建新用户
    user = User(
        username=data['username'],
        email=data.get('email'),
        real_name=data.get('real_name')
    )
    user.password = data['password']
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '注册成功',
        'data': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({
            'error': 'Bad Request',
            'message': '用户名和密码不能为空'
        }), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.verify_password(data['password']):
        return jsonify({
            'error': 'Unauthorized',
            'message': '用户名或密码错误'
        }), 401
    
    if user.status != 'active':
        return jsonify({
            'error': 'Forbidden',
            'message': '账号已被禁用，请联系管理员'
        }), 403
    
    user.last_login_at = datetime.utcnow()
    db.session.commit()
    
    additional_claims = {
        'user_id': user.id,
        'username': user.username
    }
    
    access_token = create_access_token(
        identity=user.id,
        additional_claims=additional_claims
    )
    refresh_token = create_refresh_token(identity=user.id)
    
    return jsonify({
        'message': '登录成功',
        'data': {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }
    }), 200


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新Token"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({
            'error': 'Unauthorized',
            'message': '用户不存在'
        }), 401
    
    additional_claims = {
        'user_id': user.id,
        'username': user.username
    }
    
    access_token = create_access_token(
        identity=user.id,
        additional_claims=additional_claims
    )
    
    return jsonify({
        'message': 'Token刷新成功',
        'data': {
            'access_token': access_token
        }
    }), 200


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """获取当前用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': '用户不存在'
        }), 404
    
    return jsonify({
        'message': '获取成功',
        'data': user.to_dict()
    }), 200


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """更新当前用户信息"""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': '用户不存在'
        }), 404
    
    data = request.get_json()
    
    if data.get('email'):
        existing = User.query.filter_by(email=data['email']).first()
        if existing and existing.id != user.id:
            return jsonify({
                'error': 'Conflict',
                'message': '邮箱已被使用'
            }), 409
        user.email = data['email']
    
    if data.get('real_name'):
        user.real_name = data['real_name']
    
    if data.get('password'):
        user.password = data['password']
    
    db.session.commit()
    
    return jsonify({
        'message': '更新成功',
        'data': user.to_dict()
    }), 200


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用户登出"""
    return jsonify({
        'message': '登出成功'
    }), 200
