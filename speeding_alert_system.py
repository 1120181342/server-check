#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车载超速提示系统
功能：
1. 与车辆自身速度检测系统对接API
2. 实时监测路面速度限制
3. 当车速超出限制上限时发出提示
4. 提示时间为3秒
5. 超速发生1秒内完成计算与响应
"""

import threading
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from threading import Lock, Event
from queue import Queue
import random


@dataclass
class SpeedData:
    """
    速度数据类
    用于存储车辆当前速度信息
    """
    vehicle_id: str
    speed: float  # 单位：km/h
    timestamp: datetime = field(default_factory=datetime.now)
    unit: str = "km/h"
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        :return: 包含速度数据的字典
        """
        return {
            "vehicle_id": self.vehicle_id,
            "speed": self.speed,
            "timestamp": self.timestamp.isoformat(),
            "unit": self.unit
        }


@dataclass
class SpeedLimit:
    """
    速度限制类
    用于存储当前路段的速度限制信息
    """
    location: str
    limit: float  # 单位：km/h
    last_updated: datetime = field(default_factory=datetime.now)
    is_temporary: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        :return: 包含速度限制数据的字典
        """
        return {
            "location": self.location,
            "limit": self.limit,
            "last_updated": self.last_updated.isoformat(),
            "is_temporary": self.is_temporary
        }


@dataclass
class AlertInfo:
    """
    提示信息类
    用于存储超速提示的相关信息
    """
    alert_id: str
    vehicle_id: str
    current_speed: float
    speed_limit: float
    alert_start_time: datetime
    alert_duration: float = 3.0  # 默认3秒
    is_active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典格式
        :return: 包含提示信息的字典
        """
        return {
            "alert_id": self.alert_id,
            "vehicle_id": self.vehicle_id,
            "current_speed": self.current_speed,
            "speed_limit": self.speed_limit,
            "alert_start_time": self.alert_start_time.isoformat(),
            "alert_duration": self.alert_duration,
            "is_active": self.is_active
        }


class VehicleSpeedAPI:
    """
    车辆速度检测API接口类
    模拟与车辆自身速度检测系统的对接
    """
    
    def __init__(self, vehicle_id: str):
        """
        初始化车辆速度检测API
        :param vehicle_id: 车辆唯一标识符
        """
        self.vehicle_id = vehicle_id
        self._lock = Lock()
        self._last_speed = 0.0
        self._is_connected = False
    
    def connect(self) -> bool:
        """
        连接到车辆速度检测系统
        :return: 连接是否成功
        """
        with self._lock:
            # 模拟连接过程
            time.sleep(0.1)  # 模拟连接延迟
            self._is_connected = True
            return True
    
    def disconnect(self) -> bool:
        """
        断开与车辆速度检测系统的连接
        :return: 断开是否成功
        """
        with self._lock:
            self._is_connected = False
            return True
    
    def is_connected(self) -> bool:
        """
        检查是否已连接
        :return: 连接状态
        """
        with self._lock:
            return self._is_connected
    
    def get_current_speed(self) -> Optional[SpeedData]:
        """
        获取当前车辆速度
        :return: 速度数据对象，如果获取失败则返回None
        """
        with self._lock:
            if not self._is_connected:
                return None
            
            # 模拟从车辆系统获取速度
            # 这里使用随机值模拟，实际应用中应从真实接口获取
            base_speed = self._last_speed
            # 速度变化在合理范围内
            speed_change = random.uniform(-5, 5)
            new_speed = max(0, min(150, base_speed + speed_change))
            self._last_speed = new_speed
            
            return SpeedData(
                vehicle_id=self.vehicle_id,
                speed=new_speed,
                timestamp=datetime.now()
            )
    
    def set_simulated_speed(self, speed: float):
        """
        设置模拟速度（用于测试）
        :param speed: 要设置的速度值
        """
        with self._lock:
            self._last_speed = max(0, min(150, speed))


