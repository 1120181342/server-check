"""
性能优化模块
提供路由计算的高性能实现，确保单次计算时间<1秒
"""

import asyncio
import heapq
import time
import functools
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
import threading

from .config import PERFORMANCE_CONFIG, NETWORK_TOPOLOGY
from .models import Topology, Switch, Link, LinkStatus, SwitchType


@dataclass
class RouteCacheEntry:
    """路由缓存条目"""
    source: str
    destination: str
    paths: List[Dict[str, Any]]
    timestamp: float
    hit_count: int = 0


class IncrementalRouteCalculator:
    """
    增量路由计算器
    只重新计算受影响的路径，而不是全量重新计算
    """

    def __init__(self, topology: Topology):
        self.topology = topology
        self.logger = logging.getLogger(__name__)
        self._cached_distances: Dict[str, Dict[str, float]] = {}
        self._cached_predecessors: Dict[str, Dict[str, Set[str]]] = {}
        self._last_topology_hash: int = 0

    def _calculate_topology_hash(self) -> int:
        """计算拓扑哈希值，用于检测变化"""
        active_switches = tuple(
            sorted(sw.switch_id for sw in self.topology.get_active_switches())
        )
        active_links = tuple(
            sorted(
                (link.source_switch_id, link.destination_switch_id)
                for link in self.topology.links.values()
                if link.status == LinkStatus.UP
            )
        )
        return hash((active_switches, active_links))

    def _get_adjacency_dict(self) -> Dict[str, Dict[str, int]]:
        """获取活跃的邻接字典"""
        active_switches = {
            sw.switch_id for sw in self.topology.get_active_switches()
        }
        
        adjacency = defaultdict(dict)
        for link in self.topology.links.values():
            if (
                link.status == LinkStatus.UP
                and link.source_switch_id in active_switches
                and link.destination_switch_id in active_switches
            ):
                adjacency[link.source_switch_id][link.destination_switch_id] = link.cost
                adjacency[link.destination_switch_id][link.source_switch_id] = link.cost
        
        return dict(adjacency)

    def calculate_shortest_paths(
        self,
        source: str,
        destinations: Optional[List[str]] = None,
        force_full: bool = False,
    ) -> Dict[str, Tuple[float, Set[str]]]:
        """
        计算最短路径
        使用Dijkstra算法，支持增量计算
        """
        start_time = time.time()
        
        # 检查拓扑是否变化
        current_hash = self._calculate_topology_hash()
        topology_changed = (current_hash != self._last_topology_hash)
        
        if topology_changed or force_full:
            self.logger.debug("Topology changed, performing full calculation")
            self._cached_distances.clear()
            self._cached_predecessors.clear()
            self._last_topology_hash = current_hash
        
        # 检查是否有缓存的结果
        if source in self._cached_distances and not force_full:
            # 检查是否所有目标都已缓存
            if destinations:
                all_cached = all(
                    dest in self._cached_distances[source]
                    for dest in destinations
                )
                if all_cached:
                    self.logger.debug(f"Using cached paths for source {source}")
                    return {
                        dest: (
                            self._cached_distances[source][dest],
                            self._cached_predecessors[source][dest],
                        )
                        for dest in destinations
                    }
        
        # 执行Dijkstra算法
        adjacency = self._get_adjacency_dict()
        
        if source not in adjacency:
            return {}
        
        # 初始化距离和前驱
        distances: Dict[str, float] = defaultdict(lambda: float('inf'))
        distances[source] = 0
        
        predecessors: Dict[str, Set[str]] = defaultdict(set)
        
        # 优先队列
        priority_queue = [(0.0, source)]
        visited: Set[str] = set()
        
        # 目标集合（用于提前终止）
        target_set = set(destinations) if destinations else None
        
        while priority_queue:
            current_dist, current_node = heapq.heappop(priority_queue)
            
            if current_node in visited:
                continue
            
            visited.add(current_node)
            
            # 检查超时
            if time.time() - start_time > PERFORMANCE_CONFIG["route_calculation_timeout"]:
                self.logger.warning(
                    f"Route calculation timeout for source {source}"
                )
                break
            
            # 如果所有目标都已访问，提前终止
            if target_set and target_set.issubset(visited):
                self.logger.debug(
                    f"Early termination: all targets visited for source {source}"
                )
                break
            
            # 遍历邻居
            for neighbor, cost in adjacency.get(current_node, {}).items():
                new_dist = current_dist + cost
                
                if new_dist < distances[neighbor]:
                    # 找到更短的路径
                    distances[neighbor] = new_dist
                    predecessors[neighbor].clear()
                    predecessors[neighbor].add(current_node)
                    heapq.heappush(priority_queue, (new_dist, neighbor))
                elif new_dist == distances[neighbor] and new_dist != float('inf'):
                    # 找到等价路径（ECMP）
                    predecessors[neighbor].add(current_node)
        
        # 缓存结果
        self._cached_distances[source] = dict(distances)
        self._cached_predecessors[source] = {k: v.copy() for k, v in predecessors.items()}
        
        # 构建返回结果
        result = {}
        if destinations:
            for dest in destinations:
                if dest in distances and distances[dest] != float('inf'):
                    result[dest] = (distances[dest], predecessors.get(dest, set()))
        else:
            for dest, dist in distances.items():
                if dest != source and dist != float('inf'):
                    result[dest] = (dist, predecessors.get(dest, set()))
        
        calc_time = time.time() - start_time
        self.logger.debug(
            f"Shortest path calculation for {source} completed in {calc_time:.4f}s, "
            f"found {len(result)} paths"
        )
        
        return result


