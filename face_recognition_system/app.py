import os
import base64
import io
import pickle
import numpy as np
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename
from PIL import Image
import cv2
from datetime import datetime

from config import Config
from database import EmployeeDatabase
from face_processor import FaceProcessor
from face_recognizer import FaceRecognizer

app = Flask(__name__)
CORS(app)
config = Config()
app.config.from_object(config)

db = EmployeeDatabase(config.DATABASE_PATH)
face_processor = FaceProcessor(
    min_face_size=config.MIN_FACE_SIZE,
    max_face_size=config.MAX_FACE_SIZE
)
face_recognizer = FaceRecognizer(
    tolerance=config.FACE_TOLERANCE,
    cache_dir=config.MODELS_DIR
)

def reload_face_encodings():
    face_data = db.get_all_face_encodings()
    count = face_recognizer.load_face_encodings(face_data)
    app.logger.info(f"Loaded {count} face encodings")
    return count

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/employees', methods=['GET'])
def get_employees():
    employees = db.get_all_employees()
    return jsonify({
        'success': True,
        'employees': employees
    })

@app.route('/api/employees/<employee_id>', methods=['GET'])
def get_employee(employee_id):
    employee = db.get_employee_by_id(employee_id)
    if employee:
        return jsonify({
            'success': True,
            'employee': employee
        })
    return jsonify({
        'success': False,
        'message': 'Employee not found'
    }), 404

@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.get_json()
    
    if not data or 'employee_id' not in data or 'name' not in data or 'department' not in data:
        return jsonify({
            'success': False,
            'message': 'Missing required fields: employee_id, name, department'
        }), 400
    
    if db.get_employee_by_id(data['employee_id']):
        return jsonify({
            'success': False,
            'message': 'Employee ID already exists'
        }), 400
    
    if db.add_employee(data):
        return jsonify({
            'success': True,
            'message': 'Employee added successfully',
            'employee': data
        })
    
    return jsonify({
        'success': False,
        'message': 'Failed to add employee'
    }), 500

@app.route('/api/employees/<employee_id>', methods=['PUT'])
def update_employee(employee_id):
    data = request.get_json()
    
    if not data:
        return jsonify({
            'success': False,
            'message': 'No data provided'
        }), 400
    
    if db.get_employee_by_id(employee_id):
        if db.update_employee(employee_id, data):
            return jsonify({
                'success': True,
                'message': 'Employee updated successfully'
            })
        return jsonify({
            'success': False,
            'message': 'Failed to update employee'
        }), 500
    
    return jsonify({
        'success': False,
        'message': 'Employee not found'
    }), 404

@app.route('/api/employees/<employee_id>', methods=['DELETE'])
def delete_employee(employee_id):
    if db.get_employee_by_id(employee_id):
        if db.delete_employee(employee_id):
            reload_face_encodings()
            return jsonify({
                'success': True,
                'message': 'Employee deleted successfully'
            })
        return jsonify({
            'success': False,
            'message': 'Failed to delete employee'
        }), 500
    
    return jsonify({
        'success': False,
        'message': 'Employee not found'
    }), 404

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

