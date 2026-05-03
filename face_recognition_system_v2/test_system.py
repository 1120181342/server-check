import os
import sys
import unittest
import tempfile
import shutil
import numpy as np
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime
import time
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import Config, PerformanceConfig, RecognitionConfig, StabilityConfig
from database import EmployeeDatabase, Employee, AccessLog, DatabaseConnectionPool
from face_detector import OptimizedFaceDetector, HaarCascadeDetector, FaceInfo, DetectionResult
from face_recognizer import FaceRecognizer, RecognitionResult, LRUCache
from performance import (
    CircuitBreaker, CircuitBreakerConfig, CircuitState,
    RateLimiter, PerformanceMonitor, HealthChecker,
    timed, with_circuit_breaker, rate_limited
)


class TestConfig(unittest.TestCase):
    def test_config_singleton(self):
        config1 = Config()
        config2 = Config()
        
        self.assertIs(config1, config2)
    
    def test_performance_config_defaults(self):
        perf = PerformanceConfig()
        
        self.assertEqual(perf.frame_downscale_factor, 0.5)
        self.assertEqual(perf.skip_frames, 2)
        self.assertEqual(perf.max_recognition_workers, 2)
        self.assertEqual(perf.db_connection_pool_size, 5)
        self.assertEqual(perf.recognition_timeout, 3.0)
        self.assertEqual(perf.cache_ttl_seconds, 300)
    
    def test_recognition_config_defaults(self):
        rec = RecognitionConfig()
        
        self.assertEqual(rec.face_tolerance, 0.6)
        self.assertEqual(rec.min_face_size, 80)
        self.assertEqual(rec.max_face_size, 800)
        self.assertEqual(rec.scale_factor, 1.1)
        self.assertEqual(rec.min_neighbors, 4)
        self.assertEqual(rec.max_retries, 2)
        self.assertEqual(rec.confidence_threshold, 0.7)
    
    def test_stability_config_defaults(self):
        stab = StabilityConfig()
        
        self.assertEqual(stab.health_check_interval, 30.0)
        self.assertEqual(stab.circuit_breaker_threshold, 5)
        self.assertEqual(stab.circuit_breaker_timeout, 60.0)
        self.assertEqual(stab.max_request_retries, 3)
        self.assertEqual(stab.request_timeout, 10.0)
    
    def test_directory_creation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_base_dir = Config.BASE_DIR
            try:
                Config.BASE_DIR = tmpdir
                config = Config()
                
                self.assertTrue(os.path.exists(config.DATA_DIR))
                self.assertTrue(os.path.exists(config.FACES_DIR))
                self.assertTrue(os.path.exists(config.MODELS_DIR))
                self.assertTrue(os.path.exists(config.LOGS_DIR))
                self.assertTrue(os.path.exists(config.CACHE_DIR))
            finally:
                Config.BASE_DIR = original_base_dir


