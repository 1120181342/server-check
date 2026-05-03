import sqlite3
import threading
import logging
import time
from typing import List, Dict, Optional, Any, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from queue import Queue, Empty
import pickle


logger = logging.getLogger(__name__)


@dataclass
class Employee:
    employee_id: str
    name: str
    department: str
    email: Optional[str] = None
    phone: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FaceEncoding:
    id: Optional[int]
    employee_id: str
    encoding: bytes
    image_path: Optional[str] = None
    created_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class AccessLog:
    id: Optional[int]
    employee_id: Optional[str]
    name: Optional[str]
    access_time: Optional[str]
    status: str
    confidence: Optional[float]
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DatabaseConnectionPool:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._pool: Queue = Queue(maxsize=pool_size)
        self._lock = threading.Lock()
        self._initialized = False
        
    def initialize(self):
        if self._initialized:
            return
            
        with self._lock:
            if self._initialized:
                return
                
            for _ in range(self.pool_size):
                conn = self._create_connection()
                self._pool.put(conn)
            
            self._initialized = True
            logger.info(f"Database connection pool initialized with {self.pool_size} connections")
    
    def _create_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA synchronous=NORMAL')
        conn.execute('PRAGMA temp_store=MEMORY')
        return conn
    
    @contextmanager
    def get_connection(self) -> ContextManager[sqlite3.Connection]:
        try:
            conn = self._pool.get(timeout=5.0)
        except Empty:
            logger.warning("Connection pool exhausted, creating new connection")
            conn = self._create_connection()
        
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            try:
                self._pool.put(conn, timeout=1.0)
            except Exception:
                conn.close()
    
    def close_all(self):
        while not self._pool.empty():
            try:
                conn = self._pool.get_nowait()
                conn.close()
            except Empty:
                break
        logger.info("All database connections closed")


