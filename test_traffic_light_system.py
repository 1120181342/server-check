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


def test_callback_throws_value_error():
    """测试回调抛出 ValueError"""
    print("\n" + "=" * 60)
    print("测试: 回调抛出 ValueError")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=3,
        yellow_duration=1,
        red_duration=3
    )
    system = TrafficLightSystem(config=config)
    
    normal_callback_calls = []
    
    def bad_callback(direction, color, remaining):
        raise ValueError("模拟回调中的 ValueError")
    
    def good_callback(direction, color, remaining):
        normal_callback_calls.append({
            "direction": direction,
            "color": color,
            "remaining": remaining
        })
    
    system.register_state_change_callback("bad", bad_callback)
    system.register_state_change_callback("good", good_callback)
    
    initial_count = len(normal_callback_calls)
    print(f"  初始正常回调次数: {initial_count}")
    
    try:
        system.advance_time(5)
    except Exception as e:
        assert False, f"回调抛出的异常不应该传播到调用者: {e}"
    
    final_count = len(normal_callback_calls)
    print(f"  推进后正常回调次数: {final_count}")
    assert final_count > initial_count, "即使其他回调抛出异常，正常回调也应该被调用"
    
    states = system.get_all_states()
    print(f"  系统状态: 东西={states[Direction.EAST_WEST].color.value}, 南北={states[Direction.NORTH_SOUTH].color.value}")
    
    system.unregister_state_change_callback("bad")
    system.unregister_state_change_callback("good")
    
    print("✓ 回调抛出 ValueError 测试通过")
    return True


def test_callback_throws_type_error():
    """测试回调抛出 TypeError"""
    print("\n" + "=" * 60)
    print("测试: 回调抛出 TypeError")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=2,
        yellow_duration=1,
        red_duration=2
    )
    system = TrafficLightSystem(config=config)
    
    successful_calls = []
    
    def bad_callback(direction, color, remaining):
        raise TypeError("模拟回调中的 TypeError")
    
    def tracking_callback(direction, color, remaining):
        successful_calls.append(True)
    
    system.register_state_change_callback("bad_type", bad_callback)
    system.register_state_change_callback("tracker", tracking_callback)
    
    initial_states = system.get_all_states()
    print(f"  初始状态: 东西={initial_states[Direction.EAST_WEST].color.value}")
    
    try:
        system.advance_time(4)
    except Exception as e:
        assert False, f"回调异常不应该传播: {e}"
    
    final_states = system.get_all_states()
    print(f"  推进后状态: 东西={final_states[Direction.EAST_WEST].color.value}")
    print(f"  成功调用次数: {len(successful_calls)}")
    
    assert len(successful_calls) > 0, "正常回调应该被调用"
    
    print("✓ 回调抛出 TypeError 测试通过")
    return True


def test_callback_throws_runtime_error():
    """测试回调抛出 RuntimeError"""
    print("\n" + "=" * 60)
    print("测试: 回调抛出 RuntimeError")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=4,
        yellow_duration=2,
        red_duration=4
    )
    system = TrafficLightSystem(config=config)
    
    state_before = system.get_all_states()
    cycle_before = system.get_system_info()["cycle_count"]
    
    def bad_callback(direction, color, remaining):
        raise RuntimeError("模拟回调中的严重错误")
    
    system.register_state_change_callback("runtime_error", bad_callback)
    
    try:
        system.advance_time(10)
    except Exception as e:
        assert False, f"回调的 RuntimeError 不应该传播: {e}"
    
    state_after = system.get_all_states()
    cycle_after = system.get_system_info()["cycle_count"]
    
    print(f"  推进前周期数: {cycle_before}")
    print(f"  推进后周期数: {cycle_after}")
    print(f"  推进前状态: 东西={state_before[Direction.EAST_WEST].color.value}")
    print(f"  推进后状态: 东西={state_after[Direction.EAST_WEST].color.value}")
    
    assert cycle_after > cycle_before, "即使回调抛出异常，系统也应该正常推进"
    
    print("✓ 回调抛出 RuntimeError 测试通过")
    return True


