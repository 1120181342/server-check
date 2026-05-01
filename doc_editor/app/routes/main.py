# -*- coding: utf-8 -*-
"""
文档编辑器 - 主路由
"""

from flask import Blueprint, send_from_directory

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """主页"""
    return send_from_directory('templates', 'index.html')


@main_bp.route('/<path:filename>')
def static_files(filename):
    """静态文件"""
    return send_from_directory('static', filename)
