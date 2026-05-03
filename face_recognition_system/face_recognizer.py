import face_recognition
import numpy as np
import pickle
import os
from typing import List, Tuple, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import threading

@dataclass
class RecognitionResult:
    success: bool
    employee_id: Optional[str] = None
    name: Optional[str] = None
    confidence: float = 0.0
    distance: float = 1.0
    message: str = ""

class FaceRecognizer:
    def __init__(self, tolerance: float = 0.6, cache_dir: Optional[str] = None):
        self.tolerance = tolerance
        self.cache_dir = cache_dir
        
        self._known_encodings: List[np.ndarray] = []
        self._known_employee_ids: List[str] = []
        self._known_names: List[str] = []
        
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=2)
        
        if self.cache_dir and not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)
    
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
                    continue
            
            return count
    
    def encode_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        try:
            if image.dtype == np.float32:
                image = (image + 1.0) / 2.0
                image = (image * 255).astype(np.uint8)
            
            if len(image.shape) == 2:
                image = np.stack([image, image, image], axis=2)
            
            face_locations = face_recognition.face_locations(image, model='hog')
            
            if not face_locations:
                return None
            
            encodings = face_recognition.face_encodings(image, face_locations)
            
            if encodings:
                return encodings[0]
            
            return None
        except Exception as e:
            return None
    
    def encode_face_async(self, image: np.ndarray, callback: callable = None):
        future = self._executor.submit(self.encode_face, image)
        
        if callback:
            future.add_done_callback(lambda f: callback(f.result()))
        
        return future
    
    def _compare_faces(self, known_encodings: List[np.ndarray], face_encoding: np.ndarray, 
                       tolerance: float) -> Tuple[List[bool], np.ndarray]:
        matches = face_recognition.compare_faces(known_encodings, face_encoding, tolerance=tolerance)
        face_distances = face_recognition.face_distance(known_encodings, face_encoding)
        return matches, face_distances
    
    def recognize_face(self, face_encoding: np.ndarray, tolerance: Optional[float] = None) -> RecognitionResult:
        if tolerance is None:
            tolerance = self.tolerance
        
        with self._lock:
            if not self._known_encodings:
                return RecognitionResult(
                    success=False,
                    message="No registered faces in the system"
                )
        
        matches, face_distances = self._compare_faces(
            self._known_encodings, face_encoding, tolerance
        )
        
        if True not in matches:
            return RecognitionResult(
                success=False,
                message="Face not recognized. Please try again.",
                distance=float(np.min(face_distances)) if len(face_distances) > 0 else 1.0
            )
        
        best_match_index = np.argmin(face_distances)
        
        if matches[best_match_index]:
            with self._lock:
                employee_id = self._known_employee_ids[best_match_index]
                name = self._known_names[best_match_index]
            
            distance = float(face_distances[best_match_index])
            confidence = 1.0 - distance
            
            return RecognitionResult(
                success=True,
                employee_id=employee_id,
                name=name,
                confidence=confidence,
                distance=distance,
                message=f"Welcome, {name}!"
            )
        
        return RecognitionResult(
            success=False,
            message="Face not recognized. Please try again."
        )
    
    def recognize_face_with_retry(self, face_encoding: np.ndarray, 
                                   retries: int = 3, 
                                   tolerance_decay: float = 0.05) -> RecognitionResult:
        current_tolerance = self.tolerance
        
        for i in range(retries):
            result = self.recognize_face(face_encoding, current_tolerance)
            
            if result.success:
                return result
            
            current_tolerance += tolerance_decay
        
        return RecognitionResult(
            success=False,
            message=f"Authentication failed after {retries} attempts. Please try again."
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
            return None
    
    def get_statistics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'total_registered': len(self._known_encodings),
                'tolerance': self.tolerance,
                'timestamp': datetime.now().isoformat()
            }
    
    def shutdown(self):
        self._executor.shutdown(wait=True)