def test_mixed_good_and_bad_callbacks():
    """测试混合正常和异常回调"""
    print("\n" + "=" * 60)
    print("测试: 混合正常和异常回调")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=3,
        yellow_duration=1,
        red_duration=3
    )
    system = TrafficLightSystem(config=config)
    
    callback_results = {
        "good1": [],
        "good2": [],
        "good3": [],
    }
    
    def make_bad_callback(exception_type):
        def callback(d, c, r):
            raise exception_type(f"模拟 {exception_type.__name__}")
        return callback
    
    def make_good_callback(name):
        def callback(d, c, r):
            callback_results[name].append({
                "direction": d,
                "color": c,
                "remaining": r
            })
        return callback
    
    system.register_state_change_callback("bad1", make_bad_callback(ValueError))
    system.register_state_change_callback("good1", make_good_callback("good1"))
    system.register_state_change_callback("bad2", make_bad_callback(TypeError))
    system.register_state_change_callback("good2", make_good_callback("good2"))
    system.register_state_change_callback("bad3", make_bad_callback(RuntimeError))
    system.register_state_change_callback("good3", make_good_callback("good3"))
    
    print("  注册回调: 3个异常回调 + 3个正常回调")
    
    try:
        system.advance_time(8)
    except Exception as e:
        assert False, f"混合回调中的异常不应该传播: {e}"
    
    total_good_calls = sum(len(v) for v in callback_results.values())
    print(f"  正常回调总调用次数: {total_good_calls}")
    for name, calls in callback_results.items():
        print(f"    {name}: {len(calls)} 次")
    
    assert total_good_calls > 0, "至少有一些正常回调应该被调用"
    
    info = system.get_system_info()
    print(f"  系统周期数: {info['cycle_count']}")
    
    for name in ["bad1", "bad2", "bad3", "good1", "good2", "good3"]:
        system.unregister_state_change_callback(name)
    
    print("✓ 混合正常和异常回调测试通过")
    return True


def test_callback_throws_exception_repeatedly():
    """测试回调持续抛出异常（抗压性）"""
    print("\n" + "=" * 60)
    print("测试: 回调持续抛出异常 (抗压性)")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=2,
        yellow_duration=1,
        red_duration=2
    )
    system = TrafficLightSystem(config=config)
    
    bad_callback_count = 0
    good_callback_count = 0
    
    def very_bad_callback(d, c, r):
        nonlocal bad_callback_count
        bad_callback_count += 1
        raise Exception(f"第 {bad_callback_count} 次抛出异常")
    
    def persistent_good_callback(d, c, r):
        nonlocal good_callback_count
        good_callback_count += 1
    
    system.register_state_change_callback("very_bad", very_bad_callback)
    system.register_state_change_callback("persistent_good", persistent_good_callback)
    
    total_seconds = 30
    print(f"  计划推进 {total_seconds} 秒")
    print(f"  预计触发多次状态变化")
    
    try:
        system.advance_time(total_seconds)
    except Exception as e:
        assert False, f"即使回调持续抛出异常，系统也应该继续运行: {e}"
    
    info = system.get_system_info()
    print(f"  实际完成周期数: {info['cycle_count']}")
    print(f"  异常回调被调用次数: {bad_callback_count}")
    print(f"  正常回调被调用次数: {good_callback_count}")
    
    assert info["cycle_count"] > 0, "系统应该完成多个周期"
    assert good_callback_count > 0, "正常回调应该被调用"
    assert bad_callback_count == good_callback_count, "所有回调（包括异常的）应该被调用相同次数"
    
    system.unregister_state_change_callback("very_bad")
    system.unregister_state_change_callback("persistent_good")
    
    print("✓ 回调持续抛出异常测试通过")
    return True


