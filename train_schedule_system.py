import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass, field
import heapq


@dataclass(order=True)
class TrainInfo:
    train_number: str = field(compare=False)
    origin: str = field(compare=False)
    destination: str = field(compare=False)
    arrival_time: datetime = field(compare=True)
    departure_time: datetime = field(compare=False)
    arrival_platform: int = field(compare=False)
    departure_platform: int = field(compare=False)
    is_departure: bool = field(default=False, compare=False)
    
    def is_expired(self, current_time: datetime) -> bool:
        if self.is_departure:
            return current_time > self.departure_time
        return current_time > self.arrival_time
    
    def format_arrival_info(self) -> str:
        return (
            f"列车序号: {self.train_number}, "
            f"出发地: {self.origin}, "
            f"到站时间: {self.arrival_time.strftime('%H:%M:%S')}, "
            f"到站站台: {self.arrival_platform}"
        )
    
    def format_departure_info(self) -> str:
        return (
            f"列车序号: {self.train_number}, "
            f"目的地: {self.destination}, "
            f"离站时间: {self.departure_time.strftime('%H:%M:%S')}, "
            f"离站站台: {self.departure_platform}"
        )


class TrainScheduleManager:
    def __init__(self):
        self.arrival_trains: List[TrainInfo] = []
        self.departure_trains: List[TrainInfo] = []
        self.train_lookup: Dict[str, TrainInfo] = {}
        
    def add_train(self, train: TrainInfo) -> bool:
        if train.train_number in self.train_lookup:
            return False
        
        self.train_lookup[train.train_number] = train
        
        if train.is_departure:
            heapq.heappush(self.departure_trains, train)
        else:
            heapq.heappush(self.arrival_trains, train)
        
        return True
    
    def remove_expired_trains(self, current_time: datetime) -> int:
        removed_count = 0
        
        while self.arrival_trains and self.arrival_trains[0].is_expired(current_time):
            expired_train = heapq.heappop(self.arrival_trains)
            if expired_train.train_number in self.train_lookup:
                del self.train_lookup[expired_train.train_number]
            removed_count += 1
        
        while self.departure_trains and self.departure_trains[0].is_expired(current_time):
            expired_train = heapq.heappop(self.departure_trains)
            if expired_train.train_number in self.train_lookup:
                del self.train_lookup[expired_train.train_number]
            removed_count += 1
        
        return removed_count
    
    def get_arrival_trains(self, current_time: datetime, limit: int = 10) -> List[TrainInfo]:
        self.remove_expired_trains(current_time)
        
        valid_trains = []
        for train in self.arrival_trains:
            if not train.is_expired(current_time):
                valid_trains.append(train)
            if len(valid_trains) >= limit:
                break
        
        return sorted(valid_trains, key=lambda x: x.arrival_time)
    
    def get_departure_trains(self, current_time: datetime, limit: int = 10) -> List[TrainInfo]:
        self.remove_expired_trains(current_time)
        
        valid_trains = []
        for train in self.departure_trains:
            if not train.is_expired(current_time):
                valid_trains.append(train)
            if len(valid_trains) >= limit:
                break
        
        return sorted(valid_trains, key=lambda x: x.departure_time)


