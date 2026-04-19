#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
华为5280HF服务器巡检工具 - 公共模块
包含所有共享的类和函数
"""

import argparse
import csv
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import openpyxl
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from pysnmp.hlapi import *

# 线程锁，用于线程安全的计数器和结果收集
result_lock = threading.Lock()
counter_lock = threading.Lock()

# 全局计数器
total_servers = 0
completed_servers = 0
failed_servers = 0


class HuaweiServerSNMP:
    """
    华为服务器SNMP查询类
    用于查询服务器的硬件状态信息
    """

    # 华为服务器SNMP基础OID
    HW_SERVER_BASE = '1.3.6.1.4.1.2011.2.235.1.1'

    # 各硬件状态表OID
    # 风扇状态表
    HW_FAN_TABLE = f'{HW_SERVER_BASE}.8'
    HW_FAN_DESCR = f'{HW_FAN_TABLE}.50.1.2'  # 风扇描述
    HW_FAN_STATUS = f'{HW_FAN_TABLE}.50.1.3'  # 风扇状态
    HW_FAN_SPEED = f'{HW_FAN_TABLE}.50.1.6'  # 风扇转速

    # 电源状态表
    HW_POWER_TABLE = f'{HW_SERVER_BASE}.6'
    HW_POWER_DESCR = f'{HW_POWER_TABLE}.50.1.2'  # 电源描述
    HW_POWER_STATUS = f'{HW_POWER_TABLE}.50.1.3'  # 电源状态
    HW_POWER_INPUT = f'{HW_POWER_TABLE}.50.1.7'  # 电源输入状态
    HW_POWER_OUTPUT = f'{HW_POWER_TABLE}.50.1.8'  # 电源输出状态

    # CPU状态表
    HW_CPU_TABLE = f'{HW_SERVER_BASE}.3'
    HW_CPU_DESCR = f'{HW_CPU_TABLE}.50.1.2'  # CPU描述
    HW_CPU_STATUS = f'{HW_CPU_TABLE}.50.1.3'  # CPU状态
    HW_CPU_MODEL = f'{HW_CPU_TABLE}.50.1.10'  # CPU型号

    # 内存状态表
    HW_MEMORY_TABLE = f'{HW_SERVER_BASE}.4'
    HW_MEMORY_DESCR = f'{HW_MEMORY_TABLE}.50.1.2'  # 内存描述
    HW_MEMORY_STATUS = f'{HW_MEMORY_TABLE}.50.1.3'  # 内存状态
    HW_MEMORY_SIZE = f'{HW_MEMORY_TABLE}.50.1.6'  # 内存大小

    # 硬盘状态表
    HW_DISK_TABLE = f'{HW_SERVER_BASE}.15'  # 硬盘告警表
    HW_STORAGE_TABLE = f'{HW_SERVER_BASE}.26'  # 存储设备表

    # 状态值映射
    STATUS_MAP = {
        1: '正常',
        2: '警告',
        3: '严重',
        4: '未知',
        5: '不存在'
    }

    def __init__(self, ip, community='public', port=161, timeout=5, retries=2):
        """
        初始化SNMP连接参数
        :param ip: 服务器IP地址
        :param community: SNMP团体名
        :param port: SNMP端口
        :param timeout: 超时时间（秒）
        :param retries: 重试次数
        """
        self.ip = ip
        self.community = community
        self.port = port
        self.timeout = timeout
        self.retries = retries

    def _snmp_walk(self, oid):
        """
        执行SNMP Walk操作
        :param oid: 要查询的OID
        :return: 查询结果列表 [(索引, 值), ...]
        """
        result = []
        try:
            for (errorIndication, errorStatus, errorIndex, varBinds) in nextCmd(
                    SnmpEngine(),
                    CommunityData(self.community, mpModel=1),  # SNMPv2c
                    UdpTransportTarget((self.ip, self.port), timeout=self.timeout, retries=self.retries),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                    lexicographicMode=False
            ):
                if errorIndication:
                    print(f"SNMP Walk错误 ({self.ip}): {errorIndication}")
                    return result
                elif errorStatus:
                    print(f"SNMP Walk错误状态 ({self.ip}): {errorStatus.prettyPrint()}")
                    return result
                else:
                    for varBind in varBinds:
                        oid_str = str(varBind[0])
                        value = varBind[1].prettyPrint()
                        # 提取索引（OID的最后部分）
                        if oid.startswith(oid_str) or oid_str.startswith(oid):
                            # 找到索引部分
                            if oid_str.startswith(oid):
                                index = oid_str[len(oid) + 1:]  # +1是因为点号
                                result.append((index, value))
            return result
        except Exception as e:
            print(f"SNMP Walk异常 ({self.ip}): {str(e)}")
            return result

    def _snmp_get(self, oid):
        """
        执行SNMP Get操作
        :param oid: 要查询的OID
        :return: 查询结果或None
        """
        try:
            errorIndication, errorStatus, errorIndex, varBinds = next(getCmd(
                SnmpEngine(),
                CommunityData(self.community, mpModel=1),
                UdpTransportTarget((self.ip, self.port), timeout=self.timeout, retries=self.retries),
                ContextData(),
                ObjectType(ObjectIdentity(oid))
            ))
            if errorIndication:
                return None
            elif errorStatus:
                return None
            else:
                for varBind in varBinds:
                    return varBind[1].prettyPrint()
            return None
        except Exception as e:
            return None

    def get_fan_status(self):
        """
        查询风扇状态
        :return: 风扇状态列表 [{'index': 索引, 'descr': 描述, 'status': 状态, 'speed': 转速}, ...]
        """
        fans = []

        # 获取风扇描述
        descr_results = self._snmp_walk(self.HW_FAN_DESCR)
        descr_dict = {idx: val for idx, val in descr_results}

        # 获取风扇状态
        status_results = self._snmp_walk(self.HW_FAN_STATUS)
        status_dict = {}
        for idx, val in status_results:
            try:
                status_code = int(val)
                status_dict[idx] = self.STATUS_MAP.get(status_code, f'未知({val})')
            except ValueError:
                status_dict[idx] = val

        # 获取风扇转速
        speed_results = self._snmp_walk(self.HW_FAN_SPEED)
        speed_dict = {idx: val for idx, val in speed_results}

        # 合并所有风扇信息
        all_indexes = set(list(descr_dict.keys()) + list(status_dict.keys()) + list(speed_dict.keys()))

        for idx in all_indexes:
            fan_info = {
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': status_dict.get(idx, '未知'),
                'speed': speed_dict.get(idx, 'N/A')
            }
            fans.append(fan_info)

        return fans

    def get_power_status(self):
        """
        查询电源状态
        :return: 电源状态列表 [{'index': 索引, 'descr': 描述, 'status': 状态, 'input': 输入状态, 'output': 输出状态}, ...]
        """
        powers = []

        # 获取电源描述
        descr_results = self._snmp_walk(self.HW_POWER_DESCR)
        descr_dict = {idx: val for idx, val in descr_results}

        # 获取电源状态
        status_results = self._snmp_walk(self.HW_POWER_STATUS)
        status_dict = {}
        for idx, val in status_results:
            try:
                status_code = int(val)
                status_dict[idx] = self.STATUS_MAP.get(status_code, f'未知({val})')
            except ValueError:
                status_dict[idx] = val

        # 获取电源输入状态
        input_results = self._snmp_walk(self.HW_POWER_INPUT)
        input_dict = {}
        for idx, val in input_results:
            try:
                status_code = int(val)
                input_dict[idx] = self.STATUS_MAP.get(status_code, f'未知({val})')
            except ValueError:
                input_dict[idx] = val

        # 获取电源输出状态
        output_results = self._snmp_walk(self.HW_POWER_OUTPUT)
        output_dict = {}
        for idx, val in output_results:
            try:
                status_code = int(val)
                output_dict[idx] = self.STATUS_MAP.get(status_code, f'未知({val})')
            except ValueError:
                output_dict[idx] = val

        # 合并所有电源信息
        all_indexes = set(list(descr_dict.keys()) + list(status_dict.keys()) +
                           list(input_dict.keys()) + list(output_dict.keys()))

        for idx in all_indexes:
            power_info = {
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': status_dict.get(idx, '未知'),
                'input': input_dict.get(idx, 'N/A'),
                'output': output_dict.get(idx, 'N/A')
            }
            powers.append(power_info)

        return powers

    def get_cpu_status(self):
        """
        查询CPU状态
        :return: CPU状态列表 [{'index': 索引, 'descr': 描述, 'status': 状态, 'model': 型号}, ...]
        """
        cpus = []

        # 获取CPU描述
        descr_results = self._snmp_walk(self.HW_CPU_DESCR)
        descr_dict = {idx: val for idx, val in descr_results}

        # 获取CPU状态
        status_results = self._snmp_walk(self.HW_CPU_STATUS)
        status_dict = {}
        for idx, val in status_results:
            try:
                status_code = int(val)
                status_dict[idx] = self.STATUS_MAP.get(status_code, f'未知({val})')
            except ValueError:
                status_dict[idx] = val

        # 获取CPU型号
        model_results = self._snmp_walk(self.HW_CPU_MODEL)
        model_dict = {idx: val for idx, val in model_results}

        # 合并所有CPU信息
        all_indexes = set(list(descr_dict.keys()) + list(status_dict.keys()) + list(model_dict.keys()))

        for idx in all_indexes:
            cpu_info = {
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': status_dict.get(idx, '未知'),
                'model': model_dict.get(idx, 'N/A')
            }
            cpus.append(cpu_info)

        return cpus

    def get_memory_status(self):
        """
        查询内存状态
        :return: 内存状态列表 [{'index': 索引, 'descr': 描述, 'status': 状态, 'size': 大小}, ...]
        """
        memories = []

        # 获取内存描述
        descr_results = self._snmp_walk(self.HW_MEMORY_DESCR)
        descr_dict = {idx: val for idx, val in descr_results}

        # 获取内存状态
        status_results = self._snmp_walk(self.HW_MEMORY_STATUS)
        status_dict = {}
        for idx, val in status_results:
            try:
                status_code = int(val)
                status_dict[idx] = self.STATUS_MAP.get(status_code, f'未知({val})')
            except ValueError:
                status_dict[idx] = val

        # 获取内存大小
        size_results = self._snmp_walk(self.HW_MEMORY_SIZE)
        size_dict = {idx: val for idx, val in size_results}

        # 合并所有内存信息
        all_indexes = set(list(descr_dict.keys()) + list(status_dict.keys()) + list(size_dict.keys()))

        for idx in all_indexes:
            memory_info = {
                'index': idx,
                'descr': descr_dict.get(idx, '未知'),
                'status': status_dict.get(idx, '未知'),
                'size': size_dict.get(idx, 'N/A')
            }
            memories.append(memory_info)

        return memories

    def get_disk_status(self):
        """
        查询硬盘状态
        :return: 硬盘状态列表 [{'index': 索引, 'info': 信息}, ...]
        """
        disks = []

        # 尝试从存储设备表获取
        storage_results = self._snmp_walk(self.HW_STORAGE_TABLE)
        if storage_results:
            for idx, val in storage_results:
                disk_info = {
                    'index': idx,
                    'info': val
                }
                disks.append(disk_info)

        # 如果存储设备表没有数据，尝试从告警表获取
        if not disks:
            disk_results = self._snmp_walk(self.HW_DISK_TABLE)
            for idx, val in disk_results:
                disk_info = {
                    'index': idx,
                    'info': val
                }
                disks.append(disk_info)

        return disks

    def get_status_by_type(self, check_type):
        """
        根据类型获取指定硬件状态
        :param check_type: 检查类型 ('power', 'fan', 'cpu', 'memory', 'disk', 'all')
        :return: 包含指定状态的字典
        """
        result = {
            'ip': self.ip,
            'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }

        if check_type == 'power' or check_type == 'all':
            result['power'] = self.get_power_status()
        if check_type == 'fan' or check_type == 'all':
            result['fan'] = self.get_fan_status()
        if check_type == 'cpu' or check_type == 'all':
            result['cpu'] = self.get_cpu_status()
        if check_type == 'memory' or check_type == 'all':
            result['memory'] = self.get_memory_status()
        if check_type == 'disk' or check_type == 'all':
            result['disk'] = self.get_disk_status()

        return result


class ServerChecker:
    """
    服务器巡检器类
    负责管理整个巡检流程
    """

    def __init__(self, ip_list, community='public', port=161, timeout=5, retries=2, max_workers=50, check_type='all'):
        """
        初始化巡检器
        :param ip_list: 服务器IP列表
        :param community: SNMP团体名
        :param port: SNMP端口
        :param timeout: 超时时间（秒）
        :param retries: 重试次数
        :param max_workers: 最大并发线程数
        :param check_type: 检查类型 ('power', 'fan', 'cpu', 'memory', 'disk', 'all')
        """
        self.ip_list = ip_list
        self.community = community
        self.port = port
        self.timeout = timeout
        self.retries = retries
        self.max_workers = max_workers
        self.check_type = check_type
        self.results = []

    def check_single_server(self, ip):
        """
        检查单台服务器
        :param ip: 服务器IP
        :return: 检查结果
        """
        global completed_servers, failed_servers

        try:
            snmp = HuaweiServerSNMP(
                ip=ip,
                community=self.community,
                port=self.port,
                timeout=self.timeout,
                retries=self.retries
            )

            result = snmp.get_status_by_type(self.check_type)

            with counter_lock:
                completed_servers += 1

            return result
        except Exception as e:
            with counter_lock:
                failed_servers += 1
            return {
                'ip': ip,
                'error': str(e),
                'check_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

    def run_check(self, check_name='巡检'):
        """
        执行巡检
        :param check_name: 巡检名称，用于显示
        :return: 所有检查结果
        """
        global total_servers, completed_servers, failed_servers

        total_servers = len(self.ip_list)
        completed_servers = 0
        failed_servers = 0

        print(f"\n开始{check_name}，共 {total_servers} 台服务器...")
        print(f"并发线程数: {self.max_workers}")
        print("=" * 60)

        start_time = time.time()

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_ip = {executor.submit(self.check_single_server, ip): ip for ip in self.ip_list}

            # 收集结果
            for future in as_completed(future_to_ip):
                ip = future_to_ip[future]
                try:
                    result = future.result()
                    with result_lock:
                        self.results.append(result)

                    # 显示进度
                    with counter_lock:
                        progress = (completed_servers / total_servers) * 100
                        print(f"\r进度: {completed_servers}/{total_servers} ({progress:.1f}%) - 失败: {failed_servers}", end="")

                except Exception as e:
                    print(f"\n处理服务器 {ip} 时发生错误: {str(e)}")
                    with counter_lock:
                        failed_servers += 1

        end_time = time.time()
        elapsed_time = end_time - start_time

        print("\n" + "=" * 60)
        print(f"{check_name}完成！")
        print(f"总服务器数: {total_servers}")
        print(f"成功: {completed_servers - failed_servers}")
        print(f"失败: {failed_servers}")
        print(f"耗时: {elapsed_time:.2f} 秒")

        return self.results


class ExcelHandler:
    """
    Excel文件处理类
    用于读取IP列表和写入巡检结果
    """

    @staticmethod
    def read_ip_list(file_path, sheet_name=None, ip_column=1):
        """
        从Excel文件读取IP地址列表
        :param file_path: Excel文件路径
        :param sheet_name: 工作表名称（默认使用第一个工作表）
        :param ip_column: IP地址所在列（从1开始）
        :return: IP地址列表
        """
        ip_list = []

        try:
            wb = openpyxl.load_workbook(file_path, read_only=True)

            # 选择工作表
            if sheet_name:
                ws = wb[sheet_name]
            else:
                ws = wb.active

            # 读取IP地址（跳过第一行，假设是表头）
            for row in ws.iter_rows(min_row=2, values_only=True):
                ip = row[ip_column - 1]  # 转换为0-based索引
                if ip and isinstance(ip, str) and '.' in ip:  # 简单的IP格式验证
                    ip_list.append(ip.strip())
                elif ip:
                    # 尝试转换为字符串
                    ip_str = str(ip).strip()
                    if '.' in ip_str:
                        ip_list.append(ip_str)

            wb.close()
            return ip_list
        except Exception as e:
            print(f"读取Excel文件失败: {str(e)}")
            # 尝试使用CSV格式读取
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    next(reader)  # 跳过表头
                    for row in reader:
                        if row and len(row) > ip_column - 1:
                            ip = row[ip_column - 1].strip()
                            if ip and '.' in ip:
                                ip_list.append(ip)
                return ip_list
            except Exception as e2:
                print(f"读取CSV文件也失败: {str(e2)}")
                return []

    @staticmethod
    def _get_common_styles():
        """
        获取通用的Excel样式
        :return: 样式字典
        """
        header_font = Font(bold=True, size=11)
        header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
        header_font_white = Font(bold=True, size=11, color="FFFFFF")
        center_alignment = Alignment(horizontal='center', vertical='center')
        thin_border = Border(
            left=Side(style='thin'),
            right=Side(style='thin'),
            top=Side(style='thin'),
            bottom=Side(style='thin')
        )
        success_fill = PatternFill(start_color="E2EFDA", end_color="E2EFDA", fill_type="solid")
        error_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")

        return {
            'header_font': header_font,
            'header_fill': header_fill,
            'header_font_white': header_font_white,
            'center_alignment': center_alignment,
            'thin_border': thin_border,
            'success_fill': success_fill,
            'error_fill': error_fill
        }

    @staticmethod
    def _adjust_column_width(ws):
        """
        调整工作表列宽
        :param ws: 工作表对象
        """
        for col in ws.columns:
            max_length = 0
            column = col[0].column_letter
            for cell in col:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            ws.column_dimensions[column].width = adjusted_width

    @staticmethod
    def write_power_results(results, output_file):
        """
        将电源状态巡检结果写入Excel文件
        :param results: 巡检结果列表
        :param output_file: 输出文件路径
        """
        print(f"\n正在将电源状态结果写入Excel文件: {output_file}")
        styles = ExcelHandler._get_common_styles()

        try:
            wb = openpyxl.Workbook()

            # 汇总表
            ws_summary = wb.active
            ws_summary.title = "电源状态汇总"

            summary_headers = ["序号", "服务器IP", "检查时间", "电源模块数量", "整体状态", "备注"]
            for col, header in enumerate(summary_headers, 1):
                cell = ws_summary.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 详细信息表
            ws_detail = wb.create_sheet("电源详细信息")
            detail_headers = ["服务器IP", "模块索引", "描述", "状态", "输入状态", "输出状态"]
            for col, header in enumerate(detail_headers, 1):
                cell = ws_detail.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 填充数据
            detail_row = 2
            for row_idx, result in enumerate(results, 2):
                ip = result.get('ip', '未知')
                check_time = result.get('check_time', '')

                if 'error' in result:
                    # 错误情况
                    power_count = 0
                    overall_status = "连接失败"
                    remark = result.get('error', '未知错误')
                else:
                    power_list = result.get('power', [])
                    power_count = len(power_list)

                    if power_list:
                        status_list = [p.get('status', '未知') for p in power_list]
                        if any('严重' in s or '警告' in s for s in status_list):
                            overall_status = "异常"
                        else:
                            overall_status = "正常"
                    else:
                        overall_status = "无数据"

                    remark = ""

                    # 填充详细信息
                    for power in power_list:
                        row_data = [
                            ip,
                            power.get('index', ''),
                            power.get('descr', ''),
                            power.get('status', ''),
                            power.get('input', 'N/A'),
                            power.get('output', 'N/A')
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                            if col_idx == 4 and '异常' in str(value) or '严重' in str(value) or '警告' in str(value):
                                cell.fill = styles['error_fill']
                            elif col_idx == 4 and '正常' in str(value):
                                cell.fill = styles['success_fill']
                        detail_row += 1

                # 填充汇总表
                row_data = [row_idx - 1, ip, check_time, power_count, overall_status, remark]
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                    cell.alignment = styles['center_alignment']
                    cell.border = styles['thin_border']
                    if col_idx == 5:
                        if '异常' in str(value) or '失败' in str(value):
                            cell.fill = styles['error_fill']
                        elif '正常' in str(value):
                            cell.fill = styles['success_fill']

            # 调整列宽
            ExcelHandler._adjust_column_width(ws_summary)
            ExcelHandler._adjust_column_width(ws_detail)

            wb.save(output_file)
            print(f"Excel文件已成功保存: {output_file}")

        except Exception as e:
            print(f"写入Excel文件失败: {str(e)}")
            raise

    @staticmethod
    def write_fan_results(results, output_file):
        """
        将风扇状态巡检结果写入Excel文件
        :param results: 巡检结果列表
        :param output_file: 输出文件路径
        """
        print(f"\n正在将风扇状态结果写入Excel文件: {output_file}")
        styles = ExcelHandler._get_common_styles()

        try:
            wb = openpyxl.Workbook()

            # 汇总表
            ws_summary = wb.active
            ws_summary.title = "风扇状态汇总"

            summary_headers = ["序号", "服务器IP", "检查时间", "风扇数量", "整体状态", "备注"]
            for col, header in enumerate(summary_headers, 1):
                cell = ws_summary.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 详细信息表
            ws_detail = wb.create_sheet("风扇详细信息")
            detail_headers = ["服务器IP", "风扇索引", "描述", "状态", "转速(RPM)"]
            for col, header in enumerate(detail_headers, 1):
                cell = ws_detail.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 填充数据
            detail_row = 2
            for row_idx, result in enumerate(results, 2):
                ip = result.get('ip', '未知')
                check_time = result.get('check_time', '')

                if 'error' in result:
                    fan_count = 0
                    overall_status = "连接失败"
                    remark = result.get('error', '未知错误')
                else:
                    fan_list = result.get('fan', [])
                    fan_count = len(fan_list)

                    if fan_list:
                        status_list = [f.get('status', '未知') for f in fan_list]
                        if any('严重' in s or '警告' in s for s in status_list):
                            overall_status = "异常"
                        else:
                            overall_status = "正常"
                    else:
                        overall_status = "无数据"

                    remark = ""

                    # 填充详细信息
                    for fan in fan_list:
                        row_data = [
                            ip,
                            fan.get('index', ''),
                            fan.get('descr', ''),
                            fan.get('status', ''),
                            fan.get('speed', 'N/A')
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                            if col_idx == 4 and '异常' in str(value) or '严重' in str(value) or '警告' in str(value):
                                cell.fill = styles['error_fill']
                            elif col_idx == 4 and '正常' in str(value):
                                cell.fill = styles['success_fill']
                        detail_row += 1

                # 填充汇总表
                row_data = [row_idx - 1, ip, check_time, fan_count, overall_status, remark]
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                    cell.alignment = styles['center_alignment']
                    cell.border = styles['thin_border']
                    if col_idx == 5:
                        if '异常' in str(value) or '失败' in str(value):
                            cell.fill = styles['error_fill']
                        elif '正常' in str(value):
                            cell.fill = styles['success_fill']

            # 调整列宽
            ExcelHandler._adjust_column_width(ws_summary)
            ExcelHandler._adjust_column_width(ws_detail)

            wb.save(output_file)
            print(f"Excel文件已成功保存: {output_file}")

        except Exception as e:
            print(f"写入Excel文件失败: {str(e)}")
            raise

    @staticmethod
    def write_cpu_results(results, output_file):
        """
        将CPU状态巡检结果写入Excel文件
        :param results: 巡检结果列表
        :param output_file: 输出文件路径
        """
        print(f"\n正在将CPU状态结果写入Excel文件: {output_file}")
        styles = ExcelHandler._get_common_styles()

        try:
            wb = openpyxl.Workbook()

            # 汇总表
            ws_summary = wb.active
            ws_summary.title = "CPU状态汇总"

            summary_headers = ["序号", "服务器IP", "检查时间", "CPU数量", "整体状态", "备注"]
            for col, header in enumerate(summary_headers, 1):
                cell = ws_summary.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 详细信息表
            ws_detail = wb.create_sheet("CPU详细信息")
            detail_headers = ["服务器IP", "CPU索引", "描述", "状态", "型号"]
            for col, header in enumerate(detail_headers, 1):
                cell = ws_detail.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 填充数据
            detail_row = 2
            for row_idx, result in enumerate(results, 2):
                ip = result.get('ip', '未知')
                check_time = result.get('check_time', '')

                if 'error' in result:
                    cpu_count = 0
                    overall_status = "连接失败"
                    remark = result.get('error', '未知错误')
                else:
                    cpu_list = result.get('cpu', [])
                    cpu_count = len(cpu_list)

                    if cpu_list:
                        status_list = [c.get('status', '未知') for c in cpu_list]
                        if any('严重' in s or '警告' in s for s in status_list):
                            overall_status = "异常"
                        else:
                            overall_status = "正常"
                    else:
                        overall_status = "无数据"

                    remark = ""

                    # 填充详细信息
                    for cpu in cpu_list:
                        row_data = [
                            ip,
                            cpu.get('index', ''),
                            cpu.get('descr', ''),
                            cpu.get('status', ''),
                            cpu.get('model', 'N/A')
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                            if col_idx == 4 and '异常' in str(value) or '严重' in str(value) or '警告' in str(value):
                                cell.fill = styles['error_fill']
                            elif col_idx == 4 and '正常' in str(value):
                                cell.fill = styles['success_fill']
                        detail_row += 1

                # 填充汇总表
                row_data = [row_idx - 1, ip, check_time, cpu_count, overall_status, remark]
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                    cell.alignment = styles['center_alignment']
                    cell.border = styles['thin_border']
                    if col_idx == 5:
                        if '异常' in str(value) or '失败' in str(value):
                            cell.fill = styles['error_fill']
                        elif '正常' in str(value):
                            cell.fill = styles['success_fill']

            # 调整列宽
            ExcelHandler._adjust_column_width(ws_summary)
            ExcelHandler._adjust_column_width(ws_detail)

            wb.save(output_file)
            print(f"Excel文件已成功保存: {output_file}")

        except Exception as e:
            print(f"写入Excel文件失败: {str(e)}")
            raise

    @staticmethod
    def write_memory_results(results, output_file):
        """
        将内存状态巡检结果写入Excel文件
        :param results: 巡检结果列表
        :param output_file: 输出文件路径
        """
        print(f"\n正在将内存状态结果写入Excel文件: {output_file}")
        styles = ExcelHandler._get_common_styles()

        try:
            wb = openpyxl.Workbook()

            # 汇总表
            ws_summary = wb.active
            ws_summary.title = "内存状态汇总"

            summary_headers = ["序号", "服务器IP", "检查时间", "内存模块数量", "整体状态", "备注"]
            for col, header in enumerate(summary_headers, 1):
                cell = ws_summary.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 详细信息表
            ws_detail = wb.create_sheet("内存详细信息")
            detail_headers = ["服务器IP", "内存索引", "描述", "状态", "大小"]
            for col, header in enumerate(detail_headers, 1):
                cell = ws_detail.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 填充数据
            detail_row = 2
            for row_idx, result in enumerate(results, 2):
                ip = result.get('ip', '未知')
                check_time = result.get('check_time', '')

                if 'error' in result:
                    memory_count = 0
                    overall_status = "连接失败"
                    remark = result.get('error', '未知错误')
                else:
                    memory_list = result.get('memory', [])
                    memory_count = len(memory_list)

                    if memory_list:
                        status_list = [m.get('status', '未知') for m in memory_list]
                        if any('严重' in s or '警告' in s for s in status_list):
                            overall_status = "异常"
                        else:
                            overall_status = "正常"
                    else:
                        overall_status = "无数据"

                    remark = ""

                    # 填充详细信息
                    for memory in memory_list:
                        row_data = [
                            ip,
                            memory.get('index', ''),
                            memory.get('descr', ''),
                            memory.get('status', ''),
                            memory.get('size', 'N/A')
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                            if col_idx == 4 and '异常' in str(value) or '严重' in str(value) or '警告' in str(value):
                                cell.fill = styles['error_fill']
                            elif col_idx == 4 and '正常' in str(value):
                                cell.fill = styles['success_fill']
                        detail_row += 1

                # 填充汇总表
                row_data = [row_idx - 1, ip, check_time, memory_count, overall_status, remark]
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                    cell.alignment = styles['center_alignment']
                    cell.border = styles['thin_border']
                    if col_idx == 5:
                        if '异常' in str(value) or '失败' in str(value):
                            cell.fill = styles['error_fill']
                        elif '正常' in str(value):
                            cell.fill = styles['success_fill']

            # 调整列宽
            ExcelHandler._adjust_column_width(ws_summary)
            ExcelHandler._adjust_column_width(ws_detail)

            wb.save(output_file)
            print(f"Excel文件已成功保存: {output_file}")

        except Exception as e:
            print(f"写入Excel文件失败: {str(e)}")
            raise

    @staticmethod
    def write_disk_results(results, output_file):
        """
        将硬盘状态巡检结果写入Excel文件
        :param results: 巡检结果列表
        :param output_file: 输出文件路径
        """
        print(f"\n正在将硬盘状态结果写入Excel文件: {output_file}")
        styles = ExcelHandler._get_common_styles()

        try:
            wb = openpyxl.Workbook()

            # 汇总表
            ws_summary = wb.active
            ws_summary.title = "硬盘状态汇总"

            summary_headers = ["序号", "服务器IP", "检查时间", "硬盘数量", "状态", "备注"]
            for col, header in enumerate(summary_headers, 1):
                cell = ws_summary.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 详细信息表
            ws_detail = wb.create_sheet("硬盘详细信息")
            detail_headers = ["服务器IP", "硬盘索引", "详细信息"]
            for col, header in enumerate(detail_headers, 1):
                cell = ws_detail.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 填充数据
            detail_row = 2
            for row_idx, result in enumerate(results, 2):
                ip = result.get('ip', '未知')
                check_time = result.get('check_time', '')

                if 'error' in result:
                    disk_count = 0
                    overall_status = "连接失败"
                    remark = result.get('error', '未知错误')
                else:
                    disk_list = result.get('disk', [])
                    disk_count = len(disk_list)

                    if disk_list:
                        overall_status = "有数据"
                    else:
                        overall_status = "无数据"

                    remark = ""

                    # 填充详细信息
                    for disk in disk_list:
                        row_data = [
                            ip,
                            disk.get('index', ''),
                            disk.get('info', 'N/A')
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                        detail_row += 1

                # 填充汇总表
                row_data = [row_idx - 1, ip, check_time, disk_count, overall_status, remark]
                for col_idx, value in enumerate(row_data, 1):
                    cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                    cell.alignment = styles['center_alignment']
                    cell.border = styles['thin_border']
                    if col_idx == 5 and '失败' in str(value):
                        cell.fill = styles['error_fill']

            # 调整列宽
            ExcelHandler._adjust_column_width(ws_summary)
            ExcelHandler._adjust_column_width(ws_detail)

            wb.save(output_file)
            print(f"Excel文件已成功保存: {output_file}")

        except Exception as e:
            print(f"写入Excel文件失败: {str(e)}")
            raise

    @staticmethod
    def write_all_results(results, output_file):
        """
        将所有硬件状态巡检结果写入Excel文件（综合巡检）
        :param results: 巡检结果列表
        :param output_file: 输出文件路径
        """
        print(f"\n正在将综合巡检结果写入Excel文件: {output_file}")
        styles = ExcelHandler._get_common_styles()

        try:
            wb = openpyxl.Workbook()

            # 汇总表
            ws_summary = wb.active
            ws_summary.title = "巡检汇总"

            summary_headers = [
                "序号", "服务器IP", "检查时间", "电源状态", "风扇状态",
                "CPU状态", "内存状态", "硬盘状态", "整体状态", "备注"
            ]
            for col, header in enumerate(summary_headers, 1):
                cell = ws_summary.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 详细信息表
            ws_detail = wb.create_sheet("详细信息")
            detail_headers = [
                "服务器IP", "组件类型", "组件索引", "描述", "状态", "其他信息"
            ]
            for col, header in enumerate(detail_headers, 1):
                cell = ws_detail.cell(row=1, column=col, value=header)
                cell.font = styles['header_font_white']
                cell.fill = styles['header_fill']
                cell.alignment = styles['center_alignment']
                cell.border = styles['thin_border']

            # 填充数据
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
                    # 电源状态
                    power_list = result.get('power', [])
                    if power_list:
                        power_status_list = [p.get('status', '未知') for p in power_list]
                        if any('严重' in s or '警告' in s for s in power_status_list):
                            power_status = "异常"
                        else:
                            power_status = "正常"
                    else:
                        power_status = "无数据"

                    # 风扇状态
                    fan_list = result.get('fan', [])
                    if fan_list:
                        fan_status_list = [f.get('status', '未知') for f in fan_list]
                        if any('严重' in s or '警告' in s for s in fan_status_list):
                            fan_status = "异常"
                        else:
                            fan_status = "正常"
                    else:
                        fan_status = "无数据"

                    # CPU状态
                    cpu_list = result.get('cpu', [])
                    if cpu_list:
                        cpu_status_list = [c.get('status', '未知') for c in cpu_list]
                        if any('严重' in s or '警告' in s for s in cpu_status_list):
                            cpu_status = "异常"
                        else:
                            cpu_status = "正常"
                    else:
                        cpu_status = "无数据"

                    # 内存状态
                    memory_list = result.get('memory', [])
                    if memory_list:
                        memory_status_list = [m.get('status', '未知') for m in memory_list]
                        if any('严重' in s or '警告' in s for s in memory_status_list):
                            memory_status = "异常"
                        else:
                            memory_status = "正常"
                    else:
                        memory_status = "无数据"

                    # 硬盘状态
                    disk_list = result.get('disk', [])
                    if disk_list:
                        disk_status = "有数据"
                    else:
                        disk_status = "无数据"

                    # 整体状态
                    all_statuses = [power_status, fan_status, cpu_status, memory_status]
                    if any('异常' in s or '失败' in s for s in all_statuses):
                        overall_status = "异常"
                    elif any('无数据' in s for s in all_statuses):
                        overall_status = "部分无数据"
                    else:
                        overall_status = "正常"

                    remark = ""

                    # 填充详细信息
                    # 电源
                    for power in power_list:
                        row_data = [
                            ip, "电源", power.get('index', ''),
                            power.get('descr', ''), power.get('status', ''),
                            f"输入:{power.get('input', 'N/A')}, 输出:{power.get('output', 'N/A')}"
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                        detail_row += 1

                    # 风扇
                    for fan in fan_list:
                        row_data = [
                            ip, "风扇", fan.get('index', ''),
                            fan.get('descr', ''), fan.get('status', ''),
                            f"转速:{fan.get('speed', 'N/A')}"
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                        detail_row += 1

                    # CPU
                    for cpu in cpu_list:
                        row_data = [
                            ip, "CPU", cpu.get('index', ''),
                            cpu.get('descr', ''), cpu.get('status', ''),
                            f"型号:{cpu.get('model', 'N/A')}"
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                        detail_row += 1

                    # 内存
                    for memory in memory_list:
                        row_data = [
                            ip, "内存", memory.get('index', ''),
                            memory.get('descr', ''), memory.get('status', ''),
                            f"大小:{memory.get('size', 'N/A')}"
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                        detail_row += 1

                    # 硬盘
                    for disk in disk_list:
                        row_data = [
                            ip, "硬盘", disk.get('index', ''),
                            '', '',
                            f"信息:{disk.get('info', 'N/A')}"
                        ]
                        for col_idx, value in enumerate(row_data, 1):
                            cell = ws_detail.cell(row=detail_row, column=col_idx, value=value)
                            cell.alignment = styles['center_alignment']
                            cell.border = styles['thin_border']
                        detail_row += 1

                # 填充汇总表
                row_data = [
                    row_idx - 1, ip, check_time, power_status, fan_status,
                    cpu_status, memory_status, disk_status, overall_status, remark
                ]

                for col_idx, value in enumerate(row_data, 1):
                    cell = ws_summary.cell(row=row_idx, column=col_idx, value=value)
                    cell.alignment = styles['center_alignment']
                    cell.border = styles['thin_border']

                    # 根据状态设置颜色
                    if col_idx in [4, 5, 6, 7, 8, 9]:
                        if '异常' in str(value) or '失败' in str(value):
                            cell.fill = styles['error_fill']
                        elif '正常' in str(value):
                            cell.fill = styles['success_fill']

            # 调整列宽
            for col in ws_summary.columns:
                max_length = 0
                column = col[0].column_letter
                for cell in col:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 25)
                ws_summary.column_dimensions[column].width = adjusted_width

            ExcelHandler._adjust_column_width(ws_detail)

            wb.save(output_file)
            print(f"Excel文件已成功保存: {output_file}")

        except Exception as e:
            print(f"写入Excel文件失败: {str(e)}")
            raise


def create_base_parser(description, epilog=''):
    """
    创建基础命令行参数解析器
    :param description: 描述信息
    :param epilog: 结尾帮助信息
    :return: ArgumentParser对象
    """
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
    parser.add_argument('-t', '--timeout', type=int, default=5,
                        help='SNMP超时时间（秒，默认: 5）')
    parser.add_argument('-r', '--retries', type=int, default=2,
                        help='SNMP重试次数（默认: 2）')
    parser.add_argument('-w', '--workers', type=int, default=50,
                        help='并发线程数（默认: 50，建议100-200用于大规模巡检）')
    parser.add_argument('-o', '--output', default=None,
                        help='输出Excel文件路径（默认: 自动生成时间戳命名）')

    return parser


def run_check_flow(args, check_type, check_name, output_prefix):
    """
    执行巡检流程的通用函数
    :param args: 命令行参数
    :param check_type: 检查类型
    :param check_name: 检查名称
    :param output_prefix: 输出文件前缀
    :return: 巡检结果
    """
    # 打印欢迎信息
    print("=" * 60)
    print(f"华为5280HF服务器{check_name}工具")
    print(f"版本: 1.0.0")
    print(f"运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # 读取IP列表
    print(f"\n正在读取IP列表文件: {args.ip_file}")
    ip_list = ExcelHandler.read_ip_list(
        file_path=args.ip_file,
        sheet_name=args.sheet,
        ip_column=args.column
    )

    if not ip_list:
        print("错误: 未找到有效的IP地址！")
        sys.exit(1)

    print(f"成功读取 {len(ip_list)} 个IP地址")

    # 确定输出文件名
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f'{output_prefix}_{timestamp}.xlsx'

    # 确保输出路径是绝对路径
    if not os.path.isabs(output_file):
        output_file = os.path.join(os.getcwd(), output_file)

    # 创建巡检器并执行巡检
    checker = ServerChecker(
        ip_list=ip_list,
        community=args.community,
        port=args.port,
        timeout=args.timeout,
        retries=args.retries,
        max_workers=args.workers,
        check_type=check_type
    )

    results = checker.run_check(check_name=check_name)

    # 写入结果到Excel
    if results:
        if check_type == 'power':
            ExcelHandler.write_power_results(results, output_file)
        elif check_type == 'fan':
            ExcelHandler.write_fan_results(results, output_file)
        elif check_type == 'cpu':
            ExcelHandler.write_cpu_results(results, output_file)
        elif check_type == 'memory':
            ExcelHandler.write_memory_results(results, output_file)
        elif check_type == 'disk':
            ExcelHandler.write_disk_results(results, output_file)
        elif check_type == 'all':
            ExcelHandler.write_all_results(results, output_file)

        print(f"\n{check_name}完成！结果已保存至: {output_file}")
    else:
        print("\n警告: 没有获取到任何巡检结果！")

    print("\n" + "=" * 60)
    print(f"{check_name}结束")
    print("=" * 60)

    return results
