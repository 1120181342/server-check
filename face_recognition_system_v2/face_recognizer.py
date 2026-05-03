import face_recognition
import numpy as np
import logging
import time
import pickle
import os
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor, Future
from threading import Lock
from collections import OrderedDict
from functools import lru_cache


logger = logging.getLogger(__name__)


@dataclass
class RecognitionResult:
    success: bool
    employee_id: Optional[str] = None
    name: Optional[str] = None
    confidence: float = 0.0
    distance: float = 1.0
    message: str = ""
    processing_time: float = 0.0
    retry_count: int = 0


class LRUCache:
    def __init__(self, capacity: int = 100, ttl_seconds: int = 300):
        self.capacity = capacity
        self.ttl_seconds = ttl_seconds
        self._cache: OrderedDict = OrderedDict()
        self._lock = Lock()
    
    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key not in self._cache:
                return None
            
            value, timestamp = self._cache[key]
            
            if time.time() - timestamp > self.ttl_seconds:
                del self._cache[key]
                return None
            
            self._cache.move_to_end(key)
            return value
    
    def put(self, key: str, value: Any):
        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            else:
                if len(self._cache) >= self.capacity:
                    self._cache.popitem(last=False)
            
            self._cache[key] = (value, time.time())
    
    def clear(self):
        with self._lock:
            self._cache.clear()
    
    def __len__(self):
        with self._lock:
            return len(self._cache)


