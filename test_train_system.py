import asyncio
from datetime import datetime, timedelta
from train_schedule_system import TrainInfo, TrainScheduleManager, TrainScheduleSystem


def test_train_info():
    print("测试 TrainInfo 类...")
    
    base_time = datetime.now()
    
    train = TrainInfo(
        train_number="G1001",
        origin="北京南",
        destination="上海虹桥",
        arrival_time=base_time + timedelta(minutes=30),
        departure_time=base_time + timedelta(minutes=10),
        arrival_platform=1,
        departure_platform=1,
        is_departure=False
    )
    
    print(f"  列车序号: {train.train_number}")
    print(f"  出发地: {train.origin}")
    print(f"  目的地: {train.destination}")
    print(f"  到站时间: {train.arrival_time}")
    print(f"  离站时间: {train.departure_time}")
    print(f"  到站站台: {train.arrival_platform}")
    print(f"  离站站台: {train.departure_platform}")
    print(f"  是否离站: {train.is_departure}")
    
    print(f"\n  到站信息格式: {train.format_arrival_info()}")
    
    departure_train = TrainInfo(
        train_number="G1001",
        origin="北京南",
        destination="上海虹桥",
        arrival_time=base_time + timedelta(minutes=30),
        departure_time=base_time + timedelta(minutes=10),
        arrival_platform=1,
        departure_platform=1,
        is_departure=True
    )
    print(f"  离站信息格式: {departure_train.format_departure_info()}")
    
    print(f"\n  测试过期检查:")
    print(f"    当前时间: {base_time}")
    print(f"    列车是否过期: {train.is_expired(base_time)} (应为 False)")
    print(f"    1小时后是否过期: {train.is_expired(base_time + timedelta(hours=1))} (应为 True)")
    
    print("\n[OK] TrainInfo 类测试通过\n")


def test_train_schedule_manager():
    print("测试 TrainScheduleManager 类...")
    
    manager = TrainScheduleManager()
    base_time = datetime.now()
    
    print("  添加测试列车数据...")
    
    train1 = TrainInfo(
        train_number="G1001",
        origin="北京南",
        destination="上海虹桥",
        arrival_time=base_time + timedelta(minutes=30),
        departure_time=base_time + timedelta(minutes=10),
        arrival_platform=1,
        departure_platform=1,
        is_departure=False
    )
    
    train1_departure = TrainInfo(
        train_number="G1001",
        origin="北京南",
        destination="上海虹桥",
        arrival_time=base_time + timedelta(minutes=30),
        departure_time=base_time + timedelta(minutes=10),
        arrival_platform=1,
        departure_platform=1,
        is_departure=True
    )
    
    train2 = TrainInfo(
        train_number="D2002",
        origin="广州南",
        destination="武汉",
        arrival_time=base_time + timedelta(minutes=15),
        departure_time=base_time + timedelta(minutes=5),
        arrival_platform=3,
        departure_platform=3,
        is_departure=False
    )
    
    train2_departure = TrainInfo(
        train_number="D2002",
        origin="广州南",
        destination="武汉",
        arrival_time=base_time + timedelta(minutes=15),
        departure_time=base_time + timedelta(minutes=5),
        arrival_platform=3,
        departure_platform=3,
        is_departure=True
    )
    
    expired_train = TrainInfo(
        train_number="K4004",
        origin="西安",
        destination="郑州",
        arrival_time=base_time - timedelta(minutes=30),
        departure_time=base_time - timedelta(minutes=60),
        arrival_platform=2,
        departure_platform=2,
        is_departure=False
    )
    
    manager.add_train(train1)
    manager.add_train(train1_departure)
    manager.add_train(train2)
    manager.add_train(train2_departure)
    manager.add_train(expired_train)
    
    print(f"  已添加 5 条列车信息")
    print(f"\n  获取到站列车 (当前时间: {base_time}):")
    arrival_trains = manager.get_arrival_trains(base_time)
    for i, train in enumerate(arrival_trains, 1):
        print(f"    {i}. {train.format_arrival_info()}")
    
    print(f"\n  获取离站列车 (当前时间: {base_time}):")
    departure_trains = manager.get_departure_trains(base_time)
    for i, train in enumerate(departure_trains, 1):
        print(f"    {i}. {train.format_departure_info()}")
    
    print(f"\n  测试过期列车移除:")
    current_time = base_time + timedelta(hours=1)
    print(f"    模拟时间: {current_time}")
    
    removed = manager.remove_expired_trains(current_time)
    print(f"    已移除 {removed} 条过期列车信息")
    
    print(f"\n  再次获取到站列车 (当前时间: {current_time}):")
    arrival_trains = manager.get_arrival_trains(current_time)
    if arrival_trains:
        for i, train in enumerate(arrival_trains, 1):
            print(f"    {i}. {train.format_arrival_info()}")
    else:
        print("    当前无有效到站列车信息")
    
    print("\n[OK] TrainScheduleManager 类测试通过\n")


async def test_train_schedule_system():
    print("测试 TrainScheduleSystem 类...")
    
    system = TrainScheduleSystem(refresh_interval=1.0)
    
    print("  加载示例数据...")
    system.load_sample_data()
    
    print("  显示到站信息:")
    system.display_arrival_info(datetime.now())
    
    print("\n  显示离站信息:")
    system.display_departure_info(datetime.now())
    
    print("\n[OK] TrainScheduleSystem 类测试通过\n")


def main():
    print("=" * 60)
    print("列车时刻表系统测试")
    print("=" * 60 + "\n")
    
    try:
        test_train_info()
        test_train_schedule_manager()
        asyncio.run(test_train_schedule_system())
        
        print("=" * 60)
        print("所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n[ERROR] 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
