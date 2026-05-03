"""
视频推荐系统 RESTful API 服务器
使用 Flask 框架提供 Web API 接口
"""

import sys
import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from flask import Flask, request, jsonify, make_response, send_from_directory
from werkzeug.exceptions import BadRequest, NotFound, InternalServerError

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from video_database import VideoDatabase, Video
from recommendation_engine import ContentBasedRecommender
from recommender_app import VideoRecommenderApp, UserSession


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')

app = Flask(__name__, static_folder=STATIC_DIR, static_url_path='/static')

CORS_ALLOW_ORIGIN = '*'
CORS_ALLOW_METHODS = 'GET, POST, PUT, DELETE, OPTIONS, PATCH'
CORS_ALLOW_HEADERS = 'Origin, Content-Type, Accept, Authorization, X-Requested-With'
CORS_EXPOSE_HEADERS = 'Content-Length, Content-Type, X-Total-Count'
CORS_MAX_AGE = '86400'

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = CORS_ALLOW_ORIGIN
    response.headers['Access-Control-Allow-Methods'] = CORS_ALLOW_METHODS
    response.headers['Access-Control-Allow-Headers'] = CORS_ALLOW_HEADERS
    response.headers['Access-Control-Expose-Headers'] = CORS_EXPOSE_HEADERS
    response.headers['Access-Control-Max-Age'] = CORS_MAX_AGE
    return response

@app.before_request
def handle_options_preflight():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = CORS_ALLOW_ORIGIN
        response.headers['Access-Control-Allow-Methods'] = CORS_ALLOW_METHODS
        response.headers['Access-Control-Allow-Headers'] = CORS_ALLOW_HEADERS
        response.headers['Access-Control-Max-Age'] = CORS_MAX_AGE
        response.status_code = 204
        return response

app.config['JSON_AS_ASCII'] = False
app.config['JSON_SORT_KEYS'] = False

video_db = VideoDatabase()
recommender = ContentBasedRecommender(video_db)
recommender_app = VideoRecommenderApp()


def api_response(success: bool, data: Any = None, message: str = "", status_code: int = 200):
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return make_response(jsonify(response), status_code)


def format_video_info(video: Video, score: float = 0.0, index: int = 0) -> Dict[str, Any]:
    minutes = video.duration // 60
    seconds = video.duration % 60
    
    return {
        "index": index,
        "id": video.id,
        "title": video.title,
        "description": video.description,
        "tags": video.tags,
        "category": video.category,
        "duration_seconds": video.duration,
        "duration_formatted": f"{minutes}:{seconds:02d}",
        "views": video.views,
        "likes": video.likes,
        "thumbnail_url": video.thumbnail_url,
        "relevance_score": round(score, 4)
    }


def format_user_profile(profile: Dict) -> Dict:
    return {
        "total_liked": profile.get("total_liked", 0),
        "favorite_category": profile.get("favorite_category"),
        "top_categories": profile.get("top_categories", []),
        "top_tags": profile.get("top_tags", [])
    }


@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return api_response(success=False, message=str(e), status_code=400)


@app.errorhandler(NotFound)
def handle_not_found(e):
    return api_response(success=False, message="资源不存在", status_code=404)


@app.errorhandler(InternalServerError)
def handle_internal_error(e):
    return api_response(success=False, message="服务器内部错误", status_code=500)


@app.route('/api/health', methods=['GET'])
def health_check():
    return api_response(
        success=True,
        data={
            "status": "healthy",
            "service": "video-recommender-api",
            "version": "1.0.0"
        },
        message="服务运行正常"
    )


@app.route('/api/videos', methods=['GET'])
def get_all_videos():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    category = request.args.get('category', None)
    
    if category:
        videos = video_db.get_videos_by_category(category)
    else:
        videos = video_db.get_all_videos()
    
    total = len(videos)
    start = (page - 1) * limit
    end = start + limit
    paginated_videos = videos[start:end]
    
    video_list = [format_video_info(v, 1.0, i+1) for i, v in enumerate(paginated_videos)]
    
    return api_response(
        success=True,
        data={
            "videos": video_list,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": (total + limit - 1) // limit
            }
        },
        message="获取视频列表成功"
    )


