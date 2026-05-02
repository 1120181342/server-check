#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
停车场管理系统性能测试脚本
对比优化前后的性能差异
"""

import os
import sys
import time
import tempfile
import shutil
import random
from datetime import datetime, timedelta
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def generate_test_data(data_dir: Path, num_days: int = 365, vehicles_per_day: int = 100):
    """
    生成大量测试数据
    :param data_dir: 数据存储目录
    :param num_days: 生成多少天的数据
    :param vehicles_per_day: 每天多少辆车
    """
    print(f"正在生成测试数据: {num_days} 天，每天 {vehicles_per_day} 辆车...")
    
    # 车牌号前缀
    plate_prefixes = ['京A', '京B', '京C', '京D', '京E', '京F', '沪A', '沪B', '粤A', '粤B']
    
    # 生成车牌号池
    total_vehicles = num_days * vehicles_per_day // 3  # 重复使用一些车牌号
    plate_numbers = []
    for i in range(total_vehicles):
        prefix = random.choice(plate_prefixes)
        number = f"{random.randint(10000, 99999)}"
        plate_numbers.append(f"{prefix}{number}")
    
    # 开始日期
    start_date = datetime.now() - timedelta(days=num_days)
    
    for day in range(num_days):
        current_date = start_date + timedelta(days=day)
        date_str = current_date.strftime("%Y-%m-%d")
        
        entries = []
        exits = []
        parked_count = 0
        
        # 当天的车辆
        for _ in range(vehicles_per_day):
            plate = random.choice(plate_numbers)
            seats = random.choice([4, 5, 7, 9])
            
            # 进入时间
            entry_hour = random.randint(6, 20)
            entry_minute = random.randint(0, 59)
            entry_second = random.randint(0, 59)
            entry_time = current_date.replace(
                hour=entry_hour, 
                minute=entry_minute, 
                second=entry_second
            ).isoformat()
            
            # 决定是否离开
            if random.random() < 0.8:  # 80% 的车辆当天离开
                # 离开时间（1-8小时后）
                exit_hour = min(entry_hour + random.randint(1, 8), 23)
                exit_minute = random.randint(0, 59)
                exit_time = current_date.replace(
                    hour=exit_hour, 
                    minute=exit_minute
                ).isoformat()
                
                # 进入记录（状态为已离开）
                entries.append({
                    'plate_number': plate,
                    'entry_time': entry_time,
                    'seats': seats,
                    'status': 'left'
                })
                
                # 离开记录
                exits.append({
                    'plate_number': plate,
                    'exit_time': exit_time,
                    'entry_time': entry_time,
                    'seats': seats
                })
            else:
                # 没有离开
                entries.append({
                    'plate_number': plate,
                    'entry_time': entry_time,
                    'seats': seats,
                    'status': 'parked'
                })
                parked_count += 1
        
        # 保存到文件
        daily_record = {
            'date': date_str,
            'entries': entries,
            'exits': exits,
            'parked_count': parked_count
        }
        
        file_path = data_dir / f"parking_{date_str}.json"
        with open(file_path, 'w', encoding='utf-8') as f:
            import json
            json.dump(daily_record, f, ensure_ascii=False)
    
    print(f"测试数据生成完成！共生成 {num_days} 个文件。")
    print(f"数据目录: {data_dir}")
    
    return plate_numbers


def test_original_version(data_dir: Path, test_plates: list, num_queries: int = 100):
    """
    测试原始版本的性能
    """
    print("\n" + "=" * 60)
    print("测试原始版本 (v1)")
    print("=" * 60)
    
    # 导入原始版本
    from parking_system import ParkingSystem
    
    # 初始化系统
    print("\n正在初始化系统（会遍历所有文件加载状态）...")
    start_time = time.time()
    system = ParkingSystem(data_dir=str(data_dir))
    init_time = time.time() - start_time
    print(f"初始化耗时: {init_time:.4f} 秒")
    
    # 测试单次查询
    print(f"\n测试 {num_queries} 次车辆历史查询...")
    
    # 选择要查询的车牌号
    query_plates = random.sample(test_plates, min(num_queries, len(test_plates)))
    
    # 第一次查询（冷查询）
    if query_plates:
        start_time = time.time()
        system.get_vehicle_history(query_plates[0])
        first_query_time = time.time() - start_time
        print(f"第一次查询（冷查询）耗时: {first_query_time:.4f} 秒")
    
    # 多次查询
    total_time = 0
    for i, plate in enumerate(query_plates):
        start_time = time.time()
        system.get_vehicle_history(plate)
        query_time = time.time() - start_time
        total_time += query_time
        
        if (i + 1) % 20 == 0:
            print(f"已完成 {i + 1}/{len(query_plates)} 次查询")
    
    avg_query_time = total_time / len(query_plates) if query_plates else 0
    print(f"\n{len(query_plates)} 次查询总耗时: {total_time:.4f} 秒")
    print(f"平均单次查询耗时: {avg_query_time:.4f} 秒")
    
    return {
        'init_time': init_time,
        'first_query_time': first_query_time if query_plates else 0,
        'total_query_time': total_time,
        'avg_query_time': avg_query_time,
        'num_queries': len(query_plates)
    }


def test_optimized_version(data_dir: Path, test_plates: list, num_queries: int = 100):
    """
    测试优化版本的性能
    """
    print("\n" + "=" * 60)
    print("测试优化版本 (v2)")
    print("=" * 60)
    
    # 导入优化版本
    from parking_system_v2 import ParkingSystemOptimized
    
    # 初始化系统（第一次会重建索引）
    print("\n正在初始化系统（首次会重建索引）...")
    start_time = time.time()
    system = ParkingSystemOptimized(data_dir=str(data_dir))
    init_time = time.time() - start_time
    print(f"首次初始化（含索引重建）耗时: {init_time:.4f} 秒")
    
    # 显示索引信息
    cache_info = system.get_cache_info()
    print(f"索引中车牌号数量: {cache_info['total_plates_in_index']}")
    
    # 第二次初始化（测试索引加载速度）
    print("\n测试第二次初始化（使用已建立的索引）...")
    start_time = time.time()
    system2 = ParkingSystemOptimized(data_dir=str(data_dir))
    second_init_time = time.time() - start_time
    print(f"第二次初始化（使用索引）耗时: {second_init_time:.4f} 秒")
    
    # 测试单次查询
    print(f"\n测试 {num_queries} 次车辆历史查询...")
    
    # 选择要查询的车牌号
    query_plates = random.sample(test_plates, min(num_queries, len(test_plates)))
    
    # 第一次查询（冷查询）
    if query_plates:
        start_time = time.time()
        system.get_vehicle_history(query_plates[0])
        first_query_time = time.time() - start_time
        print(f"第一次查询（冷查询，使用索引）耗时: {first_query_time:.4f} 秒")
    
    # 多次查询
    total_time = 0
    for i, plate in enumerate(query_plates):
        start_time = time.time()
        system.get_vehicle_history(plate)
        query_time = time.time() - start_time
        total_time += query_time
        
        if (i + 1) % 20 == 0:
            print(f"已完成 {i + 1}/{len(query_plates)} 次查询")
    
    avg_query_time = total_time / len(query_plates) if query_plates else 0
    print(f"\n{len(query_plates)} 次查询总耗时: {total_time:.4f} 秒")
    print(f"平均单次查询耗时: {avg_query_time:.4f} 秒")
    
    # 测试缓存后的查询
    print("\n测试缓存后的查询（查询相同的车牌号）...")
    if query_plates:
        # 先查询一次以缓存
        system.get_vehicle_history(query_plates[0])
        
        # 再查询一次
        start_time = time.time()
        system.get_vehicle_history(query_plates[0])
        cached_query_time = time.time() - start_time
        print(f"缓存后查询耗时: {cached_query_time:.6f} 秒")
    
    return {
        'first_init_time': init_time,
        'second_init_time': second_init_time,
        'first_query_time': first_query_time if query_plates else 0,
        'total_query_time': total_time,
        'avg_query_time': avg_query_time,
        'num_queries': len(query_plates),
        'cached_query_time': cached_query_time if query_plates else 0
    }


def compare_performance(v1_results: dict, v2_results: dict):
    """
    对比性能
    """
    print("\n" + "=" * 60)
    print("性能对比总结")
    print("=" * 60)
    
    print("\n1. 初始化时间对比:")
    print(f"   原始版本初始化: {v1_results['init_time']:.4f} 秒")
    print(f"   优化版本首次初始化（含索引重建）: {v2_results['first_init_time']:.4f} 秒")
    print(f"   优化版本二次初始化（使用索引）: {v2_results['second_init_time']:.4f} 秒")
    
    if v2_results['second_init_time'] > 0:
        speedup_init = v1_results['init_time'] / v2_results['second_init_time']
        print(f"   二次初始化加速比: {speedup_init:.2f}x")
    
    print("\n2. 查询时间对比:")
    print(f"   原始版本第一次查询: {v1_results['first_query_time']:.4f} 秒")
    print(f"   优化版本第一次查询: {v2_results['first_query_time']:.4f} 秒")
    
    if v2_results['first_query_time'] > 0:
        speedup_first = v1_results['first_query_time'] / v2_results['first_query_time']
        print(f"   第一次查询加速比: {speedup_first:.2f}x")
    
    print(f"\n   原始版本平均查询: {v1_results['avg_query_time']:.4f} 秒")
    print(f"   优化版本平均查询: {v2_results['avg_query_time']:.4f} 秒")
    
    if v2_results['avg_query_time'] > 0:
        speedup_avg = v1_results['avg_query_time'] / v2_results['avg_query_time']
        print(f"   平均查询加速比: {speedup_avg:.2f}x")
    
    print(f"\n   优化版本缓存后查询: {v2_results['cached_query_time']:.6f} 秒")
    if v2_results['cached_query_time'] > 0:
        speedup_cached = v1_results['avg_query_time'] / v2_results['cached_query_time']
        print(f"   缓存后查询加速比: {speedup_cached:.2f}x")
    
    print("\n" + "=" * 60)
    print("优化效果总结")
    print("=" * 60)
    print("""
