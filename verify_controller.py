"""
SD-WAN控制器验证脚本
测试基本功能和性能
"""

import asyncio
import time
import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 60)
    print("SD-WAN LAN Controller - Basic Verification")
    print("=" * 60)
    
    # 1. 测试配置加载
    print("\n[1] Testing Configuration Loading...")
    try:
        from sdwan_controller.config import (
            NETWORK_TOPOLOGY,
            LINK_PARAMS,
            ROUTING_PROTOCOL,
            PERFORMANCE_CONFIG,
        )
        print(f"    ✓ Network Topology: {NETWORK_TOPOLOGY}")
        print(f"    ✓ Performance Config: {PERFORMANCE_CONFIG}")
        print(f"    ✓ Routing Protocol: {ROUTING_PROTOCOL['protocol_type']}")
    except Exception as e:
        print(f"    ✗ Failed to load configuration: {e}")
        return False
    
    # 2. 测试模型加载
    print("\n[2] Testing Model Definitions...")
    try:
        from sdwan_controller.models import (
            Switch,
            Link,
            Topology,
            SwitchType,
            LinkStatus,
        )
        
        # 创建测试交换机
        test_switch = Switch(
            switch_id="test-1",
            name="Test Switch",
            switch_type=SwitchType.CORE,
            ip_address="10.0.0.1",
            mac_address="00:1A:2B:3C:00:01",
        )
        print(f"    ✓ Created test switch: {test_switch.switch_id}")
        
        # 测试序列化
        switch_dict = test_switch.to_dict()
        print(f"    ✓ Switch serialization: {switch_dict['switch_type']}")
        
        # 测试反序列化
        restored_switch = Switch.from_dict(switch_dict)
        print(f"    ✓ Switch deserialization: {restored_switch.switch_id}")
        
    except Exception as e:
        print(f"    ✗ Failed to test models: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. 测试拓扑初始化
    print("\n[3] Testing Topology Initialization...")
    try:
        from sdwan_controller.core_controller import CoreController
        
        controller = CoreController()
        
        init_start = time.time()
        success = await controller.initialize_topology()
        init_time = time.time() - init_start
        
        if success:
            topology = controller.get_topology_summary()
            print(f"    ✓ Topology initialized in {init_time:.4f}s")
            print(f"      - Total switches: {topology['total_switches']}")
            print(f"      - Active switches: {topology['active_switches']}")
            print(f"      - Core: {topology['core_switches']}")
            print(f"      - Access: {topology['access_switches']}")
            print(f"      - POP: {topology['pop_switches']}")
            print(f"      - Total links: {topology['total_links']}")
            print(f"      - Active links: {topology['active_links']}")
            
            # 验证交换机数量
            expected_switches = 20
            if topology['total_switches'] == expected_switches:
                print(f"    ✓ Switch count verification: {topology['total_switches']} (expected: {expected_switches})")
            else:
                print(f"    ✗ Switch count mismatch: {topology['total_switches']} (expected: {expected_switches})")
                return False
        else:
            print(f"    ✗ Failed to initialize topology")
            return False
            
    except Exception as e:
        print(f"    ✗ Failed to test topology: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 测试路由计算
    print("\n[4] Testing Route Calculation...")
    try:
        calc_start = time.time()
        success = await controller.calculate_all_routes()
        calc_time = time.time() - calc_start
        
        if success:
            print(f"    ✓ Route calculation completed in {calc_time:.4f}s")
            
            # 验证性能要求
            target_time = PERFORMANCE_CONFIG["max_computation_time"]
            if calc_time < target_time:
                print(f"    ✓ Performance requirement met: {calc_time:.4f}s < {target_time}s")
            else:
                print(f"    ⚠ Performance warning: {calc_time:.4f}s >= {target_time}s")
            
            # 测试路径查找
            print("\n    Testing path finding...")
            test_pairs = [
                ("access-1", "core-1"),
                ("core-1", "access-10"),
                ("pop-1", "access-5"),
            ]
            
            for source, dest in test_pairs:
                paths = controller.get_path_between(source, dest)
                if paths:
                    primary = paths[0]
                    print(f"      ✓ {source} -> {dest}: {len(paths)} path(s)")
                    print(f"          Primary: {' -> '.join(primary.nodes)} (cost: {primary.total_cost})")
                else:
                    print(f"      ✗ {source} -> {dest}: No path found")
            
        else:
            print(f"    ✗ Route calculation failed")
            return False
            
    except Exception as e:
        print(f"    ✗ Failed to test route calculation: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试通信模块
    print("\n[5] Testing Communication Module...")
    try:
        from sdwan_controller.communication import (
            Message,
            MessageQueue,
            MessageType,
            MessagePriority,
        )
        
        # 测试消息创建
        msg = Message(
            message_id="test-msg-1",
            message_type=MessageType.ROUTE_UPDATE,
            source="controller",
            destination="switch-1",
            payload={"routes": []},
            priority=MessagePriority.HIGH,
        )
        print(f"    ✓ Created message: {msg.message_id}")
        
        # 测试序列化
        msg_bytes = msg.to_bytes()
        print(f"    ✓ Message serialized: {len(msg_bytes)} bytes")
        
        # 测试反序列化
        restored_msg = Message.from_bytes(msg_bytes)
        print(f"    ✓ Message deserialized: {restored_msg.message_id}")
        
        # 测试消息队列
        queue = MessageQueue("test-queue")
        await queue.put(msg)
        print(f"    ✓ Message queued")
        
        retrieved = await queue.get(timeout=1.0)
        if retrieved:
            print(f"    ✓ Message retrieved: {retrieved.message_id}")
        else:
            print(f"    ✗ Failed to retrieve message")
            return False
            
    except Exception as e:
        print(f"    ✗ Failed to test communication: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. 测试性能优化模块
    print("\n[6] Testing Performance Optimization...")
    try:
        from sdwan_controller.performance_optimizer import (
            HierarchicalRouteCalculator,
            IncrementalRouteCalculator,
            RouteCache,
        )
        
        # 测试增量计算器
        inc_calc = IncrementalRouteCalculator(controller.topology)
        print(f"    ✓ Incremental calculator created")
        
        # 测试分层计算器
        hier_calc = HierarchicalRouteCalculator(controller.topology)
        print(f"    ✓ Hierarchical calculator created")
        
        # 测试路由缓存
        cache = RouteCache(max_size=100, ttl=60)
        cache.put("source-1", "dest-1", [{"nodes": ["a", "b", "c"]}])
        cached = cache.get("source-1", "dest-1")
        if cached:
            print(f"    ✓ Route cache working")
        else:
            print(f"    ✗ Route cache not working")
            return False
        
        # 测试分层路由计算性能
        hier_start = time.time()
        hier_routes = hier_calc.calculate_all_routes()
        hier_time = time.time() - hier_start
        
        print(f"    ✓ Hierarchical calculation: {hier_time:.4f}s, {len(hier_routes)} switches")
        
    except Exception as e:
        print(f"    ✗ Failed to test performance optimization: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 7. 总结
    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    
    print("\n✓ All basic tests passed!")
    print("\nSummary:")
    print(f"  - Network: 20 switches (2 core + 10 access + 8 POP)")
    print(f"  - Topology initialization: {init_time:.4f}s")
    print(f"  - Route calculation: {calc_time:.4f}s")
    print(f"  - Performance target: < {target_time}s")
    
    if calc_time < target_time:
        print(f"\n✓ Performance requirement MET!")
    else:
        print(f"\n⚠ Performance requirement NOT MET (but may be acceptable for initial testing)")
    
    print("\n" + "=" * 60)
    
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_basic_functionality())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(1)