@app.route('/api/videos/<video_id>', methods=['GET'])
def get_video(video_id):
    video = video_db.get_video(video_id)
    
    if not video:
        return api_response(success=False, message=f"视频 {video_id} 不存在", status_code=404)
    
    similar_videos = recommender.get_similar_videos(video_id, limit=5)
    similar_list = [format_video_info(v, s, i+1) for i, (v, s) in enumerate(similar_videos)]
    
    return api_response(
        success=True,
        data={
            "video": format_video_info(video, 1.0),
            "similar_videos": similar_list
        },
        message="获取视频详情成功"
    )


@app.route('/api/videos/search', methods=['GET'])
def search_videos():
    query = request.args.get('q', '')
    
    if not query:
        return api_response(success=False, message="搜索关键词不能为空", status_code=400)
    
    results = video_db.search_videos(query)
    
    video_list = [format_video_info(v, 1.0, i+1) for i, v in enumerate(results)]
    
    return api_response(
        success=True,
        data={
            "query": query,
            "videos": video_list,
            "total": len(video_list)
        },
        message=f"搜索完成，找到 {len(video_list)} 个相关视频"
    )


@app.route('/api/videos/popular', methods=['GET'])
def get_popular_videos():
    limit = request.args.get('limit', 10, type=int)
    
    popular = video_db.get_popular_videos(limit)
    
    video_list = [format_video_info(v, 1.0, i+1) for i, v in enumerate(popular)]
    
    return api_response(
        success=True,
        data={
            "videos": video_list,
            "limit": limit
        },
        message="获取热门视频成功"
    )


@app.route('/api/videos/similar/<video_id>', methods=['GET'])
def get_similar_videos(video_id):
    limit = request.args.get('limit', 6, type=int)
    
    video = video_db.get_video(video_id)
    if not video:
        return api_response(success=False, message=f"视频 {video_id} 不存在", status_code=404)
    
    similar_videos = recommender.get_similar_videos(video_id, limit=limit)
    
    video_list = [format_video_info(v, s, i+1) for i, (v, s) in enumerate(similar_videos)]
    
    return api_response(
        success=True,
        data={
            "source_video": format_video_info(video, 1.0),
            "similar_videos": video_list
        },
        message=f"找到 {len(video_list)} 个相似视频"
    )


@app.route('/api/session/create', methods=['POST'])
def create_session():
    data = request.get_json() or {}
    user_id = data.get('user_id', str(uuid.uuid4()))
    
    session = recommender_app.create_session(user_id)
    
    return api_response(
        success=True,
        data={
            "user_id": session.user_id,
            "current_round": session.current_round,
            "initial_preference": session.initial_preference
        },
        message="会话创建成功"
    )


@app.route('/api/session/<user_id>', methods=['GET'])
def get_session(user_id):
    session = recommender_app.get_session(user_id)
    
    if not session:
        return api_response(success=False, message=f"用户 {user_id} 的会话不存在", status_code=404)
    
    return api_response(
        success=True,
        data={
            "user_id": session.user_id,
            "current_round": session.current_round,
            "initial_preference": session.initial_preference,
            "liked_video_count": len(session.liked_video_ids),
            "seen_video_count": len(session.seen_video_ids)
        },
        message="获取会话信息成功"
    )


@app.route('/api/session/<user_id>', methods=['DELETE'])
def reset_session(user_id):
    result = recommender_app.reset_session(user_id)
    
    return api_response(
        success=result["success"],
        message=result["message"]
    )


@app.route('/api/recommend/first', methods=['POST'])
def first_round_recommend():
    data = request.get_json() or {}
    
    user_id = data.get('user_id')
    preference = data.get('preference', '')
    
    if not user_id:
        user_id = str(uuid.uuid4())
    
    if not preference:
        return api_response(success=False, message="视频偏好描述不能为空", status_code=400)
    
    result = recommender_app.start_first_round(user_id, preference)
    
    if not result["success"]:
        return api_response(success=False, message=result["message"], status_code=400)
    
    return api_response(
        success=True,
        data={
            "user_id": result["user_id"],
            "round": result["round"],
            "is_first_round": result["is_first_round"],
            "initial_preference": result["initial_preference"],
            "recommendations": result["recommendations"]
        },
        message=result["message"]
    )


