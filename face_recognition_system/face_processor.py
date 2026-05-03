import cv2
import numpy as np
from typing import Tuple, Optional, List
from dataclasses import dataclass

@dataclass
class FaceInfo:
    image: np.ndarray
    location: Tuple[int, int, int, int]
    landmarks: Optional[List] = None
    encoding: Optional[np.ndarray] = None

class FaceProcessor:
    def __init__(self, min_face_size: int = 100, max_face_size: int = 1000):
        self.min_face_size = min_face_size
        self.max_face_size = max_face_size
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )
        self.eye_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_eye.xml'
        )
    
    def preprocess_image(self, image: np.ndarray, target_size: Tuple[int, int] = (160, 160)) -> np.ndarray:
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
    
    def detect_faces(self, image: np.ndarray, scale_factor: float = 1.1, min_neighbors: int = 5) -> List[Tuple[int, int, int, int]]:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=scale_factor,
            minNeighbors=min_neighbors,
            minSize=(self.min_face_size, self.min_face_size),
            maxSize=(self.max_face_size, self.max_face_size)
        )
        
        if len(faces) == 0:
            return []
        
        valid_faces = []
        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]
            eyes = self.eye_cascade.detectMultiScale(face_roi)
            
            if len(eyes) >= 1:
                valid_faces.append((x, y, w, h))
        
        return valid_faces
    
    def align_face(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = face_location
        face = image[y:y+h, x:x+w]
        
        if len(face.shape) == 3:
            gray = cv2.cvtColor(face, cv2.COLOR_BGR2GRAY)
        else:
            gray = face
        
        eyes = self.eye_cascade.detectMultiScale(gray)
        
        if len(eyes) >= 2:
            eyes = sorted(eyes, key=lambda e: e[0])
            
            left_eye = eyes[0]
            right_eye = eyes[1]
            
            left_eye_center = (left_eye[0] + left_eye[2] // 2, left_eye[1] + left_eye[3] // 2)
            right_eye_center = (right_eye[0] + right_eye[2] // 2, right_eye[1] + right_eye[3] // 2)
            
            dx = right_eye_center[0] - left_eye_center[0]
            dy = right_eye_center[1] - left_eye_center[1]
            
            angle = np.degrees(np.arctan2(dy, dx))
            
            eyes_center = (
                (left_eye_center[0] + right_eye_center[0]) // 2,
                (left_eye_center[1] + right_eye_center[1]) // 2
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
    
    def extract_face(self, image: np.ndarray, face_location: Tuple[int, int, int, int]) -> np.ndarray:
        x, y, w, h = face_location
        face = image[y:y+h, x:x+w]
        
        face = self.align_face(image, face_location)
        
        face = cv2.resize(face, (160, 160))
        
        return face
    
    def enhance_image(self, image: np.ndarray) -> np.ndarray:
        if len(image.shape) == 3:
            lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l = clahe.apply(l)
            
            lab = cv2.merge((l, a, b))
            enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
            
            return enhanced
        
        return image
    
    def process_frame(self, image: np.ndarray) -> List[FaceInfo]:
        faces = []
        
        enhanced = self.enhance_image(image)
        
        face_locations = self.detect_faces(enhanced)
        
        for location in face_locations:
            face_image = self.extract_face(enhanced, location)
            preprocessed = self.preprocess_image(face_image)
            
            faces.append(FaceInfo(
                image=preprocessed,
                location=location
            ))
        
        return faces
    
    def draw_face_box(self, image: np.ndarray, face_location: Tuple[int, int, int, int], 
                       label: str = "", color: Tuple[int, int, int] = (0, 255, 0)) -> np.ndarray:
        x, y, w, h = face_location
        
        cv2.rectangle(image, (x, y), (x+w, y+h), color, 2)
        
        if label:
            cv2.putText(image, label, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)
        
        return image