def test_callback_exception_during_running():
    """测试系统运行时回调抛出异常"""
    print("\n" + "=" * 60)
    print("测试: 系统运行时回调抛出异常")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=1,
        yellow_duration=1,
        red_duration=1
    )
    system = TrafficLightSystem(config=config)
    
    exception_count = 0
    success_count = 0
    
    def exception_callback(d, c, r):
        nonlocal exception_count
        exception_count += 1
        raise ValueError(f"运行时异常 #{exception_count}")
    
    def success_callback(d, c, r):
        nonlocal success_count
        success_count += 1
    
    system.register_state_change_callback("exception", exception_callback)
    system.register_state_change_callback("success", success_callback)
    
    print("  启动系统...")
    assert system.start()
    
    time.sleep(3)
    
    print("  停止系统...")
    assert system.stop()
    
    info = system.get_system_info()
    print(f"  运行期间周期数: {info['cycle_count']}")
    print(f"  异常回调调用次数: {exception_count}")
    print(f"  正常回调调用次数: {success_count}")
    
    assert info["cycle_count"] > 0, "系统应该正常运行"
    assert success_count > 0, "正常回调应该被调用"
    
    system.unregister_state_change_callback("exception")
    system.unregister_state_change_callback("success")
    
    print("✓ 系统运行时回调抛出异常测试通过")
    return True


def test_callback_none_value():
    """测试处理可能的 None 值情况"""
    print("\n" + "=" * 60)
    print("测试: 回调处理异常参数")
    print("=" * 60)
    
    config = SystemConfig(
        green_duration=5,
        yellow_duration=2,
        red_duration=5
    )
    system = TrafficLightSystem(config=config)
    
    callback_errors = []
    
    def paranoid_callback(direction, color, remaining):
        try:
            assert direction is not None
            assert color is not None
            assert remaining is not None
            assert isinstance(remaining, int)
        except AssertionError as e:
            callback_errors.append(str(e))
    
    system.register_state_change_callback("paranoid", paranoid_callback)
    
    system.advance_time(7)
    
    states = system.get_all_states()
    info = system.get_system_info()
    
    print(f"  周期数: {info['cycle_count']}")
    print(f"  东西方向: {states[Direction.EAST_WEST].color.value}")
    print(f"  南北方向: {states[Direction.NORTH_SOUTH].color.value}")
    print(f"  回调参数验证错误数: {len(callback_errors)}")
    
    assert len(callback_errors) == 0, "回调参数应该都是有效的"
    
    system.unregister_state_change_callback("paranoid")
    
    print("✓ 回调参数有效性测试通过")
    return True


def test_unregister_nonexistent_callback():
    """测试注销不存在的回调"""
    print("\n" + "=" * 60)
    print("测试: 注销不存在的回调")
    print("=" * 60)
    
    system = TrafficLightSystem()
    
    try:
        system.unregister_state_change_callback("nonexistent")
        print("  注销不存在的回调没有抛出异常")
    except Exception as e:
        assert False, f"注销不存在的回调不应该抛出异常: {e}"
    
    try:
        system.unregister_state_change_callback("")
        print("  注销空名称回调没有抛出异常")
    except Exception as e:
        assert False, f"注销空名称回调不应该抛出异常: {e}"
    
    def sample_callback(d, c, r):
        pass
    
    system.register_state_change_callback("test", sample_callback)
    
    try:
        system.unregister_state_change_callback("test")
        print("  正常注销已存在的回调成功")
    except Exception as e:
        assert False, f"正常注销应该成功: {e}"
    
    print("✓ 注销不存在的回调测试通过")
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
        ("回调抛出 ValueError", test_callback_throws_value_error),
        ("回调抛出 TypeError", test_callback_throws_type_error),
        ("回调抛出 RuntimeError", test_callback_throws_runtime_error),
        ("混合正常和异常回调", test_mixed_good_and_bad_callbacks),
        ("回调持续抛出异常", test_callback_throws_exception_repeatedly),
        ("系统运行时回调抛出异常", test_callback_exception_during_running),
        ("回调参数有效性", test_callback_none_value),
        ("注销不存在的回调", test_unregister_nonexistent_callback),
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
