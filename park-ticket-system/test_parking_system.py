#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停车场管理系统测试脚本
"""

import os
import sys
import tempfile
import shutil
from datetime import datetime, date
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from parking_system import ParkingSystem, VehicleEntry, VehicleExit, DailyRecord


def test_basic_operations():
    """测试基本操作"""
    print("=" * 50)
    print("测试基本操作")
    print("=" * 50)
    
    # 创建临时目录用于测试
    test_dir = tempfile.mkdtemp()
    print(f"测试数据目录: {test_dir}")
    
    try:
        # 创建停车场系统实例
        system = ParkingSystem(data_dir=test_dir)
        
        # 测试 1: 车辆进入
        print("\n1. 测试车辆进入...")
        result1 = system.vehicle_entry("京A12345", 5)
        assert result1['success'], f"车辆进入失败: {result1['message']}"
        print(f"   成功: {result1['message']}")
        print(f"   车牌号: {result1['vehicle_info']['plate_number']}")
        print(f"   进入时间: {result1['vehicle_info']['entry_time']}")
        print(f"   当前车辆数: {result1['current_parked_count']}")
        
        # 测试 2: 另一辆车进入
        result2 = system.vehicle_entry("京B67890", 7)
        assert result2['success'], f"第二辆车进入失败: {result2['message']}"
        print(f"\n2. 第二辆车进入成功: {result2['message']}")
        print(f"   当前车辆数: {result2['current_parked_count']}")
        
        # 测试 3: 重复进入同一辆车
        result3 = system.vehicle_entry("京A12345", 5)
        assert not result3['success'], f"重复进入应该失败: {result3['message']}"
        print(f"\n3. 重复进入检测成功: {result3['message']}")
        
        # 测试 4: 查询当前状态
        print("\n4. 查询当前状态...")
        status = system.get_parking_status()
        print(f"   查询时间: {status['timestamp']}")
        print(f"   当前车辆数: {status['current_parked_count']}")
        assert status['current_parked_count'] == 2, f"当前车辆数不正确: {status['current_parked_count']}"
        
        # 测试 5: 车辆离开
        print("\n5. 测试车辆离开...")
        result5 = system.vehicle_exit("京A12345")
        assert result5['success'], f"车辆离开失败: {result5['message']}"
        print(f"   成功: {result5['message']}")
        print(f"   车牌号: {result5['vehicle_info']['plate_number']}")
        print(f"   进入时间: {result5['vehicle_info']['entry_time']}")
        print(f"   离开时间: {result5['vehicle_info']['exit_time']}")
        print(f"   停留时长: {result5['vehicle_info']['duration']}")
        print(f"   当前车辆数: {result5['current_parked_count']}")
        
        # 测试 6: 离开不存在的车辆
        result6 = system.vehicle_exit("京C11111")
        assert not result6['success'], f"离开不存在的车辆应该失败: {result6['message']}"
        print(f"\n6. 离开不存在车辆检测成功: {result6['message']}")
        
        # 测试 7: 查询今日记录
        print("\n7. 查询今日记录...")
        records = system.get_daily_records()
        print(f"   日期: {records['date']}")
        print(f"   总进入车辆数: {records['total_entries']}")
        print(f"   总离开车辆数: {records['total_exits']}")
        print(f"   结束时停放车辆数: {records['current_parked_at_end']}")
        assert records['total_entries'] == 2, f"总进入车辆数不正确: {records['total_entries']}"
        assert records['total_exits'] == 1, f"总离开车辆数不正确: {records['total_exits']}"
        
        # 测试 8: 查询车辆历史记录
        print("\n8. 查询车辆历史记录...")
        history = system.get_vehicle_history("京A12345")
        print(f"   车牌号: {history['plate_number']}")
        print(f"   总记录数: {history['total_records']}")
        assert history['total_records'] >= 2, f"历史记录数不正确: {history['total_records']}"
        
        # 测试 9: 列出所有有记录的日期
        print("\n9. 列出所有有记录的日期...")
        dates = system.list_available_dates()
        print(f"   有记录的日期数: {len(dates)}")
        assert len(dates) >= 1, "应该至少有一个日期有记录"
        
        print("\n" + "=" * 50)
        print("所有测试通过！")
        print("=" * 50)
        
    finally:
        # 清理临时目录
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n已清理测试数据目录: {test_dir}")


def test_data_persistence():
    """测试数据持久性"""
    print("\n" + "=" * 50)
    print("测试数据持久性")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp()
    print(f"测试数据目录: {test_dir}")
    
    try:
        # 第一次实例化并添加数据
        print("\n1. 第一次实例化并添加车辆...")
        system1 = ParkingSystem(data_dir=test_dir)
        system1.vehicle_entry("京D22222", 4)
        system1.vehicle_entry("京E33333", 5)
        
        status1 = system1.get_parking_status()
        print(f"   第一次实例化后车辆数: {status1['current_parked_count']}")
        assert status1['current_parked_count'] == 2
        
        # 验证数据文件是否创建
        data_files = list(Path(test_dir).glob("parking_*.json"))
        print(f"   创建的数据文件数: {len(data_files)}")
        assert len(data_files) == 1, f"应该创建 1 个数据文件，实际: {len(data_files)}"
        
        # 第二次实例化，验证数据是否持久化
        print("\n2. 第二次实例化，验证数据持久性...")
        system2 = ParkingSystem(data_dir=test_dir)
        
        status2 = system2.get_parking_status()
        print(f"   第二次实例化后车辆数: {status2['current_parked_count']}")
        assert status2['current_parked_count'] == 2, f"数据未持久化，车辆数: {status2['current_parked_count']}"
        
        # 一辆车离开
        print("\n3. 一辆车离开...")
        system2.vehicle_exit("京D22222")
        
        status3 = system2.get_parking_status()
        print(f"   车辆离开后车辆数: {status3['current_parked_count']}")
        assert status3['current_parked_count'] == 1
        
        # 第三次实例化，验证离开记录也被持久化
        print("\n4. 第三次实例化，验证离开记录持久性...")
        system3 = ParkingSystem(data_dir=test_dir)
        
        status4 = system3.get_parking_status()
        print(f"   第三次实例化后车辆数: {status4['current_parked_count']}")
        assert status4['current_parked_count'] == 1, f"离开记录未持久化，车辆数: {status4['current_parked_count']}"
        
        # 验证记录
        records = system3.get_daily_records()
        print(f"   总进入车辆数: {records['total_entries']}")
        print(f"   总离开车辆数: {records['total_exits']}")
        assert records['total_entries'] == 2
        assert records['total_exits'] == 1
        
        print("\n" + "=" * 50)
        print("数据持久性测试通过！")
        print("=" * 50)
        
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n已清理测试数据目录: {test_dir}")


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 50)
    print("测试边界情况")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp()
    print(f"测试数据目录: {test_dir}")
    
    try:
        system = ParkingSystem(data_dir=test_dir)
        
        # 测试 1: 空停车场状态
        print("\n1. 测试空停车场状态...")
        status = system.get_parking_status()
        print(f"   空停车场车辆数: {status['current_parked_count']}")
        assert status['current_parked_count'] == 0
        assert len(status['parked_vehicles']) == 0
        
        # 测试 2: 空停车场查询记录
        print("\n2. 测试空停车场查询记录...")
        records = system.get_daily_records()
        print(f"   空停车场总进入车辆数: {records['total_entries']}")
        print(f"   空停车场总离开车辆数: {records['total_exits']}")
        assert records['total_entries'] == 0
        assert records['total_exits'] == 0
        
        # 测试 3: 查询不存在车辆的历史
        print("\n3. 测试查询不存在车辆的历史...")
        history = system.get_vehicle_history("不存在的车牌号")
        print(f"   不存在车辆的历史记录数: {history['total_records']}")
        assert history['total_records'] == 0
        
        # 测试 4: 查询未来日期的记录
        print("\n4. 测试查询未来日期的记录...")
        future_date = "2099-12-31"
        future_records = system.get_daily_records(future_date)
        print(f"   未来日期记录数: 进入={future_records['total_entries']}, 离开={future_records['total_exits']}")
        assert future_records['total_entries'] == 0
        assert future_records['total_exits'] == 0
        assert future_records['date'] == future_date
        
        # 测试 5: 多辆车连续进出
        print("\n5. 测试多辆车连续进出...")
        system.vehicle_entry("京F44444", 5)
        system.vehicle_entry("京G55555", 7)
        system.vehicle_entry("京H66666", 4)
        system.vehicle_exit("京G55555")
        system.vehicle_entry("京I77777", 6)
        system.vehicle_exit("京F44444")
        
        status = system.get_parking_status()
        print(f"   连续操作后车辆数: {status['current_parked_count']}")
        assert status['current_parked_count'] == 2  # 京H66666 和 京I77777
        
        records = system.get_daily_records()
        print(f"   总进入: {records['total_entries']}, 总离开: {records['total_exits']}")
        assert records['total_entries'] == 4
        assert records['total_exits'] == 2
        
        # 验证停放的车辆
        parked_plates = [v['plate_number'] for v in status['parked_vehicles']]
        print(f"   当前停放车辆: {parked_plates}")
        assert "京H66666" in parked_plates
        assert "京I77777" in parked_plates
        assert "京F44444" not in parked_plates
        assert "京G55555" not in parked_plates
        
        print("\n" + "=" * 50)
        print("边界情况测试通过！")
        print("=" * 50)
        
    finally:
        if os.path.exists(test_dir):
            shutil.rmtree(test_dir)
            print(f"\n已清理测试数据目录: {test_dir}")


if __name__ == "__main__":
    print("=" * 50)
    print("开始停车场管理系统测试")
    print("=" * 50)
    print(f"测试时间: {datetime.now().isoformat()}")
    
    try:
        test_basic_operations()
        test_data_persistence()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("所有测试全部通过！")
        print("=" * 50)
        
    except AssertionError as e:
        print(f"\n测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