class EmployeeDatabase:
    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self._pool = DatabaseConnectionPool(db_path, pool_size)
        self._init_database()
        self._pool.initialize()
    
    def _init_database(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                encoding BLOB NOT NULL,
                image_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE CASCADE
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                name TEXT,
                access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT NOT NULL,
                confidence REAL,
                error_message TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees(employee_id) ON DELETE SET NULL
            )
        ''')
        
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_employee_id ON employees(employee_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_face_employee_id ON face_encodings(employee_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_time ON access_logs(access_time)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_access_status ON access_logs(status)')
        
        conn.commit()
        conn.close()
        logger.info("Database initialized successfully")
    
    def add_employee(self, employee: Employee) -> bool:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO employees (employee_id, name, department, email, phone)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    employee.employee_id,
                    employee.name,
                    employee.department,
                    employee.email,
                    employee.phone
                ))
                
                return True
        except sqlite3.IntegrityError:
            logger.warning(f"Employee ID {employee.employee_id} already exists")
            return False
        except Exception as e:
            logger.error(f"Error adding employee: {e}")
            return False
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Employee]:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM employees WHERE employee_id = ?
                ''', (employee_id,))
                
                row = cursor.fetchone()
                
                if row:
                    return Employee(
                        employee_id=row['employee_id'],
                        name=row['name'],
                        department=row['department'],
                        email=row['email'],
                        phone=row['phone'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                return None
        except Exception as e:
            logger.error(f"Error getting employee: {e}")
            return None
    
    def get_all_employees(self) -> List[Employee]:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM employees')
                rows = cursor.fetchall()
                
                return [
                    Employee(
                        employee_id=row['employee_id'],
                        name=row['name'],
                        department=row['department'],
                        email=row['email'],
                        phone=row['phone'],
                        created_at=row['created_at'],
                        updated_at=row['updated_at']
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting all employees: {e}")
            return []
    
    def update_employee(self, employee_id: str, updates: Dict[str, Any]) -> bool:
        if not updates:
            return False
        
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
                values = list(updates.values()) + [employee_id]
                
                cursor.execute(f'''
                    UPDATE employees SET {set_clause}, updated_at = CURRENT_TIMESTAMP
                    WHERE employee_id = ?
                ''', values)
                
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error updating employee: {e}")
            return False
    
    def delete_employee(self, employee_id: str) -> bool:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('DELETE FROM employees WHERE employee_id = ?', (employee_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error(f"Error deleting employee: {e}")
            return False
    
    def add_face_encoding(self, employee_id: str, encoding: bytes, image_path: Optional[str] = None) -> bool:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO face_encodings (employee_id, encoding, image_path)
                    VALUES (?, ?, ?)
                ''', (employee_id, encoding, image_path))
                
                return True
        except Exception as e:
            logger.error(f"Error adding face encoding: {e}")
            return False
    
    def get_all_face_encodings(self) -> List[Dict[str, Any]]:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT fe.id, fe.employee_id, fe.encoding, fe.image_path, e.name
                    FROM face_encodings fe
                    JOIN employees e ON fe.employee_id = e.employee_id
                ''')
                
                rows = cursor.fetchall()
                
                return [
                    {
                        'id': row['id'],
                        'employee_id': row['employee_id'],
                        'name': row['name'],
                        'encoding': row['encoding'],
                        'image_path': row['image_path']
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting face encodings: {e}")
            return []
    
    def log_access(self, log: AccessLog) -> bool:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO access_logs (employee_id, name, status, confidence, error_message)
                    VALUES (?, ?, ?, ?, ?)
                ''', (log.employee_id, log.name, log.status, log.confidence, log.error_message))
                
                return True
        except Exception as e:
            logger.error(f"Error logging access: {e}")
            return False
    
    def get_recent_access_logs(self, limit: int = 100) -> List[AccessLog]:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM access_logs
                    ORDER BY access_time DESC
                    LIMIT ?
                ''', (limit,))
                
                rows = cursor.fetchall()
                
                return [
                    AccessLog(
                        id=row['id'],
                        employee_id=row['employee_id'],
                        name=row['name'],
                        access_time=row['access_time'],
                        status=row['status'],
                        confidence=row['confidence'],
                        error_message=row['error_message']
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting access logs: {e}")
            return []
    
    def get_access_logs_by_time_range(
        self, 
        start_time: Optional[str] = None, 
        end_time: Optional[str] = None,
        limit: int = 1000
    ) -> List[AccessLog]:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                query = 'SELECT * FROM access_logs WHERE 1=1'
                params = []
                
                if start_time:
                    query += ' AND access_time >= ?'
                    params.append(start_time)
                
                if end_time:
                    query += ' AND access_time <= ?'
                    params.append(end_time)
                
                query += ' ORDER BY access_time DESC'
                
                if limit:
                    query += ' LIMIT ?'
                    params.append(limit)
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [
                    AccessLog(
                        id=row['id'],
                        employee_id=row['employee_id'],
                        name=row['name'],
                        access_time=row['access_time'],
                        status=row['status'],
                        confidence=row['confidence'],
                        error_message=row['error_message']
                    )
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Error getting access logs by time range: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        try:
            with self._pool.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT COUNT(*) as count FROM employees')
                employee_count = cursor.fetchone()['count']
                
                cursor.execute('SELECT COUNT(*) as count FROM face_encodings')
                face_count = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM access_logs 
                    WHERE date(access_time) = date('now')
                ''')
                today_access_count = cursor.fetchone()['count']
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM access_logs 
                    WHERE date(access_time) = date('now') AND status = 'success'
                ''')
                today_success_count = cursor.fetchone()['count']
                
                return {
                    'total_employees': employee_count,
                    'total_faces': face_count,
                    'today_access_count': today_access_count,
                    'today_success_count': today_success_count,
                    'today_success_rate': (today_success_count / today_access_count * 100) if today_access_count > 0 else 0
                }
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def close(self):
        self._pool.close_all()
