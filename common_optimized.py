#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
华为5280HF服务器巡检工具 - 高性能优化版本
核心优化：异步SNMP、批量查询、高并发控制、内存优化
"""

import argparse
import asyncio
import csv
import os
import sys
import time
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

try:
    import aiosnmp
    AIOSNMP_AVAILABLE = True
except ImportError:
    AIOSNMP_AVAILABLE = False


class OptimizedSNMPClient:
    """
    优化的SNMP客户端
    使用aiosnmp实现异步SNMP查询，支持批量OID查询
    """

    HW_SERVER_BASE = '1.3.6.1.4.1.2011.2.235.1.1'
    
    HW_FAN_TABLE = f'{HW_SERVER_BASE}.8'
    HW_FAN_DESCR = f'{HW_FAN_TABLE}.50.1.2'
    HW_FAN_STATUS = f'{HW_FAN_TABLE}.50.1.3'
    HW_FAN_SPEED = f'{HW_FAN_TABLE}.50.1.6'

    HW_POWER_TABLE = f'{HW_SERVER_BASE}.6'
    HW_POWER_DESCR = f'{HW_POWER_TABLE}.50.1.2'
    HW_POWER_STATUS = f'{HW_POWER_TABLE}.50.1.3'
    HW_POWER_INPUT = f'{HW_POWER_TABLE}.50.1.7'
    HW_POWER_OUTPUT = f'{HW_POWER_TABLE}.50.1.8'

    HW_CPU_TABLE = f'{HW_SERVER_BASE}.3'
    HW_CPU_DESCR = f'{HW_CPU_TABLE}.50.1.2'
    HW_CPU_STATUS = f'{HW_CPU_TABLE}.50.1.3'
    HW_CPU_MODEL = f'{HW_CPU_TABLE}.50.1.10'

    HW_MEMORY_TABLE = f'{HW_SERVER_BASE}.4'
    HW_MEMORY_DESCR = f'{HW_MEMORY_TABLE}.50.1.2'
    HW_MEMORY_STATUS = f'{HW_MEMORY_TABLE}.50.1.3'
    HW_MEMORY_SIZE = f'{HW_MEMORY_TABLE}.50.1.6'

    HW_DISK_TABLE = f'{HW_SERVER_BASE}.15'
    HW_STORAGE_TABLE = f'{HW_SERVER_BASE}.26'

    STATUS_MAP = {
        1: '正常',
        2: '警告',
        3: '严重',
        4: '未知',
        5: '不存在'
    }

    def __init__(self, ip: str, community: str = 'public', port: int = 161, 
                 timeout: float = 5.0, retries: int = 1):
        self.ip = ip
        self.community = community
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self._session: Optional[aiosnmp.Snmp] = None

    async def __aenter__(self):
        if AIOSNMP_AVAILABLE:
            self._session = aiosnmp.Snmp(
                host=self.ip,
                port=self.port,
                community=self.community,
                timeout=self.timeout,
                retries=self.retries
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._session:
            await self._session.close()
            self._session = None

    def _parse_oid_index(self, full_oid: str, base_oid: str) -> Optional[str]:
        if full_oid.startswith(base_oid + '.'):
            return full_oid[len(base_oid) + 1:]
        return None

    async def _walk(self, oid: str) -> Dict[str, str]:
        if not AIOSNMP_AVAILABLE or not self._session:
            return {}
        
        results = {}
        try:
            async for varbinds in self._session.walk(oid):
                for oid_obj, value in varbinds:
                    oid_str = str(oid_obj)
                    index = self._parse_oid_index(oid_str, oid)
                    if index:
                        results[index] = str(value) if value is not None else ''
        except Exception:
            pass
        
        return results

    async def _get_bulk(self, oids: List[str]) -> Dict[str, Optional[str]]:
        if not AIOSNMP_AVAILABLE or not self._session:
            return {oid: None for oid in oids}
        
        results = {oid: None for oid in oids}
        try:
            varbinds = await self._session.get(oids)
            for oid_obj, value in varbinds:
                oid_str = str(oid_obj)
                if oid_str in results:
                    results[oid_str] = str(value) if value is not None else None
        except Exception:
            pass
        
        return results

    def _decode_status(self, value: str) -> str:
        try:
            status_code = int(value)
            return self.STATUS_MAP.get(status_code, f'未知({value})')
        except (ValueError, TypeError):
            return value if value else '未知'

    async def get_power_status(self) -> List[Dict[str, Any]]:
        descr_task = self._walk(self.HW_POWER_DESCR)
        status_task = self._walk(self.HW_POWER_STATUS)
        input_task = self._walk(self.HW_POWER_INPUT)
        output_task = self._walk(self.HW_POWER_OUTPUT)
        
        descr_dict, status_dict, input_dict, output_dict = await asyncio.gather(
            descr_task, status_task, input_task, output_task
        )
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(input_dict.keys()) + 
            list(output_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'input': self._decode_status(input_dict.get(idx, '')),
                'output': self._decode_status(output_dict.get(idx, ''))
            })
        
        return results

    async def get_fan_status(self) -> List[Dict[str, Any]]:
        descr_task = self._walk(self.HW_FAN_DESCR)
        status_task = self._walk(self.HW_FAN_STATUS)
        speed_task = self._walk(self.HW_FAN_SPEED)
        
        descr_dict, status_dict, speed_dict = await asyncio.gather(
            descr_task, status_task, speed_task
        )
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(speed_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'speed': speed_dict.get(idx, 'N/A')
            })
        
        return results

    async def get_cpu_status(self) -> List[Dict[str, Any]]:
        descr_task = self._walk(self.HW_CPU_DESCR)
        status_task = self._walk(self.HW_CPU_STATUS)
        model_task = self._walk(self.HW_CPU_MODEL)
        
        descr_dict, status_dict, model_dict = await asyncio.gather(
            descr_task, status_task, model_task
        )
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(model_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'model': model_dict.get(idx, 'N/A')
            })
        
        return results

    async def get_memory_status(self) -> List[Dict[str, Any]]:
        descr_task = self._walk(self.HW_MEMORY_DESCR)
        status_task = self._walk(self.HW_MEMORY_STATUS)
        size_task = self._walk(self.HW_MEMORY_SIZE)
        
        descr_dict, status_dict, size_dict = await asyncio.gather(
            descr_task, status_task, size_task
        )
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(size_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'size': size_dict.get(idx, 'N/A')
            })
        
        return results

    async def get_disk_status(self) -> List[Dict[str, Any]]:
        storage_task = self._walk(self.HW_STORAGE_TABLE)
        disk_task = self._walk(self.HW_DISK_TABLE)
        
        storage_dict, disk_dict = await asyncio.gather(storage_task, disk_task)
        
        results = []
        if storage_dict:
            for idx, val in storage_dict.items():
                results.append({'index': idx, 'info': val})
        elif disk_dict:
            for idx, val in disk_dict.items():
                results.append({'index': idx, 'info': val})
        
        return results

    async def get_all_status(self) -> Dict[str, Any]:
        power_task = self.get_power_status()
        fan_task = self.get_fan_status()
        cpu_task = self.get_cpu_status()
        memory_task = self.get_memory_status()
        disk_task = self.get_disk_status()
        
        power, fan, cpu, memory, disk = await asyncio.gather(
            power_task, fan_task, cpu_task, memory_task, disk_task
        )
        
        return {
            'ip': self.ip,
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'power': power,
            'fan': fan,
            'cpu': cpu,
            'memory': memory,
            'disk': disk
        }

    async def get_status_by_type(self, check_type: str) -> Dict[str, Any]:
        if check_type == 'all':
            return await self.get_all_status()
        
        result = {
            'ip': self.ip,
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if check_type == 'power':
            result['power'] = await self.get_power_status()
        elif check_type == 'fan':
            result['fan'] = await self.get_fan_status()
        elif check_type == 'cpu':
            result['cpu'] = await self.get_cpu_status()
        elif check_type == 'memory':
            result['memory'] = await self.get_memory_status()
        elif check_type == 'disk':
            result['disk'] = await self.get_disk_status()
        
        return result


class FallbackSNMPClient:
    """
    备用SNMP客户端（使用pysnmp）
    当aiosnmp不可用时使用
    """

    HW_SERVER_BASE = '1.3.6.1.4.1.2011.2.235.1.1'
    
    HW_FAN_TABLE = f'{HW_SERVER_BASE}.8'
    HW_FAN_DESCR = f'{HW_FAN_TABLE}.50.1.2'
    HW_FAN_STATUS = f'{HW_FAN_TABLE}.50.1.3'
    HW_FAN_SPEED = f'{HW_FAN_TABLE}.50.1.6'

    HW_POWER_TABLE = f'{HW_SERVER_BASE}.6'
    HW_POWER_DESCR = f'{HW_POWER_TABLE}.50.1.2'
    HW_POWER_STATUS = f'{HW_POWER_TABLE}.50.1.3'
    HW_POWER_INPUT = f'{HW_POWER_TABLE}.50.1.7'
    HW_POWER_OUTPUT = f'{HW_POWER_TABLE}.50.1.8'

    HW_CPU_TABLE = f'{HW_SERVER_BASE}.3'
    HW_CPU_DESCR = f'{HW_CPU_TABLE}.50.1.2'
    HW_CPU_STATUS = f'{HW_CPU_TABLE}.50.1.3'
    HW_CPU_MODEL = f'{HW_CPU_TABLE}.50.1.10'

    HW_MEMORY_TABLE = f'{HW_SERVER_BASE}.4'
    HW_MEMORY_DESCR = f'{HW_MEMORY_TABLE}.50.1.2'
    HW_MEMORY_STATUS = f'{HW_MEMORY_TABLE}.50.1.3'
    HW_MEMORY_SIZE = f'{HW_MEMORY_TABLE}.50.1.6'

    HW_DISK_TABLE = f'{HW_SERVER_BASE}.15'
    HW_STORAGE_TABLE = f'{HW_SERVER_BASE}.26'

    STATUS_MAP = {
        1: '正常',
        2: '警告',
        3: '严重',
        4: '未知',
        5: '不存在'
    }

    def __init__(self, ip: str, community: str = 'public', port: int = 161, 
                 timeout: float = 5.0, retries: int = 1):
        self.ip = ip
        self.community = community
        self.port = port
        self.timeout = int(timeout)
        self.retries = retries

    def _snmp_walk(self, oid: str) -> Dict[str, str]:
        from pysnmp.hlapi import SnmpEngine, CommunityData, UdpTransportTarget
        from pysnmp.hlapi import ContextData, ObjectType, ObjectIdentity, nextCmd
        
        results = {}
        try:
            for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=1),
                UdpTransportTarget((self.ip, self.port), timeout=self.timeout, retries=self.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid)),
                lexicographicMode=False
            ):
                if errorIndication or errorStatus:
                    break
                for varBind in varBinds:
                    oid_str = str(varBind[0])
                    value = varBind[1].prettyPrint()
                    if oid_str.startswith(oid + '.'):
                        index = oid_str[len(oid) + 1:]
                        results[index] = value
        except Exception:
            pass
        return results

    def _decode_status(self, value: str) -> str:
        try:
            status_code = int(value)
            return self.STATUS_MAP.get(status_code, f'未知({value})')
        except (ValueError, TypeError):
            return value if value else '未知'

    def get_power_status(self) -> List[Dict[str, Any]]:
        descr_dict = self._snmp_walk(self.HW_POWER_DESCR)
        status_dict = self._snmp_walk(self.HW_POWER_STATUS)
        input_dict = self._snmp_walk(self.HW_POWER_INPUT)
        output_dict = self._snmp_walk(self.HW_POWER_OUTPUT)
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(input_dict.keys()) + 
            list(output_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'input': self._decode_status(input_dict.get(idx, '')),
                'output': self._decode_status(output_dict.get(idx, ''))
            })
        
        return results

    def get_fan_status(self) -> List[Dict[str, Any]]:
        descr_dict = self._snmp_walk(self.HW_FAN_DESCR)
        status_dict = self._snmp_walk(self.HW_FAN_STATUS)
        speed_dict = self._snmp_walk(self.HW_FAN_SPEED)
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(speed_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'speed': speed_dict.get(idx, 'N/A')
            })
        
        return results

    def get_cpu_status(self) -> List[Dict[str, Any]]:
        descr_dict = self._snmp_walk(self.HW_CPU_DESCR)
        status_dict = self._snmp_walk(self.HW_CPU_STATUS)
        model_dict = self._snmp_walk(self.HW_CPU_MODEL)
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(model_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'model': model_dict.get(idx, 'N/A')
            })
        
        return results

    def get_memory_status(self) -> List[Dict[str, Any]]:
        descr_dict = self._snmp_walk(self.HW_MEMORY_DESCR)
        status_dict = self._snmp_walk(self.HW_MEMORY_STATUS)
        size_dict = self._snmp_walk(self.HW_MEMORY_SIZE)
        
        all_indexes = set(
            list(descr_dict.keys()) + 
            list(status_dict.keys()) + 
            list(size_dict.keys())
        )
        
        results = []
        for idx in all_indexes:
            results.append({
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': self._decode_status(status_dict.get(idx, '')),
                'size': size_dict.get(idx, 'N/A')
            })
        
        return results

    def get_disk_status(self) -> List[Dict[str, Any]]:
        storage_dict = self._snmp_walk(self.HW_STORAGE_TABLE)
        disk_dict = self._snmp_walk(self.HW_DISK_TABLE)
        
        results = []
        if storage_dict:
            for idx, val in storage_dict.items():
                results.append({'index': idx, 'info': val})
        elif disk_dict:
            for idx, val in disk_dict.items():
                results.append({'index': idx, 'info': val})
        
        return results

    def get_all_status(self) -> Dict[str, Any]:
        return {
            'ip': self.ip,
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'power': self.get_power_status(),
            'fan': self.get_fan_status(),
            'cpu': self.get_cpu_status(),
            'memory': self.get_memory_status(),
            'disk': self.get_disk_status()
        }

    def get_status_by_type(self, check_type: str) -> Dict[str, Any]:
        if check_type == 'all':
            return self.get_all_status()
        
        result = {
            'ip': self.ip,
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        if check_type == 'power':
            result['power'] = self.get_power_status()
        elif check_type == 'fan':
            result['fan'] = self.get_fan_status()
        elif check_type == 'cpu':
            result['cpu'] = self.get_cpu_status()
        elif check_type == 'memory':
            result['memory'] = self.get_memory_status()
        elif check_type == 'disk':
            result['disk'] = self.get_disk_status()
        
        return result


class AsyncServerChecker:
    """
    异步服务器巡检器
    支持高并发、异步SNMP查询、进度跟踪
    """

    def __init__(self, ip_list: List[str], community: str = 'public', 
                 port: int = 161, timeout: float = 5.0, retries: int = 1,
                 max_concurrent: int = 200, check_type: str = 'all'):
        self.ip_list = ip_list
        self.community = community
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.max_concurrent = max_concurrent
        self.check_type = check_type
        
        self.results: List[Dict[str, Any]] = []
        self._completed = 0
        self._failed = 0
        self._total = len(ip_list)
        self._lock = asyncio.Lock()
        self._start_time = 0.0

    async def _check_single_server(self, ip: str, semaphore: asyncio.Semaphore) -> Dict[str, Any]:
        async with semaphore:
            try:
                if AIOSNMP_AVAILABLE:
                    async with OptimizedSNMPClient(
                        ip=ip,
                        community=self.community,
                        port=self.port,
                        timeout=self.timeout,
                        retries=self.retries
                    ) as client:
                        result = await client.get_status_by_type(self.check_type)
                else:
                    loop = asyncio.get_event_loop()
                    client = FallbackSNMPClient(
                        ip=ip,
                        community=self.community,
                        port=self.port,
                        timeout=self.timeout,
                        retries=self.retries
                    )
                    result = await loop.run_in_executor(
                        None, 
                        client.get_status_by_type, 
                        self.check_type
                    )
                
                async with self._lock:
                    self._completed += 1
                
                return result
                
            except Exception as e:
                async with self._lock:
                    self._failed += 1
                return {
                    'ip': ip,
                    'error': str(e),
                    'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }

    def _print_progress(self):
        elapsed = time.time() - self._start_time
        total = self._total
        completed = self._completed
        failed = self._failed
        
        if total > 0:
            progress = (completed / total) * 100
        else:
            progress = 0
        
        rate = completed / elapsed if elapsed > 0 else 0
        remaining = (total - completed) / rate if rate > 0 else 0
        
        print(
            f"\r进度: {completed}/{total} ({progress:.1f}%) | "
            f"失败: {failed} | "
            f"速度: {rate:.1f}台/秒 | "
            f"预计剩余: {remaining:.0f}秒",
            end=""
        )

    async def _progress_monitor(self):
        while self._completed + self._failed < self._total:
            await asyncio.sleep(1.0)
            self._print_progress()

    async def run_check(self, check_name: str = '巡检') -> List[Dict[str, Any]]:
        print(f"\n开始{check_name}，共 {self._total} 台服务器...")
        print(f"并发数: {self.max_concurrent}")
        print(f"SNMP模式: {'异步(aiosnmp)' if AIOSNMP_AVAILABLE else '同步(pysnmp)'}")
        print("=" * 80)
        
        self._start_time = time.time()
        self._completed = 0
        self._failed = 0
        
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        progress_task = asyncio.create_task(self._progress_monitor())
        
        tasks = [
            self._check_single_server(ip, semaphore)
            for ip in self.ip_list
        ]
        
        self.results = await asyncio.gather(*tasks)
        
        progress_task.cancel()
        try:
            await progress_task
        except asyncio.CancelledError:
            pass
        
        self._print_progress()
        print()
        
        end_time = time.time()
        elapsed_time = end_time - self._start_time
        
        print("=" * 80)
        print(f"{check_name}完成！")
        print(f"总服务器数: {self._total}")
        print(f"成功: {self._completed - self._failed}")
        print(f"失败: {self._failed}")
        print(f"耗时: {elapsed_time:.2f} 秒")
        print(f"平均速度: {self._total / elapsed_time:.2f} 台/秒")
        
        return self.results


class OptimizedExcelHandler:
    """
    优化的Excel处理器
    使用缓存样式、批量写入、预计算列宽
    """

    @staticmethod
    def _get_styles() -> Dict[str, Any]:
        return {
            'header_font': Font(bold=True, size=11),
            'header_fill': PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid"),
            'header_font_white': Font(bold=True, size=11, color="FFFFFF"),
            'center_alignment': Alignment(horizontal='center', vertical='center'),
            'thin_border': Border(
                left=Side(style='thin'),
                right=Side(style='thin'),
                top=Side(style='thin'),
                bottom=Side(style='thin')
            ),
            'success_fill': PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid"),
            'error_fill': PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        }

    @staticmethod
    def _adjust_column_width(ws, max_col_width: int = 40):
        for col_idx, col in enumerate(ws.columns, 1):
            max_length = 0
            for cell in col:
                if cell.value:
                    try:
                        length = len(str(cell.value))
                        if length > max_length:
                            max_length = length
                    except:
                        pass
            adjusted_width = min(max_length + 2, max_col_width)
            ws.column_dimensions[ws.cell(row=1, column=col_idx).column_letter].width = adjusted_width

    @staticmethod
    def _apply_cell_styles(cell, styles, is_header: bool = False, 
                           is_success: bool = False, is_error: bool = False):
        cell.alignment = styles['center_alignment']
        cell.border = styles['thin_border']
        
        if is_header:
            cell.font = styles['header_font_white']
            cell.fill = styles['header_fill']
        elif is_error:
            cell.fill = styles['error_fill']
        elif is_success:
            cell.fill = styles['success_fill']

    @staticmethod
    def read_ip_list(file_path: str, sheet_name: Optional[str] = None, 
                     ip_column: int = 1) -> List[str]:
        ip_list = []
        
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
            
            if sheet_name:
                ws = wb[sheet_name]
            else:
                ws = wb.active
            
            for row in ws.iter_rows(min_row=2, values_only=True):
                if row and len(row) >= ip_column:
                    ip = row[ip_column - 1]
                    if ip:
                        ip_str = str(ip).strip()
                        if '.' in ip_str:
                            ip_list.append(ip_str)
            
            wb.close()
            return ip_list
            
        except Exception:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader, None)
                    for row in reader:
                        if row and len(row) >= ip_column:
                            ip = row[ip_column - 1].strip()
                            if ip and '.' in ip:
                                ip_list.append(ip)
                return ip_list
            except Exception:
                return []

    @staticmethod
    def write_all_results(results: List[Dict[str, Any]], output_file: str):
        print(f"\n正在将综合巡检结果写入Excel文件: {output_file}")
        styles = OptimizedExcelHandler._get_styles()
        
        wb = openpyxl.Workbook()
        
        ws_summary = wb.active
        ws_summary.title = "巡检汇总"
        
        summary_headers = [
            "序号", "服务器IP", "检查时间", "电源状态", "风扇状态",
            "CPU状态", "内存状态", "硬盘状态", "整体状态", "备注"
        ]
        
        for col, header in enumerate(summary_headers, 1):
            cell = ws_summary.cell(row=1, column=col, value=header)
            OptimizedExcelHandler._apply_cell_styles(cell, styles, is_header=True)
        
        ws_detail = wb.create_sheet("详细信息")
        detail_headers = [
            "服务器IP", "组件类型", "组件索引", "描述", "状态", "其他信息"
        ]
        
        for col, header in enumerate(detail_headers, 1):
            cell = ws_detail.cell(row=1, column=col, value=header)
            OptimizedExcelHandler._apply_cell_styles(cell, styles, is_header=True)
        
        detail_row = 2
        
        for row_idx, result in enumerate(results, 2):
            ip = result.get('ip', '未知')
            check_time = result.get('check_time', '')
            
            if 'error' in result:
                power_status = "连接失败"
                fan_status = "连接失败"
                cpu_status = "连接失败"
                memory_status = "连接失败"
                disk_status = "连接失败"
                overall_status = "失败"
                remark = result.get('error', '未知错误')
            else:
                power_list = result.get('power', [])
                if power_list:
                    power_status_list = [p.get('status', '未知') for p in power_list]
                    if any('严重' in s or '警告' in s for s in power_status_list):
                        power_status = "异常"
                    else:
                        power_status = "正常"
                else:
                    power_status = "无数据"
                
                fan_list = result.get('fan', [])
                if fan_list:
                    fan_status_list = [f.get('status', '未知') for f in fan_list]
                    if any('严重' in s or '警告' in s for s in fan_status_list):
                        fan_status = "异常"
                    else:
                        fan_status = "正常"
                else:
                    fan_status = "无数据"
                
                cpu_list = result.get('cpu', [])
                if cpu_list:
                    cpu_status_list = [c.get('status', '未知') for c in cpu_list]
                    if any('严重' in s or '警告' in s for s in cpu_status_list):
                        cpu_status = "异常"
                    else:
                        cpu_status = "正常"
                else:
                    cpu_status = "无数据"
                
                memory_list = result.get('memory', [])
                if memory_list:
                    memory_status_list = [m.get('status', '未知') for m in memory_list]
                    if any('严重' in s or '警告' in s for s in memory_status_list):
                        memory_status = "异常"
                    else:
                        memory_status = "正常"
                else:
                    memory_status = "无数据"
                
                disk_list = result.get('disk', [])
                disk_status = "有数据" if disk_list else "无数据"
                
                all_statuses = [power_status, fan_status, cpu_status, memory_status]
                if any('异常' in s or '失败' in s for s in all_statuses):
                    overall_status = "异常"
                elif any('无数据' in s for s in all_statuses):
                    overall_status = "部分无数据"
                else:
                    overall_status = "正常"
                
                remark = ""
                
                for power in power_list:
                    row_data = [
                        ip, "电源", power.get('index', ''),
                        power.get('descr', ''), power.get('status', ''),
                        f"输入:{power.get('input', 'N/A')}, 输出:{power.get('output', 'N/A')}"
                    ]
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                        OptimizedExcelHandler._apply_cell_styles(cell, styles)
                    detail_row += 1
                
                for fan in fan_list:
                    row_data = [
                        ip, "风扇", fan.get('index', ''),
                        fan.get('descr', ''), fan.get('status', ''),
                        f"转速:{fan.get('speed', 'N/A')}"
                    ]
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                        OptimizedExcelHandler._apply_cell_styles(cell, styles)
                    detail_row += 1
                
                for cpu in cpu_list:
                    row_data = [
                        ip, "CPU", cpu.get('index', ''),
                        cpu.get('descr', ''), cpu.get('status', ''),
                        f"型号:{cpu.get('model', 'N/A')}"
                    ]
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                        OptimizedExcelHandler._apply_cell_styles(cell, styles)
                    detail_row += 1
                
                for memory in memory_list:
                    row_data = [
                        ip, "内存", memory.get('index', ''),
                        memory.get('descr', ''), memory.get('status', ''),
                        f"大小:{memory.get('size', 'N/A')}"
                    ]
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                        OptimizedExcelHandler._apply_cell_styles(cell, styles)
                    detail_row += 1
                
                for disk in disk_list:
                    row_data = [
                        ip, "硬盘", disk.get('index', ''),
                        '', '', f"信息:{disk.get('info', 'N/A')}"
                    ]
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                        OptimizedExcelHandler._apply_cell_styles(cell, styles)
                    detail_row += 1
            
            summary_row_data = [
                row_idx - 1, ip, check_time, power_status, fan_status,
                cpu_status, memory_status, disk_status, overall_status, remark
            ]
            
            for col_idx, value in enumerate(summary_row_data, 1):
                cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                
                is_error = col_idx in [4, 5, 6, 7, 8, 9] and (
                    '异常' in str(value) or '失败' in str(value)
                )
                is_success = col_idx in [4, 5, 6, 7, 8, 9] and '正常' in str(value)
                
                OptimizedExcelHandler._apply_cell_styles(
                    cell, styles, is_error=is_error, is_success=is_success
                )
        
        OptimizedExcelHandler._adjust_column_width(ws_summary, max_col_width=25)
        OptimizedExcelHandler._adjust_column_width(ws_detail, max_col_width=40)
        
        wb.save(output_file)
        print(f"Excel文件已成功保存: {output_file}")

    @staticmethod
    def write_power_results(results: List[Dict[str, Any]], output_file: str):
        OptimizedExcelHandler._write_component_results(
            results, output_file, 'power', '电源状态',
            ["序号", "服务器IP", "检查时间", "电源模块数量", "整体状态", "备注"],
            ["服务器IP", "模块索引", "描述", "状态", "输入状态", "输出状态"]
        )

    @staticmethod
    def write_fan_results(results: List[Dict[str, Any]], output_file: str):
        OptimizedExcelHandler._write_component_results(
            results, output_file, 'fan', '风扇状态',
            ["序号", "服务器IP", "检查时间", "风扇数量", "整体状态", "备注"],
            ["服务器IP", "风扇索引", "描述", "状态", "转速(RPM)"]
        )

    @staticmethod
    def write_cpu_results(results: List[Dict[str, Any]], output_file: str):
        OptimizedExcelHandler._write_component_results(
            results, output_file, 'cpu', 'CPU状态',
            ["序号", "服务器IP", "检查时间", "CPU数量", "整体状态", "备注"],
            ["服务器IP", "CPU索引", "描述", "状态", "型号"]
        )

    @staticmethod
    def write_memory_results(results: List[Dict[str, Any]], output_file: str):
        OptimizedExcelHandler._write_component_results(
            results, output_file, 'memory', '内存状态',
            ["序号", "服务器IP", "检查时间", "内存模块数量", "整体状态", "备注"],
            ["服务器IP", "内存索引", "描述", "状态", "大小"]
        )

    @staticmethod
    def write_disk_results(results: List[Dict[str, Any]], output_file: str):
        OptimizedExcelHandler._write_component_results(
            results, output_file, 'disk', '硬盘状态',
            ["序号", "服务器IP", "检查时间", "硬盘数量", "状态", "备注"],
            ["服务器IP", "硬盘索引", "详细信息"]
        )

    @staticmethod
    def _write_component_results(results: List[Dict[str, Any]], output_file: str,
                                  component_key: str, component_name: str,
                                  summary_headers: List[str], detail_headers: List[str]):
        print(f"\n正在将{component_name}结果写入Excel文件: {output_file}")
        styles = OptimizedExcelHandler._get_styles()
        
        wb = openpyxl.Workbook()
        
        ws_summary = wb.active
        ws_summary.title = f"{component_name}汇总"
        
        for col, header in enumerate(summary_headers, 1):
            cell = ws_summary.cell(row=1, column=col, value=header)
            OptimizedExcelHandler._apply_cell_styles(cell, styles, is_header=True)
        
        ws_detail = wb.create_sheet(f"{component_name}详细信息")
        
        for col, header in enumerate(detail_headers, 1):
            cell = ws_detail.cell(row=1, column=col, value=header)
            OptimizedExcelHandler._apply_cell_styles(cell, styles, is_header=True)
        
        detail_row = 2
        
        for row_idx, result in enumerate(results, 2):
            ip = result.get('ip', '未知')
            check_time = result.get('check_time', '')
            
            if 'error' in result:
                item_count = 0
                overall_status = "连接失败"
                remark = result.get('error', '未知错误')
            else:
                item_list = result.get(component_key, [])
                item_count = len(item_list)
                
                if item_list and component_key != 'disk':
                    status_list = [item.get('status', '未知') for item in item_list]
                    if any('严重' in s or '警告' in s for s in status_list):
                        overall_status = "异常"
                    else:
                        overall_status = "正常"
                elif item_list:
                    overall_status = "有数据"
                else:
                    overall_status = "无数据"
                
                remark = ""
                
                for item in item_list:
                    if component_key == 'power':
                        row_data = [
                            ip, item.get('index', ''), item.get('descr', ''),
                            item.get('status', ''), item.get('input', 'N/A'),
                            item.get('output', 'N/A')
                        ]
                    elif component_key == 'fan':
                        row_data = [
                            ip, item.get('index', ''), item.get('descr', ''),
                            item.get('status', ''), item.get('speed', 'N/A')
                        ]
                    elif component_key == 'cpu':
                        row_data = [
                            ip, item.get('index', ''), item.get('descr', ''),
                            item.get('status', ''), item.get('model', 'N/A')
                        ]
                    elif component_key == 'memory':
                        row_data = [
                            ip, item.get('index', ''), item.get('descr', ''),
                            item.get('status', ''), item.get('size', 'N/A')
                        ]
                    elif component_key == 'disk':
                        row_data = [ip, item.get('index', ''), item.get('info', 'N/A')]
                    else:
                        row_data = []
                    
                    for col_idx, value in enumerate(row_data, 1):
                        cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                        OptimizedExcelHandler._apply_cell_styles(cell, styles)
                    detail_row += 1
            
            summary_row_data = [row_idx - 1, ip, check_time, item_count, overall_status, remark]
            
            for col_idx, value in enumerate(summary_row_data, 1):
                cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                
                is_error = col_idx == 5 and (
                    '异常' in str(value) or '失败' in str(value)
                )
                is_success = col_idx == 5 and '正常' in str(value)
                
                OptimizedExcelHandler._apply_cell_styles(
                    cell, styles, is_error=is_error, is_success=is_success
                )
        
        OptimizedExcelHandler._adjust_column_width(ws_summary, max_col_width=25)
        OptimizedExcelHandler._adjust_column_width(ws_detail, max_col_width=40)
        
        wb.save(output_file)
        print(f"Excel文件已成功保存: {output_file}")


def create_base_parser(description: str, epilog: str = '') -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog
    )

    parser.add_argument('-i', '--ip-file', required=True,
                        help='包含服务器IP列表的Excel文件路径')
    parser.add_argument('-s', '--sheet', default=None,
                        help='Excel文件中的工作表名称（默认使用第一个工作表）')
    parser.add_argument('-col', '--column', type=int, default=1,
                        help='IP地址所在列号（从1开始，默认第1列）')
    parser.add_argument('-c', '--community', default='public',
                        help='SNMP团体名（默认: public）')
    parser.add_argument('-p', '--port', type=int, default=161,
                        help='SNMP端口号（默认: 161）')
    parser.add_argument('-t', '--timeout', type=float, default=3.0,
                        help='SNMP超时时间（秒，默认: 3.0，优化版本建议更短）')
    parser.add_argument('-r', '--retries', type=int, default=1,
                        help='SNMP重试次数（默认: 1，优化版本建议更少）')
    parser.add_argument('-w', '--workers', type=int, default=300,
                        help='最大并发数（默认: 300，建议200-500用于大规模巡检）')
    parser.add_argument('-o', '--output', default=None,
                        help='输出Excel文件路径（默认: 自动生成时间戳命名）')
    parser.add_argument('--no-async', action='store_true',
                        help='强制使用同步模式（不使用aiosnmp）')

    return parser


async def run_check_flow_async(args, check_type: str, check_name: str, 
                                output_prefix: str) -> List[Dict[str, Any]]:
    global AIOSNMP_AVAILABLE
    if args.no_async:
        AIOSNMP_AVAILABLE = False
    
    print("=" * 80)
    print(f"华为5280HF服务器{check_name}工具 [高性能优化版]")
    print(f"版本: 2.0.0-optimized")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"SNMP模式: {'异步(aiosnmp)' if AIOSNMP_AVAILABLE else '同步(pysnmp)'}")
    print("=" * 80)

    print(f"\n正在读取IP列表文件: {args.ip_file}")
    ip_list = OptimizedExcelHandler.read_ip_list(
        file_path=args.ip_file,
        sheet_name=args.sheet,
        ip_column=args.column
    )

    if not ip_list:
        print("错误: 未找到有效的IP地址！")
        sys.exit(1)

    print(f"成功读取 {len(ip_list)} 个IP地址")

    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'{output_prefix}_{timestamp}.xlsx'

    if not os.path.isabs(output_file):
        output_file = os.path.join(os.getcwd(), output_file)

    checker = AsyncServerChecker(
        ip_list=ip_list,
        community=args.community,
        port=args.port,
        timeout=args.timeout,
        retries=args.retries,
        max_concurrent=args.workers,
        check_type=check_type
    )

    results = await checker.run_check(check_name=check_name)

    if results:
        if check_type == 'power':
            OptimizedExcelHandler.write_power_results(results, output_file)
        elif check_type == 'fan':
            OptimizedExcelHandler.write_fan_results(results, output_file)
        elif check_type == 'cpu':
            OptimizedExcelHandler.write_cpu_results(results, output_file)
        elif check_type == 'memory':
            OptimizedExcelHandler.write_memory_results(results, output_file)
        elif check_type == 'disk':
            OptimizedExcelHandler.write_disk_results(results, output_file)
        elif check_type == 'all':
            OptimizedExcelHandler.write_all_results(results, output_file)

        print(f"\n{check_name}完成！结果已保存至: {output_file}")
    else:
        print("\n警告: 没有获取到任何巡检结果！")

    print("\n" + "=" * 80)
    print(f"{check_name}结束")
    print("=" * 80)

    return results


def run_check_flow(args, check_type: str, check_name: str, output_prefix: str):
    return asyncio.run(run_check_flow_async(args, check_type, check_name, output_prefix))
