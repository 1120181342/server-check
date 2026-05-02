#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量化停车场管理系统后端程序 - 优化版 v2.0
主要优化点：
1. 添加车牌号索引机制，避免每次查询都遍历所有文件
2. 添加内存缓存，减少文件IO操作
3. 优化文件操作，减少不必要的读取
4. 支持索引的增量更新
"""

import json
import os
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from pathlib import Path
from collections import OrderedDict


@dataclass
class VehicleEntry:
    """车辆进入记录"""
    plate_number: str
    entry_time: str
    seats: int
    status: str = "parked"  # parked, left

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class VehicleExit:
    """车辆离开记录"""
    plate_number: str
    exit_time: str
    entry_time: str
    seats: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DailyRecord:
    """每日记录"""
    date: str
    entries: List[Dict[str, Any]]
    exits: List[Dict[str, Any]]
    parked_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class LRUCache:
    """LRU 缓存实现"""
    
    def __init__(self, capacity: int = 10):
        """
        初始化 LRU 缓存
        :param capacity: 缓存容量，默认缓存最近访问的 10 个日期的记录
        """
        self.capacity = capacity
        self.cache: OrderedDict[str, DailyRecord] = OrderedDict()
    
    def get(self, key: str) -> Optional[DailyRecord]:
        """获取缓存中的记录"""
        if key not in self.cache:
            return None
        # 将访问的项移到最后（表示最近使用）
        self.cache.move_to_end(key)
        return self.cache[key]
    
    def put(self, key: str, value: DailyRecord):
        """添加记录到缓存"""
        if key in self.cache:
            # 如果已存在，更新值并移到最后
            self.cache[key] = value
            self.cache.move_to_end(key)
        else:
            # 如果不存在，添加到最后
            self.cache[key] = value
            # 检查是否超出容量
            if len(self.cache) > self.capacity:
                # 移除最旧的项（第一个）
                self.cache.popitem(last=False)
    
    def remove(self, key: str):
        """从缓存中移除指定项"""
        if key in self.cache:
            del self.cache[key]
    
    def clear(self):
        """清空缓存"""
        self.cache.clear()
    
    def keys(self) -> List[str]:
        """获取所有缓存的键"""
        return list(self.cache.keys())


class ParkingSystemOptimized:
    """优化版停车场管理系统核心类"""
    
    # 索引文件名
    INDEX_FILE_NAME = "plate_index.json"
    
    def __init__(self, data_dir: str = None, cache_capacity: int = 10):
        """
        初始化停车场管理系统
        :param data_dir: 数据存储目录，默认为当前目录下的 parking_data
        :param cache_capacity: 内存缓存容量，默认缓存最近访问的 10 个日期的记录
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "parking_data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存缓存：缓存最近访问的日期记录
        self.cache = LRUCache(capacity=cache_capacity)
        
        # 车牌号索引：plate_number -> set of dates
        self.plate_index: Dict[str, Set[str]] = {}
        
        # 内存中维护当前停车场状态
        self.current_parked: Dict[str, VehicleEntry] = {}
        
        # 今日日期字符串（缓存，避免重复计算）
        self.today_str = date.today().strftime("%Y-%m-%d")
        
        # 今日记录缓存（避免每次都读取文件）
        self.today_record: Optional[DailyRecord] = None
        
        # 索引是否已加载
        self.index_loaded = False
        
        # 初始化：加载索引和当前状态
        self._initialize()

    def _initialize(self):
        """初始化系统"""
        # 1. 首先加载车牌号索引
        self._load_plate_index()
        
        # 2. 加载当前停车场状态（从今日文件）
        self._load_current_state()

    def _get_today_file(self) -> Path:
        """获取今日数据文件路径"""
        return self.data_dir / f"parking_{self.today_str}.json"

    def _get_date_file(self, target_date: str) -> Path:
        """获取指定日期的数据文件路径"""
        return self.data_dir / f"parking_{target_date}.json"

    def _get_index_file(self) -> Path:
        """获取索引文件路径"""
        return self.data_dir / self.INDEX_FILE_NAME

    def _load_plate_index(self):
        """加载车牌号索引"""
        index_file = self._get_index_file()
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 将列表转换为集合以提高查找效率
                    self.plate_index = {
                        plate: set(dates) 
                        for plate, dates in data.items()
                    }
                self.index_loaded = True
            except (json.JSONDecodeError, KeyError, IOError):
                # 如果索引文件损坏，重建索引
                self._rebuild_plate_index()
        else:
            # 如果索引文件不存在，重建索引
            self._rebuild_plate_index()

    def _rebuild_plate_index(self):
        """重建车牌号索引（遍历所有数据文件）"""
        self.plate_index = {}
        
        # 遍历所有数据文件
        for file_path in self.data_dir.glob("parking_*.json"):
            try:
                # 从文件名提取日期
                file_name = file_path.stem
                date_str = file_name.replace('parking_', '')
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 收集该文件中的所有车牌号
                plates_in_file = set()
                
                # 从进入记录中收集
                for entry in data.get('entries', []):
                    plate = entry.get('plate_number')
                    if plate:
                        plates_in_file.add(plate)
                
                # 从离开记录中收集
                for exit_record in data.get('exits', []):
                    plate = exit_record.get('plate_number')
                    if plate:
                        plates_in_file.add(plate)
                
                # 更新索引
                for plate in plates_in_file:
                    if plate not in self.plate_index:
                        self.plate_index[plate] = set()
                    self.plate_index[plate].add(date_str)
            
            except (json.JSONDecodeError, KeyError, IOError):
                continue
        
        # 保存重建的索引
        self._save_plate_index()
        self.index_loaded = True

    def _save_plate_index(self):
        """保存车牌号索引到文件"""
        index_file = self._get_index_file()
        
        # 将集合转换为列表以便 JSON 序列化
        data = {
            plate: list(dates) 
            for plate, dates in self.plate_index.items()
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _update_plate_index(self, plate_number: str, date_str: str):
        """
        更新车牌号索引（增量更新）
        :param plate_number: 车牌号
        :param date_str: 日期字符串
        """
        if plate_number not in self.plate_index:
            self.plate_index[plate_number] = set()
        
        # 添加日期到索引
        self.plate_index[plate_number].add(date_str)
        
        # 保存索引到文件（可以考虑批量保存，但为了数据安全，每次都保存）
        self._save_plate_index()

    def _load_current_state(self):
        """加载当前停车场状态（从今日文件）"""
        # 读取今日记录
        self.today_record = self._read_daily_record(self.today_str)
        
        # 重建当前停放的车辆
        self.current_parked = {}
        for entry in self.today_record.entries:
            if entry.get('status') == 'parked':
                self.current_parked[entry['plate_number']] = VehicleEntry(
                    plate_number=entry['plate_number'],
                    entry_time=entry['entry_time'],
                    seats=entry['seats'],
                    status=entry['status']
                )

    def _read_daily_record(self, target_date: str) -> DailyRecord:
        """
        读取指定日期的记录（带缓存）
        :param target_date: 日期字符串
        :return: DailyRecord 对象
        """
        # 首先检查内存缓存
        cached = self.cache.get(target_date)
        if cached is not None:
            return cached
        
        # 检查是否是今日的特殊缓存
        if target_date == self.today_str and self.today_record is not None:
            return self.today_record
        
        # 从文件读取
        file_path = self._get_date_file(target_date)
        
        if not file_path.exists():
            record = DailyRecord(
                date=target_date,
                entries=[],
                exits=[],
                parked_count=0
            )
            # 添加到缓存
            self.cache.put(target_date, record)
            return record
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                record = DailyRecord(
                    date=data.get('date', target_date),
                    entries=data.get('entries', []),
                    exits=data.get('exits', []),
                    parked_count=data.get('parked_count', 0)
                )
                # 添加到缓存
                self.cache.put(target_date, record)
                return record
        except (json.JSONDecodeError, KeyError):
            record = DailyRecord(
                date=target_date,
                entries=[],
                exits=[],
                parked_count=0
            )
            self.cache.put(target_date, record)
            return record

    def _save_today_record(self, record: DailyRecord):
        """
        保存今日记录到文件（同时更新缓存）
        :param record: DailyRecord 对象
        """
        # 更新内存缓存
        self.today_record = record
        self.cache.put(self.today_str, record)
        
        # 写入文件
        today_file = self._get_today_file()
        with open(today_file, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

    def vehicle_entry(self, plate_number: str, seats: int) -> Dict[str, Any]:
        """
        车辆进入停车场
        :param plate_number: 车牌号
        :param seats: 座位数
        :return: 操作结果信息
        """
        # 检查车辆是否已在停车场内（内存检查，O(1) 复杂度）
        if plate_number in self.current_parked:
            return {
                'success': False,
                'message': f'车牌号 {plate_number} 已在停车场内',
                'timestamp': datetime.now().isoformat()
            }
        
        # 记录当前时间
        entry_time = datetime.now().isoformat()
        
        # 创建车辆进入记录
        vehicle = VehicleEntry(
            plate_number=plate_number,
            entry_time=entry_time,
            seats=seats,
            status='parked'
        )
        
        # 添加到内存中
        self.current_parked[plate_number] = vehicle
        
        # 获取今日记录（从缓存，无需读取文件）
        if self.today_record is None:
            self.today_record = self._read_daily_record(self.today_str)
        
        # 添加到今日记录
        self.today_record.entries.append(vehicle.to_dict())
        self.today_record.parked_count = len(self.current_parked)
        
        # 保存到文件（同时更新缓存）
        self._save_today_record(self.today_record)
        
        # 更新车牌号索引（增量更新）
        self._update_plate_index(plate_number, self.today_str)
        
        return {
            'success': True,
            'message': f'车辆 {plate_number} 已进入停车场',
            'vehicle_info': {
                'plate_number': plate_number,
                'entry_time': entry_time,
                'seats': seats
            },
            'current_parked_count': len(self.current_parked),
            'timestamp': datetime.now().isoformat()
        }

    def vehicle_exit(self, plate_number: str) -> Dict[str, Any]:
        """
        车辆离开停车场
        :param plate_number: 车牌号
        :return: 操作结果信息
        """
        # 检查车辆是否在停车场内（内存检查，O(1) 复杂度）
        if plate_number not in self.current_parked:
            return {
                'success': False,
                'message': f'车牌号 {plate_number} 不在停车场内',
                'timestamp': datetime.now().isoformat()
            }
        
        # 获取车辆信息（从内存）
        vehicle = self.current_parked[plate_number]
        
        # 记录离开时间
        exit_time = datetime.now().isoformat()
        
        # 创建离开记录
        exit_record = VehicleExit(
            plate_number=plate_number,
            exit_time=exit_time,
            entry_time=vehicle.entry_time,
            seats=vehicle.seats
        )
        
        # 从内存中移除
        del self.current_parked[plate_number]
        
        # 获取今日记录（从缓存）
        if self.today_record is None:
            self.today_record = self._read_daily_record(self.today_str)
        
        # 更新进入记录状态
        for entry in self.today_record.entries:
            if entry['plate_number'] == plate_number and entry['status'] == 'parked':
                entry['status'] = 'left'
                break
        
        # 添加离开记录
        self.today_record.exits.append(exit_record.to_dict())
        self.today_record.parked_count = len(self.current_parked)
        
        # 保存到文件（同时更新缓存）
        self._save_today_record(self.today_record)
        
        # 更新车牌号索引（增量更新，虽然离开但日期已经在索引中，所以不需要操作）
        
        # 计算停留时间
        entry_dt = datetime.fromisoformat(vehicle.entry_time)
        exit_dt = datetime.fromisoformat(exit_time)
        duration = exit_dt - entry_dt
        
        return {
            'success': True,
            'message': f'车辆 {plate_number} 已离开停车场',
            'vehicle_info': {
                'plate_number': plate_number,
                'entry_time': vehicle.entry_time,
                'exit_time': exit_time,
                'seats': vehicle.seats,
                'duration': str(duration)
            },
            'current_parked_count': len(self.current_parked),
            'timestamp': datetime.now().isoformat()
        }

    def get_parking_status(self) -> Dict[str, Any]:
        """
        获取当前停车场状态（纯内存操作，极快）
        :return: 停车场状态信息
        """
        parked_vehicles = []
        for plate, vehicle in self.current_parked.items():
            parked_vehicles.append({
                'plate_number': vehicle.plate_number,
                'entry_time': vehicle.entry_time,
                'seats': vehicle.seats
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'current_parked_count': len(self.current_parked),
            'parked_vehicles': parked_vehicles
        }

    def get_daily_records(self, target_date: str = None) -> Dict[str, Any]:
        """
        获取指定日期的完整记录（带缓存）
        :param target_date: 日期字符串，格式为 YYYY-MM-DD，默认为今日
        :return: 该日期的所有记录
        """
        if target_date is None:
            target_date = self.today_str
        
        # 从缓存读取（如果已缓存则无需读取文件）
        record = self._read_daily_record(target_date)
        
        return {
            'date': record.date,
            'total_entries': len(record.entries),
            'total_exits': len(record.exits),
            'current_parked_at_end': record.parked_count,
            'entries': record.entries,
            'exits': record.exits
        }

    def get_vehicle_history(self, plate_number: str) -> Dict[str, Any]:
        """
        查询指定车辆的历史记录（优化版：使用索引，只读取相关文件）
        :param plate_number: 车牌号
        :return: 车辆的历史记录
        """
        history = []
        
        # 首先检查索引，获取该车牌号出现过的所有日期
        if plate_number not in self.plate_index:
            # 索引中没有该车牌号，直接返回空结果
            return {
                'plate_number': plate_number,
                'total_records': 0,
                'history': []
            }
        
        # 获取该车牌号相关的日期列表
        relevant_dates = self.plate_index[plate_number]
        
        # 只读取相关日期的文件（而不是所有文件）
        for date_str in relevant_dates:
            # 从缓存读取（如果已缓存则无需读取文件）
            record = self._read_daily_record(date_str)
            
            # 搜索进入记录
            for entry in record.entries:
                if entry['plate_number'] == plate_number:
                    history.append({
                        'type': 'entry',
                        'date': date_str,
                        'plate_number': entry['plate_number'],
                        'entry_time': entry['entry_time'],
                        'seats': entry['seats'],
                        'status': entry['status']
                    })
            
            # 搜索离开记录
            for exit_rec in record.exits:
                if exit_rec['plate_number'] == plate_number:
                    history.append({
                        'type': 'exit',
                        'date': date_str,
                        'plate_number': exit_rec['plate_number'],
                        'entry_time': exit_rec['entry_time'],
                        'exit_time': exit_rec['exit_time'],
                        'seats': exit_rec['seats']
                    })
        
        # 按时间排序
        history.sort(key=lambda x: x.get('entry_time', '') or x.get('exit_time', ''))
        
        return {
            'plate_number': plate_number,
            'total_records': len(history),
            'history': history
        }

    def list_available_dates(self) -> List[str]:
        """
        列出所有有数据记录的日期（优化版：使用索引中的日期）
        :return: 日期列表
        """
        # 收集所有出现过的日期
        all_dates = set()
        for dates in self.plate_index.values():
            all_dates.update(dates)
        
        # 还要检查今日是否有文件但索引中没有（极端情况）
        today_file = self._get_today_file()
        if today_file.exists():
            all_dates.add(self.today_str)
        
        # 转换为列表并排序
        dates_list = sorted(all_dates, reverse=True)
        
        return dates_list

    def clear_cache(self):
        """清空所有缓存"""
        self.cache.clear()
        self.today_record = None

    def rebuild_index(self):
        """强制重建索引"""
        self._rebuild_plate_index()

    def get_cache_info(self) -> Dict[str, Any]:
        """
        获取缓存信息（用于调试和性能分析）
        :return: 缓存信息
        """
        return {
            'cache_capacity': self.cache.capacity,
            'cached_dates': self.cache.keys(),
            'index_loaded': self.index_loaded,
            'total_plates_in_index': len(self.plate_index),
            'today_record_cached': self.today_record is not None,
            'current_parked_count': len(self.current_parked)
        }


def main():
    """命令行交互界面"""
    import sys
    
    # 使用优化版系统
    system = ParkingSystemOptimized()
    
    print("=" * 50)
    print("        停车场管理系统 v2.0 (优化版)")
    print("=" * 50)
    print(f"数据存储目录: {system.data_dir}")
    print(f"当前停车场车辆数: {len(system.current_parked)}")
    print(f"缓存中车牌号数量: {len(system.plate_index)}")
    print()
    
    while True:
        print("\n" + "-" * 50)
        print("请选择操作:")
        print("1. 车辆进入停车场")
        print("2. 车辆离开停车场")
        print("3. 查询停车场当前状态")
        print("4. 查询今日记录")
        print("5. 查询指定日期记录")
        print("6. 查询车辆历史记录 (优化版)")
        print("7. 列出所有有记录的日期")
        print("8. 查看缓存信息")
        print("9. 清空缓存")
        print("10. 重建索引")
        print("0. 退出系统")
        print("-" * 50)
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == '1':
            # 车辆进入
            plate = input("请输入车牌号: ").strip()
            seats_input = input("请输入座位数: ").strip()
            try:
                seats = int(seats_input)
                result = system.vehicle_entry(plate, seats)
                print("\n" + "=" * 50)
                print("操作结果:")
                print(f"  状态: {'成功' if result['success'] else '失败'}")
                print(f"  信息: {result['message']}")
                if result['success']:
                    print(f"  车牌号: {result['vehicle_info']['plate_number']}")
                    print(f"  进入时间: {result['vehicle_info']['entry_time']}")
                    print(f"  座位数: {result['vehicle_info']['seats']}")
                    print(f"  当前停车场车辆数: {result['current_parked_count']}")
                print("=" * 50)
            except ValueError:
                print("错误: 座位数必须是整数")
        
        elif choice == '2':
            # 车辆离开
            plate = input("请输入车牌号: ").strip()
            result = system.vehicle_exit(plate)
            print("\n" + "=" * 50)
            print("操作结果:")
            print(f"  状态: {'成功' if result['success'] else '失败'}")
            print(f"  信息: {result['message']}")
            if result['success']:
                print(f"  车牌号: {result['vehicle_info']['plate_number']}")
                print(f"  进入时间: {result['vehicle_info']['entry_time']}")
                print(f"  离开时间: {result['vehicle_info']['exit_time']}")
                print(f"  停留时长: {result['vehicle_info']['duration']}")
                print(f"  当前停车场车辆数: {result['current_parked_count']}")
            print("=" * 50)
        
        elif choice == '3':
            # 查询当前状态
            status = system.get_parking_status()
            print("\n" + "=" * 50)
            print("停车场当前状态:")
            print(f"  查询时间: {status['timestamp']}")
            print(f"  当前停放车辆数: {status['current_parked_count']}")
            if status['parked_vehicles']:
                print("\n  停放车辆列表:")
                for i, vehicle in enumerate(status['parked_vehicles'], 1):
                    print(f"    {i}. 车牌号: {vehicle['plate_number']}")
                    print(f"       进入时间: {vehicle['entry_time']}")
                    print(f"       座位数: {vehicle['seats']}")
            else:
                print("\n  停车场内无车辆")
            print("=" * 50)
        
        elif choice == '4':
            # 查询今日记录
            records = system.get_daily_records()
            print("\n" + "=" * 50)
            print(f"日期 {records['date']} 的记录:")
            print(f"  总进入车辆数: {records['total_entries']}")
            print(f"  总离开车辆数: {records['total_exits']}")
            print(f"  结束时停放车辆数: {records['current_parked_at_end']}")
            
            if records['entries']:
                print("\n  进入记录:")
                for i, entry in enumerate(records['entries'], 1):
                    status_text = "停放中" if entry['status'] == 'parked' else "已离开"
                    print(f"    {i}. 车牌号: {entry['plate_number']}")
                    print(f"       进入时间: {entry['entry_time']}")
                    print(f"       座位数: {entry['seats']}")
                    print(f"       状态: {status_text}")
            
            if records['exits']:
                print("\n  离开记录:")
                for i, exit_rec in enumerate(records['exits'], 1):
                    print(f"    {i}. 车牌号: {exit_rec['plate_number']}")
                    print(f"       进入时间: {exit_rec['entry_time']}")
                    print(f"       离开时间: {exit_rec['exit_time']}")
                    print(f"       座位数: {exit_rec['seats']}")
            print("=" * 50)
        
        elif choice == '5':
            # 查询指定日期记录
            target_date = input("请输入日期 (格式: YYYY-MM-DD): ").strip()
            records = system.get_daily_records(target_date)
            print("\n" + "=" * 50)
            print(f"日期 {records['date']} 的记录:")
            print(f"  总进入车辆数: {records['total_entries']}")
            print(f"  总离开车辆数: {records['total_exits']}")
            print(f"  结束时停放车辆数: {records['current_parked_at_end']}")
            
            if records['entries']:
                print("\n  进入记录:")
                for i, entry in enumerate(records['entries'], 1):
                    status_text = "停放中" if entry['status'] == 'parked' else "已离开"
                    print(f"    {i}. 车牌号: {entry['plate_number']}")
                    print(f"       进入时间: {entry['entry_time']}")
                    print(f"       座位数: {entry['seats']}")
                    print(f"       状态: {status_text}")
            
            if records['exits']:
                print("\n  离开记录:")
                for i, exit_rec in enumerate(records['exits'], 1):
                    print(f"    {i}. 车牌号: {exit_rec['plate_number']}")
                    print(f"       进入时间: {exit_rec['entry_time']}")
                    print(f"       离开时间: {exit_rec['exit_time']}")
                    print(f"       座位数: {exit_rec['seats']}")
            print("=" * 50)
        
        elif choice == '6':
            # 查询车辆历史记录 (优化版)
            plate = input("请输入车牌号: ").strip()
            history = system.get_vehicle_history(plate)
            print("\n" + "=" * 50)
            print(f"车辆 {plate} 的历史记录:")
            print(f"  总记录数: {history['total_records']}")
            
            if history['history']:
                print("\n  详细记录:")
                for i, record in enumerate(history['history'], 1):
                    if record['type'] == 'entry':
                        status_text = "停放中" if record['status'] == 'parked' else "已离开"
                        print(f"    {i}. [进入] 日期: {record['date']}")
                        print(f"       进入时间: {record['entry_time']}")
                        print(f"       座位数: {record['seats']}")
                        print(f"       状态: {status_text}")
                    else:
                        print(f"    {i}. [离开] 日期: {record['date']}")
                        print(f"       进入时间: {record['entry_time']}")
                        print(f"       离开时间: {record['exit_time']}")
                        print(f"       座位数: {record['seats']}")
            else:
                print("\n  无历史记录")
            print("=" * 50)
        
        elif choice == '7':
            # 列出所有有记录的日期
            dates = system.list_available_dates()
            print("\n" + "=" * 50)
            print("所有有记录的日期:")
            if dates:
                for i, d in enumerate(dates, 1):
                    print(f"  {i}. {d}")
            else:
                print("  暂无记录")
            print("=" * 50)
        
        elif choice == '8':
            # 查看缓存信息
            cache_info = system.get_cache_info()
            print("\n" + "=" * 50)
            print("缓存信息:")
            print(f"  缓存容量: {cache_info['cache_capacity']} 个日期记录")
            print(f"  当前缓存的日期: {cache_info['cached_dates']}")
            print(f"  索引是否已加载: {cache_info['index_loaded']}")
            print(f"  索引中车牌号数量: {cache_info['total_plates_in_index']}")
            print(f"  今日记录是否缓存: {cache_info['today_record_cached']}")
            print(f"  当前停放车辆数: {cache_info['current_parked_count']}")
            print("=" * 50)
        
        elif choice == '9':
            # 清空缓存
            system.clear_cache()
            print("\n缓存已清空")
        
        elif choice == '10':
            # 重建索引
            print("\n正在重建索引...")
            system.rebuild_index()
            print(f"索引重建完成，共索引 {len(system.plate_index)} 个车牌号")
        
        elif choice == '0':
            print("\n感谢使用停车场管理系统，再见！")
            sys.exit(0)
        
        else:
            print("无效选项，请重新输入")


if __name__ == "__main__":
    main()