@app.route('/api/recommend/select', methods=['POST'])
def select_videos():
    data = request.get_json() or {}
    
    user_id = data.get('user_id')
    selected_indices = data.get('selected_indices', [])
    
    if not user_id:
        return api_response(success=False, message="用户ID不能为空", status_code=400)
    
    if not selected_indices or len(selected_indices) == 0:
        return api_response(success=False, message="请至少选择1个视频", status_code=400)
    
    result = recommender_app.process_selection(user_id, selected_indices)
    
    if not result["success"]:
        return api_response(success=False, message=result["message"], status_code=400)
    
    return api_response(
        success=True,
        data={
            "user_id": result["user_id"],
            "round": result["round"],
            "selected_videos": result["selected_videos"],
            "total_liked_count": result["total_liked_count"]
        },
        message=result["message"]
    )


@app.route('/api/recommend/next', methods=['POST'])
def next_round_recommend():
    data = request.get_json() or {}
    
    user_id = data.get('user_id')
    
    if not user_id:
        return api_response(success=False, message="用户ID不能为空", status_code=400)
    
    result = recommender_app.generate_next_round(user_id)
    
    if not result["success"]:
        return api_response(success=False, message=result["message"], status_code=400)
    
    return api_response(
        success=True,
        data={
            "user_id": result["user_id"],
            "round": result["round"],
            "is_first_round": result["is_first_round"],
            "recommendations": result["recommendations"],
            "user_profile": format_user_profile(result["user_profile"])
        },
        message=result["message"]
    )


@app.route('/api/recommend', methods=['POST'])
def full_recommend_flow():
    data = request.get_json() or {}
    
    user_id = data.get('user_id')
    preference = data.get('preference')
    selected_indices = data.get('selected_indices')
    
    if not user_id:
        user_id = str(uuid.uuid4())
    
    session = recommender_app.get_session(user_id)
    
    if not session or session.current_round == 0:
        if not preference:
            return api_response(success=False, message="首次推荐需要提供视频偏好描述", status_code=400)
        
        result = recommender_app.start_first_round(user_id, preference)
    else:
        if selected_indices is not None:
            select_result = recommender_app.process_selection(user_id, selected_indices)
            if not select_result["success"]:
                return api_response(success=False, message=select_result["message"], status_code=400)
        
        result = recommender_app.generate_next_round(user_id)
    
    if not result["success"]:
        return api_response(success=False, message=result["message"], status_code=400)
    
    return api_response(
        success=True,
        data={
            "user_id": result["user_id"],
            "round": result["round"],
            "is_first_round": result.get("is_first_round", False),
            "recommendations": result["recommendations"],
            "user_profile": format_user_profile(result.get("user_profile", {})) if result.get("user_profile") else None
        },
        message=result["message"]
    )


@app.route('/api/user/<user_id>/profile', methods=['GET'])
def get_user_profile(user_id):
    history = recommender_app.get_user_history(user_id)
    
    if not history["success"]:
        return api_response(success=False, message=history["message"], status_code=404)
    
    return api_response(
        success=True,
        data=format_user_profile(history["user_profile"]),
        message="获取用户画像成功"
    )


@app.route('/api/user/<user_id>/liked', methods=['GET'])
def get_user_liked_videos(user_id):
    history = recommender_app.get_user_history(user_id)
    
    if not history["success"]:
        return api_response(success=False, message=history["message"], status_code=404)
    
    return api_response(
        success=True,
        data={
            "videos": history["liked_videos"],
            "total": len(history["liked_videos"])
        },
        message="获取用户喜欢的视频成功"
    )


@app.route('/api/user/<user_id>/history', methods=['GET'])
def get_user_history(user_id):
    history = recommender_app.get_user_history(user_id)
    
    if not history["success"]:
        return api_response(success=False, message=history["message"], status_code=404)
    
    return api_response(
        success=True,
        data={
            "user_id": history["user_id"],
            "current_round": history["current_round"],
            "initial_preference": history["initial_preference"],
            "user_profile": format_user_profile(history["user_profile"]),
            "liked_videos": history["liked_videos"],
            "recommendation_history": history["recommendation_history"]
        },
        message="获取用户历史记录成功"
    )


@app.route('/api/categories', methods=['GET'])
def get_categories():
    all_videos = video_db.get_all_videos()
    categories = set()
    
    for video in all_videos:
        categories.add(video.category)
    
    return api_response(
        success=True,
        data={
            "categories": sorted(list(categories)),
            "total": len(categories)
        },
        message="获取视频分类成功"
    )


