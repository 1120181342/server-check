"""
视频推荐系统
==========

一个基于内容的多轮视频推荐系统，提供RESTful API接口。

模块说明:
- video_database: 视频数据库和视频数据模型
- recommendation_engine: 基于内容的推荐算法引擎
- recommender_app: 推荐应用主程序和命令行界面
- api_server: Flask RESTful API 服务器
- test_recommender: 单元测试

使用方法:
    # 命令行交互模式
    python recommender_app.py
    
    # Web API 服务器模式
    python api_server.py
    
    # 运行单元测试
    python test_recommender.py
    
    # 作为库使用
    from video_recommender import VideoRecommenderApp
    app = VideoRecommenderApp()

API端点:
    基础地址: http://localhost:5000/api
    
    会话管理:
    - POST /api/session/create     - 创建用户会话
    - GET  /api/session/{user_id}  - 获取会话信息
    - DELETE /api/session/{user_id} - 重置会话
    
    推荐系统:
    - POST /api/recommend/first    - 第一轮推荐（基于文字描述）
    - POST /api/recommend/select   - 选择喜欢的视频
    - POST /api/recommend/next     - 下一轮推荐
    - POST /api/recommend          - 完整推荐流程
    
    视频管理:
    - GET /api/videos               - 获取视频列表
    - GET /api/videos/{video_id}   - 获取视频详情
    - GET /api/videos/search?q=... - 搜索视频
    - GET /api/videos/popular      - 获取热门视频
    - GET /api/videos/similar/{id} - 获取相似视频
    
    用户信息:
    - GET /api/user/{id}/profile   - 获取用户画像
    - GET /api/user/{id}/liked     - 获取喜欢的视频
    - GET /api/user/{id}/history   - 获取历史记录
    
    元数据:
    - GET /api/categories           - 获取分类列表
    - GET /api/tags                 - 获取标签列表
    - GET /api/health               - 健康检查
"""

from .video_database import Video, VideoDatabase
from .recommendation_engine import ContentBasedRecommender, TextProcessor
from .recommender_app import VideoRecommenderApp, UserSession, CLInterface

__all__ = [
    'Video',
    'VideoDatabase',
    'ContentBasedRecommender',
    'TextProcessor',
    'VideoRecommenderApp',
    'UserSession',
    'CLInterface'
]

__version__ = '1.0.0'