class RoadSpeedLimitMonitor:
    """
    路面速度限制监测类
    实时监测当前路段的速度限制信息
    """
    
    def __init__(self, initial_limit: float = 60.0):
        """
        初始化路面速度限制监测器
        :param initial_limit: 初始速度限制
        """
        self._lock = Lock()
        self._current_limit = SpeedLimit(
            location="unknown",
            limit=initial_limit,
            is_temporary=False
        )
        self._callbacks: Dict[str, Callable] = {}
    
    def update_speed_limit(self, location: str, limit: float, is_temporary: bool = False):
        """
        更新速度限制信息
        :param location: 当前位置描述
        :param limit: 新的速度限制
        :param is_temporary: 是否为临时限速
        """
        with self._lock:
            old_limit = self._current_limit.limit
            self._current_limit = SpeedLimit(
                location=location,
                limit=limit,
                is_temporary=is_temporary
            )
            
            # 如果速度限制发生变化，通知所有注册的回调
            if old_limit != limit:
                self._notify_limit_change(self._current_limit)
    
    def get_current_limit(self) -> SpeedLimit:
        """
        获取当前速度限制
        :return: 当前速度限制信息
        """
        with self._lock:
            return SpeedLimit(
                location=self._current_limit.location,
                limit=self._current_limit.limit,
                last_updated=self._current_limit.last_updated,
                is_temporary=self._current_limit.is_temporary
            )
    
    def register_limit_change_callback(self, name: str, callback: Callable):
        """
        注册速度限制变化回调函数
        :param name: 回调名称
        :param callback: 回调函数，参数为 (speed_limit)
        """
        with self._lock:
            self._callbacks[name] = callback
    
    def unregister_limit_change_callback(self, name: str):
        """
        注销速度限制变化回调函数
        :param name: 回调名称
        """
        with self._lock:
            self._callbacks.pop(name, None)
    
    def _notify_limit_change(self, speed_limit: SpeedLimit):
        """
        通知速度限制变化
        :param speed_limit: 新的速度限制信息
        """
        for callback in self._callbacks.values():
            try:
                callback(speed_limit)
            except Exception:
                pass


class AlertManager:
    """
    提示管理器类
    负责管理超速提示的触发、持续和结束
    """
    
    def __init__(self, alert_duration: float = 3.0):
        """
        初始化提示管理器
        :param alert_duration: 提示持续时间（秒），默认为3秒
        """
        self.alert_duration = alert_duration
        self._lock = Lock()
        self._current_alert: Optional[AlertInfo] = None
        self._alert_history: list = []
        self._callbacks: Dict[str, Callable] = {}
        self._alert_counter = 0
    
    def start_alert(self, vehicle_id: str, current_speed: float, speed_limit: float) -> AlertInfo:
        """
        开始一个新的提示
        :param vehicle_id: 车辆ID
        :param current_speed: 当前速度
        :param speed_limit: 速度限制
        :return: 提示信息对象
        """
        with self._lock:
            self._alert_counter += 1
            alert_id = f"ALERT-{self._alert_counter:06d}"
            
            alert_info = AlertInfo(
                alert_id=alert_id,
                vehicle_id=vehicle_id,
                current_speed=current_speed,
                speed_limit=speed_limit,
                alert_start_time=datetime.now(),
                alert_duration=self.alert_duration,
                is_active=True
            )
            
            # 如果已经有活跃的提示，先结束它
            if self._current_alert and self._current_alert.is_active:
                self._current_alert.is_active = False
                self._alert_history.append(self._current_alert)
            
            self._current_alert = alert_info
            self._alert_history.append(alert_info)
            
            # 通知提示开始
            self._notify_alert_start(alert_info)
            
            return alert_info
    
    def stop_alert(self):
        """
        停止当前活跃的提示
        """
        with self._lock:
            if self._current_alert and self._current_alert.is_active:
                self._current_alert.is_active = False
                self._notify_alert_end(self._current_alert)
    
    def get_active_alert(self) -> Optional[AlertInfo]:
        """
        获取当前活跃的提示
        :return: 活跃的提示信息，如果没有则返回None
        """
        with self._lock:
            if self._current_alert and self._current_alert.is_active:
                # 检查是否超过持续时间
                elapsed = (datetime.now() - self._current_alert.alert_start_time).total_seconds()
                if elapsed >= self._current_alert.alert_duration:
                    self._current_alert.is_active = False
                    self._notify_alert_end(self._current_alert)
                    return None
                return AlertInfo(
                    alert_id=self._current_alert.alert_id,
                    vehicle_id=self._current_alert.vehicle_id,
                    current_speed=self._current_alert.current_speed,
                    speed_limit=self._current_alert.speed_limit,
                    alert_start_time=self._current_alert.alert_start_time,
                    alert_duration=self._current_alert.alert_duration,
                    is_active=self._current_alert.is_active
                )
            return None
    
    def get_alert_history(self) -> list:
        """
        获取提示历史
        :return: 提示历史列表
        """
        with self._lock:
            return self._alert_history.copy()
    
    def register_alert_callback(self, name: str, callback: Callable):
        """
        注册提示回调函数
        :param name: 回调名称
        :param callback: 回调函数，参数为 (alert_info, event_type)
        """
        with self._lock:
            self._callbacks[name] = callback
    
    def unregister_alert_callback(self, name: str):
        """
        注销提示回调函数
        :param name: 回调名称
        """
        with self._lock:
            self._callbacks.pop(name, None)
    
    def _notify_alert_start(self, alert_info: AlertInfo):
        """
        通知提示开始
        :param alert_info: 提示信息
        """
        for callback in self._callbacks.values():
            try:
                callback(alert_info, "start")
            except Exception:
                pass
    
    def _notify_alert_end(self, alert_info: AlertInfo):
        """
        通知提示结束
        :param alert_info: 提示信息
        """
        for callback in self._callbacks.values():
            try:
                callback(alert_info, "end")
            except Exception:
                pass


