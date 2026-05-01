# -*- coding: utf-8 -*-
"""
云资源池综合化网管系统 - 启动文件
"""

import os
from app import create_app, db
from app.models.user import User, Role
from app.models.device import Device
from app.models.alarm import Alarm
from app.models.performance import PerformanceData, NetworkTraffic

app = create_app(os.getenv('FLASK_ENV') or 'default')


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Role': Role,
        'Device': Device,
        'Alarm': Alarm,
        'PerformanceData': PerformanceData,
        'NetworkTraffic': NetworkTraffic
    }


@app.cli.command()
def initdb():
    """初始化数据库"""
    db.create_all()
    print('数据库初始化完成')


@app.cli.command()
def seed():
    """初始化数据"""
    from datetime import datetime, timedelta
    import random
    
    roles = [
        {'name': 'system_admin', 'description': '系统管理员 - 负责用户管理和系统配置'},
        {'name': 'device_admin', 'description': '设备管理员 - 负责设备配置和变更'},
        {'name': 'device_monitor', 'description': '设备监控员 - 仅负责资源监控和查看'}
    ]
    
    for role_data in roles:
        role = Role.query.filter_by(name=role_data['name']).first()
        if not role:
            role = Role(name=role_data['name'], description=role_data['description'])
            db.session.add(role)
    
    db.session.commit()
    
    admin_role = Role.query.filter_by(name='system_admin').first()
    device_admin_role = Role.query.filter_by(name='device_admin').first()
    monitor_role = Role.query.filter_by(name='device_monitor').first()
    
    users = [
        {'username': 'admin', 'password': 'admin123', 'email': 'admin@example.com', 'real_name': '系统管理员', 'role_id': admin_role.id},
        {'username': 'device_admin', 'password': 'admin123', 'email': 'device_admin@example.com', 'real_name': '设备管理员', 'role_id': device_admin_role.id},
        {'username': 'monitor', 'password': 'admin123', 'email': 'monitor@example.com', 'real_name': '设备监控员', 'role_id': monitor_role.id}
    ]
    
    for user_data in users:
        user = User.query.filter_by(username=user_data['username']).first()
        if not user:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                real_name=user_data['real_name'],
                role_id=user_data['role_id']
            )
            user.password = user_data['password']
            db.session.add(user)
    
    db.session.commit()
    
    device_types = ['server', 'switch', 'router', 'firewall', 'storage']
    device_statuses = ['online', 'offline', 'maintenance']
    locations = ['机房A', '机房B', '机房C', '云平台']
    
    devices = []
    for i in range(20):
        device = Device(
            device_name=f'设备-{i+1:03d}',
            device_type=random.choice(device_types),
            ip_address=f'192.168.1.{100+i}',
            mac_address=':'.join([f'{random.randint(0, 255):02X}' for _ in range(6)]),
            location=random.choice(locations),
            status=random.choices(device_statuses, weights=[0.7, 0.15, 0.15])[0],
            description=f'测试设备 #{i+1}',
            cpu_cores=random.choice([4, 8, 16, 32]),
            memory_total=random.choice([8, 16, 32, 64, 128]),
            storage_total=random.choice([100, 200, 500, 1000, 2000])
        )
        devices.append(device)
        db.session.add(device)
    
    db.session.commit()
    
    for device in devices:
        for j in range(24):
            timestamp = datetime.utcnow() - timedelta(hours=j)
            perf = PerformanceData(
                device_id=device.id,
                cpu_usage=random.uniform(10, 90),
                memory_usage=random.uniform(30, 85),
                memory_used=round(random.uniform(5, 50), 2),
                storage_usage=random.uniform(20, 80),
                storage_used=round(random.uniform(50, 500), 2),
                timestamp=timestamp
            )
            db.session.add(perf)
            
            traffic = NetworkTraffic(
                device_id=device.id,
                interface_name=f'eth{random.randint(0, 3)}',
                bytes_in=random.randint(1000000, 100000000),
                bytes_out=random.randint(1000000, 100000000),
                packets_in=random.randint(10000, 1000000),
                packets_out=random.randint(10000, 1000000),
                errors_in=random.randint(0, 10),
                errors_out=random.randint(0, 10),
                drops_in=random.randint(0, 5),
                drops_out=random.randint(0, 5),
                timestamp=timestamp
            )
            db.session.add(traffic)
    
    db.session.commit()
    
    alarm_types = ['cpu', 'memory', 'storage', 'network', 'other']
    severities = ['critical', 'warning', 'info']
    alarm_titles = {
        'cpu': ['CPU使用率过高告警', 'CPU负载异常', 'CPU温度警告'],
        'memory': ['内存使用率过高', '内存不足警告', '内存泄漏检测'],
        'storage': ['存储容量不足', '存储IO延迟过高', '磁盘空间警告'],
        'network': ['网络连接中断', '网络延迟过高', '端口流量异常'],
        'other': ['设备状态异常', '配置变更告警', '性能阈值告警']
    }
    
    for i in range(15):
        alarm_type = random.choice(alarm_types)
        device = random.choice(devices)
        alarm = Alarm(
            device_id=device.id,
            alarm_type=alarm_type,
            severity=random.choice(severities),
            title=random.choice(alarm_titles[alarm_type]),
            description=f'自动生成的测试告警 #{i+1}',
            status=random.choice(['active', 'acknowledged', 'resolved'])
        )
        db.session.add(alarm)
    
    db.session.commit()
    
    print('数据初始化完成')
    print('创建的用户账号:')
    print('  系统管理员: admin / admin123')
    print('  设备管理员: device_admin / admin123')
    print('  设备监控员: monitor / admin123')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
