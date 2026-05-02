"""
SD-WAN核心控制器模块
负责拓扑发现、路由计算、路径优化和集中管理
"""

import asyncio
import heapq
import time
import uuid
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
from functools import lru_cache

from .config import (
    NETWORK_TOPOLOGY,
    LINK_PARAMS,
    ROUTING_PROTOCOL,
    PERFORMANCE_CONFIG,
)
from .models import (
    Switch,
    Link,
    Topology,
    Route,
    RoutingTable,
    SwitchType,
    LinkStatus,
    RouteType,
)


@dataclass
class Path:
    """路径数据结构"""
    path_id: str
    source: str
    destination: str
    nodes: List[str]
    total_cost: int
    latency: float
    bandwidth: int
    is_primary: bool = True


class TopologyDiscovery:
    """拓扑发现模块"""

    def __init__(self, topology: Topology):
        self.topology = topology
        self.logger = logging.getLogger(__name__)

    async def discover_neighbors(self, switch_id: str) -> List[str]:
        """
        发现指定交换机的邻居
        实际环境中会使用LLDP或类似协议
        """
        switch = self.topology.get_switch(switch_id)
        if not switch or not switch.is_active:
            return []
        
        # 从邻接矩阵获取邻居
        neighbors = self.topology.adjacency_matrix.get(switch_id, {}).keys()
        return list(neighbors)

    async def update_topology(self, switch_updates: List[Dict[str, Any]]) -> bool:
        """
        更新网络拓扑
        """
        try:
            for update in switch_updates:
                switch_id = update.get("switch_id")
                if switch_id:
                    switch = self.topology.get_switch(switch_id)
                    if switch:
                        # 更新交换机状态
                        if "is_active" in update:
                            switch.is_active = update["is_active"]
                        # 更新邻居
                        if "neighbors" in update:
                            switch.neighbors = update["neighbors"]
                        switch.last_updated = time.time()
            
            self.logger.info(f"Updated topology with {len(switch_updates)} updates")
            return True
        except Exception as e:
            self.logger.error(f"Error updating topology: {e}")
            return False

    def get_topology_summary(self) -> Dict[str, Any]:
        """
        获取拓扑摘要信息
        """
        active_switches = self.topology.get_active_switches()
        core_count = sum(
            1 for s in active_switches if s.switch_type == SwitchType.CORE
        )
        access_count = sum(
            1 for s in active_switches if s.switch_type == SwitchType.ACCESS
        )
        pop_count = sum(
            1 for s in active_switches if s.switch_type == SwitchType.POP
        )
        
        active_links = sum(
            1 for link in self.topology.links.values()
            if link.status == LinkStatus.UP
        )
        
        return {
            "total_switches": len(self.topology.switches),
            "active_switches": len(active_switches),
            "core_switches": core_count,
            "access_switches": access_count,
            "pop_switches": pop_count,
            "total_links": len(self.topology.links),
            "active_links": active_links,
            "last_updated": self.topology.last_updated.isoformat(),
        }


