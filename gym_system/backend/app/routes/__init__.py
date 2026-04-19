from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from models import User, Role, OperationLog
from app import db
from datetime import datetime

def role_required(*required_roles):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            identity = get_jwt_identity()
            
            if not identity:
                return jsonify({
                    'code': 401,
                    'message': '未授权访问',
                    'data': None
                }), 401
            
            user = User.query.get(identity.get('id'))
            if not user:
                return jsonify({
                    'code': 401,
                    'message': '用户不存在',
                    'data': None
                }), 401
            
            if user.status != 1:
                return jsonify({
                    'code': 403,
                    'message': '账号已被禁用',
                    'data': None
                }), 403
            
            user_role = user.role.role_name if user.role else None
            if user_role not in required_roles:
                return jsonify({
                    'code': 403,
                    'message': '权限不足',
                    'data': None
                }), 403
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def log_operation(user_id, operation, module, detail=None, ip_address=None, user_agent=None):
    try:
        log = OperationLog(
            user_id=user_id,
            operation=operation,
            module=module,
            detail=detail,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f'Log operation failed: {e}')

def get_current_user():
    verify_jwt_in_request()
    identity = get_jwt_identity()
    if identity:
        return User.query.get(identity.get('id'))
    return None