class TestDatabaseConnectionPool(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_pool_initialization(self):
        pool = DatabaseConnectionPool(self.db_path, pool_size=3)
        pool.initialize()
        
        self.assertEqual(pool._pool.qsize(), 3)
    
    def test_get_connection(self):
        pool = DatabaseConnectionPool(self.db_path, pool_size=2)
        pool.initialize()
        
        with pool.get_connection() as conn:
            self.assertIsNotNone(conn)
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE test (id INT)')
            cursor.execute('INSERT INTO test VALUES (1)')
            conn.commit()
            
            cursor.execute('SELECT * FROM test')
            result = cursor.fetchone()
            self.assertEqual(result[0], 1)
    
    def test_connection_reuse(self):
        pool = DatabaseConnectionPool(self.db_path, pool_size=1)
        pool.initialize()
        
        with pool.get_connection() as conn1:
            pass
        
        with pool.get_connection() as conn2:
            self.assertIsNotNone(conn2)


class TestEmployeeDatabase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = EmployeeDatabase(self.db_path, pool_size=2)
    
    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_add_employee(self):
        employee = Employee(
            employee_id='EMP001',
            name='张三',
            department='技术部',
            email='zhangsan@example.com',
            phone='13800138000'
        )
        
        result = self.db.add_employee(employee)
        self.assertTrue(result)
        
        retrieved = self.db.get_employee_by_id('EMP001')
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, '张三')
        self.assertEqual(retrieved.department, '技术部')
    
    def test_duplicate_employee(self):
        employee = Employee(
            employee_id='EMP001',
            name='张三',
            department='技术部'
        )
        
        self.db.add_employee(employee)
        result = self.db.add_employee(employee)
        
        self.assertFalse(result)
    
    def test_get_all_employees(self):
        employees = [
            Employee(employee_id='EMP001', name='张三', department='技术部'),
            Employee(employee_id='EMP002', name='李四', department='市场部')
        ]
        
        for emp in employees:
            self.db.add_employee(emp)
        
        all_employees = self.db.get_all_employees()
        self.assertEqual(len(all_employees), 2)
    
    def test_update_employee(self):
        employee = Employee(
            employee_id='EMP001',
            name='张三',
            department='技术部'
        )
        
        self.db.add_employee(employee)
        
        updates = {'name': '张三丰', 'phone': '13900139000'}
        result = self.db.update_employee('EMP001', updates)
        
        self.assertTrue(result)
        
        retrieved = self.db.get_employee_by_id('EMP001')
        self.assertEqual(retrieved.name, '张三丰')
        self.assertEqual(retrieved.phone, '13900139000')
    
    def test_delete_employee(self):
        employee = Employee(
            employee_id='EMP001',
            name='张三',
            department='技术部'
        )
        
        self.db.add_employee(employee)
        self.assertIsNotNone(self.db.get_employee_by_id('EMP001'))
        
        result = self.db.delete_employee('EMP001')
        self.assertTrue(result)
        
        self.assertIsNone(self.db.get_employee_by_id('EMP001'))
    
    def test_access_logs(self):
        log = AccessLog(
            id=None,
            employee_id='EMP001',
            name='张三',
            access_time=datetime.now().isoformat(),
            status='success',
            confidence=0.95
        )
        
        result = self.db.log_access(log)
        self.assertTrue(result)
        
        logs = self.db.get_recent_access_logs(10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].status, 'success')
        self.assertEqual(logs[0].employee_id, 'EMP001')
    
    def test_access_logs_by_time_range(self):
        import time
        
        self.db.log_access(AccessLog(
            id=None, employee_id='EMP001', name='张三',
            access_time=None, status='success', confidence=0.95
        ))
        time.sleep(0.01)
        
        mid_time = time.strftime('%Y-%m-%d %H:%M:%S')
        time.sleep(0.01)
        
        self.db.log_access(AccessLog(
            id=None, employee_id='EMP002', name='李四',
            access_time=None, status='success', confidence=0.88
        ))
        
        all_logs = self.db.get_recent_access_logs(100)
        self.assertEqual(len(all_logs), 2)
        
        future_time = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time() + 3600))
        logs_from_mid = self.db.get_access_logs_by_time_range(start_time=mid_time)
        self.assertEqual(len(logs_from_mid), 1)
    
    def test_statistics(self):
        employee = Employee(employee_id='EMP001', name='张三', department='技术部')
        self.db.add_employee(employee)
        
        self.db.log_access(AccessLog(
            id=None, employee_id='EMP001', name='张三',
            access_time=None, status='success', confidence=0.95
        ))
        
        stats = self.db.get_statistics()
        
        self.assertIn('total_employees', stats)
        self.assertIn('today_access_count', stats)
        self.assertIn('today_success_count', stats)
        self.assertIn('today_success_rate', stats)


class TestLRUCache(unittest.TestCase):
    def test_cache_operations(self):
        cache = LRUCache(capacity=3, ttl_seconds=300)
        
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')
        
        self.assertEqual(len(cache), 3)
        self.assertEqual(cache.get('key1'), 'value1')
    
    def test_cache_eviction(self):
        cache = LRUCache(capacity=2, ttl_seconds=300)
        
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        cache.put('key3', 'value3')
        
        self.assertEqual(len(cache), 2)
        self.assertIsNone(cache.get('key1'))
        self.assertIsNotNone(cache.get('key2'))
        self.assertIsNotNone(cache.get('key3'))
    
    def test_cache_ttl(self):
        cache = LRUCache(capacity=3, ttl_seconds=0.1)
        
        cache.put('key1', 'value1')
        self.assertEqual(cache.get('key1'), 'value1')
        
        time.sleep(0.2)
        
        self.assertIsNone(cache.get('key1'))
    
    def test_cache_clear(self):
        cache = LRUCache(capacity=3, ttl_seconds=300)
        
        cache.put('key1', 'value1')
        cache.put('key2', 'value2')
        
        self.assertEqual(len(cache), 2)
        
        cache.clear()
        
        self.assertEqual(len(cache), 0)