class HierarchicalRouteCalculator:
    """
    分层路由计算器
    利用网络拓扑的层次结构优化路由计算
    - 核心层：负责域间路由
    - 汇聚层：负责区域内路由
    - 接入层：负责本地路由
    """

    def __init__(self, topology: Topology):
        self.topology = topology
        self.logger = logging.getLogger(__name__)
        self._incremental_calculator = IncrementalRouteCalculator(topology)
        
        # 按类型分组的交换机
        self._core_switches: List[str] = []
        self._access_switches: List[str] = []
        self._pop_switches: List[str] = []
        self._group_switches()

    def _group_switches(self) -> None:
        """按类型分组交换机"""
        self._core_switches = []
        self._access_switches = []
        self._pop_switches = []
        
        for switch in self.topology.switches.values():
            if switch.switch_type == SwitchType.CORE:
                self._core_switches.append(switch.switch_id)
            elif switch.switch_type == SwitchType.ACCESS:
                self._access_switches.append(switch.switch_id)
            elif switch.switch_type == SwitchType.POP:
                self._pop_switches.append(switch.switch_id)
        
        self.logger.debug(
            f"Grouped switches: {len(self._core_switches)} core, "
            f"{len(self._access_switches)} access, {len(self._pop_switches)} POP"
        )

    def calculate_all_routes(self) -> Dict[str, Dict[str, Any]]:
        """
        分层计算所有路由
        1. 首先计算核心层之间的路由
        2. 然后计算各区域内的路由
        3. 最后汇总路由信息
        """
        start_time = time.time()
        all_routes: Dict[str, Dict[str, Any]] = {}
        
        # 确保交换机分组是最新的
        self._group_switches()
        
        # 计算核心层路由（作为骨干）
        core_routes = self._calculate_core_routes()
        
        # 计算各接入交换机的路由
        for access_id in self._access_switches:
            access_routes = self._calculate_access_routes(access_id, core_routes)
            all_routes[access_id] = access_routes
        
        # 计算各POP交换机的路由
        for pop_id in self._pop_switches:
            pop_routes = self._calculate_pop_routes(pop_id, core_routes)
            all_routes[pop_id] = pop_routes
        
        # 计算核心交换机的路由
        for core_id in self._core_switches:
            core_full_routes = self._calculate_core_full_routes(core_id)
            all_routes[core_id] = core_full_routes
        
        total_time = time.time() - start_time
        self.logger.info(
            f"Hierarchical route calculation completed in {total_time:.4f}s"
        )
        
        # 检查是否超时
        if total_time > PERFORMANCE_CONFIG["max_computation_time"]:
            self.logger.warning(
                f"Route calculation exceeded time limit: {total_time:.4f}s > "
                f"{PERFORMANCE_CONFIG['max_computation_time']}s"
            )
        
        return all_routes

    def _calculate_core_routes(self) -> Dict[str, Dict[str, Any]]:
        """计算核心层之间的路由"""
        routes: Dict[str, Dict[str, Any]] = {}
        
        for core_id in self._core_switches:
            # 计算到其他核心交换机的路由
            other_cores = [c for c in self._core_switches if c != core_id]
            if other_cores:
                result = self._incremental_calculator.calculate_shortest_paths(
                    core_id, other_cores
                )
                routes[core_id] = result
        
        return routes

    def _calculate_access_routes(
        self,
        access_id: str,
        core_routes: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """计算接入交换机的路由"""
        routes = {}
        
        # 1. 到核心交换机的路由（通常是直连或1跳）
        result = self._incremental_calculator.calculate_shortest_paths(
            access_id, self._core_switches
        )
        routes.update(result)
        
        # 2. 到其他接入交换机的路由（通过核心）
        other_accesses = [a for a in self._access_switches if a != access_id]
        if other_accesses:
            # 计算通过核心的路径
            access_result = self._incremental_calculator.calculate_shortest_paths(
                access_id, other_accesses
            )
            routes.update(access_result)
        
        # 3. 到POP交换机的路由
        pop_result = self._incremental_calculator.calculate_shortest_paths(
            access_id, self._pop_switches
        )
        routes.update(pop_result)
        
        return routes

    def _calculate_pop_routes(
        self,
        pop_id: str,
        core_routes: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """计算POP交换机的路由"""
        routes = {}
        
        # 1. 到核心交换机的路由
        result = self._incremental_calculator.calculate_shortest_paths(
            pop_id, self._core_switches
        )
        routes.update(result)
        
        # 2. 到接入交换机的路由
        access_result = self._incremental_calculator.calculate_shortest_paths(
            pop_id, self._access_switches
        )
        routes.update(access_result)
        
        # 3. 到其他POP交换机的路由
        other_pops = [p for p in self._pop_switches if p != pop_id]
        if other_pops:
            pop_result = self._incremental_calculator.calculate_shortest_paths(
                pop_id, other_pops
            )
            routes.update(pop_result)
        
        return routes

    def _calculate_core_full_routes(self, core_id: str) -> Dict[str, Any]:
        """计算核心交换机的完整路由"""
        all_destinations = (
            [c for c in self._core_switches if c != core_id]
            + self._access_switches
            + self._pop_switches
        )
        
        result = self._incremental_calculator.calculate_shortest_paths(
            core_id, all_destinations
        )
        return result


class ParallelRouteCalculator:
    """
    并行路由计算器
    使用多线程并行计算多个源的路由
    """

    def __init__(self, topology: Topology, max_workers: int = 4):
        self.topology = topology
        self.max_workers = max_workers
        self.logger = logging.getLogger(__name__)
        self._thread_local = threading.local()

    def _get_calculator(self) -> IncrementalRouteCalculator:
        """获取线程本地的计算器实例"""
        if not hasattr(self._thread_local, 'calculator'):
            self._thread_local.calculator = IncrementalRouteCalculator(self.topology)
        return self._thread_local.calculator

    def _calculate_for_source(self, args: Tuple[str, Optional[List[str]]]) -> Tuple[str, Dict[str, Any]]:
        """
        计算单个源的路由（用于多线程）
        """
        source, destinations = args
        calculator = self._get_calculator()
        result = calculator.calculate_shortest_paths(source, destinations)
        return (source, result)

    async def calculate_parallel(
        self,
        sources: List[str],
        destinations: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """
        并行计算多个源的路由
        """
        start_time = time.time()
        
        # 准备参数
        args_list = [(source, destinations) for source in sources]
        
        # 使用线程池执行
        loop = asyncio.get_event_loop()
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures = [
                loop.run_in_executor(executor, self._calculate_for_source, args)
                for args in args_list
            ]
            
            # 等待所有任务完成
            results = await asyncio.gather(*futures)
        
        # 整理结果
        all_routes = {}
        for source, routes in results:
            all_routes[source] = routes
        
        total_time = time.time() - start_time
        self.logger.info(
            f"Parallel route calculation for {len(sources)} sources "
            f"completed in {total_time:.4f}s"
        )
        
        return all_routes


class RouteCache:
    """
    路由缓存
    提供高效的路由缓存机制，减少重复计算
    """

    def __init__(self, max_size: int = 1000, ttl: float = 60.0):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[Tuple[str, str], RouteCacheEntry] = {}
        self._access_order: List[Tuple[str, str]] = []
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)

    def get(self, source: str, destination: str) -> Optional[List[Dict[str, Any]]]:
        """
        获取缓存的路由
        """
        key = (source, destination)
        
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            
            # 检查是否过期
            if time.time() - entry.timestamp > self.ttl:
                self.logger.debug(f"Cache entry expired for {source} -> {destination}")
                del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
                return None
            
            # 更新访问顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            # 更新命中计数
            entry.hit_count += 1
            
            return entry.paths

    def put(
        self,
        source: str,
        destination: str,
        paths: List[Dict[str, Any]],
    ) -> None:
        """
        缓存路由
        """
        key = (source, destination)
        
        with self._lock:
            # 检查是否需要清理
            if len(self._cache) >= self.max_size:
                self._evict()
            
            # 添加新条目
            self._cache[key] = RouteCacheEntry(
                source=source,
                destination=destination,
                paths=paths,
                timestamp=time.time(),
            )
            
            # 更新访问顺序
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)
            
            self.logger.debug(f"Cached route: {source} -> {destination}")

    def _evict(self, count: int = 10) -> None:
        """
        驱逐过期或最少使用的条目
        """
        # 首先驱逐过期的
        current_time = time.time()
        keys_to_remove = [
            key
            for key, entry in self._cache.items()
            if current_time - entry.timestamp > self.ttl
        ]
        
        for key in keys_to_remove:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
        
        # 如果还需要驱逐，使用LRU
        if len(self._cache) >= self.max_size:
            # 按访问顺序驱逐最早的
            keys_to_evict = self._access_order[:count]
            for key in keys_to_evict:
                if key in self._cache:
                    del self._cache[key]
                if key in self._access_order:
                    self._access_order.remove(key)
        
        self.logger.debug(f"Evicted {len(keys_to_remove)} cache entries")

    def invalidate(self, source: Optional[str] = None, destination: Optional[str] = None) -> None:
        """
        使缓存失效
        """
        with self._lock:
            if source is None and destination is None:
                # 清空所有
                self._cache.clear()
                self._access_order.clear()
                self.logger.info("Invalidated all cache entries")
            elif source is not None:
                # 使特定源的缓存失效
                keys_to_remove = [
                    key for key in self._cache if key[0] == source
                ]
                for key in keys_to_remove:
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                self.logger.info(f"Invalidated cache entries for source {source}")
            elif destination is not None:
                # 使特定目的地的缓存失效
                keys_to_remove = [
                    key for key in self._cache if key[1] == destination
                ]
                for key in keys_to_remove:
                    del self._cache[key]
                    if key in self._access_order:
                        self._access_order.remove(key)
                self.logger.info(f"Invalidated cache entries for destination {destination}")

    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计
        """
        with self._lock:
            total_hits = sum(entry.hit_count for entry in self._cache.values())
            
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "ttl": self.ttl,
                "total_hits": total_hits,
                "utilization": len(self._cache) / self.max_size if self.max_size > 0 else 0,
            }


def timed_operation(logger: logging.Logger, operation_name: str):
    """
    装饰器：记录操作执行时间
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                logger.debug(
                    f"Operation {operation_name} took {elapsed:.4f}s"
                )
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                logger.debug(
                    f"Operation {operation_name} took {elapsed:.4f}s"
                )
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
