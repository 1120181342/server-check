from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, create_refresh_token, jwt_required, get_jwt_identity
from models import User, Role, Coach, Student
from app import db
from datetime import datetime
from routes import log_operation, get_current_user

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({
                'code': 400,
                'message': '请求数据为空',
                'data': None
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'code': 400,
                'message': '用户名和密码不能为空',
                'data': None
            }), 400
        
        user = User.query.filter_by(username=username).first()
        
        if not user or not user.check_password(password):
            return jsonify({
                'code': 401,
                'message': '用户名或密码错误',
                'data': None
            }), 401
        
        if user.status != 1:
            return jsonify({
                'code': 403,
                'message': '账号已被禁用，请联系管理员',
                'data': None
            }), 403
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token = create_access_token(identity={
            'id': user.id,
            'username': user.username,
            'role': user.role.role_name
        })
        refresh_token = create_refresh_token(identity={
            'id': user.id,
            'username': user.username,
            'role': user.role.role_name
        })
        
        log_operation(
            user_id=user.id,
            operation='用户登录',
            module='认证',
            detail=f'用户 {user.username} 登录系统',
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string
        )
        
        user_info = user.to_dict()
        
        if user.role.role_name == 'coach':
            coach = Coach.query.filter_by(user_id=user.id).first()
            if coach:
                user_info['coach_info'] = coach.to_dict()
        elif user.role.role_name == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                user_info['student_info'] = student.to_dict()
        
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user_info': user_info
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'登录失败: {str(e)}',
            'data': None
        }), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    try:
        identity = get_jwt_identity()
        user = User.query.get(identity.get('id'))
        
        if not user or user.status != 1:
            return jsonify({
                'code': 401,
                'message': '用户不存在或已被禁用',
                'data': None
            }), 401
        
        new_access_token = create_access_token(identity={
            'id': user.id,
            'username': user.username,
            'role': user.role.role_name
        })
        
        return jsonify({
            'code': 200,
            'message': 'Token刷新成功',
            'data': {
                'access_token': new_access_token
            }
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'Token刷新失败: {str(e)}',
            'data': None
        }), 500

@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    try:
        user = get_current_user()
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户不存在',
                'data': None
            }), 401
        
        user_info = user.to_dict()
        
        if user.role.role_name == 'coach':
            coach = Coach.query.filter_by(user_id=user.id).first()
            if coach:
                user_info['coach_info'] = coach.to_dict()
        elif user.role.role_name == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                user_info['student_info'] = student.to_dict()
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': user_info
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取用户信息失败: {str(e)}',
            'data': None
        }), 500

@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    try:
        data = request.get_json()
        user = get_current_user()
        
        if not user:
            return jsonify({
                'code': 401,
                'message': '用户不存在',
                'data': None
            }), 401
        
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        if not old_password or not new_password:
            return jsonify({
                'code': 400,
                'message': '原密码和新密码不能为空',
                'data': None
            }), 400
        
        if not user.check_password(old_password):
            return jsonify({
                'code': 400,
                'message': '原密码错误',
                'data': None
            }), 400
        
        if len(new_password) < 6:
            return jsonify({
                'code': 400,
                'message': '新密码长度不能少于6位',
                'data': None
            }), 400
        
        user.set_password(new_password)
        db.session.commit()
        
        log_operation(
            user_id=user.id,
            operation='修改密码',
            module='认证',
            detail=f'用户 {user.username} 修改了密码',
            ip_address=request.remote_addr
        )
        
        return jsonify({
            'code': 200,
            'message': '密码修改成功',
            'data': None
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'code': 500,
            'message': f'密码修改失败: {str(e)}',
            'data': None
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        user = get_current_user()
        
        if user:
            log_operation(
                user_id=user.id,
                operation='用户登出',
                module='认证',
                detail=f'用户 {user.username} 退出系统',
                ip_address=request.remote_addr
            )
        
        return jsonify({
            'code': 200,
            'message': '登出成功',
            'data': None
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'登出失败: {str(e)}',
            'data': None
        }), 500