class FaceRecognizer:
    def __init__(
        self,
        tolerance: float = 0.6,
        cache_dir: Optional[str] = None,
        max_workers: int = 2,
        cache_capacity: int = 100,
        cache_ttl_seconds: int = 300
    ):
        self.tolerance = tolerance
        self.cache_dir = cache_dir
        
        self._known_encodings: List[np.ndarray] = []
        self._known_employee_ids: List[str] = []
        self._known_names: List[str] = []
        
        self._lock = Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        
        self._encoding_cache = LRUCache(capacity=cache_capacity, ttl_seconds=cache_ttl_seconds)
        self._recognition_cache = LRUCache(capacity=cache_capacity, ttl_seconds=cache_ttl_seconds)
        
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"FaceRecognizer initialized with tolerance={tolerance}, workers={max_workers}")
    
    def load_face_encodings(self, face_data: List[Dict[str, Any]]) -> int:
        with self._lock:
            self._known_encodings = []
            self._known_employee_ids = []
            self._known_names = []
            
            count = 0
            for data in face_data:
                try:
                    if isinstance(data['encoding'], bytes):
                        encoding = pickle.loads(data['encoding'])
                    else:
                        encoding = np.array(data['encoding'])
                    
                    if isinstance(encoding, list):
                        encoding = np.array(encoding)
                    
                    self._known_encodings.append(encoding)
                    self._known_employee_ids.append(data['employee_id'])
                    self._known_names.append(data['name'])
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to load encoding for {data.get('employee_id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Loaded {count} face encodings")
            return count
    
    def encode_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        try:
            if image.dtype == np.float32:
                image = (image + 1.0) / 2.0
                image = (image * 255).astype(np.uint8)
            
            if len(image.shape) == 2:
                image = np.stack([image, image, image], axis=2)
            
            cache_key = self._hash_image(image)
            cached = self._encoding_cache.get(cache_key)
            if cached is not None:
                return cached
            
            face_locations = face_recognition.face_locations(image, model='hog')
            
            if not face_locations:
                return None
            
            encodings = face_recognition.face_encodings(image, face_locations)
            
            if encodings:
                encoding = encodings[0]
                self._encoding_cache.put(cache_key, encoding)
                return encoding
            
            return None
        except Exception as e:
            logger.error(f"Face encoding error: {e}")
            return None
    
    def _hash_image(self, image: np.ndarray) -> str:
        small = image[::8, ::8]
        return str(hash(small.tobytes()))
    
    def encode_face_async(self, image: np.ndarray, callback: callable = None) -> Future:
        future = self._executor.submit(self.encode_face, image)
        
        if callback:
            future.add_done_callback(lambda f: callback(f.result()))
        
        return future
    
    def _compare_faces(
        self, 
        known_encodings: List[np.ndarray], 
        face_encoding: np.ndarray, 
        tolerance: float
    ) -> Tuple[List[bool], np.ndarray]:
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=tolerance)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        return matches, face_distances
    
    def recognize_face(
        self, 
        face_encoding: np.ndarray, 
        tolerance: Optional[float] = None
    ) -> RecognitionResult:
        start_time = time.time()
        
        if tolerance is None:
            tolerance = self.tolerance
        
        with self._lock:
            if not self._known_encodings:
                return RecognitionResult(
                    success=False,
                    message="No registered faces in the system",
                    processing_time=time.time() - start_time
                )
        
        cache_key = self._hash_encoding(face_encoding)
        cached = self._recognition_cache.get(cache_key)
        if cached is not None:
            cached.processing_time = time.time() - start_time
            return cached
        
        matches, face_distances = self._compare_faces(
            self._known_encodings, face_encoding, tolerance
        )
        
        if True not in matches:
            result = RecognitionResult(
                success=False,
                message="Face not recognized. Please try again.",
                distance=float(np.min(face_distances)) if len(face_distances) > 0 else 1.0,
                processing_time=time.time() - start_time
            )
            self._recognition_cache.put(cache_key, result)
            return result
        
        best_match_index = np.argmin(face_distances)
        
        if matches[best_match_index]:
            with self._lock:
                employee_id = self._known_employee_ids[best_match_index]
                name = self._known_names[best_match_index]
            
            distance = float(face_distances[best_match_index])
            confidence = 1.0 - distance
            
            result = RecognitionResult(
                success=True,
                employee_id=employee_id,
                name=name,
                confidence=confidence,
                distance=distance,
                message=f"Welcome, {name}!",
                processing_time=time.time() - start_time
            )
            self._recognition_cache.put(cache_key, result)
            return result
        
        result = RecognitionResult(
            success=False,
            message="Face not recognized. Please try again.",
            processing_time=time.time() - start_time
        )
        self._recognition_cache.put(cache_key, result)
        return result
    
    def _hash_encoding(self, encoding: np.ndarray) -> str:
        rounded = np.round(encoding, decimals=3)
        return str(hash(rounded.tobytes()))
    
    def recognize_face_with_retry(
        self, 
        face_encoding: np.ndarray, 
        retries: int = 3, 
        tolerance_decay: float = 0.05
    ) -> RecognitionResult:
        start_time = time.time()
        current_tolerance = self.tolerance
        
        for i in range(retries):
            result = self.recognize_face(face_encoding, current_tolerance)
            
            if result.success:
                result.retry_count = i
                result.processing_time = time.time() - start_time
                return result
            
            current_tolerance += tolerance_decay
        
        return RecognitionResult(
            success=False,
            message=f"Authentication failed after {retries} attempts. Please try again.",
            processing_time=time.time() - start_time,
            retry_count=retries
        )
    
    def batch_encode_faces(self, images: List[np.ndarray]) -> List[Optional[np.ndarray]]:
        encodings = []
        
        for image in images:
            encoding = self.encode_face(image)
            encodings.append(encoding)
        
        return encodings
    
    def save_encoding_to_cache(self, employee_id: str, encoding: np.ndarray) -> bool:
        if not self.cache_dir:
            return False
        
        try:
            cache_path = os.path.join(self.cache_dir, f"{employee_id}.pkl")
            with open(cache_path, 'wb') as f:
                pickle.dump(encoding, f)
            return True
        except Exception as e:
            logger.error(f"Failed to save encoding to cache: {e}")
            return False
    
    def load_encoding_from_cache(self, employee_id: str) -> Optional[np.ndarray]:
        if not self.cache_dir:
            return None
        
        cache_path = os.path.join(self.cache_dir, f"{employee_id}.pkl")
        
        if not os.path.exists(cache_path):
            return None
        
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except Exception as e:
            logger.error(f"Failed to load encoding from cache: {e}")
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'total_registered': len(self._known_encodings),
                'tolerance': self.tolerance,
                'encoding_cache_size': len(self._encoding_cache),
                'recognition_cache_size': len(self._recognition_cache),
                'timestamp': time.time()
            }
    
    def clear_caches(self):
        self._encoding_cache.clear()
        self._recognition_cache.clear()
        logger.info("All caches cleared")
    
    def shutdown(self):
        self._executor.shutdown(wait=True)
        logger.info("FaceRecognizer shutdown complete")