class RouteCalculator:
    """
    路由计算器
    实现高效的最短路径算法，支持ECMP
    """

    def __init__(self, topology: Topology):
        self.topology = topology
        self.logger = logging.getLogger(__name__)
        self._route_cache: Dict[Tuple[str, str], List[Path]] = {}
        self._cache_timestamp: float = 0
        self._cache_ttl = PERFORMANCE_CONFIG.get("cache_ttl", 60)

    def _clear_expired_cache(self):
        """清除过期的缓存"""
        current_time = time.time()
        if current_time - self._cache_timestamp > self._cache_ttl:
            self._route_cache.clear()
            self._cache_timestamp = current_time
            self.logger.debug("Route cache cleared due to TTL expiration")

    def _get_active_adjacency(self) -> Dict[str, Dict[str, int]]:
        """
        获取仅包含活跃节点和链路的邻接矩阵
        """
        active_switches = {
            sw.switch_id for sw in self.topology.get_active_switches()
        }
        
        active_adjacency = defaultdict(dict)
        for source, neighbors in self.topology.adjacency_matrix.items():
            if source in active_switches:
                for dest, cost in neighbors.items():
                    if dest in active_switches:
                        # 检查链路状态
                        link = self._find_link(source, dest)
                        if link and link.status == LinkStatus.UP:
                            active_adjacency[source][dest] = cost
        
        return dict(active_adjacency)

    def _find_link(self, source: str, dest: str) -> Optional[Link]:
        """
        查找两个交换机之间的链路
        """
        for link in self.topology.links.values():
            if (
                (link.source_switch_id == source and link.destination_switch_id == dest)
                or (link.source_switch_id == dest and link.destination_switch_id == source)
            ):
                return link
        return None

    def calculate_shortest_paths(
        self,
        source: str,
        destination: Optional[str] = None,
        force_full: bool = False,
    ) -> Dict[str, List[Path]]:
        """
        计算最短路径
        使用Dijkstra算法，支持ECMP（等价多路径）
        
        参数:
            source: 源节点ID
            destination: 目标节点ID（如果为None，则计算到所有可达节点的路径）
            force_full: 是否强制全量计算（禁用缓存和提前退出优化）
        """
        start_time = time.time()
        
        # 全量计算模式下禁用缓存
        if not force_full:
            self._clear_expired_cache()
        
        adjacency = self._get_active_adjacency()
        
        # 检查源节点是否存在且活跃
        if source not in adjacency:
            self.logger.warning(f"Source switch {source} not active or not found")
            return {}
        
        # 初始化距离和前驱
        distances: Dict[str, float] = defaultdict(lambda: float('inf'))
        distances[source] = 0
        
        # 前驱节点（支持ECMP）
        predecessors: Dict[str, Set[str]] = defaultdict(set)
        
        # 优先队列
        priority_queue = [(0, source)]
        visited: Set[str] = set()
        
        while priority_queue:
            current_distance, current_node = heapq.heappop(priority_queue)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # 全量计算模式下禁用提前退出
            if not force_full and destination and current_node == destination:
                # 非全量模式下，如果指定了目的地且已到达，可提前退出
                break
            
            # 检查超时
            if time.time() - start_time > PERFORMANCE_CONFIG["route_calculation_timeout"]:
                self.logger.warning(
                    f"Route calculation timeout for source {source}"
                )
                break
            
            # 遍历邻居
            for neighbor, cost in adjacency.get(current_node, {}).items():
                new_distance = current_distance + cost
                
                if new_distance < distances[neighbor]:
                    # 找到更短的路径
                    distances[neighbor] = new_distance
                    predecessors[neighbor].clear()
                    predecessors[neighbor].add(current_node)
                    heapq.heappush(priority_queue, (new_distance, neighbor))
                elif new_distance == distances[neighbor] and new_distance != float('inf'):
                    # 找到等价路径（ECMP）
                    predecessors[neighbor].add(current_node)
        
        # 构建路径
        paths: Dict[str, List[Path]] = defaultdict(list)
        
        # 全量计算模式下，总是计算到所有可达节点的路径
        if force_full or destination is None:
            target_nodes = [k for k in distances.keys() if k != source and distances[k] != float('inf')]
        else:
            target_nodes = [destination] if distances.get(destination, float('inf')) != float('inf') else []
        
        for target in target_nodes:
            if target == source:
                continue
            
            if distances[target] == float('inf'):
                continue
            
            # 使用回溯法构建所有最短路径
            all_paths = self._build_all_paths(
                source, target, predecessors, distances
            )
            
            paths[target] = all_paths
            
            # 全量计算模式下禁用缓存
            if not force_full and PERFORMANCE_CONFIG.get("cache_enabled", True):
                self._route_cache[(source, target)] = all_paths
        
        calculation_time = time.time() - start_time
        self.logger.debug(
            f"Route calculation from {source} completed in {calculation_time:.4f}s"
        )
        
        return dict(paths)

    def _build_all_paths(
        self,
        source: str,
        target: str,
        predecessors: Dict[str, Set[str]],
        distances: Dict[str, float],
    ) -> List[Path]:
        """
        构建所有最短路径（支持ECMP）
        """
        all_paths: List[Path] = []
        
        # 使用栈进行深度优先搜索
        stack = [(target, [target])]
        
        while stack:
            current, path = stack.pop()
            
            if current == source:
                # 找到完整路径
                full_path = list(reversed(path))
                path_obj = self._create_path_object(full_path, distances[target])
                all_paths.append(path_obj)
                continue
            
            # 遍历前驱节点
            for pred in predecessors.get(current, []):
                if pred not in path:
                    stack.append((pred, path + [pred]))
        
        # 对路径进行排序
        all_paths.sort(key=lambda p: len(p.nodes))
        
        # 标记主路径和备用路径
        for i, path in enumerate(all_paths):
            path.is_primary = (i == 0)
        
        # 限制最大ECMP路径数
        max_paths = ROUTING_PROTOCOL.get("max_ecmp_paths", 4)
        return all_paths[:max_paths]

    def _create_path_object(self, nodes: List[str], total_cost: float) -> Path:
        """
        创建路径对象
        """
        # 计算额外的路径属性
        total_latency = 0.0
        min_bandwidth = float('inf')
        
        for i in range(len(nodes) - 1):
            link = self._find_link(nodes[i], nodes[i + 1])
            if link:
                total_latency += link.latency
                min_bandwidth = min(min_bandwidth, link.bandwidth)
        
        return Path(
            path_id=str(uuid.uuid4()),
            source=nodes[0],
            destination=nodes[-1],
            nodes=nodes,
            total_cost=int(total_cost),
            latency=total_latency,
            bandwidth=min_bandwidth if min_bandwidth != float('inf') else 0,
        )

    def get_cached_path(self, source: str, destination: str) -> Optional[List[Path]]:
        """
        获取缓存的路径
        """
        if not PERFORMANCE_CONFIG.get("cache_enabled", True):
            return None
        
        self._clear_expired_cache()
        return self._route_cache.get((source, destination))


