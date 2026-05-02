"""
SD-WAN控制器主程序
整合所有模块，提供完整的SD-WAN控制功能
"""

import asyncio
import logging
import time
import json
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from .config import (
    NETWORK_TOPOLOGY,
    LINK_PARAMS,
    ROUTING_PROTOCOL,
    PERFORMANCE_CONFIG,
    LOGGING_CONFIG,
)
from .models import SwitchType, Route, RouteType
from .core_controller import CoreController
from .switch_simulator import SimulatedSwitch
from .communication import (
    ChannelBroker,
    ControlPlaneChannel,
    DataPlaneChannel,
    MessageType,
    MessagePriority,
)
from .performance_optimizer import (
    HierarchicalRouteCalculator,
    ParallelRouteCalculator,
    RouteCache,
    timed_operation,
)


# 配置日志
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG["level"]),
    format=LOGGING_CONFIG["format"],
    filename=LOGGING_CONFIG["file"],
)
logger = logging.getLogger(__name__)


@dataclass
class ControllerStats:
    """控制器统计信息"""
    startup_time: float
    topology_initialization_time: float
    initial_route_calculation_time: float
    total_route_calculations: int = 0
    total_topology_updates: int = 0
    average_calculation_time: float = 0.0


class SDWANController:
    """
    SD-WAN主控制器类
    整合所有模块，提供统一的控制接口
    """

    def __init__(self):
        self.startup_time = time.time()
        
        # 核心控制器
        self.core_controller = CoreController()
        
        # 模拟交换机
        self.switches: Dict[str, SimulatedSwitch] = {}
        
        # 通信机制
        self.channel_broker = ChannelBroker()
        self.control_channel: Optional[ControlPlaneChannel] = None
        
        # 性能优化组件
        self.hierarchical_calculator: Optional[HierarchicalRouteCalculator] = None
        self.parallel_calculator: Optional[ParallelRouteCalculator] = None
        self.route_cache: Optional[RouteCache] = None
        
        # 统计信息
        self.stats = ControllerStats(
            startup_time=self.startup_time,
            topology_initialization_time=0.0,
            initial_route_calculation_time=0.0,
        )
        
        self.running = False
        self._main_task: Optional[asyncio.Task] = None
        
        logger.info("SD-WAN Controller initialized")

    async def initialize(self) -> bool:
        """
        初始化控制器
        包括拓扑初始化、交换机创建、路由计算
        """
        logger.info("Initializing SD-WAN Controller...")
        
        try:
            # 1. 初始化核心控制器拓扑
            init_start = time.time()
            success = await self.core_controller.initialize_topology()
            if not success:
                logger.error("Failed to initialize core controller topology")
                return False
            self.stats.topology_initialization_time = time.time() - init_start
            
            # 2. 创建模拟交换机
            await self._create_simulated_switches()
            
            # 3. 初始化通信通道
            await self._initialize_communication()
            
            # 4. 初始化性能优化组件
            self.hierarchical_calculator = HierarchicalRouteCalculator(
                self.core_controller.topology
            )
            self.parallel_calculator = ParallelRouteCalculator(
                self.core_controller.topology,
                max_workers=4,
            )
            self.route_cache = RouteCache(
                max_size=1000,
                ttl=PERFORMANCE_CONFIG.get("cache_ttl", 60),
            )
            
            # 5. 执行初始路由计算
            route_start = time.time()
            success = await self.calculate_all_routes()
            if not success:
                logger.error("Failed to perform initial route calculation")
                return False
            self.stats.initial_route_calculation_time = time.time() - route_start
            
            logger.info(
                f"SD-WAN Controller initialized successfully. "
                f"Topology init: {self.stats.topology_initialization_time:.4f}s, "
                f"Route calc: {self.stats.initial_route_calculation_time:.4f}s"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error during initialization: {e}", exc_info=True)
            return False

    async def _create_simulated_switches(self) -> None:
        """创建模拟交换机"""
        logger.info("Creating simulated switches...")
        
        # 从核心控制器的拓扑创建模拟交换机
        for switch_id, switch_model in self.core_controller.topology.switches.items():
            simulated_switch = SimulatedSwitch(
                switch_id=switch_model.switch_id,
                name=switch_model.name,
                switch_type=switch_model.switch_type,
                ip_address=switch_model.ip_address,
                mac_address=switch_model.mac_address,
            )
            
            # 添加接口
            for iface in switch_model.interfaces:
                simulated_switch.add_interface(
                    name=iface["name"],
                    speed=iface["speed"],
                    status=iface["status"],
                    ip_address=switch_model.ip_address,
                    mac_address=switch_model.mac_address,
                )
            
            self.switches[switch_id] = simulated_switch
        
        # 建立交换机之间的连接
        await self._establish_switch_connections()
        
        logger.info(f"Created {len(self.switches)} simulated switches")

    async def _establish_switch_connections(self) -> None:
        """建立交换机之间的连接"""
        logger.info("Establishing switch connections...")
        
        connections_made = 0
        
        for link in self.core_controller.topology.links.values():
            source_switch = self.switches.get(link.source_switch_id)
            dest_switch = self.switches.get(link.destination_switch_id)
            
            if source_switch and dest_switch:
                # 使用第一个可用接口
                source_ifaces = list(source_switch.data_plane.interfaces.keys())
                dest_ifaces = list(dest_switch.data_plane.interfaces.keys())
                
                if source_ifaces and dest_ifaces:
                    source_switch.connect_to(
                        dest_switch,
                        source_ifaces[0],
                        dest_ifaces[0],
                    )
                    connections_made += 1
        
        logger.info(f"Established {connections_made} switch connections")

    async def _initialize_communication(self) -> None:
        """初始化通信通道"""
        logger.info("Initializing communication channels...")
        
        # 启动通道代理
        await self.channel_broker.start()
        
        # 创建控制平面通道
        self.control_channel = ControlPlaneChannel(controller_id="sdwan-controller")
        await self.control_channel.start()
        self.channel_broker.register_control_channel(self.control_channel)
        
        # 注册消息处理器
        self.control_channel.register_handler(
            MessageType.TOPOLOGY_REPORT,
            self._handle_topology_report,
        )
        self.control_channel.register_handler(
            MessageType.STATISTICS_REPORT,
            self._handle_statistics_report,
        )
        self.control_channel.register_handler(
            MessageType.PACKET_IN,
            self._handle_packet_in,
        )
        
        # 为每个交换机创建数据平面通道
        for switch_id, switch in self.switches.items():
            data_channel = DataPlaneChannel(switch_id=switch_id)
            await data_channel.start()
            self.channel_broker.register_data_channel(data_channel)
            
            # 注册交换机的消息处理器
            data_channel.register_handler(
                MessageType.ROUTE_UPDATE,
                self._create_route_update_handler(switch),
            )
            data_channel.register_handler(
                MessageType.FLOW_INSTALL,
                self._create_flow_install_handler(switch),
            )
        
        logger.info("Communication channels initialized")

    async def _handle_topology_report(self, message) -> None:
        """处理拓扑报告消息"""
        logger.debug(f"Received topology report from {message.source}")
        # TODO: 处理拓扑报告

    async def _handle_statistics_report(self, message) -> None:
        """处理统计报告消息"""
        logger.debug(f"Received statistics report from {message.source}")
        # TODO: 处理统计报告

    async def _handle_packet_in(self, message) -> None:
        """处理Packet-In消息"""
        logger.debug(f"Received packet-in from {message.source}")
        # TODO: 处理Packet-In

    def _create_route_update_handler(self, switch: SimulatedSwitch):
        """创建路由更新消息处理器"""
        async def handler(message):
            logger.debug(
                f"Switch {switch.switch_id} received route update"
            )
            # TODO: 应用路由更新
        return handler

    def _create_flow_install_handler(self, switch: SimulatedSwitch):
        """创建流表安装消息处理器"""
        async def handler(message):
            logger.debug(
                f"Switch {switch.switch_id} received flow install"
            )
            # TODO: 安装流表
        return handler

    @timed_operation(logger, "calculate_all_routes")
    async def calculate_all_routes(
        self,
        optimize_strategy: str = "cost",
        force_full_calculation: bool = True,
    ) -> bool:
        """
        计算所有路由
        
        参数:
            optimize_strategy: 优化策略
            force_full_calculation: 是否强制全量计算（禁用分层优化、缓存和提前退出）
        """
        if force_full_calculation:
            logger.info(
                "Calculating ALL routes in FULL mode "
                "(no hierarchical optimization, no cache, complete Dijkstra for all nodes)..."
            )
            # 全量计算模式：直接使用核心控制器的全量计算
            result = await self.core_controller.calculate_all_routes(
                optimize_strategy=optimize_strategy,
                force_full_calculation=True,
            )
            
            # 将核心控制器的路由表应用到模拟交换机
            await self._apply_routes_from_core_controller()
            
            # 更新统计
            self.stats.total_route_calculations += 1
            
            return result
        else:
            logger.info("Calculating all routes with optimization...")
            
            if not self.hierarchical_calculator:
                # 回退到核心控制器的计算方法
                return await self.core_controller.calculate_all_routes(
                    optimize_strategy=optimize_strategy,
                    force_full_calculation=False,
                )
            
            # 使用分层路由计算器
            routes = self.hierarchical_calculator.calculate_all_routes()
            
            # 更新统计
            self.stats.total_route_calculations += 1
            
            # 将路由应用到交换机
            await self._apply_routes_to_switches(routes)
            
            logger.info(f"Route calculation complete for {len(routes)} switches")
            return True

    async def _apply_routes_to_switches(
        self,
        routes: Dict[str, Dict[str, Any]],
    ) -> None:
        """将路由应用到交换机"""
        for switch_id, switch_routes in routes.items():
            switch = self.switches.get(switch_id)
            if switch:
                # 转换为Route对象
                route_objects = {}
                for dest, (cost, predecessors) in switch_routes.items():
                    # 构建下一跳信息
                    next_hop = None
                    if predecessors:
                        # 选择一个下一跳
                        next_hop = next(iter(predecessors))
                    
                    route = Route(
                        route_id=f"route-{switch_id}-{dest}",
                        destination=dest,
                        next_hop=next_hop or dest,
                        cost=int(cost),
                        route_type=RouteType.DYNAMIC,
                        interface="",  # 接口将在数据平面确定
                    )
                    route_objects[dest] = route
                
                # 更新交换机路由表
                switch.update_routing_table(route_objects)
        
        logger.debug(f"Applied routes to {len(routes)} switches")

    async def _apply_routes_from_core_controller(self) -> None:
        """将核心控制器的路由表应用到模拟交换机"""
        applied_count = 0
        
        for switch_id, routing_table in self.core_controller.routing_tables.items():
            switch = self.switches.get(switch_id)
            if switch:
                # 将路由表转换为Route对象字典
                route_objects = {}
                for dest, route in routing_table.routes.items():
                    route_objects[dest] = route
                
                # 更新交换机路由表
                switch.update_routing_table(route_objects)
                applied_count += 1
        
        logger.info(f"Applied routes from core controller to {applied_count} switches")

    def get_path_between(
        self,
        source: str,
        destination: str,
        optimize_strategy: str = "cost",
        force_full: bool = False,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        获取两个节点之间的路径
        
        参数:
            source: 源节点ID
            destination: 目标节点ID
            optimize_strategy: 优化策略
            force_full: 是否强制全量计算（禁用缓存）
        """
        # 全量计算模式下禁用缓存
        if not force_full and self.route_cache:
            cached = self.route_cache.get(source, destination)
            if cached:
                logger.debug(f"Using cached path: {source} -> {destination}")
                return cached
        
        # 计算路径
        paths = self.core_controller.get_path_between(
            source=source,
            destination=destination,
            optimize_strategy=optimize_strategy,
            force_full=force_full,
        )
        
        if paths:
            # 转换为可缓存的格式
            cacheable_paths = [
                {
                    "path_id": path.path_id,
                    "source": path.source,
                    "destination": path.destination,
                    "nodes": path.nodes,
                    "total_cost": path.total_cost,
                    "latency": path.latency,
                    "bandwidth": path.bandwidth,
                    "is_primary": path.is_primary,
                }
                for path in paths
            ]
            
            # 缓存结果（非全量模式）
            if not force_full and self.route_cache:
                self.route_cache.put(source, destination, cacheable_paths)
            
            return cacheable_paths
        
        return None

    async def update_link_status(
        self,
        link_id: str,
        new_status: str,
    ) -> bool:
        """
        更新链路状态
        触发增量路由计算
        """
        logger.info(f"Updating link {link_id} status to {new_status}")
        
        link = self.core_controller.topology.get_link(link_id)
        if not link:
            logger.warning(f"Link {link_id} not found")
            return False
        
        # 更新链路状态
        from .models import LinkStatus
        link.status = LinkStatus(new_status)
        
        # 使相关缓存失效
        if self.route_cache:
            self.route_cache.invalidate(source=link.source_switch_id)
            self.route_cache.invalidate(source=link.destination_switch_id)
        
        # 更新统计
        self.stats.total_topology_updates += 1
        
        # 触发重新计算
        # 对于链路状态变化，可以只重新计算受影响的路径
        # 这里简化为全量重新计算
        await self.calculate_all_routes()
        
        logger.info(f"Link {link_id} status updated, routes recalculated")
        return True

    def get_status(self) -> Dict[str, Any]:
        """
        获取控制器状态
        """
        topology_summary = self.core_controller.get_topology_summary()
        
        return {
            "controller": {
                "version": "1.0.0",
                "running": self.running,
                "startup_time": self.startup_time,
                "uptime": time.time() - self.startup_time,
            },
            "topology": topology_summary,
            "statistics": {
                "total_route_calculations": self.stats.total_route_calculations,
                "total_topology_updates": self.stats.total_topology_updates,
                "initial_route_calculation_time": self.stats.initial_route_calculation_time,
                "topology_initialization_time": self.stats.topology_initialization_time,
            },
            "cache": self.route_cache.get_stats() if self.route_cache else {},
            "switches": {
                switch_id: switch.get_status()
                for switch_id, switch in self.switches.items()
            },
        }

    async def start(self) -> None:
        """启动控制器"""
        if self.running:
            logger.warning("Controller is already running")
            return
        
        # 首先初始化
        success = await self.initialize()
        if not success:
            logger.error("Failed to initialize controller")
            return
        
        self.running = True
        
        # 启动所有交换机
        for switch in self.switches.values():
            await switch.start()
        
        logger.info("SD-WAN Controller started successfully")
        
        # 打印启动摘要
        self._print_startup_summary()

    async def stop(self) -> None:
        """停止控制器"""
        if not self.running:
            logger.warning("Controller is not running")
            return
        
        self.running = False
        
        # 停止所有交换机
        for switch in self.switches.values():
            await switch.stop()
        
        # 停止通信通道
        await self.channel_broker.stop()
        
        logger.info("SD-WAN Controller stopped")

    def _print_startup_summary(self) -> None:
        """打印启动摘要"""
        topology = self.core_controller.get_topology_summary()
        
        print("\n" + "=" * 60)
        print("SD-WAN LAN Controller - Startup Summary")
        print("=" * 60)
        print(f"\nNetwork Topology:")
        print(f"  Total Switches: {topology['total_switches']}")
        print(f"  Active Switches: {topology['active_switches']}")
        print(f"    - Core: {topology['core_switches']}")
        print(f"    - Access: {topology['access_switches']}")
        print(f"    - POP: {topology['pop_switches']}")
        print(f"  Total Links: {topology['total_links']}")
        print(f"  Active Links: {topology['active_links']}")
        print(f"\nPerformance:")
        print(f"  Topology Initialization: {self.stats.topology_initialization_time:.4f}s")
        print(f"  Initial Route Calculation: {self.stats.initial_route_calculation_time:.4f}s")
        print(f"  Target Max Calculation Time: {PERFORMANCE_CONFIG['max_computation_time']}s")
        print(f"\nFeatures:")
        print(f"  Dynamic Routing Protocol: {ROUTING_PROTOCOL['protocol_type']}")
        print(f"  ECMP Enabled: {ROUTING_PROTOCOL['ecmp_enabled']}")
        print(f"  Max ECMP Paths: {ROUTING_PROTOCOL['max_ecmp_paths']}")
        print(f"  Route Caching: {PERFORMANCE_CONFIG['cache_enabled']}")
        print(f"  Control/Data Plane Isolation: Enabled")
        print("\n" + "=" * 60)
        print("Controller is running. Press Ctrl+C to stop.")
        print("=" * 60 + "\n")


async def main():
    """主函数"""
    controller = SDWANController()
    
    try:
        await controller.start()
        
        # 保持运行
        while controller.running:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await controller.stop()


if __name__ == "__main__":
    asyncio.run(main())
