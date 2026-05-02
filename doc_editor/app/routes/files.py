# -*- coding: utf-8 -*-
"""
文档编辑器 - 文件操作路由
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from app.models.user import User
from app.models.document import Document

files_bp = Blueprint('files', __name__)


def get_user_file_path(user_id, filename=None):
    """获取用户文件存储路径"""
    base_path = current_app.config['FILE_STORAGE_PATH']
    user_path = base_path / str(user_id)
    
    # 确保用户目录存在
    if not os.path.exists(user_path):
        os.makedirs(user_path, exist_ok=True)
    
    if filename:
        return user_path / filename
    return user_path


@files_bp.route('/', methods=['GET'])
@jwt_required()
def list_files():
    """获取用户所有文件列表"""
    current_user_id = get_jwt_identity()
    
    documents = Document.query.filter_by(user_id=current_user_id).order_by(
        Document.updated_at.desc()
    ).all()
    
    return jsonify({
        'message': '获取成功',
        'data': [doc.to_dict() for doc in documents]
    }), 200


@files_bp.route('/new', methods=['POST'])
@jwt_required()
def new_file():
    """新建文件"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    filename = data.get('filename', 'untitled.txt')
    
    # 确保文件名以.txt结尾
    if not filename.endswith('.txt'):
        filename += '.txt'
    
    # 检查同名文件是否存在
    existing = Document.query.filter_by(
        user_id=current_user_id, 
        filename=filename
    ).first()
    
    if existing:
        return jsonify({
            'error': 'Conflict',
            'message': f'文件 "{filename}" 已存在'
        }), 409
    
    # 获取文件路径
    file_path = get_user_file_path(current_user_id, filename)
    
    # 创建空文件
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write('')
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'创建文件失败: {str(e)}'
        }), 500
    
    # 创建数据库记录
    document = Document(
        user_id=current_user_id,
        filename=filename,
        file_path=str(file_path),
        file_size=0
    )
    
    db.session.add(document)
    db.session.commit()
    
    return jsonify({
        'message': '文件创建成功',
        'data': document.to_dict()
    }), 201


@files_bp.route('/<int:doc_id>', methods=['GET'])
@jwt_required()
def get_file(doc_id):
    """打开文件（获取文件内容）"""
    current_user_id = get_jwt_identity()
    
    document = Document.query.filter_by(id=doc_id, user_id=current_user_id).first()
    
    if not document:
        return jsonify({
            'error': 'Not Found',
            'message': '文件不存在'
        }), 404
    
    # 读取文件内容
    try:
        with open(document.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'读取文件失败: {str(e)}'
        }), 500
    
    result = document.to_dict()
    result['content'] = content
    
    return jsonify({
        'message': '获取成功',
        'data': result
    }), 200


@files_bp.route('/<int:doc_id>', methods=['PUT'])
@jwt_required()
def save_file(doc_id):
    """保存文件"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    document = Document.query.filter_by(id=doc_id, user_id=current_user_id).first()
    
    if not document:
        return jsonify({
            'error': 'Not Found',
            'message': '文件不存在'
        }), 404
    
    content = data.get('content', '')
    
    # 写入文件内容
    try:
        with open(document.file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'保存文件失败: {str(e)}'
        }), 500
    
    # 更新文件信息
    document.file_size = len(content.encode('utf-8'))
    document.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'message': '保存成功',
        'data': document.to_dict()
    }), 200


@files_bp.route('/<int:doc_id>/save-as', methods=['POST'])
@jwt_required()
def save_as_file(doc_id):
    """另存为文件"""
    current_user_id = get_jwt_identity()
    data = request.get_json()
    
    new_filename = data.get('filename')
    
    if not new_filename:
        return jsonify({
            'error': 'Bad Request',
            'message': '文件名不能为空'
        }), 400
    
    # 确保文件名以.txt结尾
    if not new_filename.endswith('.txt'):
        new_filename += '.txt'
    
    # 检查同名文件是否存在
    existing = Document.query.filter_by(
        user_id=current_user_id, 
        filename=new_filename
    ).first()
    
    if existing:
        return jsonify({
            'error': 'Conflict',
            'message': f'文件 "{new_filename}" 已存在'
        }), 409
    
    # 获取原文件内容
    original = Document.query.filter_by(id=doc_id, user_id=current_user_id).first()
    
    if not original:
        return jsonify({
            'error': 'Not Found',
            'message': '原文件不存在'
        }), 404
    
    # 读取原文件内容
    try:
        with open(original.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'读取原文件失败: {str(e)}'
        }), 500
    
    # 创建新文件
    new_file_path = get_user_file_path(current_user_id, new_filename)
    
    try:
        with open(new_file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'创建新文件失败: {str(e)}'
        }), 500
    
    # 创建新的数据库记录
    new_document = Document(
        user_id=current_user_id,
        filename=new_filename,
        file_path=str(new_file_path),
        file_size=len(content.encode('utf-8'))
    )
    
    db.session.add(new_document)
    db.session.commit()
    
    return jsonify({
        'message': '另存为成功',
        'data': new_document.to_dict()
    }), 201


@files_bp.route('/<int:doc_id>', methods=['DELETE'])
@jwt_required()
def delete_file(doc_id):
    """删除文件"""
    current_user_id = get_jwt_identity()
    
    document = Document.query.filter_by(id=doc_id, user_id=current_user_id).first()
    
    if not document:
        return jsonify({
            'error': 'Not Found',
            'message': '文件不存在'
        }), 404
    
    # 删除物理文件
    try:
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
    except Exception as e:
        return jsonify({
            'error': 'Internal Server Error',
            'message': f'删除文件失败: {str(e)}'
        }), 500
    
    # 删除数据库记录
    db.session.delete(document)
    db.session.commit()
    
    return jsonify({
        'message': '删除成功'
    }), 200
