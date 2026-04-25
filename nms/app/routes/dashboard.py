# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 仪表板路由
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app import db
from app.models.user import User
from app.models.device import Device
from app.models.alarm import Alarm
from app.models.performance import PerformanceData, NetworkTraffic

dashboard_bp = Blueprint('dashboard', __name__)


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


@dashboard_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_summary():
    """获取仪表板概览数据"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    total_devices = Device.query.count()
    online_devices = Device.query.filter_by(status='online').count()
    offline_devices = Device.query.filter_by(status='offline').count()
    maintenance_devices = Device.query.filter_by(status='maintenance').count()
    
    total_alarms = Alarm.query.count()
    active_alarms = Alarm.query.filter_by(status='active').count()
    critical_alarms = Alarm.query.filter_by(severity='critical').filter(
        Alarm.status.in_(['active', 'acknowledged'])
    ).count()
    
    critical_count = Alarm.query.filter_by(severity='critical').count()
    warning_count = Alarm.query.filter_by(severity='warning').count()
    info_count = Alarm.query.filter_by(severity='info').count()
    
    return jsonify({
        'message': '获取成功',
        'data': {
            'total_devices': total_devices,
            'online_devices': online_devices,
            'offline_devices': offline_devices,
            'maintenance_devices': maintenance_devices,
            'total_alarms': total_alarms,
            'active_alarms': active_alarms,
            'critical_alarms': critical_alarms,
            'device_status': {
                'online': online_devices,
                'offline': offline_devices,
                'maintenance': maintenance_devices
            },
            'alarm_severity': {
                'critical': critical_count,
                'warning': warning_count,
                'info': info_count
            }
        }
    }), 200


@dashboard_bp.route('/trends', methods=['GET'])
@jwt_required()
def get_trends():
    """获取性能趋势数据（用于折线图）"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    hours = int(request.args.get('hours', 24))
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    performance_data = db.session.query(
        func.strftime('%H:%M', PerformanceData.timestamp).label('time'),
        func.avg(PerformanceData.cpu_usage).label('avg_cpu'),
        func.avg(PerformanceData.memory_usage).label('avg_memory'),
        func.avg(PerformanceData.storage_usage).label('avg_storage')
    ).filter(
        PerformanceData.timestamp >= start_time
    ).group_by(
        func.strftime('%H:%M', PerformanceData.timestamp)
    ).order_by(
        func.strftime('%H:%M', PerformanceData.timestamp)
    ).all()
    
    labels = []
    cpu_data = []
    memory_data = []
    storage_data = []
    
    for row in performance_data:
        labels.append(row.time)
        cpu_data.append(round(float(row.avg_cpu), 2) if row.avg_cpu else 0)
        memory_data.append(round(float(row.avg_memory), 2) if row.avg_memory else 0)
        storage_data.append(round(float(row.avg_storage), 2) if row.avg_storage else 0)
    
    return jsonify({
        'message': '获取成功',
        'data': {
            'labels': labels,
            'cpu': cpu_data,
            'memory': memory_data,
            'storage': storage_data
        }
    }), 200


@dashboard_bp.route('/network-traffic', methods=['GET'])
@jwt_required()
def get_network_traffic_trends():
    """获取整体网络流量趋势"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    hours = int(request.args.get('hours', 24))
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    traffic_data = db.session.query(
        func.strftime('%H:%M', NetworkTraffic.timestamp).label('time'),
        func.sum(NetworkTraffic.bytes_in).label('total_bytes_in'),
        func.sum(NetworkTraffic.bytes_out).label('total_bytes_out'),
        func.sum(NetworkTraffic.packets_in).label('total_packets_in'),
        func.sum(NetworkTraffic.packets_out).label('total_packets_out')
    ).filter(
        NetworkTraffic.timestamp >= start_time
    ).group_by(
        func.strftime('%H:%M', NetworkTraffic.timestamp)
    ).order_by(
        func.strftime('%H:%M', NetworkTraffic.timestamp)
    ).all()
    
    labels = []
    bytes_in = []
    bytes_out = []
    packets_in = []
    packets_out = []
    
    for row in traffic_data:
        labels.append(row.time)
        bytes_in.append(int(row.total_bytes_in) if row.total_bytes_in else 0)
        bytes_out.append(int(row.total_bytes_out) if row.total_bytes_out else 0)
        packets_in.append(int(row.total_packets_in) if row.total_packets_in else 0)
        packets_out.append(int(row.total_packets_out) if row.total_packets_out else 0)
    
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


@dashboard_bp.route('/top-devices', methods=['GET'])
@jwt_required()
def get_top_devices():
    """获取Top设备（按CPU/内存使用率）"""
    if not has_permission('device_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    limit = int(request.args.get('limit', 10))
    
    latest_performance = db.session.query(
        PerformanceData.device_id,
        PerformanceData.cpu_usage,
        PerformanceData.memory_usage,
        PerformanceData.storage_usage,
        func.max(PerformanceData.timestamp).label('latest_time')
    ).group_by(
        PerformanceData.device_id
    ).subquery()
    
    top_devices = db.session.query(
        Device,
        latest_performance.c.cpu_usage,
        latest_performance.c.memory_usage,
        latest_performance.c.storage_usage
    ).join(
        latest_performance,
        Device.id == latest_performance.c.device_id
    ).order_by(
        latest_performance.c.cpu_usage.desc()
    ).limit(limit).all()
    
    result = []
    for row in top_devices:
        device = row.Device
        result.append({
            'id': device.id,
            'device_name': device.device_name,
            'device_type': device.device_type,
            'ip_address': device.ip_address,
            'status': device.status,
            'cpu_usage': round(float(row.cpu_usage), 2) if row.cpu_usage else 0,
            'memory_usage': round(float(row.memory_usage), 2) if row.memory_usage else 0,
            'storage_usage': round(float(row.storage_usage), 2) if row.storage_usage else 0
        })
    
    return jsonify({
        'message': '获取成功',
        'data': result
    }), 200


@dashboard_bp.route('/active-alarms', methods=['GET'])
@jwt_required()
def get_active_alarms():
    """获取活跃告警列表"""
    if not has_permission('alarm_query'):
        return jsonify({
            'error': 'Forbidden',
            'message': '无权限访问'
        }), 403
    
    limit = int(request.args.get('limit', 10))
    
    alarms = Alarm.query.filter(
        Alarm.status.in_(['active', 'acknowledged'])
    ).order_by(
        Alarm.severity.desc(),
        Alarm.created_at.desc()
    ).limit(limit).all()
    
    result = []
    for alarm in alarms:
        result.append(alarm.to_dict(include_device=True))
    
    return jsonify({
        'message': '获取成功',
        'data': result
    }), 200


@dashboard_bp.route('/device-types', methods=['GET'])
@jwt_required()
def get_device_type_stats():
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
