#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量化停车场管理系统后端程序
功能：
1. 记录停车场现有车辆数量
2. 记录进入停车场的车辆信息（车牌号、进入时间、座位数）
3. 记录离开停车场的车辆信息（车牌号、离开时间）
4. 数据每天留存为一个文件，实现车辆数据可追溯
"""

import json
import os
import time
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path


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


class ParkingSystem:
    """停车场管理系统核心类"""

    def __init__(self, data_dir: str = None):
        """
        初始化停车场管理系统
        :param data_dir: 数据存储目录，默认为当前目录下的 parking_data
        """
        if data_dir is None:
            data_dir = Path(__file__).parent / "parking_data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 内存中维护当前停车场状态
        self.current_parked: Dict[str, VehicleEntry] = {}
        self._load_current_state()

    def _get_today_file(self) -> Path:
        """获取今日数据文件路径"""
        today = date.today().strftime("%Y-%m-%d")
        return self.data_dir / f"parking_{today}.json"

    def _get_date_file(self, target_date: str) -> Path:
        """获取指定日期的数据文件路径"""
        return self.data_dir / f"parking_{target_date}.json"

    def _load_current_state(self):
        """加载当前停车场状态（从今日文件）"""
        today_file = self._get_today_file()
        if today_file.exists():
            try:
                with open(today_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 重新构建当前停放的车辆
                    self.current_parked = {}
                    for entry in data.get('entries', []):
                        if entry.get('status') == 'parked':
                            self.current_parked[entry['plate_number']] = VehicleEntry(
                                plate_number=entry['plate_number'],
                                entry_time=entry['entry_time'],
                                seats=entry['seats'],
                                status=entry['status']
                            )
            except (json.JSONDecodeError, KeyError):
                self.current_parked = {}

    def _save_today_record(self, record: DailyRecord):
        """保存今日记录到文件"""
        today_file = self._get_today_file()
        with open(today_file, 'w', encoding='utf-8') as f:
            json.dump(record.to_dict(), f, ensure_ascii=False, indent=2)

    def _read_daily_record(self, target_date: str = None) -> DailyRecord:
        """
        读取指定日期的记录
        :param target_date: 日期字符串，格式为 YYYY-MM-DD，默认为今日
        :return: DailyRecord 对象
        """
        if target_date is None:
            target_date = date.today().strftime("%Y-%m-%d")
        
        file_path = self._get_date_file(target_date)
        
        if not file_path.exists():
            return DailyRecord(
                date=target_date,
                entries=[],
                exits=[],
                parked_count=0
            )
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return DailyRecord(
                    date=data.get('date', target_date),
                    entries=data.get('entries', []),
                    exits=data.get('exits', []),
                    parked_count=data.get('parked_count', 0)
                )
        except (json.JSONDecodeError, KeyError):
            return DailyRecord(
                date=target_date,
                entries=[],
                exits=[],
                parked_count=0
            )

    def vehicle_entry(self, plate_number: str, seats: int) -> Dict[str, Any]:
        """
        车辆进入停车场
        :param plate_number: 车牌号
        :param seats: 座位数
        :return: 操作结果信息
        """
        # 检查车辆是否已在停车场内
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
        
        # 读取今日记录并更新
        record = self._read_daily_record()
        record.entries.append(vehicle.to_dict())
        record.parked_count = len(self.current_parked)
        
        # 保存到文件
        self._save_today_record(record)
        
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
        # 检查车辆是否在停车场内
        if plate_number not in self.current_parked:
            return {
                'success': False,
                'message': f'车牌号 {plate_number} 不在停车场内',
                'timestamp': datetime.now().isoformat()
            }
        
        # 获取车辆信息
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
        
        # 更新今日记录
        record = self._read_daily_record()
        
        # 更新进入记录状态
        for entry in record.entries:
            if entry['plate_number'] == plate_number and entry['status'] == 'parked':
                entry['status'] = 'left'
                break
        
        # 添加离开记录
        record.exits.append(exit_record.to_dict())
        record.parked_count = len(self.current_parked)
        
        # 保存到文件
        self._save_today_record(record)
        
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
        获取当前停车场状态
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
        获取指定日期的完整记录
        :param target_date: 日期字符串，格式为 YYYY-MM-DD，默认为今日
        :return: 该日期的所有记录
        """
        if target_date is None:
            target_date = date.today().strftime("%Y-%m-%d")
        
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
        查询指定车辆的历史记录（在所有数据文件中搜索）
        :param plate_number: 车牌号
        :return: 车辆的历史记录
        """
        history = []
        
        # 遍历所有数据文件
        for file_path in self.data_dir.glob("parking_*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    file_date = data.get('date', '')
                    
                    # 搜索进入记录
                    for entry in data.get('entries', []):
                        if entry['plate_number'] == plate_number:
                            history.append({
                                'type': 'entry',
                                'date': file_date,
                                'plate_number': entry['plate_number'],
                                'entry_time': entry['entry_time'],
                                'seats': entry['seats'],
                                'status': entry['status']
                            })
                    
                    # 搜索离开记录
                    for exit_record in data.get('exits', []):
                        if exit_record['plate_number'] == plate_number:
                            history.append({
                                'type': 'exit',
                                'date': file_date,
                                'plate_number': exit_record['plate_number'],
                                'entry_time': exit_record['entry_time'],
                                'exit_time': exit_record['exit_time'],
                                'seats': exit_record['seats']
                            })
            except (json.JSONDecodeError, KeyError, IOError):
                continue
        
        # 按时间排序
        history.sort(key=lambda x: x.get('entry_time', '') or x.get('exit_time', ''))
        
        return {
            'plate_number': plate_number,
            'total_records': len(history),
            'history': history
        }

    def list_available_dates(self) -> List[str]:
        """
        列出所有有数据记录的日期
        :return: 日期列表
        """
        dates = []
        for file_path in self.data_dir.glob("parking_*.json"):
            # 从文件名提取日期，格式为 parking_YYYY-MM-DD.json
            file_name = file_path.stem
            date_str = file_name.replace('parking_', '')
            dates.append(date_str)
        
        dates.sort(reverse=True)
        return dates


def main():
    """命令行交互界面"""
    import sys
    
    system = ParkingSystem()
    
    print("=" * 50)
    print("        停车场管理系统 v1.0")
    print("=" * 50)
    print(f"数据存储目录: {system.data_dir}")
    print(f"当前停车场车辆数: {len(system.current_parked)}")
    print()
    
    while True:
        print("\n" + "-" * 50)
        print("请选择操作:")
        print("1. 车辆进入停车场")
        print("2. 车辆离开停车场")
        print("3. 查询停车场当前状态")
        print("4. 查询今日记录")
        print("5. 查询指定日期记录")
        print("6. 查询车辆历史记录")
        print("7. 列出所有有记录的日期")
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
            # 查询车辆历史记录
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
        
        elif choice == '0':
            print("\n感谢使用停车场管理系统，再见！")
            sys.exit(0)
        
        else:
            print("无效选项，请重新输入")


if __name__ == "__main__":
    main()