class PathOptimizer:
    """
    路径优化器
    提供基于不同策略的路径优化
    """

    def __init__(self, topology: Topology):
        self.topology = topology
        self.logger = logging.getLogger(__name__)

    def optimize_by_latency(self, paths: List[Path]) -> List[Path]:
        """
        基于延迟优化路径
        """
        if not paths:
            return []
        
        # 按延迟排序
        optimized = sorted(paths, key=lambda p: p.latency)
        
        # 更新主路径标记
        for i, path in enumerate(optimized):
            path.is_primary = (i == 0)
        
        self.logger.debug(f"Optimized {len(paths)} paths by latency")
        return optimized

    def optimize_by_bandwidth(self, paths: List[Path]) -> List[Path]:
        """
        基于带宽优化路径
        """
        if not paths:
            return []
        
        # 按带宽降序排序
        optimized = sorted(paths, key=lambda p: p.bandwidth, reverse=True)
        
        # 更新主路径标记
        for i, path in enumerate(optimized):
            path.is_primary = (i == 0)
        
        self.logger.debug(f"Optimized {len(paths)} paths by bandwidth")
        return optimized

    def optimize_by_hop_count(self, paths: List[Path]) -> List[Path]:
        """
        基于跳数优化路径
        """
        if not paths:
            return []
        
        # 按跳数排序
        optimized = sorted(paths, key=lambda p: len(p.nodes))
        
        # 更新主路径标记
        for i, path in enumerate(optimized):
            path.is_primary = (i == 0)
        
        self.logger.debug(f"Optimized {len(paths)} paths by hop count")
        return optimized

    def optimize_load_balancing(self, paths: List[Path]) -> List[Path]:
        """
        负载均衡优化
        确保所有可用路径都能被利用
        """
        if not paths:
            return []
        
        # 确保所有路径都被标记为可用
        for path in paths:
            path.is_primary = True
        
        self.logger.debug(f"Optimized {len(paths)} paths for load balancing")
        return paths


