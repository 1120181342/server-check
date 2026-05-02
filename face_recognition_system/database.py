import sqlite3
import json
import os
from datetime import datetime
from typing import List, Dict, Optional, Any

class EmployeeDatabase:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        conn = self._get_connection()
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
        
        conn.commit()
        conn.close()
    
    def add_employee(self, employee_data: Dict[str, Any]) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO employees (employee_id, name, department, email, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                employee_data['employee_id'],
                employee_data['name'],
                employee_data['department'],
                employee_data.get('email'),
                employee_data.get('phone')
            ))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            conn.close()
            return False
    
    def add_face_encoding(self, employee_id: str, encoding: bytes, image_path: Optional[str] = None) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO face_encodings (employee_id, encoding, image_path)
                VALUES (?, ?, ?)
            ''', (employee_id, encoding, image_path))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False
    
    def get_employee_by_id(self, employee_id: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM employees WHERE employee_id = ?
        ''', (employee_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return dict(row)
        return None
    
    def get_all_employees(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM employees')
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_all_face_encodings(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT fe.id, fe.employee_id, fe.encoding, fe.image_path, e.name
            FROM face_encodings fe
            JOIN employees e ON fe.employee_id = e.employee_id
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def update_employee(self, employee_id: str, updates: Dict[str, Any]) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [employee_id]
        
        cursor.execute(f'''
            UPDATE employees SET {set_clause}, updated_at = CURRENT_TIMESTAMP
            WHERE employee_id = ?
        ''', values)
        
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def delete_employee(self, employee_id: str) -> bool:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM employees WHERE employee_id = ?', (employee_id,))
        affected = cursor.rowcount
        conn.commit()
        conn.close()
        
        return affected > 0
    
    def log_access(self, status: str, employee_id: Optional[str] = None, name: Optional[str] = None, 
                   confidence: Optional[float] = None, error_message: Optional[str] = None) -> bool:
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO access_logs (employee_id, name, status, confidence, error_message)
                VALUES (?, ?, ?, ?, ?)
            ''', (employee_id, name, status, confidence, error_message))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False
    
    def get_recent_access_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM access_logs
            ORDER BY access_time DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