class SpeedingAlertSystem:
    """
    超速提示系统核心类
    整合所有模块，实现完整的超速检测和提示功能
    """
    
    def __init__(self, vehicle_id: str, initial_speed_limit: float = 60.0, alert_duration: float = 3.0):
        """
        初始化超速提示系统
        :param vehicle_id: 车辆唯一标识符
        :param initial_speed_limit: 初始速度限制
        :param alert_duration: 提示持续时间（秒）
        """
        self.vehicle_id = vehicle_id
        
        # 初始化子系统
        self.speed_api = VehicleSpeedAPI(vehicle_id)
        self.limit_monitor = RoadSpeedLimitMonitor(initial_speed_limit)
        self.alert_manager = AlertManager(alert_duration)
        
        # 线程安全控制
        self._lock = Lock()
        self._stop_event = Event()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        
        # 性能指标
        self._performance_metrics = {
            "speed_check_count": 0,
            "overspeed_count": 0,
            "avg_response_time_ms": 0,
            "max_response_time_ms": 0,
            "min_response_time_ms": float('inf')
        }
        
        # 注册回调
        self._register_callbacks()
    
    def _register_callbacks(self):
        """
        注册各种回调函数
        """
        # 速度限制变化回调
        self.limit_monitor.register_limit_change_callback(
            "system_logger",
            self._on_limit_change
        )
        
        # 提示回调
        self.alert_manager.register_alert_callback(
            "system_logger",
            self._on_alert_event
        )
    
    def _on_limit_change(self, speed_limit: SpeedLimit):
        """
        速度限制变化处理函数
        :param speed_limit: 新的速度限制信息
        """
        print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] 速度限制已更新: "
              f"{speed_limit.limit} km/h (位置: {speed_limit.location})")
    
    def _on_alert_event(self, alert_info: AlertInfo, event_type: str):
        """
        提示事件处理函数
        :param alert_info: 提示信息
        :param event_type: 事件类型 ('start' 或 'end')
        """
        if event_type == "start":
            print(f"\n[{datetime.now().strftime('%H:%M:%S.%f')}] ⚠️  超速警告! "
                  f"当前速度: {alert_info.current_speed:.1f} km/h, "
                  f"限速: {alert_info.speed_limit:.1f} km/h")
            print(f"                  提示ID: {alert_info.alert_id}")
            print(f"                  提示将持续 {alert_info.alert_duration} 秒\n")
        elif event_type == "end":
            print(f"[{datetime.now().strftime('%H:%M:%S.%f')}] ✓ 提示已结束 (ID: {alert_info.alert_id})")
    
    def start(self) -> bool:
        """
        启动超速提示系统
        :return: 启动是否成功
        """
        with self._lock:
            if self._running:
                print("系统已经在运行中！")
                return False
            
            # 连接到车辆速度API
            print("正在连接到车辆速度检测系统...")
            if not self.speed_api.connect():
                print("连接到车辆速度检测系统失败！")
                return False
            print("成功连接到车辆速度检测系统")
            
            # 启动监控线程
            self._stop_event.clear()
            self._running = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self._monitor_thread.start()
            
            print("超速提示系统已启动")
            return True
    
    def stop(self) -> bool:
        """
        停止超速提示系统
        :return: 停止是否成功
        """
        with self._lock:
            if not self._running:
                print("系统尚未启动！")
                return False
            
            # 停止监控线程
            self._stop_event.set()
            if self._monitor_thread:
                self._monitor_thread.join(timeout=2.0)
            
            # 断开速度API连接
            self.speed_api.disconnect()
            
            # 停止任何活跃的提示
            self.alert_manager.stop_alert()
            
            self._running = False
            print("超速提示系统已停止")
            return True
    
    def is_running(self) -> bool:
        """
        检查系统是否正在运行
        :return: 运行状态
        """
        with self._lock:
            return self._running
    
    def update_speed_limit(self, location: str, limit: float, is_temporary: bool = False):
        """
        更新速度限制
        :param location: 当前位置
        :param limit: 新的速度限制
        :param is_temporary: 是否为临时限速
        """
        self.limit_monitor.update_speed_limit(location, limit, is_temporary)
    
    def set_simulated_speed(self, speed: float):
        """
        设置模拟速度（用于测试）
        :param speed: 速度值
        """
        self.speed_api.set_simulated_speed(speed)
    
    def get_system_status(self) -> Dict[str, Any]:
        """
        获取系统状态
        :return: 系统状态信息
        """
        with self._lock:
            speed_data = self.speed_api.get_current_speed()
            speed_limit = self.limit_monitor.get_current_limit()
            active_alert = self.alert_manager.get_active_alert()
            
            return {
                "running": self._running,
                "vehicle_id": self.vehicle_id,
                "connected_to_vehicle": self.speed_api.is_connected(),
                "current_speed": speed_data.speed if speed_data else None,
                "speed_limit": speed_limit.limit,
                "speed_limit_location": speed_limit.location,
                "active_alert": active_alert.to_dict() if active_alert else None,
                "performance_metrics": self._performance_metrics.copy()
            }
    
    def _monitor_loop(self):
        """
        监控主循环
        实时监测速度和限速，检测超速并触发提示
        """
        # 监控循环的目标频率：每秒检查多次以确保1秒内响应
        # 这里使用0.1秒的间隔，确保在超速发生后最多0.1秒内检测到
        check_interval = 0.1  # 100ms检查一次
        
        while not self._stop_event.is_set():
            start_time = time.perf_counter()
            
            try:
                # 1. 获取当前速度（时间戳记录开始）
                speed_data = self.speed_api.get_current_speed()
                if not speed_data:
                    time.sleep(check_interval)
                    continue
                
                # 2. 获取当前速度限制
                speed_limit = self.limit_monitor.get_current_limit()
                
                # 3. 检查是否超速
                is_speeding = speed_data.speed > speed_limit.limit
                
                # 4. 处理超速检测结果
                with self._lock:
                    self._performance_metrics["speed_check_count"] += 1
                
                if is_speeding:
                    with self._lock:
                        self._performance_metrics["overspeed_count"] += 1
                    
                    # 检查是否已有活跃的提示
                    active_alert = self.alert_manager.get_active_alert()
                    if not active_alert:
                        # 触发新的提示
                        self.alert_manager.start_alert(
                            vehicle_id=self.vehicle_id,
                            current_speed=speed_data.speed,
                            speed_limit=speed_limit.limit
                        )
                
                # 5. 更新性能指标
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                
                with self._lock:
                    pm = self._performance_metrics
                    # 更新平均响应时间
                    total_checks = pm["speed_check_count"]
                    pm["avg_response_time_ms"] = (
                        (pm["avg_response_time_ms"] * (total_checks - 1) + response_time_ms) / total_checks
                    )
                    # 更新最大/最小响应时间
                    pm["max_response_time_ms"] = max(pm["max_response_time_ms"], response_time_ms)
                    pm["min_response_time_ms"] = min(pm["min_response_time_ms"], response_time_ms)
                
            except Exception as e:
                print(f"监控循环错误: {e}")
            
            # 计算下次检查的时间
            elapsed = time.perf_counter() - start_time
            sleep_time = max(0, check_interval - elapsed)
            time.sleep(sleep_time)
    
    def __del__(self):
        """
        析构函数，确保系统停止
        """
        if self._running:
            self.stop()