class TrainScheduleSystem:
    def __init__(self, refresh_interval: float = 1.0):
        self.manager = TrainScheduleManager()
        self.refresh_interval = refresh_interval
        self.running = False
        self.display_limit = 10
        
    def load_sample_data(self):
        base_time = datetime.now()
        
        sample_trains = [
            TrainInfo(
                train_number="G1001",
                origin="北京南",
                destination="上海虹桥",
                arrival_time=base_time + timedelta(minutes=10),
                departure_time=base_time + timedelta(minutes=5),
                arrival_platform=1,
                departure_platform=1,
                is_departure=False
            ),
            TrainInfo(
                train_number="G1001",
                origin="北京南",
                destination="上海虹桥",
                arrival_time=base_time + timedelta(minutes=10),
                departure_time=base_time + timedelta(minutes=5),
                arrival_platform=1,
                departure_platform=1,
                is_departure=True
            ),
            TrainInfo(
                train_number="D2002",
                origin="广州南",
                destination="武汉",
                arrival_time=base_time + timedelta(minutes=15),
                departure_time=base_time + timedelta(minutes=8),
                arrival_platform=3,
                departure_platform=3,
                is_departure=False
            ),
            TrainInfo(
                train_number="D2002",
                origin="广州南",
                destination="武汉",
                arrival_time=base_time + timedelta(minutes=15),
                departure_time=base_time + timedelta(minutes=8),
                arrival_platform=3,
                departure_platform=3,
                is_departure=True
            ),
            TrainInfo(
                train_number="G3003",
                origin="成都东",
                destination="重庆西",
                arrival_time=base_time + timedelta(minutes=20),
                departure_time=base_time + timedelta(minutes=12),
                arrival_platform=5,
                departure_platform=5,
                is_departure=False
            ),
            TrainInfo(
                train_number="G3003",
                origin="成都东",
                destination="重庆西",
                arrival_time=base_time + timedelta(minutes=20),
                departure_time=base_time + timedelta(minutes=12),
                arrival_platform=5,
                departure_platform=5,
                is_departure=True
            ),
            TrainInfo(
                train_number="K4004",
                origin="西安",
                destination="郑州",
                arrival_time=base_time + timedelta(minutes=25),
                departure_time=base_time + timedelta(minutes=18),
                arrival_platform=2,
                departure_platform=2,
                is_departure=False
            ),
            TrainInfo(
                train_number="K4004",
                origin="西安",
                destination="郑州",
                arrival_time=base_time + timedelta(minutes=25),
                departure_time=base_time + timedelta(minutes=18),
                arrival_platform=2,
                departure_platform=2,
                is_departure=True
            ),
            TrainInfo(
                train_number="G5005",
                origin="南京南",
                destination="杭州东",
                arrival_time=base_time + timedelta(minutes=30),
                departure_time=base_time + timedelta(minutes=22),
                arrival_platform=4,
                departure_platform=4,
                is_departure=False
            ),
            TrainInfo(
                train_number="G5005",
                origin="南京南",
                destination="杭州东",
                arrival_time=base_time + timedelta(minutes=30),
                departure_time=base_time + timedelta(minutes=22),
                arrival_platform=4,
                departure_platform=4,
                is_departure=True
            ),
        ]
        
        for train in sample_trains:
            self.manager.add_train(train)
    
    def display_arrival_info(self, current_time: datetime):
        arrival_trains = self.manager.get_arrival_trains(current_time, self.display_limit)
        
        print("\n" + "=" * 60)
        print(f"到站信息 (当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        print("=" * 60)
        
        if arrival_trains:
            for i, train in enumerate(arrival_trains, 1):
                print(f"{i}. {train.format_arrival_info()}")
        else:
            print("当前无有效到站列车信息")
        
        print("=" * 60)
    
    def display_departure_info(self, current_time: datetime):
        departure_trains = self.manager.get_departure_trains(current_time, self.display_limit)
        
        print("\n" + "=" * 60)
        print(f"离站信息 (当前时间: {current_time.strftime('%Y-%m-%d %H:%M:%S')})")
        print("=" * 60)
        
        if departure_trains:
            for i, train in enumerate(departure_trains, 1):
                print(f"{i}. {train.format_departure_info()}")
        else:
            print("当前无有效离站列车信息")
        
        print("=" * 60)
    
    async def refresh_loop(self):
        while self.running:
            current_time = datetime.now()
            
            self.display_arrival_info(current_time)
            self.display_departure_info(current_time)
            
            removed = self.manager.remove_expired_trains(current_time)
            if removed > 0:
                print(f"\n已自动移除 {removed} 条过期列车信息")
            
            await asyncio.sleep(self.refresh_interval)
    
    async def start(self):
        print("正在启动列车时刻表系统...")
        print(f"刷新间隔: {self.refresh_interval} 秒")
        print(f"显示限制: 每次显示 {self.display_limit} 条信息")
        print("-" * 60)
        
        self.load_sample_data()
        print("已加载示例数据")
        
        self.running = True
        
        try:
            await self.refresh_loop()
        except KeyboardInterrupt:
            print("\n正在停止列车时刻表系统...")
            self.running = False


async def main():
    system = TrainScheduleSystem(refresh_interval=2.0)
    await system.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n系统已停止")
