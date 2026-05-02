# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 告警管理路由
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from app.models.user import User
from app.models.alarm import Alarm

alarms_bp = Blueprint('alarms', __name__)


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


@alarms_bp.route('/', methods=['GET'])
@jwt_required()
def get_alarms():
    """获取告警列表"""
    if not has_permission('alarm_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    severity = request.args.get('severity', '')
    status = request.args.get('status', '')
    
    query = Alarm.query
    
    if severity:
        query = query.filter(Alarm.severity == severity)
    if status:
        query = query.filter(Alarm.status == status)
    
    alarms = query.order_by(Alarm.created_at.desc()).all()
    
    result = []
    for alarm in alarms:
        result.append(alarm.to_dict(include_device=True))
    
    return jsonify({
        'message': '获取成功',
        'data': result
    }), 200


@alarms_bp.route('/<int:alarm_id>', methods=['GET'])
@jwt_required()
def get_alarm(alarm_id):
    """获取单个告警详情"""
    if not has_permission('alarm_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    alarm = Alarm.query.get(alarm_id)
    
    if not alarm:
        return jsonify({
            'error': 'Not Found',
            'message': '告警不存在'
        }), 404
    
    return jsonify({
        'message': '获取成功',
        'data': alarm.to_dict(include_device=True)
    }), 200


@alarms_bp.route('/', methods=['POST'])
@jwt_required()
def create_alarm():
    """创建告警"""
    if not has_permission('alarm_modify'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    data = request.get_json()
    
    if not data.get('title'):
        return jsonify({
            'error': 'Bad Request',
            'message': '告警标题不能为空'
        }), 400
    
    alarm = Alarm(
        device_id=data.get('device_id'),
        alarm_type=data.get('alarm_type', 'other'),
        severity=data.get('severity', 'info'),
        title=data['title'],
        description=data.get('description'),
        status=data.get('status', 'active')
    )
    
    db.session.add(alarm)
    db.session.commit()
    
    return jsonify({
        'message': '创建告警成功',
        'data': alarm.to_dict()
    }), 201


@alarms_bp.route('/<int:alarm_id>', methods=['PUT'])
@jwt_required()
def update_alarm(alarm_id):
    """更新告警"""
    if not has_permission('alarm_modify'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    alarm = Alarm.query.get(alarm_id)
    
    if not alarm:
        return jsonify({
            'error': 'Not Found',
            'message': '告警不存在'
        }), 404
    
    data = request.get_json()
    
    if data.get('title'):
        alarm.title = data['title']
    if data.get('description'):
        alarm.description = data['description']
    if data.get('severity'):
        alarm.severity = data['severity']
    if data.get('status'):
        alarm.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'message': '更新告警成功',
        'data': alarm.to_dict()
    }), 200


@alarms_bp.route('/<int:alarm_id>/acknowledge', methods=['POST'])
@jwt_required()
def acknowledge_alarm(alarm_id):
    """确认告警"""
    if not has_permission('alarm_modify'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    alarm = Alarm.query.get(alarm_id)
    
    if not alarm:
        return jsonify({
            'error': 'Not Found',
            'message': '告警不存在'
        }), 404
    
    current_user = get_current_user()
    
    alarm.status = 'acknowledged'
    alarm.acknowledged_at = datetime.utcnow()
    if current_user:
        alarm.acknowledged_by = current_user.id
    
    db.session.commit()
    
    return jsonify({
        'message': '确认告警成功',
        'data': alarm.to_dict()
    }), 200


@alarms_bp.route('/<int:alarm_id>/resolve', methods=['POST'])
@jwt_required()
def resolve_alarm(alarm_id):
    """解决告警"""
    if not has_permission('alarm_modify'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    alarm = Alarm.query.get(alarm_id)
    
    if not alarm:
        return jsonify({
            'error': 'Not Found',
            'message': '告警不存在'
        }), 404
    
    data = request.get_json() or {}
    current_user = get_current_user()
    
    alarm.status = 'resolved'
    alarm.resolved_at = datetime.utcnow()
    if current_user:
        alarm.resolved_by = current_user.id
    if data.get('resolution_notes'):
        alarm.resolution_notes = data['resolution_notes']
    
    db.session.commit()
    
    return jsonify({
        'message': '解决告警成功',
        'data': alarm.to_dict()
    }), 200


@alarms_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_alarm_stats():
    """获取告警统计"""
    if not has_permission('alarm_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    total = Alarm.query.count()
    active = Alarm.query.filter_by(status='active').count()
    acknowledged = Alarm.query.filter_by(status='acknowledged').count()
    resolved = Alarm.query.filter_by(status='resolved').count()
    
    critical = Alarm.query.filter_by(severity='critical').count()
    warning = Alarm.query.filter_by(severity='warning').count()
    info = Alarm.query.filter_by(severity='info').count()
    
    return jsonify({
        'message': '获取成功',
        'data': {
            'total': total,
            'by_status': {
                'active': active,
                'acknowledged': acknowledged,
                'resolved': resolved
            },
            'by_severity': {
                'critical': critical,
                'warning': warning,
                'info': info
            }
        }
    }), 200