def main():
    """
    命令行交互界面
    """
    import sys
    
    print("=" * 60)
    print("        车载超速提示系统 v1.0")
    print("=" * 60)
    print("功能:")
    print("  1. 与车辆速度检测系统对接")
    print("  2. 实时监测路面速度限制")
    print("  3. 超速时自动发出3秒提示")
    print("  4. 确保超速发生后1秒内响应")
    print("=" * 60)
    
    # 创建系统实例
    system = SpeedingAlertSystem(
        vehicle_id="VEH-001",
        initial_speed_limit=60.0,
        alert_duration=3.0
    )
    
    def alert_callback(alert_info, event_type):
        """
        自定义提示回调函数
        """
        if event_type == "start":
            # 这里可以添加声音提示、视觉提示等
            print(f"🚗 超速警告! 速度: {alert_info.current_speed:.1f} km/h, 限速: {alert_info.speed_limit:.1f} km/h")
            print(f"   请立即减速！提示将持续 {alert_info.alert_duration} 秒")
    
    def limit_change_callback(speed_limit):
        """
        自定义限速变化回调函数
        """
        temp_msg = " (临时限速)" if speed_limit.is_temporary else ""
        print(f"📍 限速更新: {speed_limit.limit} km/h - {speed_limit.location}{temp_msg}")
    
    # 注册自定义回调
    system.alert_manager.register_alert_callback("user_alert", alert_callback)
    system.limit_monitor.register_limit_change_callback("user_limit", limit_change_callback)
    
    print("\n系统已初始化，等待您的操作...")
    
    while True:
        print("\n" + "-" * 60)
        print("请选择操作:")
        print("1. 启动超速提示系统")
        print("2. 停止超速提示系统")
        print("3. 查看系统状态")
        print("4. 查看性能指标")
        print("5. 设置模拟速度 (用于测试)")
        print("6. 更新速度限制 (用于测试)")
        print("7. 查看提示历史")
        print("0. 退出系统")
        print("-" * 60)
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == '1':
            if system.is_running():
                print("\n系统已经在运行中！")
            else:
                system.start()
        
        elif choice == '2':
            if not system.is_running():
                print("\n系统尚未启动！")
            else:
                system.stop()
        
        elif choice == '3':
            status = system.get_system_status()
            print("\n" + "=" * 60)
            print("系统状态:")
            print("=" * 60)
            print(f"  运行状态: {'运行中' if status['running'] else '已停止'}")
            print(f"  车辆ID: {status['vehicle_id']}")
            print(f"  车辆连接状态: {'已连接' if status['connected_to_vehicle'] else '未连接'}")
            print(f"  当前速度: {status['current_speed']:.1f} km/h" if status['current_speed'] else "  当前速度: 未知")
            print(f"  当前限速: {status['speed_limit']} km/h (位置: {status['speed_limit_location']})")
            if status['active_alert']:
                print(f"  活跃提示: 是 (ID: {status['active_alert']['alert_id']})")
            else:
                print("  活跃提示: 无")
            print("=" * 60)
        
        elif choice == '4':
            status = system.get_system_status()
            pm = status['performance_metrics']
            print("\n" + "=" * 60)
            print("性能指标:")
            print("=" * 60)
            print(f"  速度检查次数: {pm['speed_check_count']}")
            print(f"  超速检测次数: {pm['overspeed_count']}")
            print(f"  平均响应时间: {pm['avg_response_time_ms']:.3f} ms")
            print(f"  最大响应时间: {pm['max_response_time_ms']:.3f} ms")
            print(f"  最小响应时间: {pm['min_response_time_ms']:.3f} ms" if pm['min_response_time_ms'] != float('inf') else "  最小响应时间: 无数据")
            print("=" * 60)
        
        elif choice == '5':
            try:
                speed_input = input("请输入模拟速度 (km/h): ").strip()
                speed = float(speed_input)
                if 0 <= speed <= 200:
                    system.set_simulated_speed(speed)
                    print(f"\n已设置模拟速度: {speed} km/h")
                else:
                    print("速度值应在0-200之间")
            except ValueError:
                print("请输入有效的数字")
        
        elif choice == '6':
            try:
                limit_input = input("请输入新的速度限制 (km/h): ").strip()
                limit = float(limit_input)
                location = input("请输入位置描述: ").strip() or "当前路段"
                is_temp_input = input("是否为临时限速? (y/n): ").strip().lower()
                is_temporary = is_temp_input == 'y'
                
                if 20 <= limit <= 120:
                    system.update_speed_limit(location, limit, is_temporary)
                    print(f"\n已更新速度限制: {limit} km/h (位置: {location})")
                else:
                    print("速度限制值应在20-120之间")
            except ValueError:
                print("请输入有效的数字")
        
        elif choice == '7':
            history = system.alert_manager.get_alert_history()
            print("\n" + "=" * 60)
            print("提示历史:")
            print("=" * 60)
            if history:
                for i, alert in enumerate(history, 1):
                    status = "活跃" if alert.is_active else "已结束"
                    print(f"{i}. ID: {alert.alert_id}")
                    print(f"   速度: {alert.current_speed:.1f} km/h, 限速: {alert.speed_limit:.1f} km/h")
                    print(f"   开始时间: {alert.alert_start_time.strftime('%H:%M:%S')}")
                    print(f"   状态: {status}")
                    print()
            else:
                print("暂无提示历史")
            print("=" * 60)
        
        elif choice == '0':
            system.stop()
            print("\n感谢使用车载超速提示系统，再见！")
            sys.exit(0)
        
        else:
            print("无效选项，请重新输入")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n系统已停止")
