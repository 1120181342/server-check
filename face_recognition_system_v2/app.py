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
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from config import Config
from database import EmployeeDatabase, Employee, AccessLog
from face_detector import OptimizedFaceDetector, FaceInfo
from face_recognizer import FaceRecognizer, RecognitionResult
from performance import (
    CircuitBreaker, CircuitBreakerConfig,
    RateLimiter, PerformanceMonitor, HealthChecker,
    timed, with_circuit_breaker, rate_limited
)


logger = logging.getLogger(__name__)

config = Config()

app = Flask(__name__)
CORS(app)
app.config.from_object(config)

db: Optional[EmployeeDatabase] = None
face_detector: Optional[OptimizedFaceDetector] = None
face_recognizer: Optional[FaceRecognizer] = None

recognition_circuit: Optional[CircuitBreaker] = None
database_circuit: Optional[CircuitBreaker] = None
recognition_limiter: Optional[RateLimiter] = None
performance_monitor: Optional[PerformanceMonitor] = None
health_checker: Optional[HealthChecker] = None


def init_components():
    global db, face_detector, face_recognizer
    global recognition_circuit, database_circuit, recognition_limiter
    global performance_monitor, health_checker
    
    logger.info("Initializing components...")
    
    db = EmployeeDatabase(
        db_path=config.DATABASE_PATH,
        pool_size=config.PERFORMANCE.db_connection_pool_size
    )
    
    face_detector = OptimizedFaceDetector(
        min_face_size=config.RECOGNITION.min_face_size,
        max_face_size=config.RECOGNITION.max_face_size,
        scale_factor=config.RECOGNITION.scale_factor,
        min_neighbors=config.RECOGNITION.min_neighbors,
        downscale_factor=config.PERFORMANCE.frame_downscale_factor,
        skip_frames=config.PERFORMANCE.skip_frames
    )
    
    face_recognizer = FaceRecognizer(
        tolerance=config.RECOGNITION.face_tolerance,
        cache_dir=config.CACHE_DIR,
        max_workers=config.PERFORMANCE.max_recognition_workers,
        cache_ttl_seconds=config.PERFORMANCE.cache_ttl_seconds
    )
    
    recognition_circuit = CircuitBreaker(
        config=CircuitBreakerConfig(
            failure_threshold=config.STABILITY.circuit_breaker_threshold,
            recovery_timeout=config.STABILITY.circuit_breaker_timeout
        ),
        name="recognition"
    )
    
    database_circuit = CircuitBreaker(
        config=CircuitBreakerConfig(
            failure_threshold=config.STABILITY.circuit_breaker_threshold,
            recovery_timeout=config.STABILITY.circuit_breaker_timeout
        ),
        name="database"
    )
    
    recognition_limiter = RateLimiter(
        rate=5.0,
        capacity=10,
        name="recognition"
    )
    
    performance_monitor = PerformanceMonitor(
        window_size=1000,
        name="face_recognition"
    )
    
    health_checker = HealthChecker(
        check_interval=config.STABILITY.health_check_interval,
        name="system"
    )
    
    health_checker.register_check("database", check_database_health)
    health_checker.register_check("face_recognition", check_recognition_health)
    
    health_checker.start()
    
    reload_face_encodings()
    
    logger.info("All components initialized successfully")


def check_database_health() -> bool:
    try:
        if db is None:
            return False
        employees = db.get_all_employees()
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


def check_recognition_health() -> bool:
    try:
        if face_recognizer is None:
            return False
        stats = face_recognizer.get_statistics()
        return stats is not None
    except Exception as e:
        logger.error(f"Recognition health check failed: {e}")
        return False


