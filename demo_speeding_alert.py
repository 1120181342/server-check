#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车载超速提示系统演示脚本
演示系统的核心功能：
1. 速度检测
2. 限速监测
3. 超速检测与提示
4. 性能指标
"""

import time
import threading
from datetime import datetime

# 导入系统模块
from speeding_alert_system import (
    SpeedingAlertSystem,
    SpeedData,
    SpeedLimit,
    AlertInfo
)


def print_system_status(system):
    """打印系统状态"""
    status = system.get_system_status()
    
    print("\n" + "=" * 60)
    print(f"系统状态 [{datetime.now().strftime('%H:%M:%S')}]")
    print("=" * 60)
    print(f"  运行状态: {'运行中' if status['running'] else '已停止'}")
    print(f"  车辆连接: {'已连接' if status['connected_to_vehicle'] else '未连接'}")
    
    if status['current_speed'] is not None:
        # 检查是否超速
        is_speeding = status['current_speed'] > status['speed_limit']
        speed_color = "⚠️  超速" if is_speeding else "正常"
        print(f"  当前速度: {status['current_speed']:.1f} km/h ({speed_color})")
    else:
        print(f"  当前速度: 未知")
    
    print(f"  速度限制: {status['speed_limit']} km/h")
    print(f"  位置: {status['speed_limit_location']}")
    
    if status['active_alert']:
        alert = status['active_alert']
        print(f"  活跃提示: 是 (ID: {alert['alert_id']})")
        print(f"  提示详情: 速度 {alert['current_speed']:.1f} km/h > 限速 {alert['speed_limit']:.1f} km/h")
    else:
        print("  活跃提示: 无")
    
    pm = status['performance_metrics']
    print(f"\n  性能指标:")
    print(f"    速度检查次数: {pm['speed_check_count']}")
    print(f"    超速检测次数: {pm['overspeed_count']}")
    print(f"    平均响应时间: {pm['avg_response_time_ms']:.3f} ms")
    print(f"    最大响应时间: {pm['max_response_time_ms']:.3f} ms")
    print("=" * 60)


def demo_basic_functionality():
    """
    演示基本功能
    """
    print("\n" + "#" * 60)
    print("# 演示1: 基本功能演示")
    print("#" * 60)
    
    # 创建系统实例
    system = SpeedingAlertSystem(
        vehicle_id="DEMO-001",
        initial_speed_limit=60.0,
        alert_duration=3.0
    )
    
    # 启动系统
    print("\n[1] 启动超速提示系统...")
    system.start()
    
    # 等待系统稳定
    time.sleep(1)
    
    # 打印初始状态
    print("\n[2] 打印初始系统状态...")
    print_system_status(system)
    
    # 设置正常速度
    print("\n[3] 设置正常速度 (55 km/h)...")
    system.set_simulated_speed(55.0)
    time.sleep(0.5)
    print_system_status(system)
    
    # 设置超速
    print("\n[4] 设置超速 (70 km/h)...")
    system.set_simulated_speed(70.0)
    
    # 等待系统检测到超速并触发提示
    print("    等待系统检测超速...")
    time.sleep(0.5)
    
    # 打印状态
    print_system_status(system)
    
    # 等待提示持续
    print("\n[5] 等待提示持续 (3秒提示)...")
    time.sleep(2)
    print_system_status(system)
    
    # 等待提示结束
    print("\n[6] 等待提示结束...")
    time.sleep(2)
    print_system_status(system)
    
    # 停止系统
    print("\n[7] 停止系统...")
    system.stop()


def demo_performance():
    """
    演示性能指标
    """
    print("\n" + "#" * 60)
    print("# 演示2: 性能指标演示 (确保1秒内响应)")
    print("#" * 60)
    
    # 创建系统实例
    system = SpeedingAlertSystem(
        vehicle_id="PERF-001",
        initial_speed_limit=60.0,
        alert_duration=3.0
    )
    
    # 用于记录提示时间
    alert_times = []
    
    def alert_callback(alert_info, event_type):
        if event_type == "start":
            alert_times.append({
                "alert_id": alert_info.alert_id,
                "time": time.perf_counter()
            })
    
    # 注册回调
    system.alert_manager.register_alert_callback("perf_test", alert_callback)
    
    # 启动系统
    print("\n[1] 启动系统并等待稳定...")
    system.start()
    time.sleep(1)
    
    # 第一次测试：从正常速度到超速
    print("\n[2] 第一次超速测试:")
    print("    设置正常速度 (50 km/h)...")
    system.set_simulated_speed(50.0)
    time.sleep(0.5)
    
    # 记录时间
    start_time = time.perf_counter()
    
    # 设置超速
    print("    设置超速 (75 km/h)...")
    system.set_simulated_speed(75.0)
    
    # 等待提示
    print("    等待系统响应...")
    max_wait = 1.5
    wait_start = time.perf_counter()
    
    while len(alert_times) < 1 and (time.perf_counter() - wait_start) < max_wait:
        time.sleep(0.05)
    
    # 计算响应时间
    if len(alert_times) >= 1:
        response_time = (alert_times[0]["time"] - start_time) * 1000
        print(f"    ✓ 系统响应时间: {response_time:.2f} ms")
        
        # 检查是否在1秒内
        if response_time < 1000:
            print(f"    ✓ 符合要求: 响应时间小于1秒")
        else:
            print(f"    ✗ 不符合要求: 响应时间超过1秒")
    else:
        print("    ✗ 系统未在规定时间内响应")
    
    # 打印性能指标
    print_system_status(system)
    
    # 等待提示结束
    time.sleep(4)
    
    # 第二次测试：确保响应时间稳定
    print("\n[3] 第二次超速测试 (验证稳定性):")
    
    # 先回到正常速度
    system.set_simulated_speed(50.0)
    time.sleep(0.5)
    
    # 重置提示时间
    alert_times.clear()
    
    # 记录时间
    start_time = time.perf_counter()
    
    # 设置超速
    print("    再次设置超速 (80 km/h)...")
    system.set_simulated_speed(80.0)
    
    # 等待提示
    print("    等待系统响应...")
    wait_start = time.perf_counter()
    
    while len(alert_times) < 1 and (time.perf_counter() - wait_start) < max_wait:
        time.sleep(0.05)
    
    # 计算响应时间
    if len(alert_times) >= 1:
        response_time = (alert_times[0]["time"] - start_time) * 1000
        print(f"    ✓ 系统响应时间: {response_time:.2f} ms")
        
        if response_time < 1000:
            print(f"    ✓ 符合要求: 响应时间小于1秒")
        else:
            print(f"    ✗ 不符合要求: 响应时间超过1秒")
    else:
        print("    ✗ 系统未在规定时间内响应")
    
    # 打印最终性能指标
    print("\n[4] 最终性能指标:")
    print_system_status(system)
    
    # 停止系统
    print("\n[5] 停止系统...")
    system.stop()


def demo_speed_limit_changes():
    """
    演示速度限制变化
    """
    print("\n" + "#" * 60)
    print("# 演示3: 速度限制变化演示")
    print("#" * 60)
    
    # 创建系统实例
    system = SpeedingAlertSystem(
        vehicle_id="LIMIT-001",
        initial_speed_limit=60.0,
        alert_duration=3.0
    )
    
    # 用于记录限速变化
    limit_changes = []
    
    def limit_callback(speed_limit):
        limit_changes.append({
            "limit": speed_limit.limit,
            "location": speed_limit.location,
            "is_temporary": speed_limit.is_temporary,
            "time": datetime.now()
        })
    
    # 注册回调
    system.limit_monitor.register_limit_change_callback("limit_test", limit_callback)
    
    # 启动系统
    print("\n[1] 启动系统...")
    system.start()
    time.sleep(1)
    
    # 初始状态
    print_system_status(system)
    
    # 模拟进入高速公路
    print("\n[2] 进入高速公路 (限速120 km/h)...")
    system.update_speed_limit("G15沈海高速", 120.0, False)
    time.sleep(0.5)
    
    # 设置速度在限速内
    system.set_simulated_speed(110.0)
    time.sleep(0.5)
    print_system_status(system)
    
    # 模拟进入市区道路
    print("\n[3] 进入市区道路 (限速60 km/h)...")
    system.update_speed_limit("上海市浦东新区世纪大道", 60.0, False)
    time.sleep(0.5)
    
    # 当前速度110超过了新限速60，应该触发提示
    print("    当前速度110 km/h 超过新限速60 km/h...")
    time.sleep(1)
    print_system_status(system)
    
    # 模拟临时限速
    print("\n[4] 遇到施工路段 (临时限速40 km/h)...")
    system.update_speed_limit("施工路段 (临时)", 40.0, True)
    time.sleep(0.5)
    print_system_status(system)
    
    # 减速
    print("\n[5] 减速到35 km/h...")
    system.set_simulated_speed(35.0)
    time.sleep(1)
    print_system_status(system)
    
    # 打印限速变化历史
    print("\n[6] 限速变化历史:")
    for i, change in enumerate(limit_changes, 1):
        temp_mark = " (临时)" if change["is_temporary"] else ""
        print(f"    {i}. {change['time'].strftime('%H:%M:%S')} - "
              f"{change['location']}: {change['limit']} km/h{temp_mark}")
    
    # 停止系统
    print("\n[7] 停止系统...")
    system.stop()


def demo_alert_duration():
    """
    演示提示持续3秒
    """
    print("\n" + "#" * 60)
    print("# 演示4: 提示持续时间演示 (3秒)")
    print("#" * 60)
    
    # 创建系统实例，设置3秒提示
    system = SpeedingAlertSystem(
        vehicle_id="DURATION-001",
        initial_speed_limit=60.0,
        alert_duration=3.0
    )
    
    # 用于记录提示事件
    alert_events = []
    
    def alert_callback(alert_info, event_type):
        alert_events.append({
            "event_type": event_type,
            "alert_id": alert_info.alert_id,
            "time": time.perf_counter()
        })
    
    # 注册回调
    system.alert_manager.register_alert_callback("duration_test", alert_callback)
    
    # 启动系统
    print("\n[1] 启动系统...")
    system.start()
    time.sleep(1)
    
    # 设置超速
    print("\n[2] 设置超速 (70 km/h)...")
    system.set_simulated_speed(70.0)
    
    # 等待提示开始和结束
    print("    等待提示开始和结束...")
    
    max_wait = 6.0
    wait_start = time.perf_counter()
    
    while len(alert_events) < 2 and (time.perf_counter() - wait_start) < max_wait:
        time.sleep(0.1)
    
    # 分析结果
    if len(alert_events) >= 2:
        start_event = None
        end_event = None
        
        for event in alert_events:
            if event["event_type"] == "start":
                start_event = event
            elif event["event_type"] == "end":
                end_event = event
        
        if start_event and end_event:
            duration = end_event["time"] - start_event["time"]
            print(f"\n[3] 提示持续时间分析:")
            print(f"    提示开始时间: {start_event['time']:.3f}")
            print(f"    提示结束时间: {end_event['time']:.3f}")
            print(f"    实际持续时间: {duration:.3f} 秒")
            
            # 验证是否接近3秒
            if 2.5 <= duration <= 3.5:
                print(f"    ✓ 符合要求: 持续时间接近3秒 (允许±0.5秒误差)")
            else:
                print(f"    ✗ 不符合要求: 持续时间与3秒相差较大")
        else:
            print("    无法找到完整的开始和结束事件")
    else:
        print(f"    只捕获到 {len(alert_events)} 个事件，预期2个")
    
    # 打印状态
    print_system_status(system)
    
    # 停止系统
    print("\n[4] 停止系统...")
    system.stop()


def main():
    """
    主函数：运行所有演示
    """
    print("=" * 60)
    print("        车载超速提示系统演示")
    print("=" * 60)
    print("演示内容:")
    print("  1. 基本功能演示")
    print("  2. 性能指标演示 (确保1秒内响应)")
    print("  3. 速度限制变化演示")
    print("  4. 提示持续时间演示 (3秒)")
    print("=" * 60)
    
    # 运行所有演示
    try:
        demo_basic_functionality()
        demo_performance()
        demo_speed_limit_changes()
        demo_alert_duration()
        
        print("\n" + "=" * 60)
        print("✓ 所有演示完成！")
        print("=" * 60)
        print("\n系统特性总结:")
        print("  1. ✓ 与车辆速度检测系统对接API")
        print("  2. ✓ 实时监测路面速度限制")
        print("  3. ✓ 超速时自动发出3秒提示")
        print("  4. ✓ 确保超速发生后1秒内响应")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n演示被用户中断")
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
