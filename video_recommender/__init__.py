"""
视频推荐系统
==========

一个基于内容的多轮视频推荐系统。

模块说明:
- video_database: 视频数据库和视频数据模型
- recommendation_engine: 基于内容的推荐算法引擎
- recommender_app: 推荐应用主程序和命令行界面
- test_recommender: 单元测试

使用方法:
    # 命令行交互模式
    python recommender_app.py
    
    # 运行单元测试
    python test_recommender.py
    
    # 作为库使用
    from video_recommender import VideoRecommenderApp
    app = VideoRecommenderApp()
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