def reload_face_encodings() -> int:
    if db is None or face_recognizer is None:
        return 0
    
    face_data = db.get_all_face_encodings()
    count = face_recognizer.load_face_encodings(face_data)
    logger.info(f"Loaded {count} face encodings")
    return count


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/health', methods=['GET'])
def health_check():
    if health_checker is None:
        return jsonify({
            'success': False,
            'message': 'Health checker not initialized'
        }), 503
    
    status = health_checker.get_status()
    
    return jsonify({
        'success': status['healthy'],
        'healthy': status['healthy'],
        'timestamp': status['timestamp'],
        'details': status['details']
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    if db is None or face_recognizer is None or performance_monitor is None:
        return jsonify({
            'success': False,
            'message': 'Components not initialized'
        }), 500
    
    try:
        db_stats = db.get_statistics()
        recognizer_stats = face_recognizer.get_statistics()
        perf_stats = performance_monitor.get_all_stats()
        
        circuit_stats = {
            'recognition': recognition_circuit.get_metrics() if recognition_circuit else {},
            'database': database_circuit.get_metrics() if database_circuit else {}
        }
        
        return jsonify({
            'success': True,
            'database': db_stats,
            'recognizer': recognizer_stats,
            'performance': perf_stats,
            'circuit_breakers': circuit_stats
        })
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/employees', methods=['GET'])
@timed(performance_monitor, 'get_employees')
@with_circuit_breaker(database_circuit)
def get_employees():
    if db is None:
        return jsonify({
            'success': False,
            'message': 'Database not initialized'
        }), 500
    
    try:
        employees = db.get_all_employees()
        return jsonify({
            'success': True,
            'employees': [e.to_dict() for e in employees]
        })
    except Exception as e:
        logger.error(f"Error getting employees: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/employees/<employee_id>', methods=['GET'])
@timed(performance_monitor, 'get_employee')
@with_circuit_breaker(database_circuit)
def get_employee(employee_id: str):
    if db is None:
        return jsonify({
            'success': False,
            'message': 'Database not initialized'
        }), 500
    
    try:
        employee = db.get_employee_by_id(employee_id)
        if employee:
            return jsonify({
                'success': True,
                'employee': employee.to_dict()
            })
        return jsonify({
            'success': False,
            'message': 'Employee not found'
        }), 404
    except Exception as e:
        logger.error(f"Error getting employee: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/employees', methods=['POST'])
@timed(performance_monitor, 'add_employee')
@with_circuit_breaker(database_circuit)
def add_employee():
    if db is None:
        return jsonify({
            'success': False,
            'message': 'Database not initialized'
        }), 500
    
    try:
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
        
        employee = Employee(
            employee_id=data['employee_id'],
            name=data['name'],
            department=data['department'],
            email=data.get('email'),
            phone=data.get('phone')
        )
        
        if db.add_employee(employee):
            return jsonify({
                'success': True,
                'message': 'Employee added successfully',
                'employee': employee.to_dict()
            })
        
        return jsonify({
            'success': False,
            'message': 'Failed to add employee'
        }), 500
        
    except Exception as e:
        logger.error(f"Error adding employee: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/employees/<employee_id>', methods=['PUT'])
@timed(performance_monitor, 'update_employee')
@with_circuit_breaker(database_circuit)
def update_employee(employee_id: str):
    if db is None:
        return jsonify({
            'success': False,
            'message': 'Database not initialized'
        }), 500
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': 'No data provided'
            }), 400
        
        if db.get_employee_by_id(employee_id):
            updates = {}
            if 'name' in data:
                updates['name'] = data['name']
            if 'department' in data:
                updates['department'] = data['department']
            if 'email' in data:
                updates['email'] = data['email']
            if 'phone' in data:
                updates['phone'] = data['phone']
            
            if updates:
                if db.update_employee(employee_id, updates):
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
        
    except Exception as e:
        logger.error(f"Error updating employee: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/employees/<employee_id>', methods=['DELETE'])
@timed(performance_monitor, 'delete_employee')
@with_circuit_breaker(database_circuit)
def delete_employee(employee_id: str):
    if db is None:
        return jsonify({
            'success': False,
            'message': 'Database not initialized'
        }), 500
    
    try:
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
        
    except Exception as e:
        logger.error(f"Error deleting employee: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def allowed_file(filename: str) -> bool:
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


@app.route('/api/employees/<employee_id>/face', methods=['POST'])
@timed(performance_monitor, 'upload_face')
@with_circuit_breaker(database_circuit)
def upload_face(employee_id: str):
    if db is None or face_detector is None or face_recognizer is None:
        return jsonify({
            'success': False,
            'message': 'Components not initialized'
        }), 500
    
    try:
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
            image = Image.open(file)
            image_np = np.array(image)
            
            if len(image_np.shape) == 3 and image_np.shape[2] == 4:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGBA2BGR)
            elif len(image_np.shape) == 3:
                image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
            
            detection_result = face_detector.detect(image_np)
            
            if not detection_result.success or not detection_result.faces:
                return jsonify({
                    'success': False,
                    'message': 'No face detected in the image'
                }), 400
            
            face_info = detection_result.faces[0]
            
            if face_info.quality_score < 0.5:
                return jsonify({
                    'success': False,
                    'message': f'Face quality too low ({face_info.quality_score:.2f}). Please provide a clearer image.'
                }), 400
            
            aligned_face = face_detector.align_face(image_np, face_info.location)
            preprocessed = face_detector.preprocess_for_recognition(aligned_face)
            
            encoding = face_recognizer.encode_face(preprocessed)
            
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
                    'image_path': image_path,
                    'quality_score': face_info.quality_score
                })
            
            return jsonify({
                'success': False,
                'message': 'Failed to save face encoding'
            }), 500
        
        return jsonify({
            'success': False,
            'message': 'Invalid file type'
        }), 400
        
    except Exception as e:
        logger.error(f"Error processing face: {e}")
        return jsonify({
            'success': False,
            'message': f'Error processing image: {str(e)}'
        }), 500


@app.route('/api/recognize', methods=['POST'])
@timed(performance_monitor, 'recognize')
@with_circuit_breaker(recognition_circuit)
@rate_limited(recognition_limiter, tokens=1)
def recognize():
    if db is None or face_detector is None or face_recognizer is None:
        return jsonify({
            'success': False,
            'message': 'Components not initialized'
        }), 500
    
    start_time = datetime.now()
    
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'message': 'No image data provided'
            }), 400
        
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
        
        detection_result = face_detector.detect(image_np)
        
        if not detection_result.success or not detection_result.faces:
            log = AccessLog(
                id=None,
                employee_id=None,
                name=None,
                access_time=start_time.isoformat(),
                status='failed',
                confidence=None,
                error_message='No face detected'
            )
            db.log_access(log)
            
            return jsonify({
                'success': False,
                'message': 'No face detected. Please position your face in the camera.',
                'retry': True
            })
        
        face_info = detection_result.faces[0]
        
        if face_info.quality_score < 0.3:
            log = AccessLog(
                id=None,
                employee_id=None,
                name=None,
                access_time=start_time.isoformat(),
                status='failed',
                confidence=None,
                error_message=f'Low face quality: {face_info.quality_score:.2f}'
            )
            db.log_access(log)
            
            return jsonify({
                'success': False,
                'message': 'Face quality too low. Please adjust your position and try again.',
                'retry': True,
                'quality_score': face_info.quality_score
            })
        
        aligned_face = face_detector.align_face(image_np, face_info.location)
        preprocessed = face_detector.preprocess_for_recognition(aligned_face)
        
        encoding = face_recognizer.encode_face(preprocessed)
        
        if encoding is None:
            log = AccessLog(
                id=None,
                employee_id=None,
                name=None,
                access_time=start_time.isoformat(),
                status='failed',
                confidence=None,
                error_message='Failed to extract face features'
            )
            db.log_access(log)
            
            return jsonify({
                'success': False,
                'message': 'Failed to process face. Please try again.',
                'retry': True
            })
        
        result = face_recognizer.recognize_face_with_retry(
            encoding,
            retries=config.RECOGNITION.max_retries
        )
        
        if result.success:
            log = AccessLog(
                id=None,
                employee_id=result.employee_id,
                name=result.name,
                access_time=start_time.isoformat(),
                status='success',
                confidence=result.confidence
            )
            db.log_access(log)
            
            return jsonify({
                'success': True,
                'employee_id': result.employee_id,
                'name': result.name,
                'confidence': result.confidence,
                'distance': result.distance,
                'message': result.message,
                'processing_time': result.processing_time,
                'retry_count': result.retry_count,
                'quality_score': face_info.quality_score
            })
        else:
            log = AccessLog(
                id=None,
                employee_id=None,
                name=None,
                access_time=start_time.isoformat(),
                status='failed',
                confidence=None,
                error_message=result.message
            )
            db.log_access(log)
            
            return jsonify({
                'success': False,
                'message': result.message,
                'retry': True,
                'distance': result.distance,
                'processing_time': result.processing_time,
                'retry_count': result.retry_count
            })
            
    except Exception as e:
        logger.error(f"Recognition error: {e}")
        
        log = AccessLog(
            id=None,
            employee_id=None,
            name=None,
            access_time=start_time.isoformat(),
            status='failed',
            confidence=None,
            error_message=f'System error: {str(e)}'
        )
        if db:
            db.log_access(log)
        
        return jsonify({
            'success': False,
            'message': 'System error occurred. Please try again.',
            'retry': True
        }), 500


