#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路口红绿灯系统
功能：
1. 支持双向交通（东西方向、南北方向）
2. 绿灯时间60秒，红灯时间60秒，黄灯时间3秒
3. 只涉及直行，不涉及转弯
4. 抗压性好，可应对极端测试
"""

import threading
import time
import enum
from datetime import datetime, timedelta
from typing import Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from threading import Lock, Event


class LightColor(enum.Enum):
    """信号灯颜色枚举"""
    RED = "red"
    YELLOW = "yellow"
    GREEN = "green"


class Direction(enum.Enum):
    """方向枚举"""
    EAST_WEST = "east_west"
    NORTH_SOUTH = "north_south"


@dataclass
class LightState:
    """信号灯状态"""
    direction: Direction
    color: LightColor
    remaining_seconds: int
    last_change_time: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "direction": self.direction.value,
            "color": self.color.value,
            "remaining_seconds": self.remaining_seconds,
            "last_change_time": self.last_change_time.isoformat()
        }


@dataclass
class SystemConfig:
    """系统配置"""
    green_duration: int = 60
    yellow_duration: int = 3
    red_duration: int = 60
    
    def validate(self) -> bool:
        if self.green_duration <= 0:
            return False
        if self.yellow_duration <= 0:
            return False
        if self.red_duration <= 0:
            return False
        return True


class TrafficLightSystem:
    """红绿灯系统核心类"""
    
    def __init__(self, config: Optional[SystemConfig] = None):
        """
        初始化红绿灯系统
        :param config: 系统配置，默认使用标准配置
        """
        self.config = config or SystemConfig()
        if not self.config.validate():
            raise ValueError("无效的系统配置：所有时间必须大于0")
        
        self._lock = Lock()
        self._stop_event = Event()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        
        self._east_west_state = LightState(
            direction=Direction.EAST_WEST,
            color=LightColor.GREEN,
            remaining_seconds=self.config.green_duration
        )
        
        self._north_south_state = LightState(
            direction=Direction.NORTH_SOUTH,
            color=LightColor.RED,
            remaining_seconds=self.config.red_duration
        )
        
        self._cycle_count = 0
        self._total_operation_time = timedelta(0)
        self._state_change_callbacks: Dict[str, Callable] = {}
        self._start_time: Optional[datetime] = None
    
    def _get_current_state(self, direction: Direction) -> LightState:
        """获取指定方向的当前状态（内部使用，不加锁）"""
        if direction == Direction.EAST_WEST:
            return self._east_west_state
        return self._north_south_state
    
    def _set_state(self, direction: Direction, color: LightColor, remaining: int):
        """设置指定方向的状态（内部使用，不加锁）"""
        now = datetime.now()
        if direction == Direction.EAST_WEST:
            self._east_west_state.color = color
            self._east_west_state.remaining_seconds = remaining
            self._east_west_state.last_change_time = now
        else:
            self._north_south_state.color = color
            self._north_south_state.remaining_seconds = remaining
            self._north_south_state.last_change_time = now
        
        self._notify_state_change(direction, color, remaining)
    
    def _notify_state_change(self, direction: Direction, color: LightColor, remaining: int):
        """通知状态变化"""
        for callback in self._state_change_callbacks.values():
            try:
                callback(direction, color, remaining)
            except Exception:
                pass
    
    def register_state_change_callback(self, name: str, callback: Callable):
        """
        注册状态变化回调函数
        :param name: 回调名称
        :param callback: 回调函数，参数为 (direction, color, remaining_seconds)
        """
        with self._lock:
            self._state_change_callbacks[name] = callback
    
    def unregister_state_change_callback(self, name: str):
        """
        注销状态变化回调函数
        :param name: 回调名称
        """
        with self._lock:
            self._state_change_callbacks.pop(name, None)
    
    def get_state(self, direction: Direction) -> LightState:
        """
        获取指定方向的当前状态
        :param direction: 方向
        :return: 信号灯状态
        """
        with self._lock:
            state = self._get_current_state(direction)
            return LightState(
                direction=state.direction,
                color=state.color,
                remaining_seconds=state.remaining_seconds,
                last_change_time=state.last_change_time
            )
    
    def get_all_states(self) -> Dict[Direction, LightState]:
        """
        获取所有方向的当前状态
        :return: 方向到状态的映射
        """
        with self._lock:
            return {
                Direction.EAST_WEST: LightState(
                    direction=self._east_west_state.direction,
                    color=self._east_west_state.color,
                    remaining_seconds=self._east_west_state.remaining_seconds,
                    last_change_time=self._east_west_state.last_change_time
                ),
                Direction.NORTH_SOUTH: LightState(
                    direction=self._north_south_state.direction,
                    color=self._north_south_state.color,
                    remaining_seconds=self._north_south_state.remaining_seconds,
                    last_change_time=self._north_south_state.last_change_time
                )
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息
        :return: 系统信息字典
        """
        with self._lock:
            now = datetime.now()
            uptime = (now - self._start_time) if self._start_time else timedelta(0)
            
            return {
                "running": self._running,
                "cycle_count": self._cycle_count,
                "uptime_seconds": int(uptime.total_seconds()),
                "config": {
                    "green_duration": self.config.green_duration,
                    "yellow_duration": self.config.yellow_duration,
                    "red_duration": self.config.red_duration
                },
                "start_time": self._start_time.isoformat() if self._start_time else None
            }
    
    def _transition_states(self):
        """执行状态转换"""
        ew_state = self._get_current_state(Direction.EAST_WEST)
        ns_state = self._get_current_state(Direction.NORTH_SOUTH)
        
        if ew_state.color == LightColor.GREEN and ns_state.color == LightColor.RED:
            self._set_state(Direction.EAST_WEST, LightColor.YELLOW, self.config.yellow_duration)
            self._set_state(Direction.NORTH_SOUTH, LightColor.RED, self.config.yellow_duration)
        
        elif ew_state.color == LightColor.YELLOW and ns_state.color == LightColor.RED:
            self._set_state(Direction.EAST_WEST, LightColor.RED, self.config.red_duration)
            self._set_state(Direction.NORTH_SOUTH, LightColor.GREEN, self.config.green_duration)
            self._cycle_count += 1
        
        elif ew_state.color == LightColor.RED and ns_state.color == LightColor.GREEN:
            self._set_state(Direction.EAST_WEST, LightColor.RED, self.config.yellow_duration)
            self._set_state(Direction.NORTH_SOUTH, LightColor.YELLOW, self.config.yellow_duration)
        
        elif ew_state.color == LightColor.RED and ns_state.color == LightColor.YELLOW:
            self._set_state(Direction.EAST_WEST, LightColor.GREEN, self.config.green_duration)
            self._set_state(Direction.NORTH_SOUTH, LightColor.RED, self.config.red_duration)
            self._cycle_count += 1
    
    def _run_loop(self):
        """系统运行主循环"""
        while not self._stop_event.is_set():
            with self._lock:
                ew_state = self._get_current_state(Direction.EAST_WEST)
                ns_state = self._get_current_state(Direction.NORTH_SOUTH)
                
                ew_state.remaining_seconds -= 1
                ns_state.remaining_seconds -= 1
                
                if ew_state.remaining_seconds <= 0 or ns_state.remaining_seconds <= 0:
                    self._transition_states()
            
            time.sleep(1)
    
    def start(self):
        """启动红绿灯系统"""
        with self._lock:
            if self._running:
                return False
            
            self._stop_event.clear()
            self._running = True
            self._start_time = datetime.now()
            
            self._set_state(Direction.EAST_WEST, LightColor.GREEN, self.config.green_duration)
            self._set_state(Direction.NORTH_SOUTH, LightColor.RED, self.config.red_duration)
            
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()
            
            return True
    
    def stop(self):
        """停止红绿灯系统"""
        with self._lock:
            if not self._running:
                return False
            
            self._stop_event.set()
            self._running = False
            
            if self._start_time:
                self._total_operation_time += datetime.now() - self._start_time
            
            return True
    
    def reset(self):
        """重置系统状态"""
        self.stop()
        
        with self._lock:
            self._cycle_count = 0
            self._total_operation_time = timedelta(0)
            self._start_time = None
            
            self._east_west_state = LightState(
                direction=Direction.EAST_WEST,
                color=LightColor.GREEN,
                remaining_seconds=self.config.green_duration
            )
            
            self._north_south_state = LightState(
                direction=Direction.NORTH_SOUTH,
                color=LightColor.RED,
                remaining_seconds=self.config.red_duration
            )
    
    def is_running(self) -> bool:
        """检查系统是否正在运行"""
        with self._lock:
            return self._running
    
    def advance_time(self, seconds: int):
        """
        手动推进时间（用于测试）
        :param seconds: 要推进的秒数
        """
        if seconds <= 0:
            return
        
        with self._lock:
            for _ in range(seconds):
                ew_state = self._get_current_state(Direction.EAST_WEST)
                ns_state = self._get_current_state(Direction.NORTH_SOUTH)
                
                ew_state.remaining_seconds -= 1
                ns_state.remaining_seconds -= 1
                
                if ew_state.remaining_seconds <= 0 or ns_state.remaining_seconds <= 0:
                    self._transition_states()


