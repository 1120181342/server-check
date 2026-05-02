import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'face-recognition-secret-key-2024'
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATABASE_PATH = os.path.join(BASE_DIR, 'data', 'employees.db')
    FACES_DIR = os.path.join(BASE_DIR, 'data', 'faces')
    MODELS_DIR = os.path.join(BASE_DIR, 'data', 'models')
    
    FACE_TOLERANCE = 0.6
    MIN_FACE_SIZE = 100
    MAX_FACE_SIZE = 1000
    
    RECOGNITION_TIMEOUT = 5.0
    RETRY_COUNT = 3
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    def __init__(self):
        self._ensure_directories()
    
    def _ensure_directories(self):
        for dir_path in [self.FACES_DIR, self.MODELS_DIR, os.path.dirname(self.DATABASE_PATH)]:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path)