@app.route('/api/access-logs', methods=['GET'])
@timed(performance_monitor, 'get_access_logs')
@with_circuit_breaker(database_circuit)
def get_access_logs():
    if db is None:
        return jsonify({
            'success': False,
            'message': 'Database not initialized'
        }), 500
    
    try:
        start_time = request.args.get('start_time', None)
        end_time = request.args.get('end_time', None)
        limit = request.args.get('limit', 1000, type=int)
        
        if start_time or end_time:
            logs = db.get_access_logs_by_time_range(start_time, end_time, limit)
        else:
            logs = db.get_recent_access_logs(limit)
        
        return jsonify({
            'success': True,
            'logs': [log.to_dict() for log in logs]
        })
    except Exception as e:
        logger.error(f"Error getting access logs: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


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


@app.before_request
def before_request():
    pass


@app.after_request
def after_request(response):
    return response


def shutdown():
    logger.info("Shutting down application...")
    
    if health_checker:
        health_checker.stop()
    
    if face_recognizer:
        face_recognizer.shutdown()
    
    if db:
        db.close()
    
    logger.info("Application shutdown complete")


import atexit
atexit.register(shutdown)


if __name__ == '__main__':
    init_components()
    logger.info(f"Starting server on {config.HOST}:{config.PORT}")
    app.run(debug=config.DEBUG, host=config.HOST, port=config.PORT, threaded=True)