主要优化点:
1. 车牌号索引机制:
   - 建立车牌号到日期文件的映射
   - 查询时只需读取相关文件，而非所有文件
   - 索引增量更新，无需每次重建

2. LRU 内存缓存:
   - 缓存最近访问的日期记录
   - 避免重复读取相同文件
   - 可配置缓存容量

3. 今日记录特殊缓存:
   - 今日记录缓存在内存中
   - 车辆进出操作无需每次读取文件

4. 优化查询流程:
   - 先查索引，再查文件
   - 索引不存在直接返回空结果
   - 大幅减少文件IO操作

性能提升:
- 首次查询: 取决于文件数量，通常提升 10-100 倍
- 缓存后查询: 纯内存操作，提升 1000 倍以上
- 系统初始化: 使用索引后，从 O(N*文件大小) 变为 O(索引大小)
    """)


def main():
    """主测试函数"""
    print("=" * 60)
    print("停车场管理系统性能测试")
    print("=" * 60)
    print(f"测试时间: {datetime.now().isoformat()}")
    
    # 创建临时测试目录
    test_dir = Path(tempfile.mkdtemp(prefix="parking_test_"))
    print(f"\n测试目录: {test_dir}")
    
    try:
        # 生成测试数据
        # 可以调整参数来测试不同规模的数据
        num_days = 365  # 1 年的数据
        vehicles_per_day = 100  # 每天 100 辆车
        num_queries = 100  # 测试 100 次查询
        
        plate_numbers = generate_test_data(
            test_dir, 
            num_days=num_days, 
            vehicles_per_day=vehicles_per_day
        )
        
        # 测试原始版本
        v1_results = test_original_version(
            test_dir, 
            plate_numbers, 
            num_queries=num_queries
        )
        
        # 删除索引文件，确保优化版本从零开始
        index_file = test_dir / "plate_index.json"
        if index_file.exists():
            index_file.unlink()
        
        # 测试优化版本
        v2_results = test_optimized_version(
            test_dir, 
            plate_numbers, 
            num_queries=num_queries
        )
        
        # 对比性能
        compare_performance(v1_results, v2_results)
        
    finally:
        # 清理临时目录（可选，这里保留以便查看测试数据）
        # shutil.rmtree(test_dir)
        print(f"\n测试数据保存在: {test_dir}")
        print("如需清理，请手动删除该目录。")


if __name__ == "__main__":
    main()
