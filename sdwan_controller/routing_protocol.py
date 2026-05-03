"""
动态路由协议模块
实现链路状态路由协议（类似OSPF/IS-IS）
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from .config import ROUTING_PROTOCOL
from .models import Switch, Link, LinkStatus, SwitchType


class HelloState(Enum):
    """Hello协议状态"""
    DOWN = "down"
    INIT = "init"
    TWO_WAY = "two_way"
    EXSTART = "exstart"
    EXCHANGE = "exchange"
    LOADING = "loading"
    FULL = "full"


class LSA(Enum):
    """链路状态通告类型"""
    ROUTER_LSA = 1  # 路由器LSA
    NETWORK_LSA = 2  # 网络LSA
    SUMMARY_LSA = 3  # 汇总LSA
    AS_EXTERNAL_LSA = 5  # AS外部LSA


@dataclass
class HelloPacket:
    """Hello数据包"""
    packet_id: str
    source_router_id: str
    destination_router_id: str
    source_ip: str
    destination_ip: str
    area_id: int
    router_priority: int
    hello_interval: int
    dead_interval: int
    designated_router: Optional[str]
    backup_designated_router: Optional[str]
    active_neighbors: List[str]
    timestamp: float = field(default_factory=time.time)


@dataclass
class LinkStateAdvertisement:
    """链路状态通告"""
    lsa_id: str
    lsa_type: LSA
    advertising_router: str
    sequence_number: int
    age: int
    checksum: int
    length: int
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def is_valid(self) -> bool:
        """检查LSA是否有效（未过期）"""
        current_age = int(time.time() - self.timestamp) + self.age
        return current_age < ROUTING_PROTOCOL["max_lsa_age"]


@dataclass
class Neighbor:
    """邻居数据结构"""
    neighbor_id: str
    neighbor_ip: str
    state: HelloState = HelloState.DOWN
    priority: int = 1
    last_hello_received: float = 0
    last_hello_sent: float = 0
    dead_timer: float = 0
    is_designated_router: bool = False
    is_backup_designated_router: bool = False
    lsdb_sync_complete: bool = False


class LinkStateDatabase:
    """链路状态数据库"""

    def __init__(self, router_id: str):
        self.router_id = router_id
        self.lsas: Dict[str, LinkStateAdvertisement] = {}
        self.logger = logging.getLogger(__name__)

    def add_lsa(self, lsa: LinkStateAdvertisement) -> bool:
        """添加LSA到数据库"""
        if lsa.lsa_id in self.lsas:
            existing_lsa = self.lsas[lsa.lsa_id]
            # 检查是否需要更新（序列号更高或更年轻）
            if lsa.sequence_number > existing_lsa.sequence_number:
                self.lsas[lsa.lsa_id] = lsa
                self.logger.debug(
                    f"Updated LSA {lsa.lsa_id} with higher sequence number"
                )
                return True
            elif (
                lsa.sequence_number == existing_lsa.sequence_number
                and lsa.age < existing_lsa.age
            ):
                self.lsas[lsa.lsa_id] = lsa
                self.logger.debug(
                    f"Updated LSA {lsa.lsa_id} with younger age"
                )
                return True
            return False
        else:
            self.lsas[lsa.lsa_id] = lsa
            self.logger.debug(f"Added new LSA {lsa.lsa_id}")
            return True

    def remove_lsa(self, lsa_id: str) -> bool:
        """从数据库中移除LSA"""
        if lsa_id in self.lsas:
            del self.lsas[lsa_id]
            self.logger.debug(f"Removed LSA {lsa_id}")
            return True
        return False

    def get_lsa(self, lsa_id: str) -> Optional[LinkStateAdvertisement]:
        """获取指定LSA"""
        return self.lsas.get(lsa_id)

    def get_all_valid_lsas(self) -> List[LinkStateAdvertisement]:
        """获取所有有效的LSA"""
        self._cleanup_expired_lsas()
        return list(self.lsas.values())

    def get_lsas_by_router(self, router_id: str) -> List[LinkStateAdvertisement]:
        """获取指定路由器生成的LSA"""
        self._cleanup_expired_lsas()
        return [
            lsa
            for lsa in self.lsas.values()
            if lsa.advertising_router == router_id
        ]

    def _cleanup_expired_lsas(self) -> None:
        """清理过期的LSA"""
        expired_lsas = [
            lsa_id
            for lsa_id, lsa in self.lsas.items()
            if not lsa.is_valid()
        ]
        for lsa_id in expired_lsas:
            del self.lsas[lsa_id]
        if expired_lsas:
            self.logger.debug(f"Cleaned up {len(expired_lsas)} expired LSAs")

    def get_summary(self) -> Dict[str, Any]:
        """获取LSDB摘要"""
        self._cleanup_expired_lsas()
        lsa_types = defaultdict(int)
        for lsa in self.lsas.values():
            lsa_types[lsa.lsa_type.value] += 1
        
        return {
            "router_id": self.router_id,
            "total_lsas": len(self.lsas),
            "lsa_types": dict(lsa_types),
        }


from collections import defaultdict


class HelloProtocol:
    """Hello协议实现"""

    def __init__(
        self,
        router_id: str,
        router_ip: str,
        area_id: int = 0,
        priority: int = 1,
    ):
        self.router_id = router_id
        self.router_ip = router_ip
        self.area_id = area_id
        self.priority = priority
        self.neighbors: Dict[str, Neighbor] = {}
        self.designated_router: Optional[str] = None
        self.backup_designated_router: Optional[str] = None
        self.hello_interval = ROUTING_PROTOCOL["hello_interval"]
        self.dead_interval = ROUTING_PROTOCOL["dead_interval"]
        self.running = False
        self._hello_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)

    async def start(self) -> None:
        """启动Hello协议"""
        self.running = True
        self._hello_task = asyncio.create_task(self._hello_loop())
        self.logger.info(
            f"Hello protocol started for router {self.router_id}"
        )

    async def stop(self) -> None:
        """停止Hello协议"""
        self.running = False
        if self._hello_task:
            self._hello_task.cancel()
            try:
                await self._hello_task
            except asyncio.CancelledError:
                pass
        self.logger.info(
            f"Hello protocol stopped for router {self.router_id}"
        )

    async def _hello_loop(self) -> None:
        """Hello消息发送循环"""
        while self.running:
            try:
                await self._send_hello_to_all_neighbors()
                await self._check_dead_neighbors()
                await asyncio.sleep(self.hello_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in hello loop: {e}")
                await asyncio.sleep(1)

    async def _send_hello_to_all_neighbors(self) -> None:
        """向所有邻居发送Hello消息"""
        for neighbor_id, neighbor in self.neighbors.items():
            hello_packet = self._create_hello_packet(neighbor_id)
            # 实际环境中会通过网络发送
            neighbor.last_hello_sent = time.time()
            self.logger.debug(
                f"Sent Hello to {neighbor_id}, state: {neighbor.state.value}"
            )

    async def _check_dead_neighbors(self) -> None:
        """检查失效的邻居"""
        current_time = time.time()
        neighbors_to_remove = []
        
        for neighbor_id, neighbor in self.neighbors.items():
            time_since_last_hello = current_time - neighbor.last_hello_received
            
            if time_since_last_hello > self.dead_interval:
                self.logger.warning(
                    f"Neighbor {neighbor_id} is dead (no hello for "
                    f"{time_since_last_hello:.1f}s)"
                )
                neighbors_to_remove.append(neighbor_id)
        
        for neighbor_id in neighbors_to_remove:
            del self.neighbors[neighbor_id]
        
        if neighbors_to_remove:
            self._elect_designated_router()

    def _create_hello_packet(self, destination_router_id: str) -> HelloPacket:
        """创建Hello数据包"""
        return HelloPacket(
            packet_id=str(uuid.uuid4()),
            source_router_id=self.router_id,
            destination_router_id=destination_router_id,
            source_ip=self.router_ip,
            destination_ip="",  # 实际环境中会填充
            area_id=self.area_id,
            router_priority=self.priority,
            hello_interval=self.hello_interval,
            dead_interval=self.dead_interval,
            designated_router=self.designated_router,
            backup_designated_router=self.backup_designated_router,
            active_neighbors=list(self.neighbors.keys()),
        )

    async def receive_hello(self, hello_packet: HelloPacket) -> None:
        """接收并处理Hello数据包"""
        neighbor_id = hello_packet.source_router_id
        
        if neighbor_id == self.router_id:
            return  # 忽略自己发送的Hello
        
        self.logger.debug(f"Received Hello from {neighbor_id}")
        
        # 检查邻居是否已存在
        if neighbor_id not in self.neighbors:
            # 创建新邻居
            neighbor = Neighbor(
                neighbor_id=neighbor_id,
                neighbor_ip=hello_packet.source_ip,
                state=HelloState.INIT,
                priority=hello_packet.router_priority,
            )
            self.neighbors[neighbor_id] = neighbor
            self.logger.info(f"New neighbor detected: {neighbor_id}")
        else:
            neighbor = self.neighbors[neighbor_id]
        
        neighbor.last_hello_received = time.time()
        
        # 检查是否在对方的邻居列表中（双向通信）
        if self.router_id in hello_packet.active_neighbors:
            if neighbor.state == HelloState.INIT:
                neighbor.state = HelloState.TWO_WAY
                self.logger.info(
                    f"Neighbor {neighbor_id} reached TWO_WAY state"
                )
                # 触发DR选举
                self._elect_designated_router()
        
        # 更新DR/BDR信息
        if hello_packet.designated_router:
            neighbor.is_designated_router = (
                hello_packet.designated_router == neighbor_id
            )
        if hello_packet.backup_designated_router:
            neighbor.is_backup_designated_router = (
                hello_packet.backup_designated_router == neighbor_id
            )

    def _elect_designated_router(self) -> None:
        """选举指定路由器(DR)和备份指定路由器(BDR)"""
        if len(self.neighbors) < 1:
            self.designated_router = None
            self.backup_designated_router = None
            return
        
        # 收集所有路由器（包括自己）
        all_routers = [
            (self.router_id, self.priority)
        ]
        all_routers.extend(
            (neighbor_id, neighbor.priority)
            for neighbor_id, neighbor in self.neighbors.items()
        )
        
        # 按优先级排序（优先级高的优先）
        all_routers.sort(key=lambda x: x[1], reverse=True)
        
        # 选举DR
        self.designated_router = all_routers[0][0]
        
        # 选举BDR
        if len(all_routers) > 1:
            self.backup_designated_router = all_routers[1][0]
        else:
            self.backup_designated_router = None
        
        self.logger.info(
            f"DR election complete: DR={self.designated_router}, "
            f"BDR={self.backup_designated_router}"
        )

    def get_neighbor_states(self) -> Dict[str, str]:
        """获取所有邻居的状态"""
        return {
            neighbor_id: neighbor.state.value
            for neighbor_id, neighbor in self.neighbors.items()
        }


class LinkStateRouting:
    """链路状态路由协议主类"""

    def __init__(self, router_id: str, router_ip: str, area_id: int = 0):
        self.router_id = router_id
        self.router_ip = router_ip
        self.area_id = area_id
        self.lsdb = LinkStateDatabase(router_id)
        self.hello_protocol = HelloProtocol(router_id, router_ip, area_id)
        self.running = False
        self._lsa_refresh_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(__name__)
        # 用于模拟通信的回调
        self.send_lsa_callback = None
        self.receive_lsa_callback = None

    async def start(self) -> None:
        """启动路由协议"""
        self.running = True
        await self.hello_protocol.start()
        self._lsa_refresh_task = asyncio.create_task(self._lsa_refresh_loop())
        self.logger.info(
            f"Link state routing started for router {self.router_id}"
        )

    async def stop(self) -> None:
        """停止路由协议"""
        self.running = False
        await self.hello_protocol.stop()
        if self._lsa_refresh_task:
            self._lsa_refresh_task.cancel()
            try:
                await self._lsa_refresh_task
            except asyncio.CancelledError:
                pass
        self.logger.info(
            f"Link state routing stopped for router {self.router_id}"
        )

    async def _lsa_refresh_loop(self) -> None:
        """LSA刷新循环"""
        while self.running:
            try:
                await self._refresh_own_lsas()
                await asyncio.sleep(ROUTING_PROTOCOL["lsa_refresh_time"])
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in LSA refresh loop: {e}")
                await asyncio.sleep(1)

    async def _refresh_own_lsas(self) -> None:
        """刷新自己生成的LSA"""
        own_lsas = self.lsdb.get_lsas_by_router(self.router_id)
        
        for lsa in own_lsas:
            # 更新序列号和年龄
            new_lsa = LinkStateAdvertisement(
                lsa_id=lsa.lsa_id,
                lsa_type=lsa.lsa_type,
                advertising_router=lsa.advertising_router,
                sequence_number=lsa.sequence_number + 1,
                age=0,
                checksum=lsa.checksum,
                length=lsa.length,
                data=lsa.data.copy(),
            )
            self.lsdb.add_lsa(new_lsa)
            
            # 泛洪更新的LSA
            await self._flood_lsa(new_lsa)
        
        if own_lsas:
            self.logger.debug(f"Refreshed {len(own_lsas)} LSAs")

    async def generate_router_lsa(
        self,
        links: List[Dict[str, Any]],
    ) -> LinkStateAdvertisement:
        """生成路由器LSA"""
        lsa_data = {
            "links": links,
            "router_type": "border",  # 可以根据实际情况设置
        }
        
        lsa = LinkStateAdvertisement(
            lsa_id=f"{self.router_id}:{LSA.ROUTER_LSA.value}:{int(time.time())}",
            lsa_type=LSA.ROUTER_LSA,
            advertising_router=self.router_id,
            sequence_number=1,
            age=0,
            checksum=0,  # 实际环境中需要计算
            length=len(str(lsa_data)),
            data=lsa_data,
        )
        
        self.lsdb.add_lsa(lsa)
        await self._flood_lsa(lsa)
        
        self.logger.info(f"Generated Router LSA: {lsa.lsa_id}")
        return lsa

    async def _flood_lsa(self, lsa: LinkStateAdvertisement) -> None:
        """泛洪LSA到所有邻居"""
        if self.send_lsa_callback:
            await self.send_lsa_callback(lsa)
        else:
            self.logger.debug(f"Would flood LSA {lsa.lsa_id} to neighbors")

    async def receive_lsa(self, lsa: LinkStateAdvertisement, source_router: str) -> None:
        """接收并处理LSA"""
        # 添加到LSDB
        if self.lsdb.add_lsa(lsa):
            self.logger.debug(
                f"Received new/updated LSA {lsa.lsa_id} from {source_router}"
            )
            # 继续泛洪到其他邻居（除了来源）
            await self._flood_lsa_to_others(lsa, source_router)

    async def _flood_lsa_to_others(
        self, lsa: LinkStateAdvertisement, exclude_router: str
    ) -> None:
        """泛洪LSA到除了指定路由器之外的所有邻居"""
        if self.send_lsa_callback:
            # 实际环境中需要过滤掉exclude_router
            await self.send_lsa_callback(lsa)

    def build_topology_from_lsdb(self) -> Dict[str, Any]:
        """从LSDB构建拓扑信息"""
        valid_lsas = self.lsdb.get_all_valid_lsas()
        router_lsas = [lsa for lsa in valid_lsas if lsa.lsa_type == LSA.ROUTER_LSA]
        
        topology = {
            "routers": set(),
            "links": [],
        }
        
        for lsa in router_lsas:
            router_id = lsa.advertising_router
            topology["routers"].add(router_id)
            
            links = lsa.data.get("links", [])
            for link in links:
                topology["links"].append({
                    "from": router_id,
                    "to": link.get("neighbor_id"),
                    "cost": link.get("cost", 1),
                    "interface": link.get("interface"),
                })
        
        return {
            "routers": list(topology["routers"]),
            "links": topology["links"],
            "total_routers": len(topology["routers"]),
            "total_links": len(topology["links"]),
        }

    def get_status(self) -> Dict[str, Any]:
        """获取路由协议状态"""
        return {
            "router_id": self.router_id,
            "router_ip": self.router_ip,
            "area_id": self.area_id,
            "running": self.running,
            "neighbors": self.hello_protocol.get_neighbor_states(),
            "lsdb_summary": self.lsdb.get_summary(),
            "designated_router": self.hello_protocol.designated_router,
            "backup_designated_router": self.hello_protocol.backup_designated_router,
        }
