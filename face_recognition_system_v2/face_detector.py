import cv2
import numpy as np
import logging
import time
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


logger = logging.getLogger(__name__)


@dataclass
class FaceInfo:
    image: np.ndarray
    location: Tuple[int, int, int, int]
    confidence: float = 1.0
    landmarks: Optional[List[Tuple[int, int]]] = None
    quality_score: float = 0.0
    angle: float = 0.0


@dataclass
class DetectionResult:
    success: bool
    faces: List[FaceInfo] = field(default_factory=list)
    processing_time: float = 0.0
    error_message: Optional[str] = None


class BaseFaceDetector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray) -> DetectionResult:
        pass
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        pass


class HaarCascadeDetector(BaseFaceDetector):
    def __init__(
        self,
        min_face_size: int = 80,
        max_face_size: int = 800,
        scale_factor: float = 1.1,
        min_neighbors: int = 4
    ):
        self.min_face_size = min_face_size
        self.max_face_size = max_face_size
        self.scale_factor = scale_factor
        self.min_neighbors = min_neighbors
        
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
        self.profile_face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_profileface.xml'
        )
        
        logger.info("HaarCascadeDetector initialized")
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        gray = cv2.equalizeHist(gray)
        
        return gray
    
    def enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            lab = cv2.merge((l, a, b))
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return enhanced
        
        return image
    
    def detect(self, image: np.ndarray) -> DetectionResult:
        start_time = time.time()
        
        try:
            enhanced = self.enhance_contrast(image)
            gray = self.preprocess(enhanced)
            
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=self.scale_factor,
                minNeighbors=self.min_neighbors,
                minSize=(self.min_face_size, self.min_face_size),
                maxSize=(self.max_face_size, self.max_face_size)
            )
            
            if len(faces) == 0:
                profile_faces = self.profile_face_cascade.detectMultiScale(
                    gray,
                    scaleFactor=self.scale_factor,
                    minNeighbors=self.min_neighbors,
                    minSize=(self.min_face_size, self.min_face_size),
                    maxSize=(self.max_face_size, self.max_face_size)
                )
                faces = profile_faces
            
            if len(faces) == 0:
                return DetectionResult(
                    success=True,
                    faces=[],
                    processing_time=time.time() - start_time
                )
            
            face_infos = []
            
            for (x, y, w, h) in faces:
                face_roi = gray[y:y+h, x:x+w]
                
                eyes = self.eye_cascade.detectMultiScale(face_roi)
                
                quality_score = self._calculate_quality(face_roi, len(eyes))
                angle = self._estimate_angle(eyes, w, h)
                
                face_image = enhanced[y:y+h, x:x+w]
                
                face_info = FaceInfo(
                    image=face_image,
                    location=(x, y, w, h),
                    confidence=1.0,
                    quality_score=quality_score,
                    angle=angle
                )
                
                face_infos.append(face_info)
            
            return DetectionResult(
                success=True,
                faces=face_infos,
                processing_time=time.time() - start_time
            )
            
        except Exception as e:
            logger.error(f"Face detection error: {e}")
            return DetectionResult(
                success=False,
                faces=[],
                processing_time=time.time() - start_time,
                error_message=str(e)
            )
    
    def _calculate_quality(self, face_roi: np.ndarray, eye_count: int) -> float:
        score = 0.0
        
        blur_score = cv2.Laplacian(face_roi, cv2.CV_64F).var()
        if blur_score > 100:
            score += 0.4
        elif blur_score > 50:
            score += 0.2
        
        if eye_count >= 2:
            score += 0.4
        elif eye_count >= 1:
            score += 0.2
        
        brightness = np.mean(face_roi)
        if 50 < brightness < 200:
            score += 0.2
        
        return min(score, 1.0)
    
    def _estimate_angle(self, eyes: List[Tuple], face_width: int, face_height: int) -> float:
        if len(eyes) < 2:
            return 0.0
        
        eyes = sorted(eyes, key=lambda e: e[0])
        
        left_eye = eyes[0]
        right_eye = eyes[1]
        
        left_center = (left_eye[0] + left_eye[2] // 2, left_eye[1] + left_eye[3] // 2)
        right_center = (right_eye[0] + right_eye[2] // 2, right_eye[1] + right_eye[3] // 2)
        
        dx = right_center[0] - left_center[0]
        dy = right_center[1] - left_center[1]
        
        if dx == 0:
            return 0.0
        
        angle = np.degrees(np.arctan2(dy, dx))
        
        return angle


class OptimizedFaceDetector:
    def __init__(
        self,
        min_face_size: int = 80,
        max_face_size: int = 800,
        scale_factor: float = 1.1,
        min_neighbors: int = 4,
        downscale_factor: float = 0.5,
        skip_frames: int = 2
    ):
        self.detector = HaarCascadeDetector(
            min_face_size=min_face_size,
            max_face_size=max_face_size,
            scale_factor=scale_factor,
            min_neighbors=min_neighbors
        )
        
        self.downscale_factor = downscale_factor
        self.skip_frames = skip_frames
        self._frame_count = 0
        self._last_faces: List[FaceInfo] = []
        
        logger.info(f"OptimizedFaceDetector initialized with downscale={downscale_factor}, skip_frames={skip_frames}")
    
    def detect(self, image: np.ndarray) -> DetectionResult:
        start_time = time.time()
        
        self._frame_count += 1
        
        if self._frame_count % (self.skip_frames + 1) != 0 and self._last_faces:
            return DetectionResult(
                success=True,
                faces=self._last_faces,
                processing_time=time.time() - start_time
            )
        
        if self.downscale_factor < 1.0:
            height, width = image.shape[:2]
            new_width = int(width * self.downscale_factor)
            new_height = int(height * self.downscale_factor)
            small_image = cv2.resize(image, (new_width, new_height))
        else:
            small_image = image
        
        result = self.detector.detect(small_image)
        
        if result.success and result.faces:
            scaled_faces = []
            for face in result.faces:
                x, y, w, h = face.location
                scale = 1.0 / self.downscale_factor
                
                scaled_location = (
                    int(x * scale),
                    int(y * scale),
                    int(w * scale),
                    int(h * scale)
                )
                
                sx, sy, sw, sh = scaled_location
                original_face = image[sy:sy+sh, sx:sx+sw]
                
                scaled_face = FaceInfo(
                    image=original_face,
                    location=scaled_location,
                    confidence=face.confidence,
                    quality_score=face.quality_score,
                    angle=face.angle
                )
                
                scaled_faces.append(scaled_face)
            
            self._last_faces = scaled_faces
            
            return DetectionResult(
                success=True,
                faces=scaled_faces,
                processing_time=time.time() - start_time
            )
        
        self._last_faces = []
        return DetectionResult(
            success=result.success,
            faces=[],
            processing_time=time.time() - start_time,
            error_message=result.error_message
        )
    
    def align_face(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = face_location
        face = image[y:y+h, x:x+w]
        
        if len(face.shape) == 3:
            gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        else:
            gray = face
        
        eyes = self.detector.eye_cascade.detectMultiScale(gray)
        
        if len(eyes) >= 2:
            eyes = sorted(eyes, key=lambda e: e[0])
            
            left_eye = eyes[0]
            right_eye = eyes[1]
            
            left_center = (left_eye[0] + left_eye[2] // 2, left_eye[1] + left_eye[3] // 2)
            right_center = (right_eye[0] + right_eye[2] // 2, right_eye[1] + right_eye[3] // 2)
            
            dx = right_center[0] - left_center[0]
            dy = right_center[1] - left_center[1]
            
            if dx != 0:
                angle = np.degrees(np.arctan2(dy, dx))
                
                eyes_center = (
                    (left_center[0] + right_center[0]) // 2,
                    (left_center[1] + right_center[1]) // 2
                )
                
                rotation_matrix = cv2.getRotationMatrix2D(eyes_center, angle, 1.0)
                
                aligned_face = cv2.warpAffine(
                    face,
                    rotation_matrix,
                    (w, h),
                    flags=cv2.INTER_CUBIC,
                    borderMode=cv2.BORDER_CONSTANT
                )
                
                return aligned_face
        
        return face
    
    def preprocess_for_recognition(self, image: np.ndarray, target_size: Tuple[int, int] = (160, 160)) -> np.ndarray:
        if len(image.shape) == 2:
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        elif image.shape[2] == 4:
            image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        elif image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        image = cv2.resize(image, target_size)
        
        image = image.astype(np.float32) / 255.0
        image = (image - 0.5) * 2.0
        
        return image
    
    def draw_face_box(
        self, 
        image: np.ndarray, 
        face_location: Tuple[int, int, int, int], 
        label: str = "", 
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 2
    ) -> np.ndarray:
        x, y, w, h = face_location
        
        cv2.rectangle(image, (x, y), (x+w, y+h), color, thickness)
        
        if label:
            label_size, baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.9, 2)
            cv2.rectangle(
                image, 
                (x, y - label_size[1] - 10), 
                (x + label_size[0], y), 
                color, 
                cv2.FILLED
            )
            cv2.putText(image, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        
        return image
