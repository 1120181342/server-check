import os
import logging
from typing import Optional
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler


@dataclass
class PerformanceConfig:
    frame_downscale_factor: float = 0.5
    skip_frames: int = 2
    max_recognition_workers: int = 2
    db_connection_pool_size: int = 5
    frame_buffer_size: int = 30
    recognition_timeout: float = 3.0
    cache_ttl_seconds: int = 300


@dataclass
class RecognitionConfig:
    face_tolerance: float = 0.6
    min_face_size: int = 80
    max_face_size: int = 800
    scale_factor: float = 1.1
    min_neighbors: int = 4
    max_retries: int = 2
    confidence_threshold: float = 0.7


@dataclass
class StabilityConfig:
    health_check_interval: float = 30.0
    circuit_breaker_threshold: int = 5
    circuit_breaker_timeout: float = 60.0
    max_request_retries: int = 3
    request_timeout: float = 10.0


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'face-recognition-optimized-2024'
    
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    DATABASE_PATH = os.path.join(DATA_DIR, 'employees.db')
    FACES_DIR = os.path.join(DATA_DIR, 'faces')
    MODELS_DIR = os.path.join(DATA_DIR, 'models')
    LOGS_DIR = os.path.join(DATA_DIR, 'logs')
    CACHE_DIR = os.path.join(DATA_DIR, 'cache')
    
    PERFORMANCE = PerformanceConfig()
    RECOGNITION = RecognitionConfig()
    STABILITY = StabilityConfig()
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'bmp'}
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024
    
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', '5001'))
    
    _instance: Optional['Config'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._ensure_directories()
        self._setup_logging()
        self._initialized = True
    
    def _ensure_directories(self):
        directories = [
            self.DATA_DIR,
            self.FACES_DIR,
            self.MODELS_DIR,
            self.LOGS_DIR,
            self.CACHE_DIR,
            os.path.dirname(self.DATABASE_PATH)
        ]
        
        for dir_path in directories:
            if not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
    
    def _setup_logging(self):
        log_file = os.path.join(self.LOGS_DIR, 'face_recognition.log')
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding='utf-8'
        )
        
        console_handler = logging.StreamHandler()
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        
        if self.DEBUG:
            root_logger.setLevel(logging.DEBUG)
        
        logging.info("Config initialized successfully")
        logging.info(f"Data directory: {self.DATA_DIR}")
        logging.info(f"Log file: {log_file}")
