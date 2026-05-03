#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
车载超速提示系统测试文件
测试内容：
1. 速度检测API功能
2. 速度限制监测功能
3. 提示管理器功能
4. 整体系统功能测试
5. 性能测试 - 确保1秒内响应
"""

import unittest
import time
import threading
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# 导入要测试的模块
from speeding_alert_system import (
    SpeedData, 
    SpeedLimit, 
    AlertInfo,
    VehicleSpeedAPI,
    RoadSpeedLimitMonitor,
    AlertManager,
    SpeedingAlertSystem
)


class TestSpeedData(unittest.TestCase):
    """测试速度数据类"""
    
    def test_speed_data_creation(self):
        """测试创建速度数据对象"""
        speed_data = SpeedData(
            vehicle_id="TEST-001",
            speed=65.5,
            timestamp=datetime(2023, 1, 1, 12, 0, 0)
        )
        
        self.assertEqual(speed_data.vehicle_id, "TEST-001")
        self.assertEqual(speed_data.speed, 65.5)
        self.assertEqual(speed_data.unit, "km/h")
    
    def test_speed_data_to_dict(self):
        """测试速度数据转换为字典"""
        test_time = datetime(2023, 1, 1, 12, 0, 0)
        speed_data = SpeedData(
            vehicle_id="TEST-001",
            speed=70.0,
            timestamp=test_time
        )
        
        data_dict = speed_data.to_dict()
        
        self.assertIn("vehicle_id", data_dict)
        self.assertIn("speed", data_dict)
        self.assertIn("timestamp", data_dict)
        self.assertIn("unit", data_dict)
        self.assertEqual(data_dict["vehicle_id"], "TEST-001")
        self.assertEqual(data_dict["speed"], 70.0)


class TestSpeedLimit(unittest.TestCase):
    """测试速度限制类"""
    
    def test_speed_limit_creation(self):
        """测试创建速度限制对象"""
        speed_limit = SpeedLimit(
            location="高速公路段",
            limit=120.0,
            is_temporary=False
        )
        
        self.assertEqual(speed_limit.location, "高速公路段")
        self.assertEqual(speed_limit.limit, 120.0)
        self.assertFalse(speed_limit.is_temporary)
    
    def test_temporary_speed_limit(self):
        """测试临时限速"""
        speed_limit = SpeedLimit(
            location="施工路段",
            limit=60.0,
            is_temporary=True
        )
        
        self.assertEqual(speed_limit.limit, 60.0)
        self.assertTrue(speed_limit.is_temporary)


class TestAlertInfo(unittest.TestCase):
    """测试提示信息类"""
    
    def test_alert_info_creation(self):
        """测试创建提示信息对象"""
        start_time = datetime(2023, 1, 1, 12, 0, 0)
        alert_info = AlertInfo(
            alert_id="ALERT-001",
            vehicle_id="TEST-001",
            current_speed=75.5,
            speed_limit=60.0,
            alert_start_time=start_time,
            alert_duration=3.0
        )
        
        self.assertEqual(alert_info.alert_id, "ALERT-001")
        self.assertEqual(alert_info.current_speed, 75.5)
        self.assertEqual(alert_info.speed_limit, 60.0)
        self.assertEqual(alert_info.alert_duration, 3.0)
        self.assertTrue(alert_info.is_active)


class TestVehicleSpeedAPI(unittest.TestCase):
    """测试车辆速度检测API"""
    
    def setUp(self):
        """测试前设置"""
        self.api = VehicleSpeedAPI("TEST-001")
    
    def test_connect(self):
        """测试连接到车辆系统"""
        self.assertFalse(self.api.is_connected())
        result = self.api.connect()
        self.assertTrue(result)
        self.assertTrue(self.api.is_connected())
    
    def test_disconnect(self):
        """测试断开连接"""
        self.api.connect()
        self.assertTrue(self.api.is_connected())
        
        result = self.api.disconnect()
        self.assertTrue(result)
        self.assertFalse(self.api.is_connected())
    
    def test_get_speed_without_connection(self):
        """测试未连接时获取速度"""
        speed_data = self.api.get_current_speed()
        self.assertIsNone(speed_data)
    
    def test_get_speed_with_connection(self):
        """测试连接后获取速度"""
        self.api.connect()
        speed_data = self.api.get_current_speed()
        
        self.assertIsNotNone(speed_data)
        self.assertIsInstance(speed_data.speed, float)
        self.assertGreaterEqual(speed_data.speed, 0.0)
        self.assertLessEqual(speed_data.speed, 150.0)
    
    def test_set_simulated_speed(self):
        """测试设置模拟速度"""
        self.api.connect()
        self.api.set_simulated_speed(80.0)
        
        # 获取速度应该接近80（可能有微小变化）
        speed_data = self.api.get_current_speed()
        self.assertIsNotNone(speed_data)
        # 由于模拟速度有随机变化，这里检查是否在合理范围内
        self.assertGreaterEqual(speed_data.speed, 75.0)
        self.assertLessEqual(speed_data.speed, 85.0)


class TestRoadSpeedLimitMonitor(unittest.TestCase):
    """测试路面速度限制监测器"""
    
    def setUp(self):
        """测试前设置"""
        self.monitor = RoadSpeedLimitMonitor(initial_limit=60.0)
        self.callback_called = False
        self.last_limit = None
    
    def limit_change_callback(self, speed_limit):
        """限速变化回调函数"""
        self.callback_called = True
        self.last_limit = speed_limit
    
    def test_initial_limit(self):
        """测试初始限速"""
        limit = self.monitor.get_current_limit()
        self.assertEqual(limit.limit, 60.0)
    
    def test_update_limit(self):
        """测试更新限速"""
        self.monitor.update_speed_limit("市区道路", 50.0, False)
        
        limit = self.monitor.get_current_limit()
        self.assertEqual(limit.limit, 50.0)
        self.assertEqual(limit.location, "市区道路")
    
    def test_callback_on_limit_change(self):
        """测试限速变化时触发回调"""
        self.monitor.register_limit_change_callback("test", self.limit_change_callback)
        
        # 初始状态
        self.assertFalse(self.callback_called)
        
        # 更新限速
        self.monitor.update_speed_limit("高速公路", 120.0)
        
        # 验证回调被调用
        self.assertTrue(self.callback_called)
        self.assertIsNotNone(self.last_limit)
        self.assertEqual(self.last_limit.limit, 120.0)
    
    def test_no_callback_on_same_limit(self):
        """测试相同限速时不触发回调"""
        self.monitor.register_limit_change_callback("test", self.limit_change_callback)
        
        # 初始状态
        self.assertFalse(self.callback_called)
        
        # 设置相同的限速（只是位置不同）
        self.monitor.update_speed_limit("不同位置", 60.0)
        
        # 回调应该被调用，因为位置变了？或者只有限速变化才触发？
        # 让我们检查实现：只有当limit变化时才通知回调
        # 实际上我们的实现是如果old_limit != limit才通知
        # 让我们重新测试
        
        # 先改一个不同的限速
        self.monitor.update_speed_limit("位置1", 50.0)
        self.assertTrue(self.callback_called)
        
        # 重置
        self.callback_called = False
        self.last_limit = None
        
        # 再改一个相同的限速
        self.monitor.update_speed_limit("位置2", 50.0)
        
        # 不应该触发回调，因为限速值相同
        self.assertFalse(self.callback_called)


class TestAlertManager(unittest.TestCase):
    """测试提示管理器"""
    
    def setUp(self):
        """测试前设置"""
        self.alert_manager = AlertManager(alert_duration=3.0)
        self.callback_events = []
    
    def alert_callback(self, alert_info, event_type):
        """提示事件回调函数"""
        self.callback_events.append({
            "alert_info": alert_info,
            "event_type": event_type
        })
    
    def test_start_alert(self):
        """测试开始提示"""
        alert_info = self.alert_manager.start_alert(
            vehicle_id="TEST-001",
            current_speed=70.0,
            speed_limit=60.0
        )
        
        self.assertIsNotNone(alert_info)
        self.assertEqual(alert_info.current_speed, 70.0)
        self.assertEqual(alert_info.speed_limit, 60.0)
        self.assertTrue(alert_info.is_active)
    
    def test_get_active_alert(self):
        """测试获取活跃提示"""
        # 初始状态没有活跃提示
        active = self.alert_manager.get_active_alert()
        self.assertIsNone(active)
        
        # 开始一个提示
        alert_info = self.alert_manager.start_alert(
            vehicle_id="TEST-001",
            current_speed=70.0,
            speed_limit=60.0
        )
        
        # 应该能获取到活跃提示
        active = self.alert_manager.get_active_alert()
        self.assertIsNotNone(active)
        self.assertEqual(active.alert_id, alert_info.alert_id)
    
    def test_stop_alert(self):
        """测试停止提示"""
        self.alert_manager.start_alert(
            vehicle_id="TEST-001",
            current_speed=70.0,
            speed_limit=60.0
        )
        
        # 验证有活跃提示
        self.assertIsNotNone(self.alert_manager.get_active_alert())
        
        # 停止提示
        self.alert_manager.stop_alert()
        
        # 验证没有活跃提示
        active = self.alert_manager.get_active_alert()
        if active:
            self.assertFalse(active.is_active)
    
    def test_alert_callback(self):
        """测试提示回调"""
        self.alert_manager.register_alert_callback("test", self.alert_callback)
        
        # 开始提示
        self.alert_manager.start_alert(
            vehicle_id="TEST-001",
            current_speed=70.0,
            speed_limit=60.0
        )
        
        # 验证开始回调被调用
        self.assertEqual(len(self.callback_events), 1)
        self.assertEqual(self.callback_events[0]["event_type"], "start")
        
        # 停止提示
        self.alert_manager.stop_alert()
        
        # 验证结束回调被调用
        self.assertEqual(len(self.callback_events), 2)
        self.assertEqual(self.callback_events[1]["event_type"], "end")


class TestSpeedingAlertSystem(unittest.TestCase):
    """测试超速提示系统整体功能"""
    
    def setUp(self):
        """测试前设置"""
        self.system = SpeedingAlertSystem(
            vehicle_id="TEST-001",
            initial_speed_limit=60.0,
            alert_duration=3.0
        )
    
    def tearDown(self):
        """测试后清理"""
        if self.system.is_running():
            self.system.stop()
    
    def test_system_initialization(self):
        """测试系统初始化"""
        status = self.system.get_system_status()
        
        self.assertEqual(status["vehicle_id"], "TEST-001")
        self.assertEqual(status["speed_limit"], 60.0)
        self.assertFalse(status["running"])
        self.assertFalse(status["connected_to_vehicle"])
    
    def test_system_start(self):
        """测试系统启动"""
        self.assertFalse(self.system.is_running())
        
        result = self.system.start()
        self.assertTrue(result)
        self.assertTrue(self.system.is_running())
        
        status = self.system.get_system_status()
        self.assertTrue(status["running"])
        self.assertTrue(status["connected_to_vehicle"])
    
    def test_system_stop(self):
        """测试系统停止"""
        self.system.start()
        self.assertTrue(self.system.is_running())
        
        result = self.system.stop()
        self.assertTrue(result)
        self.assertFalse(self.system.is_running())
    
    def test_update_speed_limit(self):
        """测试更新速度限制"""
        self.system.update_speed_limit("高速公路", 120.0, False)
        
        status = self.system.get_system_status()
        self.assertEqual(status["speed_limit"], 120.0)
        self.assertEqual(status["speed_limit_location"], "高速公路")
    
    def test_set_simulated_speed(self):
        """测试设置模拟速度"""
        self.system.start()
        self.system.set_simulated_speed(80.0)
        
        status = self.system.get_system_status()
        # 速度应该在80左右（有随机变化）
        self.assertIsNotNone(status["current_speed"])


class TestSystemPerformance(unittest.TestCase):
    """测试系统性能 - 确保1秒内响应"""
    
    def setUp(self):
        """测试前设置"""
        self.system = SpeedingAlertSystem(
            vehicle_id="TEST-001",
            initial_speed_limit=60.0,
            alert_duration=3.0
        )
        self.alert_triggered = False
        self.alert_trigger_time = None
        self.speeding_start_time = None
    
    def tearDown(self):
        """测试后清理"""
        if self.system.is_running():
            self.system.stop()
    
    def alert_callback(self, alert_info, event_type):
        """提示回调函数"""
        if event_type == "start":
            self.alert_triggered = True
            self.alert_trigger_time = time.perf_counter()
    
    def test_response_time_under_one_second(self):
        """
        测试响应时间是否在1秒内
        这是关键性能测试：确保超速发生后1秒内系统能够响应
        """
        # 注册回调
        self.system.alert_manager.register_alert_callback("performance_test", self.alert_callback)
        
        # 启动系统
        self.system.start()
        
        # 等待系统稳定
        time.sleep(0.5)
        
        # 记录超速开始时间
        self.speeding_start_time = time.perf_counter()
        
        # 设置超速速度
        self.system.set_simulated_speed(75.0)  # 超过60的限速
        
        # 等待系统检测到超速并触发提示
        # 最多等待1.5秒，确保我们能检测到是否在1秒内响应
        max_wait_time = 1.5
        start_wait = time.perf_counter()
        
        while not self.alert_triggered and (time.perf_counter() - start_wait) < max_wait_time:
            time.sleep(0.05)  # 50ms检查一次
        
        # 验证提示是否被触发
        self.assertTrue(self.alert_triggered, "系统未在规定时间内检测到超速并触发提示")
        
        # 计算响应时间
        if self.alert_triggered and self.alert_trigger_time:
            response_time = self.alert_trigger_time - self.speeding_start_time
            print(f"\n超速响应时间: {response_time * 1000:.2f} ms")
            
            # 验证响应时间是否小于1秒
            self.assertLess(response_time, 1.0, f"响应时间 ({response_time * 1000:.2f} ms) 超过1秒限制")
            
            # 另外检查系统记录的性能指标
            status = self.system.get_system_status()
            pm = status["performance_metrics"]
            
            print(f"系统记录的平均响应时间: {pm['avg_response_time_ms']:.3f} ms")
            print(f"系统记录的最大响应时间: {pm['max_response_time_ms']:.3f} ms")
            print(f"系统记录的最小响应时间: {pm['min_response_time_ms']:.3f} ms")
            print(f"速度检查次数: {pm['speed_check_count']}")
            print(f"超速检测次数: {pm['overspeed_count']}")
            
            # 系统记录的响应时间也应该远小于1秒
            self.assertLess(pm['avg_response_time_ms'], 100.0, "系统平均响应时间超过100ms")
            self.assertLess(pm['max_response_time_ms'], 500.0, "系统最大响应时间超过500ms")
    
    def test_alert_duration_three_seconds(self):
        """
        测试提示持续时间是否为3秒
        """
        # 注册回调
        alert_events = []
        
        def track_alert_events(alert_info, event_type):
            alert_events.append({
                "event_type": event_type,
                "time": time.perf_counter()
            })
        
        self.system.alert_manager.register_alert_callback("duration_test", track_alert_events)
        
        # 启动系统
        self.system.start()
        
        # 等待系统稳定
        time.sleep(0.5)
        
        # 设置超速速度
        self.system.set_simulated_speed(75.0)
        
        # 等待提示开始和结束
        max_wait_time = 5.0  # 等待最多5秒
        start_wait = time.perf_counter()
        
        while len(alert_events) < 2 and (time.perf_counter() - start_wait) < max_wait_time:
            time.sleep(0.1)
        
        # 验证有开始和结束事件
        self.assertEqual(len(alert_events), 2, "应该有开始和结束两个事件")
        
        start_event = alert_events[0]
        end_event = alert_events[1]
        
        self.assertEqual(start_event["event_type"], "start")
        self.assertEqual(end_event["event_type"], "end")
        
        # 计算持续时间
        duration = end_event["time"] - start_event["time"]
        print(f"\n提示持续时间: {duration:.2f} 秒")
        
        # 验证持续时间接近3秒（允许有0.5秒的误差）
        self.assertAlmostEqual(duration, 3.0, delta=0.5, 
                               msg=f"提示持续时间 ({duration:.2f}秒) 与预期的3秒不符")


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def setUp(self):
        """测试前设置"""
        self.system = SpeedingAlertSystem(
            vehicle_id="TEST-001",
            initial_speed_limit=60.0,
            alert_duration=3.0
        )
    
    def tearDown(self):
        """测试后清理"""
        if self.system.is_running():
            self.system.stop()
    
    def test_speed_exactly_at_limit(self):
        """测试速度刚好等于限速"""
        self.system.start()
        
        # 设置速度刚好等于限速
        self.system.set_simulated_speed(60.0)
        
        # 运行一段时间
        time.sleep(1.0)
        
        # 检查是否有活跃提示（不应该有）
        status = self.system.get_system_status()
        self.assertIsNone(status["active_alert"], "速度等于限速时不应该触发提示")
    
    def test_speed_just_over_limit(self):
        """测试速度刚好超过限速"""
        alert_triggered = []
        
        def alert_callback(alert_info, event_type):
            if event_type == "start":
                alert_triggered.append(True)
        
        self.system.alert_manager.register_alert_callback("edge_test", alert_callback)
        self.system.start()
        
        # 设置速度刚好超过限速
        self.system.set_simulated_speed(60.1)
        
        # 等待系统检测
        time.sleep(0.5)
        
        # 应该触发提示
        self.assertTrue(len(alert_triggered) > 0, "速度超过限速时应该触发提示")
    
    def test_multiple_overspeed_situations(self):
        """测试多次超速情况"""
        alert_count = []
        
        def alert_callback(alert_info, event_type):
            if event_type == "start":
                alert_count.append(alert_info.alert_id)
        
        self.system.alert_manager.register_alert_callback("multiple_test", alert_callback)
        self.system.start()
        
        # 第一次超速
        self.system.set_simulated_speed(70.0)
        time.sleep(0.5)
        
        # 回到限速以下
        self.system.set_simulated_speed(50.0)
        time.sleep(0.5)
        
        # 等待第一次提示结束
        time.sleep(3.0)
        
        # 第二次超速
        self.system.set_simulated_speed(80.0)
        time.sleep(0.5)
        
        # 应该有两次不同的提示
        self.assertGreaterEqual(len(alert_count), 2, "应该触发至少两次提示")
        self.assertNotEqual(alert_count[0], alert_count[1], "每次提示应该有不同的ID")
    
    def test_temporary_speed_limit(self):
        """测试临时限速"""
        limit_changes = []
        
        def limit_callback(speed_limit):
            limit_changes.append(speed_limit)
        
        self.system.limit_monitor.register_limit_change_callback("temp_test", limit_callback)
        
        # 更新为临时限速
        self.system.update_speed_limit("施工路段", 40.0, is_temporary=True)
        
        # 验证限速已更新
        status = self.system.get_system_status()
        self.assertEqual(status["speed_limit"], 40.0)
        self.assertEqual(len(limit_changes), 1)
        self.assertTrue(limit_changes[0].is_temporary)
        
        # 恢复正常限速
        self.system.update_speed_limit("正常路段", 60.0, is_temporary=False)
        
        status = self.system.get_system_status()
        self.assertEqual(status["speed_limit"], 60.0)


def run_performance_tests():
    """
    单独运行性能测试
    """
    print("\n" + "=" * 60)
    print("性能测试 - 确保1秒内响应超速")
    print("=" * 60)
    
    # 创建测试套件
    performance_suite = unittest.TestSuite()
    performance_suite.addTest(TestSystemPerformance('test_response_time_under_one_second'))
    performance_suite.addTest(TestSystemPerformance('test_alert_duration_three_seconds'))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(performance_suite)
    
    # 输出结果
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✓ 性能测试通过！")
        print("  - 系统能够在1秒内响应超速情况")
        print("  - 提示持续时间为3秒")
    else:
        print("✗ 性能测试失败！")
    print("=" * 60)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    import sys
    
    # 检查命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == "--performance":
        # 只运行性能测试
        success = run_performance_tests()
        sys.exit(0 if success else 1)
    else:
        # 运行所有测试
        print("运行所有测试...")
        unittest.main(verbosity=2)
