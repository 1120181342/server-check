# -*- coding: utf-8 -*-
"""
文档编辑器 - 启动文件
"""

import os
from app import create_app, db
from app.models.user import User

app = create_app(os.getenv('FLASK_ENV') or 'default')


@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User
    }


@app.cli.command()
def initdb():
    """初始化数据库"""
    db.create_all()
    print('数据库初始化完成')


@app.cli.command()
def seed():
    """初始化测试数据"""
    # 创建测试用户
    test_users = [
        {'username': 'admin', 'password': 'admin123', 'email': 'admin@example.com', 'real_name': '管理员'},
        {'username': 'user1', 'password': 'user123', 'email': 'user1@example.com', 'real_name': '用户一'}
    ]
    
    for user_data in test_users:
        existing = User.query.filter_by(username=user_data['username']).first()
        if not existing:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                real_name=user_data['real_name']
            )
            user.password = user_data['password']
            db.session.add(user)
    
    db.session.commit()
    
    print('测试数据初始化完成')
    print('创建的测试用户:')
    print('  admin / admin123')
    print('  user1 / user123')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
