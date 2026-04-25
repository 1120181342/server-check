# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 用户管理路由
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func

from app import db
from app.models.user import User, Role

users_bp = Blueprint('users', __name__)


def get_current_user():
    """获取当前用户"""
    current_user_id = get_jwt_identity()
    return User.query.get(current_user_id)


def has_permission(permission):
    """检查权限"""
    user = get_current_user()
    if user and user.has_permission(permission):
        return True
    return False


@users_bp.route('/', methods=['GET'])
@jwt_required()
def get_users():
    """获取用户列表"""
    if not has_permission('user_manage'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    users = User.query.all()
    
    result = []
    for user in users:
        result.append(user.to_dict(include_role=True))
    
    return jsonify({
        'message': '获取成功',
        'data': result
    }), 200


@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """获取单个用户详情"""
    if not has_permission('user_manage'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': '用户不存在'
        }), 404
    
    return jsonify({
        'message': '获取成功',
        'data': user.to_dict(include_role=True)
    }), 200


@users_bp.route('/', methods=['POST'])
@jwt_required()
def create_user():
    """创建用户"""
    if not has_permission('user_manage'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    data = request.get_json()
    
    if not data.get('username') or not data.get('password'):
        return jsonify({
            'error': 'Bad Request',
            'message': '用户名和密码不能为空'
        }), 400
    
    existing_user = User.query.filter_by(username=data['username']).first()
    if existing_user:
        return jsonify({
            'error': 'Conflict',
            'message': '用户名已存在'
        }), 409
    
    if data.get('email'):
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({
                'error': 'Conflict',
                'message': '邮箱已被使用'
            }), 409
    
    user = User(
        username=data['username'],
        email=data.get('email'),
        real_name=data.get('real_name'),
        phone=data.get('phone'),
        status=data.get('status', 'active'),
        role_id=data.get('role_id')
    )
    user.password = data['password']
    
    db.session.add(user)
    db.session.commit()
    
    return jsonify({
        'message': '创建用户成功',
        'data': user.to_dict(include_role=True)
    }), 201


@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user(user_id):
    """更新用户"""
    if not has_permission('user_manage'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': '用户不存在'
        }), 404
    
    data = request.get_json()
    
    if data.get('username') and data['username'] != user.username:
        existing_user = User.query.filter_by(username=data['username']).first()
        if existing_user:
            return jsonify({
                'error': 'Conflict',
                'message': '用户名已存在'
            }), 409
        user.username = data['username']
    
    if data.get('email') and data['email'] != user.email:
        existing_email = User.query.filter_by(email=data['email']).first()
        if existing_email:
            return jsonify({
                'error': 'Conflict',
                'message': '邮箱已被使用'
            }), 409
        user.email = data['email']
    
    if data.get('real_name'):
        user.real_name = data['real_name']
    if data.get('phone'):
        user.phone = data['phone']
    if data.get('status'):
        user.status = data['status']
    if data.get('role_id'):
        user.role_id = data['role_id']
    if data.get('password'):
        user.password = data['password']
    
    db.session.commit()
    
    return jsonify({
        'message': '更新用户成功',
        'data': user.to_dict(include_role=True)
    }), 200


@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    """删除用户"""
    if not has_permission('user_manage'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    current_user = get_current_user()
    if current_user and current_user.id == user_id:
        return jsonify({
            'error': 'Bad Request',
            'message': '不能删除自己的账号'
        }), 400
    
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({
            'error': 'Not Found',
            'message': '用户不存在'
        }), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({
        'message': '删除用户成功'
    }), 200


@users_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """获取角色列表"""
    if not has_permission('user_manage'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    roles = Role.query.all()
    
    result = []
    for role in roles:
        result.append(role.to_dict())
    
    return jsonify({
        'message': '获取成功',
        'data': result
    }), 200
