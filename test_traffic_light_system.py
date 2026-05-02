#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
红绿灯系统测试脚本
包含基本功能测试、边界情况测试、抗压性测试和极端测试
"""

import sys
import time
import threading
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent))

from traffic_light_system import (
    TrafficLightSystem, SystemConfig, LightColor, Direction, LightState
)


def test_basic_initialization():
    """测试基本初始化"""
    print("=" * 60)
    print("测试: 基本初始化")
    print("=" * 60)
    
    system = TrafficLightSystem()
    
    assert not system.is_running(), "新系统应该处于停止状态"
    
    states = system.get_all_states()
    assert Direction.EAST_WEST in states
    assert Direction.NORTH_SOUTH in states
    
    ew_state = states[Direction.EAST_WEST]
    ns_state = states[Direction.NORTH_SOUTH]
    
    assert ew_state.color == LightColor.GREEN, "东西方向初始应该是绿灯"
    assert ew_state.remaining_seconds == 60, "绿灯时间应该是60秒"
    
    assert ns_state.color == LightColor.RED, "南北方向初始应该是红灯"
    assert ns_state.remaining_seconds == 60, "红灯时间应该是60秒"
    
    info = system.get_system_info()
    assert not info["running"]
    assert info["cycle_count"] == 0
    assert info["uptime_seconds"] == 0
    
    print("✓ 基本初始化测试通过")
    return True


def test_custom_config():
    """测试自定义配置"""
    print("\n" + "=" * 60)
    print("测试: 自定义配置")
    print("=" * 60)
    
    custom_config = SystemConfig(
        green_duration=30,
        yellow_duration=5,
        red_duration=30
    )
    
    assert custom_config.validate(), "配置应该有效"
    
    system = TrafficLightSystem(config=custom_config)
    
    states = system.get_all_states()
    ew_state = states[Direction.EAST_WEST]
    ns_state = states[Direction.NORTH_SOUTH]
    
    assert ew_state.remaining_seconds == 30, "自定义绿灯时间应该是30秒"
    assert ns_state.remaining_seconds == 30, "自定义红灯时间应该是30秒"
    
    print("✓ 自定义配置测试通过")
    return True


def test_invalid_config():
    """测试无效配置"""
    print("\n" + "=" * 60)
    print("测试: 无效配置")
    print("=" * 60)
    
    invalid_configs = [
        SystemConfig(green_duration=0, yellow_duration=3, red_duration=60),
        SystemConfig(green_duration=60, yellow_duration=-1, red_duration=60),
        SystemConfig(green_duration=60, yellow_duration=3, red_duration=0),
    ]
    
    for i, config in enumerate(invalid_configs, 1):
        assert not config.validate(), f"配置 {i} 应该无效"
        try:
            TrafficLightSystem(config=config)
            assert False, f"应该抛出 ValueError"
        except ValueError:
            pass
    
    print("✓ 无效配置测试通过")
    return True


def test_state_transitions_manual():
    """测试手动状态转换（使用 advance_time）"""
    print("\n" + "=" * 60)
    print("测试: 手动状态转换")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=5,
        yellow_duration=2,
        red_duration=5
    )
    system = TrafficLightSystem(config=config)
    
    print("初始状态:")
    states = system.get_all_states()
    print(f"  东西方向: {states[Direction.EAST_WEST].color.value} ({states[Direction.EAST_WEST].remaining_seconds}s)")
    print(f"  南北方向: {states[Direction.NORTH_SOUTH].color.value} ({states[Direction.NORTH_SOUTH].remaining_seconds}s)")
    
    assert states[Direction.EAST_WEST].color == LightColor.GREEN
    assert states[Direction.NORTH_SOUTH].color == LightColor.RED
    
    print("\n推进 5 秒 (绿灯结束)...")
    system.advance_time(5)
    
    states = system.get_all_states()
    print(f"  东西方向: {states[Direction.EAST_WEST].color.value} ({states[Direction.EAST_WEST].remaining_seconds}s)")
    print(f"  南北方向: {states[Direction.NORTH_SOUTH].color.value} ({states[Direction.NORTH_SOUTH].remaining_seconds}s)")
    
    assert states[Direction.EAST_WEST].color == LightColor.YELLOW, "东西方向应该变为黄灯"
    assert states[Direction.NORTH_SOUTH].color == LightColor.RED, "南北方向仍为红灯"
    
    print("\n推进 2 秒 (黄灯结束)...")
    system.advance_time(2)
    
    states = system.get_all_states()
    print(f"  东西方向: {states[Direction.EAST_WEST].color.value} ({states[Direction.EAST_WEST].remaining_seconds}s)")
    print(f"  南北方向: {states[Direction.NORTH_SOUTH].color.value} ({states[Direction.NORTH_SOUTH].remaining_seconds}s)")
    
    assert states[Direction.EAST_WEST].color == LightColor.RED, "东西方向应该变为红灯"
    assert states[Direction.NORTH_SOUTH].color == LightColor.GREEN, "南北方向应该变为绿灯"
    
    info = system.get_system_info()
    assert info["cycle_count"] == 1, "应该完成1个周期"
    
    print("\n推进 7 秒 (南北绿灯 + 黄灯结束)...")
    system.advance_time(7)
    
    states = system.get_all_states()
    print(f"  东西方向: {states[Direction.EAST_WEST].color.value} ({states[Direction.EAST_WEST].remaining_seconds}s)")
    print(f"  南北方向: {states[Direction.NORTH_SOUTH].color.value} ({states[Direction.NORTH_SOUTH].remaining_seconds}s)")
    
    assert states[Direction.EAST_WEST].color == LightColor.GREEN, "东西方向应该变回绿灯"
    assert states[Direction.NORTH_SOUTH].color == LightColor.RED, "南北方向应该变回红灯"
    
    info = system.get_system_info()
    assert info["cycle_count"] == 2, "应该完成2个周期"
    
    print("✓ 手动状态转换测试通过")
    return True


def test_start_stop():
    """测试启动和停止"""
    print("\n" + "=" * 60)
    print("测试: 启动和停止")
    print("=" * 60)
    
    system = TrafficLightSystem()
    
    assert not system.is_running()
    assert system.start() == True, "第一次启动应该成功"
    assert system.is_running()
    assert system.start() == False, "重复启动应该失败"
    
    time.sleep(0.1)
    
    assert system.stop() == True, "停止应该成功"
    assert not system.is_running()
    assert system.stop() == False, "重复停止应该失败"
    
    info = system.get_system_info()
    print(f"  运行时间: {info['uptime_seconds']} 秒")
    
    print("✓ 启动和停止测试通过")
    return True


def test_state_change_callbacks():
    """测试状态变化回调"""
    print("\n" + "=" * 60)
    print("测试: 状态变化回调")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=3,
        yellow_duration=1,
        red_duration=3
    )
    system = TrafficLightSystem(config=config)
    
    callback_calls: List[Dict[str, Any]] = []
    
    def test_callback(direction, color, remaining):
        callback_calls.append({
            "direction": direction,
            "color": color,
            "remaining": remaining
        })
    
    system.register_state_change_callback("test", test_callback)
    
    initial_count = len(callback_calls)
    print(f"  初始回调次数: {initial_count}")
    
    system.advance_time(3)
    
    print(f"  推进后回调次数: {len(callback_calls)}")
    assert len(callback_calls) > initial_count, "应该有回调被调用"
    
    system.unregister_state_change_callback("test")
    
    system.advance_time(2)
    count_after_unregister = len(callback_calls)
    print(f"  注销后回调次数: {count_after_unregister}")
    
    print("✓ 状态变化回调测试通过")
    return True


def test_reset():
    """测试重置功能"""
    print("\n" + "=" * 60)
    print("测试: 重置功能")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=5,
        yellow_duration=2,
        red_duration=5
    )
    system = TrafficLightSystem(config=config)
    
    system.advance_time(15)
    
    info = system.get_system_info()
    assert info["cycle_count"] > 0, "操作后周期数应该大于0"
    
    states = system.get_all_states()
    initial_colors = (states[Direction.EAST_WEST].color, states[Direction.NORTH_SOUTH].color)
    
    system.reset()
    
    info = system.get_system_info()
    assert info["cycle_count"] == 0, "重置后周期数应该为0"
    assert not system.is_running(), "重置后应该停止"
    
    states = system.get_all_states()
    assert states[Direction.EAST_WEST].color == LightColor.GREEN
    assert states[Direction.NORTH_SOUTH].color == LightColor.RED
    assert states[Direction.EAST_WEST].remaining_seconds == 5
    assert states[Direction.NORTH_SOUTH].remaining_seconds == 5
    
    print("✓ 重置功能测试通过")
    return True


def test_get_state_thread_safety():
    """测试线程安全的状态获取"""
    print("\n" + "=" * 60)
    print("测试: 线程安全 - 状态获取")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=2,
        yellow_duration=1,
        red_duration=2
    )
    system = TrafficLightSystem(config=config)
    
    errors = []
    results = []
    
    def read_states(repeat_count: int):
        try:
            for _ in range(repeat_count):
                states = system.get_all_states()
                ew = states[Direction.EAST_WEST]
                ns = states[Direction.NORTH_SOUTH]
                results.append((ew.color, ns.color))
                time.sleep(0.001)
        except Exception as e:
            errors.append(str(e))
    
    threads = []
    for i in range(10):
        t = threading.Thread(target=read_states, args=(100,))
        threads.append(t)
        t.start()
    
    system.start()
    time.sleep(1)
    system.stop()
    
    for t in threads:
        t.join(timeout=5)
    
    assert len(errors) == 0, f"不应该有错误: {errors}"
    print(f"  成功执行 {len(results)} 次状态读取")
    
    print("✓ 线程安全测试通过")
    return True


def test_concurrent_advance_time():
    """测试并发时间推进（抗压性测试）"""
    print("\n" + "=" * 60)
    print("测试: 并发时间推进 (抗压性测试)")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=100,
        yellow_duration=10,
        red_duration=100
    )
    system = TrafficLightSystem(config=config)
    
    errors = []
    total_advancements = 0
    
    def advance_task(seconds: int, count: int):
        nonlocal total_advancements
        try:
            for _ in range(count):
                system.advance_time(seconds)
                total_advancements += seconds
        except Exception as e:
            errors.append(str(e))
    
    num_threads = 50
    operations_per_thread = 100
    
    threads = []
    for i in range(num_threads):
        t = threading.Thread(target=advance_task, args=(1, operations_per_thread))
        threads.append(t)
    
    for t in threads:
        t.start()
    
    for t in threads:
        t.join(timeout=30)
    
    assert len(errors) == 0, f"并发操作不应该有错误: {errors}"
    
    expected_advancements = num_threads * operations_per_thread
    print(f"  预期推进: {expected_advancements} 秒")
    print(f"  实际推进: {total_advancements} 秒")
    print(f"  周期数: {system.get_system_info()['cycle_count']}")
    
    print("✓ 并发时间推进测试通过")
    return True


def test_extreme_cycle_count():
    """测试极端周期数（抗压性测试）"""
    print("\n" + "=" * 60)
    print("测试: 极端周期数 (抗压性测试)")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=1,
        yellow_duration=1,
        red_duration=1
    )
    system = TrafficLightSystem(config=config)
    
    target_cycles = 100
    total_seconds = target_cycles * 4
    
    print(f"  目标周期数: {target_cycles}")
    print(f"  需要推进: {total_seconds} 秒")
    
    system.advance_time(total_seconds)
    
    info = system.get_system_info()
    print(f"  实际周期数: {info['cycle_count']}")
    
    assert info["cycle_count"] >= target_cycles, f"周期数应该至少为 {target_cycles}"
    
    states = system.get_all_states()
    ew_color = states[Direction.EAST_WEST].color
    ns_color = states[Direction.NORTH_SOUTH].color
    
    valid_pairs = [
        (LightColor.GREEN, LightColor.RED),
        (LightColor.YELLOW, LightColor.RED),
        (LightColor.RED, LightColor.GREEN),
        (LightColor.RED, LightColor.YELLOW),
    ]
    
    assert (ew_color, ns_color) in valid_pairs, f"无效的状态组合: {ew_color}, {ns_color}"
    
    print("✓ 极端周期数测试通过")
    return True


def test_rapid_start_stop():
    """测试快速启动停止（抗压性测试）"""
    print("\n" + "=" * 60)
    print("测试: 快速启动停止 (抗压性测试)")
    print("=" * 60)
    
    system = TrafficLightSystem()
    
    errors = []
    
    for i in range(100):
        try:
            system.start()
            time.sleep(0.001)
            system.stop()
            time.sleep(0.001)
        except Exception as e:
            errors.append(str(e))
    
    assert len(errors) == 0, f"快速启动停止不应该有错误: {errors}"
    print("  完成 100 次快速启动停止")
    
    print("✓ 快速启动停止测试通过")
    return True


def test_callback_stress():
    """测试回调压力（抗压性测试）"""
    print("\n" + "=" * 60)
    print("测试: 回调压力 (抗压性测试)")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=2,
        yellow_duration=1,
        red_duration=2
    )
    system = TrafficLightSystem(config=config)
    
    callback_counts = {}
    
    def make_callback(name):
        def callback(d, c, r):
            if name not in callback_counts:
                callback_counts[name] = 0
            callback_counts[name] += 1
        return callback
    
    num_callbacks = 20
    for i in range(num_callbacks):
        system.register_state_change_callback(f"callback_{i}", make_callback(f"callback_{i}"))
    
    system.advance_time(20)
    
    total_calls = sum(callback_counts.values())
    print(f"  注册回调数: {num_callbacks}")
    print(f"  总回调次数: {total_calls}")
    
    for name, count in callback_counts.items():
        print(f"    {name}: {count} 次")
    
    print("✓ 回调压力测试通过")
    return True


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("测试: 边界情况")
    print("=" * 60)
    
    system = TrafficLightSystem()
    
    print("  测试: advance_time(0)...")
    initial_states = system.get_all_states()
    system.advance_time(0)
    states_after = system.get_all_states()
    assert states_after[Direction.EAST_WEST].remaining_seconds == initial_states[Direction.EAST_WEST].remaining_seconds
    print("    ✓ 推进0秒无变化")
    
    print("  测试: advance_time(-1)...")
    system.advance_time(-1)
    states_after_negative = system.get_all_states()
    assert states_after_negative[Direction.EAST_WEST].remaining_seconds == states_after[Direction.EAST_WEST].remaining_seconds
    print("    ✓ 推进负数秒无变化")
    
    print("  测试: 停止后获取状态...")
    system.stop()
    states = system.get_all_states()
    assert Direction.EAST_WEST in states
    assert Direction.NORTH_SOUTH in states
    print("    ✓ 停止后仍可获取状态")
    
    print("  测试: 停止后advance_time...")
    system.advance_time(5)
    states = system.get_all_states()
    print(f"    ✓ 停止后推进时间: 东西={states[Direction.EAST_WEST].color.value}")
    
    print("✓ 边界情况测试通过")
    return True


def test_system_info_consistency():
    """测试系统信息一致性"""
    print("\n" + "=" * 60)
    print("测试: 系统信息一致性")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=10,
        yellow_duration=2,
        red_duration=10
    )
    system = TrafficLightSystem(config=config)
    
    info = system.get_system_info()
    assert info["config"]["green_duration"] == 10
    assert info["config"]["yellow_duration"] == 2
    assert info["config"]["red_duration"] == 10
    assert not info["running"]
    assert info["cycle_count"] == 0
    assert info["uptime_seconds"] == 0
    assert info["start_time"] is None
    
    system.start()
    time.sleep(0.1)
    
    info_running = system.get_system_info()
    assert info_running["running"]
    assert info_running["start_time"] is not None
    
    system.stop()
    
    info_stopped = system.get_system_info()
    assert not info_stopped["running"]
    
    print("✓ 系统信息一致性测试通过")
    return True


def main():
    """运行所有测试"""
    print("=" * 60)
    print("开始红绿灯系统测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")
    print()
    
    tests = [
        ("基本初始化", test_basic_initialization),
        ("自定义配置", test_custom_config),
        ("无效配置", test_invalid_config),
        ("手动状态转换", test_state_transitions_manual),
        ("启动和停止", test_start_stop),
        ("状态变化回调", test_state_change_callbacks),
        ("重置功能", test_reset),
        ("线程安全 - 状态获取", test_get_state_thread_safety),
        ("并发时间推进", test_concurrent_advance_time),
        ("极端周期数", test_extreme_cycle_count),
        ("快速启动停止", test_rapid_start_stop),
        ("回调压力", test_callback_stress),
        ("边界情况", test_edge_cases),
        ("系统信息一致性", test_system_info_consistency),
    ]
    
    passed = 0
    failed = 0
    failed_tests = []
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                failed_tests.append(test_name)
        except Exception as e:
            failed += 1
            failed_tests.append(test_name)
            print(f"\n✗ {test_name} 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"总测试数: {len(tests)}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    
    if failed_tests:
        print("\n失败的测试:")
        for name in failed_tests:
            print(f"  - {name}")
        sys.exit(1)
    else:
        print("\n✓ 所有测试全部通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()
