from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from models import Role
from routes import get_current_user

common_bp = Blueprint('common', __name__)

@common_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    try:
        roles = Role.query.all()
        result = [r.to_dict() for r in roles]
        
        return jsonify({
            'code': 200,
            'message': '获取成功',
            'data': result
        })
        
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'获取角色列表失败: {str(e)}',
            'data': None
        }), 500

@common_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'code': 200,
        'message': '服务运行正常',
        'data': {
            'status': 'healthy',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
    })

@common_bp.route('/test-db', methods=['GET'])
def test_db():
    try:
        from app import db
        db.session.execute('SELECT 1')
        return jsonify({
            'code': 200,
            'message': '数据库连接正常',
            'data': None
        })
    except Exception as e:
        return jsonify({
            'code': 500,
            'message': f'数据库连接失败: {str(e)}',
            'data': None
        }), 500
