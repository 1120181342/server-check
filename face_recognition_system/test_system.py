import os
import sys
import unittest
import tempfile
import shutil
import numpy as np
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import EmployeeDatabase
from face_processor import FaceProcessor, FaceInfo
from face_recognizer import FaceRecognizer, RecognitionResult

class TestConfig(unittest.TestCase):
    def test_config_initialization(self):
        config = Config()
        
        self.assertIsNotNone(config.SECRET_KEY)
        self.assertTrue(os.path.exists(config.FACES_DIR))
        self.assertTrue(os.path.exists(config.MODELS_DIR))
        self.assertEqual(config.FACE_TOLERANCE, 0.6)
        self.assertEqual(config.MIN_FACE_SIZE, 100)
    
    def test_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = Config.BASE_DIR
            try:
                Config.BASE_DIR = tmpdir
                config = Config()
                
                self.assertTrue(os.path.exists(config.FACES_DIR))
                self.assertTrue(os.path.exists(config.MODELS_DIR))
            finally:
                Config.BASE_DIR = original_base_dir

class TestEmployeeDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = EmployeeDatabase(self.db_path)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_add_employee(self):
        employee = {
            'employee_id': 'EMP001',
            'name': '张三',
            'department': '技术部',
            'email': 'zhangsan@example.com',
            'phone': '13800138000'
        }
        
        result = self.db.add_employee(employee)
        self.assertTrue(result)
        
        retrieved = self.db.get_employee_by_id('EMP001')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved['name'], '张三')
    
    def test_duplicate_employee(self):
        employee = {
            'employee_id': 'EMP001',
            'name': '张三',
            'department': '技术部'
        }
        
        self.db.add_employee(employee)
        result = self.db.add_employee(employee)
        
        self.assertFalse(result)
    
    def test_get_all_employees(self):
        employees = [
            {'employee_id': 'EMP001', 'name': '张三', 'department': '技术部'},
            {'employee_id': 'EMP002', 'name': '李四', 'department': '市场部'}
        ]
        
        for emp in employees:
            self.db.add_employee(emp)
        
        all_employees = self.db.get_all_employees()
        self.assertEqual(len(all_employees), 2)
    
    def test_update_employee(self):
        employee = {
            'employee_id': 'EMP001',
            'name': '张三',
            'department': '技术部'
        }
        
        self.db.add_employee(employee)
        
        updates = {'name': '张三丰', 'phone': '13900139000'}
        result = self.db.update_employee('EMP001', updates)
        
        self.assertTrue(result)
        
        retrieved = self.db.get_employee_by_id('EMP001')
        self.assertEqual(retrieved['name'], '张三丰')
        self.assertEqual(retrieved['phone'], '13900139000')
    
    def test_delete_employee(self):
        employee = {
            'employee_id': 'EMP001',
            'name': '张三',
            'department': '技术部'
        }
        
        self.db.add_employee(employee)
        self.assertIsNotNone(self.db.get_employee_by_id('EMP001'))
        
        result = self.db.delete_employee('EMP001')
        self.assertTrue(result)
        
        self.assertIsNone(self.db.get_employee_by_id('EMP001'))
    
    def test_access_logs(self):
        result = self.db.log_access(
            status='success',
            employee_id='EMP001',
            name='张三',
            confidence=0.95
        )
        self.assertTrue(result)
        
        logs = self.db.get_recent_access_logs(10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['status'], 'success')
        self.assertEqual(logs[0]['employee_id'], 'EMP001')
    
    def test_access_logs_by_time_range(self):
        import time
        
        self.db.log_access(status='success', employee_id='EMP001', name='张三', confidence=0.95)
        time.sleep(0.01)
        
        mid_time = time.strftime('%Y-%m-%d %H:%M:%S')
        time.sleep(0.01)
        
        self.db.log_access(status='success', employee_id='EMP002', name='李四', confidence=0.88)
        
        all_logs = self.db.get_recent_access_logs(100)
        self.assertEqual(len(all_logs), 2)
        
        future_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 3600))
        logs_from_mid = self.db.get_access_logs_by_time_range(start_time=mid_time)
        self.assertEqual(len(logs_from_mid), 1)
        
        past_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() - 3600))
        logs_to_past = self.db.get_access_logs_by_time_range(end_time=past_time)
        self.assertEqual(len(logs_to_past), 0)
        
        logs_between = self.db.get_access_logs_by_time_range(start_time=past_time, end_time=future_time)
        self.assertEqual(len(logs_between), 2)
        
        logs_with_limit = self.db.get_access_logs_by_time_range(limit=1)
        self.assertEqual(len(logs_with_limit), 1)

class TestFaceProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = FaceProcessor(min_face_size=50, max_face_size=500)
    
    def test_preprocess_image(self):
        test_image = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        
        processed = self.processor.preprocess_image(test_image, target_size=(160, 160))
        
        self.assertEqual(processed.shape, (160, 160, 3))
        self.assertTrue(np.all(processed >= -1.0))
        self.assertTrue(np.all(processed <= 1.0))
    
    def test_detect_faces_no_face(self):
        test_image = np.random.randint(0, 256, (480, 640, 3), dtype=np.uint8)
        
        faces = self.processor.detect_faces(test_image)
        
        self.assertEqual(len(faces), 0)
    
    def test_face_info_dataclass(self):
        image = np.random.rand(160, 160, 3)
        location = (100, 100, 200, 200)
        
        face_info = FaceInfo(image=image, location=location)
        
        self.assertEqual(face_info.image.shape, image.shape)
        self.assertEqual(face_info.location, location)
        self.assertIsNone(face_info.landmarks)
        self.assertIsNone(face_info.encoding)

class TestFaceRecognizer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.recognizer = FaceRecognizer(tolerance=0.6, cache_dir=self.temp_dir)
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.recognizer.shutdown()
    
    def test_initialization(self):
        stats = self.recognizer.get_statistics()
        self.assertEqual(stats['total_registered'], 0)
        self.assertEqual(stats['tolerance'], 0.6)
    
    def test_load_face_encodings(self):
        import pickle
        
        mock_encoding = np.random.rand(128).astype(np.float64)
        encoding_bytes = pickle.dumps(mock_encoding)
        
        test_data = [
            {
                'employee_id': 'EMP001',
                'name': '张三',
                'encoding': encoding_bytes
            }
        ]
        
        count = self.recognizer.load_face_encodings(test_data)
        
        self.assertEqual(count, 1)
        stats = self.recognizer.get_statistics()
        self.assertEqual(stats['total_registered'], 1)
    
    def test_recognition_result_dataclass(self):
        result = RecognitionResult(
            success=True,
            employee_id='EMP001',
            name='张三',
            confidence=0.95,
            distance=0.05,
            message='欢迎，张三！'
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.employee_id, 'EMP001')
        self.assertEqual(result.name, '张三')
        self.assertEqual(result.confidence, 0.95)
    
    def test_cache_operations(self):
        test_encoding = np.random.rand(128)
        
        save_result = self.recognizer.save_encoding_to_cache('EMP001', test_encoding)
        self.assertTrue(save_result)
        
        loaded = self.recognizer.load_encoding_from_cache('EMP001')
        self.assertIsNotNone(loaded)
        np.testing.assert_array_equal(loaded, test_encoding)
        
        not_found = self.recognizer.load_encoding_from_cache('NONEXISTENT')
        self.assertIsNone(not_found)

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = EmployeeDatabase(self.db_path)
        self.processor = FaceProcessor()
        self.recognizer = FaceRecognizer(cache_dir=os.path.join(self.temp_dir, 'cache'))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        self.recognizer.shutdown()
    
    def test_employee_registration_flow(self):
        employee = {
            'employee_id': 'EMP001',
            'name': '张三',
            'department': '技术部'
        }
        
        result = self.db.add_employee(employee)
        self.assertTrue(result)
        
        test_encoding = np.random.rand(128)
        import pickle
        encoding_bytes = pickle.dumps(test_encoding)
        
        face_result = self.db.add_face_encoding('EMP001', encoding_bytes, 'test.jpg')
        self.assertTrue(face_result)
        
        face_data = self.db.get_all_face_encodings()
        self.assertEqual(len(face_data), 1)
        
        load_count = self.recognizer.load_face_encodings(face_data)
        self.assertEqual(load_count, 1)
    
    def test_access_logging_integration(self):
        employee = {
            'employee_id': 'EMP001',
            'name': '张三',
            'department': '技术部'
        }
        self.db.add_employee(employee)
        
        log_result = self.db.log_access(
            status='success',
            employee_id='EMP001',
            name='张三',
            confidence=0.92
        )
        self.assertTrue(log_result)
        
        logs = self.db.get_recent_access_logs(10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['employee_id'], 'EMP001')
        self.assertEqual(logs[0]['confidence'], 0.92)

if __name__ == '__main__':
    unittest.main(verbosity=2)