class TestCircuitBreaker(unittest.TestCase):
    def test_initial_state(self):
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0),
            name='test'
        )
        
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        self.assertTrue(breaker.can_execute())
    
    def test_circuit_open_on_failures(self):
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=2, recovery_timeout=1.0),
            name='test'
        )
        
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.OPEN)
        
        self.assertFalse(breaker.can_execute())
    
    def test_circuit_recovery(self):
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=1, recovery_timeout=0.1),
            name='test'
        )
        
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.OPEN)
        
        time.sleep(0.2)
        
        self.assertTrue(breaker.can_execute())
        self.assertEqual(breaker.state, CircuitState.HALF_OPEN)
    
    def test_circuit_close_after_success(self):
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(
                failure_threshold=1, 
                recovery_timeout=0.1,
                success_threshold=2
            ),
            name='test'
        )
        
        breaker.record_failure()
        time.sleep(0.2)
        
        breaker.record_success()
        self.assertEqual(breaker.state, CircuitState.HALF_OPEN)
        
        breaker.record_success()
        self.assertEqual(breaker.state, CircuitState.CLOSED)
    
    def test_circuit_metrics(self):
        breaker = CircuitBreaker(name='test')
        
        breaker.record_success()
        breaker.record_success()
        breaker.record_failure()
        
        metrics = breaker.get_metrics()
        
        self.assertEqual(metrics['total_requests'], 3)
        self.assertEqual(metrics['successful_requests'], 2)
        self.assertEqual(metrics['failed_requests'], 1)
    
    def test_circuit_reset(self):
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60),
            name='test'
        )
        
        breaker.record_failure()
        self.assertEqual(breaker.state, CircuitState.OPEN)
        
        breaker.reset()
        
        self.assertEqual(breaker.state, CircuitState.CLOSED)
        metrics = breaker.get_metrics()
        self.assertEqual(metrics['total_requests'], 0)


class TestRateLimiter(unittest.TestCase):
    def test_initial_tokens(self):
        limiter = RateLimiter(rate=10.0, capacity=20, name='test')
        
        self.assertEqual(limiter.get_available_tokens(), 20.0)
    
    def test_try_acquire_success(self):
        limiter = RateLimiter(rate=10.0, capacity=5, name='test')
        
        for _ in range(5):
            self.assertTrue(limiter.try_acquire())
        
        self.assertEqual(limiter.get_available_tokens(), 0.0)
        self.assertFalse(limiter.try_acquire())
    
    def test_token_refill(self):
        limiter = RateLimiter(rate=10.0, capacity=5, name='test')
        
        for _ in range(5):
            limiter.try_acquire()
        
        self.assertEqual(limiter.get_available_tokens(), 0.0)
        
        time.sleep(0.3)
        
        self.assertGreater(limiter.get_available_tokens(), 0.0)
    
    def test_acquire_with_timeout(self):
        limiter = RateLimiter(rate=20.0, capacity=2, name='test')
        
        for _ in range(2):
            self.assertTrue(limiter.acquire(tokens=1, timeout=0.1))
        
        self.assertFalse(limiter.acquire(tokens=1, timeout=0.1))


class TestPerformanceMonitor(unittest.TestCase):
    def test_record_and_stats(self):
        monitor = PerformanceMonitor(window_size=100, name='test')
        
        for i in range(10):
            monitor.record('latency', i + 1)
        
        stats = monitor.get_stats('latency')
        
        self.assertEqual(stats['count'], 10)
        self.assertEqual(stats['mean'], 5.5)
        self.assertEqual(stats['min'], 1.0)
        self.assertEqual(stats['max'], 10.0)
    
    def test_percentiles(self):
        monitor = PerformanceMonitor(window_size=100, name='test')
        
        values = list(range(1, 101))
        for v in values:
            monitor.record('latency', v)
        
        stats = monitor.get_stats('latency')
        
        self.assertEqual(stats['p50'], 50.0)
        self.assertEqual(stats['p95'], 95.0)
        self.assertEqual(stats['p99'], 99.0)
    
    def test_clear(self):
        monitor = PerformanceMonitor(window_size=100, name='test')
        
        monitor.record('latency', 1.0)
        monitor.record('latency', 2.0)
        
        stats = monitor.get_stats('latency')
        self.assertEqual(stats['count'], 2)
        
        monitor.clear('latency')
        
        stats = monitor.get_stats('latency')
        self.assertEqual(stats['count'], 0)


