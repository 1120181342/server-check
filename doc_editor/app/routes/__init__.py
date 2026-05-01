# -*- coding: utf-8 -*-
"""
文档编辑器 - 路由初始化
"""

from app.routes.auth import auth_bp
from app.routes.files import files_bp
from app.routes.main import main_bp

__all__ = ['auth_bp', 'files_bp', 'main_bp']
