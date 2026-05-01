# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 设备管理路由
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from sqlalchemy import func

from app import db
from app.models.user import User
from app.models.device import Device
from app.models.performance import PerformanceData, NetworkTraffic

devices_bp = Blueprint('devices', __name__)


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


@devices_bp.route('/', methods=['GET'])
@jwt_required()
def get_devices():
    """获取设备列表"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    search = request.args.get('search', '')
    
    query = Device.query
    
    if search:
        query = query.filter(
            (Device.device_name.like(f'%{search}%')) |
            (Device.ip_address.like(f'%{search}%'))
        )
    
    devices = query.all()
    
    result = []
    for device in devices:
        device_dict = device.to_dict(include_latest_metrics=True)
        result.append(device_dict)
    
    return jsonify({
        'message': '获取成功',
        'data': result
    }), 200


@devices_bp.route('/<int:device_id>', methods=['GET'])
@jwt_required()
def get_device(device_id):
    """获取单个设备详情"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({
            'error': 'Not Found',
            'message': '设备不存在'
        }), 404
    
    return jsonify({
        'message': '获取成功',
        'data': device.to_dict(include_latest_metrics=True)
    }), 200


@devices_bp.route('/', methods=['POST'])
@jwt_required()
def create_device():
    """创建设备"""
    if not has_permission('device_modify'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    data = request.get_json()
    
    if not data.get('device_name'):
        return jsonify({
            'error': 'Bad Request',
            'message': '设备名称不能为空'
        }), 400
    
    device = Device(
        device_name=data['device_name'],
        device_type=data.get('device_type'),
        ip_address=data.get('ip_address'),
        mac_address=data.get('mac_address'),
        location=data.get('location'),
        status=data.get('status', 'online'),
        description=data.get('description'),
        cpu_cores=data.get('cpu_cores', 0),
        memory_total=data.get('memory_total', 0),
        storage_total=data.get('storage_total', 0)
    )
    
    db.session.add(device)
    db.session.commit()
    
    return jsonify({
        'message': '创建设备成功',
        'data': device.to_dict()
    }), 201


@devices_bp.route('/<int:device_id>', methods=['PUT'])
@jwt_required()
def update_device(device_id):
    """更新设备"""
    if not has_permission('device_modify'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({
            'error': 'Not Found',
            'message': '设备不存在'
        }), 404
    
    data = request.get_json()
    
    if data.get('device_name'):
        device.device_name = data['device_name']
    if data.get('device_type'):
        device.device_type = data['device_type']
    if data.get('ip_address'):
        device.ip_address = data['ip_address']
    if data.get('mac_address'):
        device.mac_address = data['mac_address']
    if data.get('location'):
        device.location = data['location']
    if data.get('status'):
        device.status = data['status']
    if data.get('description'):
        device.description = data['description']
    if data.get('cpu_cores') is not None:
        device.cpu_cores = data['cpu_cores']
    if data.get('memory_total') is not None:
        device.memory_total = data['memory_total']
    if data.get('storage_total') is not None:
        device.storage_total = data['storage_total']
    
    db.session.commit()
    
    return jsonify({
        'message': '更新设备成功',
        'data': device.to_dict()
    }), 200


@devices_bp.route('/<int:device_id>', methods=['DELETE'])
@jwt_required()
def delete_device(device_id):
    """删除设备"""
    if not has_permission('device_modify'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限进行此操作'
        }), 403
    
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({
            'error': 'Not Found',
            'message': '设备不存在'
        }), 404
    
    PerformanceData.query.filter_by(device_id=device_id).delete()
    NetworkTraffic.query.filter_by(device_id=device_id).delete()
    
    db.session.delete(device)
    db.session.commit()
    
    return jsonify({
        'message': '删除设备成功'
    }), 200


@devices_bp.route('/<int:device_id>/performance', methods=['GET'])
@jwt_required()
def get_device_performance(device_id):
    """获取设备性能历史数据（用于折线图）"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({
            'error': 'Not Found',
            'message': '设备不存在'
        }), 404
    
    hours = int(request.args.get('hours', 24))
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    performance_data = PerformanceData.query.filter(
        PerformanceData.device_id == device_id,
        PerformanceData.timestamp >= start_time
    ).order_by(PerformanceData.timestamp.asc()).all()
    
    labels = []
    cpu_data = []
    memory_data = []
    storage_data = []
    
    for data in performance_data:
        labels.append(data.timestamp.strftime('%H:%M'))
        cpu_data.append(round(data.cpu_usage, 2))
        memory_data.append(round(data.memory_usage, 2))
        storage_data.append(round(data.storage_usage, 2))
    
    return jsonify({
        'message': '获取成功',
        'data': {
            'labels': labels,
            'cpu': cpu_data,
            'memory': memory_data,
            'storage': storage_data
        }
    }), 200


@devices_bp.route('/<int:device_id>/network-traffic', methods=['GET'])
@jwt_required()
def get_device_network_traffic(device_id):
    """获取设备网络流量历史数据（用于折线图）"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    device = Device.query.get(device_id)
    
    if not device:
        return jsonify({
            'error': 'Not Found',
            'message': '设备不存在'
        }), 404
    
    hours = int(request.args.get('hours', 24))
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    traffic_data = NetworkTraffic.query.filter(
        NetworkTraffic.device_id == device_id,
        NetworkTraffic.timestamp >= start_time
    ).order_by(NetworkTraffic.timestamp.asc()).all()
    
    labels = []
    bytes_in = []
    bytes_out = []
    packets_in = []
    packets_out = []
    
    for data in traffic_data:
        labels.append(data.timestamp.strftime('%H:%M'))
        bytes_in.append(data.bytes_in)
        bytes_out.append(data.bytes_out)
        packets_in.append(data.packets_in)
        packets_out.append(data.packets_out)
    
    return jsonify({
        'message': '获取成功',
        'data': {
            'labels': labels,
            'bytes_in': bytes_in,
            'bytes_out': bytes_out,
            'packets_in': packets_in,
            'packets_out': packets_out
        }
    }), 200


@devices_bp.route('/types', methods=['GET'])
@jwt_required()
def get_device_types():
    """获取设备类型统计"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    result = db.session.query(
        Device.device_type,
        func.count(Device.id).label('count')
    ).group_by(Device.device_type).all()
    
    data = {}
    for row in result:
        data[row.device_type] = row.count
    
    return jsonify({
        'message': '获取成功',
        'data': data
    }), 200
