# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 数据模型
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Role(db.Model):
    """角色模型"""
    
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, comment='角色名称')
    description = db.Column(db.String(200), comment='角色描述')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    PERMISSIONS = {
        'system_admin': {
            'user_manage': True,
            'device_query': True,
            'device_modify': False,
            'alarm_query': True,
            'alarm_modify': False,
            'performance_query': True,
            'performance_modify': False
        },
        'device_admin': {
            'user_manage': False,
            'device_query': True,
            'device_modify': True,
            'alarm_query': True,
            'alarm_modify': True,
            'performance_query': True,
            'performance_modify': True
        },
        'device_monitor': {
            'user_manage': False,
            'device_query': True,
            'device_modify': False,
            'alarm_query': True,
            'alarm_modify': False,
            'performance_query': True,
            'performance_modify': False
        }
    }
    
    def has_permission(self, permission):
        """检查角色是否有指定权限"""
        role_permissions = self.PERMISSIONS.get(self.name, {})
        return role_permissions.get(permission, False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class User(db.Model):
    """用户模型"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, comment='用户名')
    password_hash = db.Column(db.String(256), nullable=False, comment='密码哈希')
    email = db.Column(db.String(120), unique=True, nullable=True, comment='邮箱')
    real_name = db.Column(db.String(50), comment='真实姓名')
    phone = db.Column(db.String(20), comment='联系电话')
    status = db.Column(db.String(20), default='active', comment='状态: active/inactive')
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), comment='角色ID')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, comment='最后登录时间')
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """检查用户是否有指定权限"""
        if self.role:
            return self.role.has_permission(permission)
        return False
    
    def to_dict(self, include_role=True):
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'real_name': self.real_name,
            'phone': self.phone,
            'status': self.status,
            'role_id': self.role_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None
        }
        if include_role and self.role:
            data['role'] = self.role.to_dict()
        return data


class Device(db.Model):
    """设备模型"""
    
    __tablename__ = 'devices'
    
    id = db.Column(db.Integer, primary_key=True)
    device_name = db.Column(db.String(100), nullable=False, comment='设备名称')
    device_type = db.Column(db.String(50), comment='设备类型: server/switch/router/firewall/storage')
    ip_address = db.Column(db.String(50), comment='IP地址')
    mac_address = db.Column(db.String(50), comment='MAC地址')
    location = db.Column(db.String(200), comment='位置')
    status = db.Column(db.String(20), default='online', comment='状态: online/offline/maintenance')
    description = db.Column(db.Text, comment='设备描述')
    cpu_cores = db.Column(db.Integer, default=0, comment='CPU核心数')
    memory_total = db.Column(db.Float, default=0, comment='总内存(GB)')
    storage_total = db.Column(db.Float, default=0, comment='总存储(GB)')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    alarms = db.relationship('Alarm', backref='device', lazy='dynamic')
    performance_data = db.relationship('PerformanceData', backref='device', lazy='dynamic')
    network_traffic = db.relationship('NetworkTraffic', backref='device', lazy='dynamic')
    
    def to_dict(self, include_latest_metrics=False):
        data = {
            'id': self.id,
            'device_name': self.device_name,
            'device_type': self.device_type,
            'ip_address': self.ip_address,
            'mac_address': self.mac_address,
            'location': self.location,
            'status': self.status,
            'description': self.description,
            'cpu_cores': self.cpu_cores,
            'memory_total': self.memory_total,
            'storage_total': self.storage_total,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_latest_metrics:
            latest_perf = self.performance_data.order_by(PerformanceData.timestamp.desc()).first()
            if latest_perf:
                data['latest_performance'] = {
                    'cpu_usage': latest_perf.cpu_usage,
                    'memory_usage': latest_perf.memory_usage,
                    'storage_usage': latest_perf.storage_usage,
                    'timestamp': latest_perf.timestamp.isoformat() if latest_perf.timestamp else None
                }
        
        return data


class Alarm(db.Model):
    """告警模型"""
    
    __tablename__ = 'alarms'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), comment='设备ID')
    alarm_type = db.Column(db.String(50), comment='告警类型: cpu/memory/storage/network/other')
    severity = db.Column(db.String(20), default='info', comment='严重级别: critical/warning/info')
    title = db.Column(db.String(200), nullable=False, comment='告警标题')
    description = db.Column(db.Text, comment='告警描述')
    status = db.Column(db.String(20), default='active', comment='状态: active/acknowledged/resolved')
    acknowledged_at = db.Column(db.DateTime, comment='确认时间')
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='确认人ID')
    resolved_at = db.Column(db.DateTime, comment='解决时间')
    resolved_by = db.Column(db.Integer, db.ForeignKey('users.id'), comment='解决人ID')
    resolution_notes = db.Column(db.Text, comment='解决说明')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self, include_device=True):
        data = {
            'id': self.id,
            'device_id': self.device_id,
            'alarm_type': self.alarm_type,
            'severity': self.severity,
            'title': self.title,
            'description': self.description,
            'status': self.status,
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'acknowledged_by': self.acknowledged_by,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'resolution_notes': self.resolution_notes,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_device and self.device:
            data['device'] = {
                'id': self.device.id,
                'device_name': self.device.device_name,
                'ip_address': self.device.ip_address
            }
        
        return data


class PerformanceData(db.Model):
    """性能数据模型"""
    
    __tablename__ = 'performance_data'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), comment='设备ID')
    cpu_usage = db.Column(db.Float, default=0, comment='CPU使用率(%)')
    memory_usage = db.Column(db.Float, default=0, comment='内存使用率(%)')
    memory_used = db.Column(db.Float, default=0, comment='已用内存(GB)')
    storage_usage = db.Column(db.Float, default=0, comment='存储使用率(%)')
    storage_used = db.Column(db.Float, default=0, comment='已用存储(GB)')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'memory_used': self.memory_used,
            'storage_usage': self.storage_usage,
            'storage_used': self.storage_used,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class NetworkTraffic(db.Model):
    """网络流量模型"""
    
    __tablename__ = 'network_traffic'
    
    id = db.Column(db.Integer, primary_key=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), comment='设备ID')
    interface_name = db.Column(db.String(50), comment='接口名称')
    bytes_in = db.Column(db.BigInteger, default=0, comment='入流量(字节)')
    bytes_out = db.Column(db.BigInteger, default=0, comment='出流量(字节)')
    packets_in = db.Column(db.BigInteger, default=0, comment='入包数')
    packets_out = db.Column(db.BigInteger, default=0, comment='出包数')
    errors_in = db.Column(db.Integer, default=0, comment='入错误数')
    errors_out = db.Column(db.Integer, default=0, comment='出错误数')
    drops_in = db.Column(db.Integer, default=0, comment='入丢包数')
    drops_out = db.Column(db.Integer, default=0, comment='出丢包数')
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'device_id': self.device_id,
            'interface_name': self.interface_name,
            'bytes_in': self.bytes_in,
            'bytes_out': self.bytes_out,
            'packets_in': self.packets_in,
            'packets_out': self.packets_out,
            'errors_in': self.errors_in,
            'errors_out': self.errors_out,
            'drops_in': self.drops_in,
            'drops_out': self.drops_out,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