@app.route('/api/tags', methods=['GET'])
def get_tags():
    all_videos = video_db.get_all_videos()
    tags = set()
    
    for video in all_videos:
        for tag in video.tags:
            tags.add(tag)
    
    return api_response(
        success=True,
        data={
            "tags": sorted(list(tags)),
            "total": len(tags)
        },
        message="获取视频标签成功"
    )


@app.route('/', methods=['GET'])
def index():
    index_file = os.path.join(STATIC_DIR, 'index.html')
    if os.path.exists(index_file):
        return send_from_directory(STATIC_DIR, 'index.html')
    
    return api_response(
        success=True,
        data={
            "service": "视频推荐系统 API",
            "version": "1.0.0",
            "endpoints": {
                "健康检查": "GET /api/health",
                "视频管理": {
                    "获取视频列表": "GET /api/videos",
                    "获取视频详情": "GET /api/videos/<video_id>",
                    "搜索视频": "GET /api/videos/search?q=<关键词>",
                    "获取热门视频": "GET /api/videos/popular",
                    "获取相似视频": "GET /api/videos/similar/<video_id>"
                },
                "会话管理": {
                    "创建会话": "POST /api/session/create",
                    "获取会话": "GET /api/session/<user_id>",
                    "重置会话": "DELETE /api/session/<user_id>"
                },
                "推荐系统": {
                    "第一轮推荐": "POST /api/recommend/first",
                    "选择视频": "POST /api/recommend/select",
                    "下一轮推荐": "POST /api/recommend/next",
                    "完整推荐流程": "POST /api/recommend"
                },
                "用户信息": {
                    "获取用户画像": "GET /api/user/<user_id>/profile",
                    "获取喜欢的视频": "GET /api/user/<user_id>/liked",
                    "获取历史记录": "GET /api/user/<user_id>/history"
                },
                "元数据": {
                    "获取分类列表": "GET /api/categories",
                    "获取标签列表": "GET /api/tags"
                }
            }
        },
        message="欢迎使用视频推荐系统 API"
    )


@app.route('/api', methods=['GET'])
def api_info():
    return api_response(
        success=True,
        data={
            "service": "视频推荐系统 API",
            "version": "1.0.0",
            "endpoints": {
                "健康检查": "GET /api/health",
                "视频管理": {
                    "获取视频列表": "GET /api/videos",
                    "获取视频详情": "GET /api/videos/<video_id>",
                    "搜索视频": "GET /api/videos/search?q=<关键词>",
                    "获取热门视频": "GET /api/videos/popular",
                    "获取相似视频": "GET /api/videos/similar/<video_id>"
                },
                "会话管理": {
                    "创建会话": "POST /api/session/create",
                    "获取会话": "GET /api/session/<user_id>",
                    "重置会话": "DELETE /api/session/<user_id>"
                },
                "推荐系统": {
                    "第一轮推荐": "POST /api/recommend/first",
                    "选择视频": "POST /api/recommend/select",
                    "下一轮推荐": "POST /api/recommend/next",
                    "完整推荐流程": "POST /api/recommend"
                },
                "用户信息": {
                    "获取用户画像": "GET /api/user/<user_id>/profile",
                    "获取喜欢的视频": "GET /api/user/<user_id>/liked",
                    "获取历史记录": "GET /api/user/<user_id>/history"
                },
                "元数据": {
                    "获取分类列表": "GET /api/categories",
                    "获取标签列表": "GET /api/tags"
                }
            }
        },
        message="欢迎使用视频推荐系统 API"
    )


if __name__ == '__main__':
    print("="*70)
    print("                    视频推荐系统 API 服务器")
    print("="*70)
    print(f"🌐 服务地址:       http://localhost:5000")
    print(f"📱 前端测试页面:   http://localhost:5000/")
    print(f"📚 API 文档:       http://localhost:5000/api")
    print(f"❤️ 健康检查:       http://localhost:5000/api/health")
    print("="*70)
    print("📌 API端点说明:")
    print("   - 会话管理:   /api/session/*")
    print("   - 推荐系统:   /api/recommend/*")
    print("   - 视频管理:   /api/videos/*")
    print("   - 用户信息:   /api/user/<user_id>/*")
    print("   - 元数据:     /api/categories, /api/tags")
    print("="*70)
    print("🚀 正在启动服务器...")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