class TestHealthChecker(unittest.TestCase):
    def test_register_and_run_checks(self):
        checker = HealthChecker(check_interval=1.0, name='test')
        
        check_called = [False]
        def mock_check():
            check_called[0] = True
            return True
        
        checker.register_check('database', mock_check)
        
        checker.run_checks()
        
        self.assertTrue(check_called[0])
        
        status = checker.get_status()
        self.assertTrue(status['healthy'])
    
    def test_failed_check(self):
        checker = HealthChecker(check_interval=1.0, name='test')
        
        def failing_check():
            return False
        
        checker.register_check('database', failing_check)
        
        checker.run_checks()
        
        status = checker.get_status()
        self.assertFalse(status['healthy'])
    
    def test_unregister_check(self):
        checker = HealthChecker(check_interval=1.0, name='test')
        
        check_called = [False]
        def mock_check():
            check_called[0] = True
            return True
        
        checker.register_check('database', mock_check)
        checker.unregister_check('database')
        
        checker.run_checks()
        
        self.assertFalse(check_called[0])


class TestPerformanceDecorators(unittest.TestCase):
    def test_timed_decorator(self):
        monitor = PerformanceMonitor(window_size=100, name='test')
        
        @timed(monitor, 'test_metric')
        def test_function():
            time.sleep(0.01)
            return 'success'
        
        result = test_function()
        
        self.assertEqual(result, 'success')
        
        stats = monitor.get_stats('test_metric')
        self.assertEqual(stats['count'], 1)
        self.assertGreater(stats['mean'], 0.0)
    
    def test_circuit_breaker_decorator(self):
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60),
            name='test'
        )
        
        call_count = [0]
        
        @with_circuit_breaker(breaker)
        def failing_function():
            call_count[0] += 1
            raise Exception('Test error')
        
        with self.assertRaises(Exception):
            failing_function()
        
        self.assertEqual(call_count[0], 1)
        self.assertEqual(breaker.state, CircuitState.OPEN)
        
        with self.assertRaises(Exception):
            failing_function()
        
        self.assertEqual(call_count[0], 1)
    
    def test_rate_limiter_decorator(self):
        limiter = RateLimiter(rate=10.0, capacity=1, name='test')
        
        call_count = [0]
        
        @rate_limited(limiter, tokens=1)
        def test_function():
            call_count[0] += 1
            return 'success'
        
        result = test_function()
        self.assertEqual(result, 'success')
        self.assertEqual(call_count[0], 1)
        
        with self.assertRaises(Exception):
            test_function()
        
        self.assertEqual(call_count[0], 1)


class TestFaceDetector(unittest.TestCase):
    def test_detection_result_dataclass(self):
        result = DetectionResult(
            success=True,
            faces=[],
            processing_time=0.05,
            error_message=None
        )
        
        self.assertTrue(result.success)
        self.assertEqual(len(result.faces), 0)
        self.assertEqual(result.processing_time, 0.05)
    
    def test_face_info_dataclass(self):
        test_image = np.random.rand(100, 100, 3)
        location = (10, 10, 50, 50)
        
        face_info = FaceInfo(
            image=test_image,
            location=location,
            confidence=0.9,
            quality_score=0.85,
            angle=5.0
        )
        
        self.assertEqual(face_info.image.shape, test_image.shape)
        self.assertEqual(face_info.location, location)
        self.assertEqual(face_info.confidence, 0.9)
        self.assertEqual(face_info.quality_score, 0.85)
        self.assertEqual(face_info.angle, 5.0)
    
    def test_optimized_detector_skip_frames(self):
        detector = OptimizedFaceDetector(
            min_face_size=80,
            max_face_size=800,
            skip_frames=2
        )
        
        self.assertEqual(detector.skip_frames, 2)
    
    def test_haar_cascade_initialization(self):
        detector = HaarCascadeDetector(
            min_face_size=80,
            max_face_size=800,
            scale_factor=1.1,
            min_neighbors=4
        )
        
        self.assertIsNotNone(detector.face_cascade)
        self.assertIsNotNone(detector.eye_cascade)