@app.route('/api/employees/<employee_id>/face', methods=['POST'])
def upload_face(employee_id):
    employee = db.get_employee_by_id(employee_id)
    if not employee:
        return jsonify({
            'success': False,
            'message': 'Employee not found'
        }), 404
    
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'message': 'No file part'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'message': 'No selected file'
        }), 400
    
    if file and allowed_file(file.filename):
        try:
            image = Image.open(file)
            image_np = np.array(image)
            
            if len(image_np.shape) == 3 and image_np.shape[2] == 4:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
            elif len(image_np.shape) == 3:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            faces = face_processor.process_frame(image_np)
            
            if not faces:
                return jsonify({
                    'success': False,
                    'message': 'No face detected in the image'
                }), 400
            
            face_info = faces[0]
            
            encoding = face_recognizer.encode_face(face_info.image)
            
            if encoding is None:
                return jsonify({
                    'success': False,
                    'message': 'Failed to extract face features'
                }), 500
            
            filename = secure_filename(f"{employee_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg")
            image_path = os.path.join(config.FACES_DIR, filename)
            
            face_image = Image.fromarray((face_info.image + 1.0) * 127.5).convert('RGB')
            face_image.save(image_path)
            
            encoding_bytes = pickle.dumps(encoding)
            
            if db.add_face_encoding(employee_id, encoding_bytes, image_path):
                reload_face_encodings()
                return jsonify({
                    'success': True,
                    'message': 'Face uploaded and registered successfully',
                    'image_path': image_path
                })
            
            return jsonify({
                'success': False,
                'message': 'Failed to save face encoding'
            }), 500
            
        except Exception as e:
            app.logger.error(f"Error processing face: {str(e)}")
            return jsonify({
                'success': False,
                'message': f'Error processing image: {str(e)}'
            }), 500
    
    return jsonify({
        'success': False,
        'message': 'Invalid file type'
    }), 400

@app.route('/api/recognize', methods=['POST'])
def recognize():
    data = request.get_json()
    
    if not data or 'image' not in data:
        return jsonify({
            'success': False,
            'message': 'No image data provided'
        }), 400
    
    try:
        image_data = data['image']
        
        if image_data.startswith('data:image'):
            image_data = image_data.split(',')[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        image_np = np.array(image)
        
        if len(image_np.shape) == 3 and image_np.shape[2] == 4:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
        elif len(image_np.shape) == 3:
            image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        
        faces = face_processor.process_frame(image_np)
        
        if not faces:
            db.log_access(
                status='failed',
                error_message='No face detected'
            )
            return jsonify({
                'success': False,
                'message': 'No face detected. Please position your face in the camera.',
                'retry': True
            })
        
        face_info = faces[0]
        
        encoding = face_recognizer.encode_face(face_info.image)
        
        if encoding is None:
            db.log_access(
                status='failed',
                error_message='Failed to extract face features'
            )
            return jsonify({
                'success': False,
                'message': 'Failed to process face. Please try again.',
                'retry': True
            })
        
        result = face_recognizer.recognize_face_with_retry(
            encoding,
            retries=config.RETRY_COUNT
        )
        
        if result.success:
            db.log_access(
                status='success',
                employee_id=result.employee_id,
                name=result.name,
                confidence=result.confidence
            )
            return jsonify({
                'success': True,
                'employee_id': result.employee_id,
                'name': result.name,
                'confidence': result.confidence,
                'distance': result.distance,
                'message': result.message
            })
        else:
            db.log_access(
                status='failed',
                error_message=result.message
            )
            return jsonify({
                'success': False,
                'message': result.message,
                'retry': True,
                'distance': result.distance
            })
            
    except Exception as e:
        app.logger.error(f"Recognition error: {str(e)}")
        db.log_access(
            status='failed',
            error_message=f'System error: {str(e)}'
        )
        return jsonify({
            'success': False,
            'message': 'System error occurred. Please try again.',
            'retry': True
        }), 500

@app.route('/api/access-logs', methods=['GET'])
def get_access_logs():
    limit = request.args.get('limit', 100, type=int)
    logs = db.get_recent_access_logs(limit)
    return jsonify({
        'success': True,
        'logs': logs
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    stats = face_recognizer.get_statistics()
    employees = db.get_all_employees()
    logs = db.get_recent_access_logs(1)
    
    stats['total_employees'] = len(employees)
    stats['last_access'] = logs[0]['access_time'] if logs else None
    
    return jsonify({
        'success': True,
        'stats': stats
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': 'Resource not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'success': False,
        'message': 'Internal server error'
    }), 500

if __name__ == '__main__':
    reload_face_encodings()
    app.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