class CoreController:
    """
    核心控制器
    整合拓扑发现、路由计算和路径优化功能
    """

    def __init__(self):
        self.topology = Topology()
        self.topology_discovery = TopologyDiscovery(self.topology)
        self.route_calculator = RouteCalculator(self.topology)
        self.path_optimizer = PathOptimizer(self.topology)
        self.routing_tables: Dict[str, RoutingTable] = {}
        self.logger = logging.getLogger(__name__)

    async def initialize_topology(self) -> bool:
        """
        初始化网络拓扑
        创建20台交换机：2核心 + 10接入 + 8 POP
        """
        try:
            self.logger.info("Initializing network topology...")
            
            # 创建核心交换机
            for i in range(NETWORK_TOPOLOGY["core_switches"]):
                switch_id = f"core-{i+1}"
                switch = Switch(
                    switch_id=switch_id,
                    name=f"Core Switch {i+1}",
                    switch_type=SwitchType.CORE,
                    ip_address=f"10.0.0.{i+1}",
                    mac_address=f"00:1A:2B:3C:{(i+1):02X}:00",
                    interfaces=[
                        {"name": "GigabitEthernet0/0", "speed": 1000, "status": "up"},
                        {"name": "GigabitEthernet0/1", "speed": 1000, "status": "up"},
                        {"name": "GigabitEthernet0/2", "speed": 1000, "status": "up"},
                        {"name": "GigabitEthernet0/3", "speed": 1000, "status": "up"},
                    ],
                )
                self.topology.add_switch(switch)
                self.routing_tables[switch_id] = RoutingTable(switch_id=switch_id)
            
            # 创建接入交换机
            for i in range(NETWORK_TOPOLOGY["access_switches"]):
                switch_id = f"access-{i+1}"
                switch = Switch(
                    switch_id=switch_id,
                    name=f"Access Switch {i+1}",
                    switch_type=SwitchType.ACCESS,
                    ip_address=f"10.0.1.{i+1}",
                    mac_address=f"00:1A:2B:3D:{(i+1):02X}:00",
                    interfaces=[
                        {"name": "GigabitEthernet0/0", "speed": 1000, "status": "up"},
                        {"name": "GigabitEthernet0/1", "speed": 1000, "status": "up"},
                        {"name": "FastEthernet0/0", "speed": 100, "status": "up"},
                        {"name": "FastEthernet0/1", "speed": 100, "status": "up"},
                    ],
                )
                self.topology.add_switch(switch)
                self.routing_tables[switch_id] = RoutingTable(switch_id=switch_id)
            
            # 创建POP交换机
            for i in range(NETWORK_TOPOLOGY["pop_switches"]):
                switch_id = f"pop-{i+1}"
                switch = Switch(
                    switch_id=switch_id,
                    name=f"POP Switch {i+1}",
                    switch_type=SwitchType.POP,
                    ip_address=f"10.0.2.{i+1}",
                    mac_address=f"00:1A:2B:3E:{(i+1):02X}:00",
                    interfaces=[
                        {"name": "GigabitEthernet0/0", "speed": 1000, "status": "up"},
                        {"name": "GigabitEthernet0/1", "speed": 1000, "status": "up"},
                        {"name": "GigabitEthernet0/2", "speed": 1000, "status": "up"},
                    ],
                )
                self.topology.add_switch(switch)
                self.routing_tables[switch_id] = RoutingTable(switch_id=switch_id)
            
            # 创建链路
            await self._create_links()
            
            self.logger.info(
                f"Topology initialized: {len(self.topology.switches)} switches, "
                f"{len(self.topology.links)} links"
            )
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize topology: {e}")
            return False

    async def _create_links(self) -> None:
        """
        创建网络链路
        """
        link_id_counter = 1
        
        # 核心交换机之间的全连接
        core_switches = [
            sw.switch_id
            for sw in self.topology.switches.values()
            if sw.switch_type == SwitchType.CORE
        ]
        
        for i in range(len(core_switches)):
            for j in range(i + 1, len(core_switches)):
                link = Link(
                    link_id=f"link-{link_id_counter}",
                    source_switch_id=core_switches[i],
                    destination_switch_id=core_switches[j],
                    source_interface="GigabitEthernet0/0",
                    destination_interface="GigabitEthernet0/0",
                    cost=LINK_PARAMS["core_core_cost"],
                    bandwidth=1000,
                    latency=0.1,
                    status=LinkStatus.UP,
                )
                self.topology.add_link(link)
                link_id_counter += 1
        
        # 接入交换机与核心交换机的连接
        # 每个接入交换机连接到两个核心交换机（冗余）
        access_switches = [
            sw.switch_id
            for sw in self.topology.switches.values()
            if sw.switch_type == SwitchType.ACCESS
        ]
        
        for access_id in access_switches:
            for i, core_id in enumerate(core_switches[:2]):
                link = Link(
                    link_id=f"link-{link_id_counter}",
                    source_switch_id=access_id,
                    destination_switch_id=core_id,
                    source_interface=f"GigabitEthernet0/{i}",
                    destination_interface=f"GigabitEthernet0/{i+1}",
                    cost=LINK_PARAMS["core_access_cost"],
                    bandwidth=1000,
                    latency=0.5,
                    status=LinkStatus.UP,
                )
                self.topology.add_link(link)
                link_id_counter += 1
        
        # POP交换机与核心交换机的连接
        pop_switches = [
            sw.switch_id
            for sw in self.topology.switches.values()
            if sw.switch_type == SwitchType.POP
        ]
        
        for pop_id in pop_switches:
            for i, core_id in enumerate(core_switches[:2]):
                link = Link(
                    link_id=f"link-{link_id_counter}",
                    source_switch_id=pop_id,
                    destination_switch_id=core_id,
                    source_interface=f"GigabitEthernet0/{i}",
                    destination_interface=f"GigabitEthernet0/{i+2}",
                    cost=LINK_PARAMS["core_pop_cost"],
                    bandwidth=1000,
                    latency=0.3,
                    status=LinkStatus.UP,
                )
                self.topology.add_link(link)
                link_id_counter += 1
        
        # 接入交换机之间的部分连接（用于冗余）
        for i in range(0, len(access_switches), 2):
            if i + 1 < len(access_switches):
                link = Link(
                    link_id=f"link-{link_id_counter}",
                    source_switch_id=access_switches[i],
                    destination_switch_id=access_switches[i + 1],
                    source_interface="FastEthernet0/0",
                    destination_interface="FastEthernet0/0",
                    cost=LINK_PARAMS["access_access_cost"],
                    bandwidth=100,
                    latency=1.0,
                    status=LinkStatus.UP,
                )
                self.topology.add_link(link)
                link_id_counter += 1
        
        # POP交换机之间的部分连接
        for i in range(0, len(pop_switches), 2):
            if i + 1 < len(pop_switches):
                link = Link(
                    link_id=f"link-{link_id_counter}",
                    source_switch_id=pop_switches[i],
                    destination_switch_id=pop_switches[i + 1],
                    source_interface="GigabitEthernet0/2",
                    destination_interface="GigabitEthernet0/2",
                    cost=LINK_PARAMS["pop_pop_cost"],
                    bandwidth=1000,
                    latency=0.8,
                    status=LinkStatus.UP,
                )
                self.topology.add_link(link)
                link_id_counter += 1
        
        self.logger.debug(f"Created {link_id_counter - 1} links")

    async def calculate_all_routes(
        self,
        optimize_strategy: str = "cost",
        force_full_calculation: bool = True,
    ) -> bool:
        """
        为所有交换机计算路由表
        
        参数:
            optimize_strategy: 优化策略（cost/latency/bandwidth/hop_count/load_balancing）
            force_full_calculation: 是否强制全量计算（禁用所有优化，确保计算完整性）
        """
        start_time = time.time()
        
        if force_full_calculation:
            self.logger.info(
                "Starting FULL route calculation for all switches "
                "(cache disabled, no early exit optimization)..."
            )
        else:
            self.logger.info("Starting route calculation for all switches...")
        
        active_switches = self.topology.get_active_switches()
        total_switches = len(active_switches)
        
        for idx, switch in enumerate(active_switches):
            self.logger.debug(
                f"Calculating routes for switch {idx+1}/{total_switches}: {switch.switch_id}"
            )
            
            # 计算从当前交换机到所有其他交换机的路径
            # 全量计算模式下禁用缓存和提前退出
            paths = self.route_calculator.calculate_shortest_paths(
                source=switch.switch_id,
                destination=None,  # 计算到所有目标的路径
                force_full=force_full_calculation,
            )
            
            # 更新路由表
            routing_table = self.routing_tables.get(switch.switch_id)
            if routing_table:
                # 全量计算模式下，先清空路由表再添加新路由
                if force_full_calculation:
                    routing_table.routes.clear()
                
                for dest, dest_paths in paths.items():
                    if not dest_paths:
                        continue
                    
                    # 根据优化策略选择路径
                    if optimize_strategy == "latency":
                        optimized = self.path_optimizer.optimize_by_latency(dest_paths)
                    elif optimize_strategy == "bandwidth":
                        optimized = self.path_optimizer.optimize_by_bandwidth(dest_paths)
                    elif optimize_strategy == "hop_count":
                        optimized = self.path_optimizer.optimize_by_hop_count(dest_paths)
                    elif optimize_strategy == "load_balancing":
                        optimized = self.path_optimizer.optimize_load_balancing(dest_paths)
                    else:
                        optimized = dest_paths
                    
                    primary_path = optimized[0]
                    
                    # 创建路由对象
                    route = Route(
                        route_id=str(uuid.uuid4()),
                        destination=dest,
                        next_hop=primary_path.nodes[1] if len(primary_path.nodes) > 1 else dest,
                        cost=primary_path.total_cost,
                        route_type=RouteType.DYNAMIC,
                        interface="",
                        is_ecmp=len(optimized) > 1,
                        ecmp_paths=[
                            {
                                "next_hop": path.nodes[1] if len(path.nodes) > 1 else dest,
                                "cost": path.total_cost,
                                "path": path.nodes,
                            }
                            for path in optimized[1:]
                        ],
                    )
                    
                    routing_table.add_route(route)
        
        calculation_time = time.time() - start_time
        
        mode = "FULL" if force_full_calculation else "OPTIMIZED"
        self.logger.info(
            f"Route calculation ({mode} mode) completed in {calculation_time:.4f}s "
            f"for {total_switches} switches"
        )
        
        # 检查是否超时
        if calculation_time > PERFORMANCE_CONFIG["max_computation_time"]:
            self.logger.warning(
                f"Route calculation exceeded time limit: {calculation_time:.4f}s > "
                f"{PERFORMANCE_CONFIG['max_computation_time']}s"
            )
            return False
        
        return True

    def get_routing_table(self, switch_id: str) -> Optional[RoutingTable]:
        """
        获取指定交换机的路由表
        """
        return self.routing_tables.get(switch_id)

    def get_topology_summary(self) -> Dict[str, Any]:
        """
        获取拓扑摘要
        """
        return self.topology_discovery.get_topology_summary()

    def get_path_between(
        self,
        source: str,
        destination: str,
        optimize_strategy: str = "cost",
        force_full: bool = False,
    ) -> Optional[List[Path]]:
        """
        获取两个节点之间的路径
        
        参数:
            source: 源节点ID
            destination: 目标节点ID
            optimize_strategy: 优化策略
            force_full: 是否强制全量计算（禁用缓存）
        """
        # 全量计算模式下禁用缓存
        if not force_full:
            # 首先检查缓存
            cached = self.route_calculator.get_cached_path(source, destination)
            if cached:
                return cached
        
        # 计算路径
        paths = self.route_calculator.calculate_shortest_paths(
            source=source,
            destination=destination,
            force_full=force_full,
        )
        
        if destination not in paths:
            return None
        
        dest_paths = paths[destination]
        
        # 根据优化策略优化
        if optimize_strategy == "latency":
            return self.path_optimizer.optimize_by_latency(dest_paths)
        elif optimize_strategy == "bandwidth":
            return self.path_optimizer.optimize_by_bandwidth(dest_paths)
        elif optimize_strategy == "hop_count":
            return self.path_optimizer.optimize_by_hop_count(dest_paths)
        elif optimize_strategy == "load_balancing":
            return self.path_optimizer.optimize_load_balancing(dest_paths)
        
        return dest_paths