class TestFaceRecognizer(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_recognition_result_dataclass(self):
        result = RecognitionResult(
            success=True,
            employee_id='EMP001',
            name='张三',
            confidence=0.95,
            distance=0.05,
            message='欢迎，张三！',
            processing_time=0.1,
            retry_count=0
        )
        
        self.assertTrue(result.success)
        self.assertEqual(result.employee_id, 'EMP001')
        self.assertEqual(result.name, '张三')
        self.assertEqual(result.confidence, 0.95)
        self.assertEqual(result.distance, 0.05)
    
    def test_recognizer_initialization(self):
        recognizer = FaceRecognizer(
            tolerance=0.6,
            cache_dir=self.temp_dir,
            max_workers=2
        )
        
        stats = recognizer.get_statistics()
        self.assertEqual(stats['total_registered'], 0)
        self.assertEqual(stats['tolerance'], 0.6)
    
    def test_load_face_encodings(self):
        import pickle
        
        recognizer = FaceRecognizer(tolerance=0.6)
        
        mock_encoding = np.random.rand(128).astype(np.float64)
        encoding_bytes = pickle.dumps(mock_encoding)
        
        test_data = [
            {
                'employee_id': 'EMP001',
                'name': '张三',
                'encoding': encoding_bytes
            }
        ]
        
        count = recognizer.load_face_encodings(test_data)
        
        self.assertEqual(count, 1)
        stats = recognizer.get_statistics()
        self.assertEqual(stats['total_registered'], 1)
    
    def test_cache_file_operations(self):
        recognizer = FaceRecognizer(
            tolerance=0.6,
            cache_dir=self.temp_dir
        )
        
        test_encoding = np.random.rand(128)
        
        save_result = recognizer.save_encoding_to_cache('EMP001', test_encoding)
        self.assertTrue(save_result)
        
        loaded = recognizer.load_encoding_from_cache('EMP001')
        self.assertIsNotNone(loaded)
        np.testing.assert_array_equal(loaded, test_encoding)
        
        not_found = recognizer.load_encoding_from_cache('NONEXISTENT')
        self.assertIsNone(not_found)


class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, 'test.db')
        self.db = EmployeeDatabase(self.db_path, pool_size=2)
    
    def tearDown(self):
        self.db.close()
        shutil.rmtree(self.temp_dir)
    
    def test_employee_registration_flow(self):
        employee = Employee(
            employee_id='EMP001',
            name='张三',
            department='技术部'
        )
        
        result = self.db.add_employee(employee)
        self.assertTrue(result)
        
        log = AccessLog(
            id=None,
            employee_id='EMP001',
            name='张三',
            access_time=datetime.now().isoformat(),
            status='success',
            confidence=0.92
        )
        
        log_result = self.db.log_access(log)
        self.assertTrue(log_result)
        
        logs = self.db.get_recent_access_logs(10)
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0].employee_id, 'EMP001')
        self.assertEqual(logs[0].confidence, 0.92)
    
    def test_performance_components_together(self):
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(failure_threshold=3, recovery_timeout=1.0),
            name='test'
        )
        
        limiter = RateLimiter(rate=10.0, capacity=5, name='test')
        
        monitor = PerformanceMonitor(window_size=100, name='test')
        
        call_count = [0]
        
        @timed(monitor, 'operation')
        @with_circuit_breaker(breaker)
        @rate_limited(limiter, tokens=1)
        def test_operation():
            call_count[0] += 1
            return 'success'
        
        for _ in range(5):
            result = test_operation()
            self.assertEqual(result, 'success')
        
        self.assertEqual(call_count[0], 5)
        
        stats = monitor.get_stats('operation')
        self.assertEqual(stats['count'], 5)
        
        breaker_stats = breaker.get_metrics()
        self.assertEqual(breaker_stats['successful_requests'], 5)


if __name__ == '__main__':
    unittest.main(verbosity=2)