def main():
    """命令行交互界面"""
    import sys
    
    print("=" * 60)
    print("        路口红绿灯系统 v1.0")
    print("=" * 60)
    print("配置:")
    print(f"  绿灯时间: 60秒")
    print(f"  黄灯时间: 3秒")
    print(f"  红灯时间: 60秒")
    print("=" * 60)
    
    system = TrafficLightSystem()
    
    def state_change_callback(direction: Direction, color: LightColor, remaining: int):
        dir_name = "东西方向" if direction == Direction.EAST_WEST else "南北方向"
        color_name = {"red": "红灯", "yellow": "黄灯", "green": "绿灯"}[color.value]
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {dir_name} 变为 {color_name} (剩余 {remaining} 秒)")
    
    system.register_state_change_callback("cli_display", state_change_callback)
    
    print("\n系统已初始化，等待您的操作...")
    
    while True:
        print("\n" + "-" * 60)
        print("请选择操作:")
        print("1. 启动红绿灯系统")
        print("2. 停止红绿灯系统")
        print("3. 查看当前状态")
        print("4. 查看系统信息")
        print("5. 重置系统")
        print("0. 退出系统")
        print("-" * 60)
        
        choice = input("请输入选项编号: ").strip()
        
        if choice == '1':
            if system.is_running():
                print("\n系统已经在运行中！")
            else:
                system.start()
                print("\n红绿灯系统已启动！")
                print("初始状态:")
                print("  东西方向: 绿灯 (60秒)")
                print("  南北方向: 红灯 (60秒)")
        
        elif choice == '2':
            if not system.is_running():
                print("\n系统尚未启动！")
            else:
                system.stop()
                print("\n红绿灯系统已停止！")
        
        elif choice == '3':
            states = system.get_all_states()
            print("\n" + "=" * 60)
            print("当前信号灯状态:")
            print("=" * 60)
            
            for direction, state in states.items():
                dir_name = "东西方向" if direction == Direction.EAST_WEST else "南北方向"
                color_name = {"red": "红灯", "yellow": "黄灯", "green": "绿灯"}[state.color.value]
                print(f"  {dir_name}: {color_name} (剩余 {state.remaining_seconds} 秒)")
            
            print("=" * 60)
        
        elif choice == '4':
            info = system.get_system_info()
            print("\n" + "=" * 60)
            print("系统信息:")
            print("=" * 60)
            print(f"  运行状态: {'运行中' if info['running'] else '已停止'}")
            print(f"  完成周期数: {info['cycle_count']}")
            print(f"  运行时间: {info['uptime_seconds']} 秒")
            print(f"  绿灯时间: {info['config']['green_duration']} 秒")
            print(f"  黄灯时间: {info['config']['yellow_duration']} 秒")
            print(f"  红灯时间: {info['config']['red_duration']} 秒")
            if info['start_time']:
                print(f"  启动时间: {info['start_time']}")
            print("=" * 60)
        
        elif choice == '5':
            system.reset()
            print("\n系统已重置！")
        
        elif choice == '0':
            system.stop()
            print("\n感谢使用红绿灯系统，再见！")
            sys.exit(0)
        
        else:
            print("无效选项，请重新输入")


if __name__ == "__main__":
    main()
