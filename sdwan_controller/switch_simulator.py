"""
交换机模拟器模块
模拟网络交换机的数据平面和控制平面功能
"""

import asyncio
import time
import uuid
import logging
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import deque

from .config import (
    NETWORK_TOPOLOGY,
    LINK_PARAMS,
    ROUTING_PROTOCOL,
    COMMUNICATION_CONFIG,
)
from .models import Switch, Link, RoutingTable, Route, SwitchType, LinkStatus, RouteType
from .routing_protocol import LinkStateRouting, HelloPacket, LinkStateAdvertisement


class PacketType(Enum):
    """数据包类型枚举"""
    CONTROL = "control"
    DATA = "data"
    HELLO = "hello"
    LSA = "lsa"
    ARP = "arp"
    ICMP = "icmp"


@dataclass
class Packet:
    """数据包结构"""
    packet_id: str
    packet_type: PacketType
    source_ip: str
    destination_ip: str
    source_mac: str
    destination_mac: str
    source_switch_id: str
    destination_switch_id: Optional[str]
    payload: Dict[str, Any]
    ttl: int = 64
    timestamp: float = field(default_factory=time.time)
    is_broadcast: bool = False


@dataclass
class Interface:
    """网络接口"""
    name: str
    speed: int
    status: str
    ip_address: str
    mac_address: str
    connected_to: Optional[Tuple[str, str]] = None  # (switch_id, interface_name)
    input_packets: int = 0
    output_packets: int = 0
    input_errors: int = 0
    output_errors: int = 0
    last_flapped: float = field(default_factory=time.time)


@dataclass
class MacAddressTableEntry:
    """MAC地址表条目"""
    mac_address: str
    interface: str
    vlan_id: int = 1
    timestamp: float = field(default_factory=time.time)
    is_static: bool = False


class DataPlane:
    """
    数据平面实现
    负责数据包转发、MAC地址学习等功能
    """

    def __init__(self, switch_id: str, mac_address: str):
        self.switch_id = switch_id
        self.switch_mac = mac_address
        self.interfaces: Dict[str, Interface] = {}
        self.mac_address_table: Dict[str, MacAddressTableEntry] = {}
        self.routing_table: Dict[str, Route] = {}
        self.arp_cache: Dict[str, str] = {}  # IP -> MAC
        self.packet_buffer: deque = deque(maxlen=1000)
        self.logger = logging.getLogger(f"{switch_id}-dataplane")
        self.running = False
        self._forwarding_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """启动数据平面"""
        self.running = True
        self._forwarding_task = asyncio.create_task(self._forwarding_loop())
        self.logger.info("Data plane started")

    async def stop(self) -> None:
        """停止数据平面"""
        self.running = False
        if self._forwarding_task:
            self._forwarding_task.cancel()
            try:
                await self._forwarding_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Data plane stopped")

    def add_interface(self, interface: Interface) -> None:
        """添加网络接口"""
        self.interfaces[interface.name] = interface
        self.logger.debug(f"Added interface {interface.name}")

    def remove_interface(self, interface_name: str) -> None:
        """移除网络接口"""
        if interface_name in self.interfaces:
            del self.interfaces[interface_name]
            self.logger.debug(f"Removed interface {interface_name}")

    def update_routing_table(self, routes: Dict[str, Route]) -> None:
        """更新路由表"""
        self.routing_table = routes.copy()
        self.logger.debug(f"Updated routing table with {len(routes)} routes")

    async def _forwarding_loop(self) -> None:
        """数据包转发循环"""
        while self.running:
            try:
                if self.packet_buffer:
                    packet = self.packet_buffer.popleft()
                    await self._forward_packet(packet)
                else:
                    await asyncio.sleep(0.001)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Error in forwarding loop: {e}")
                await asyncio.sleep(0.1)

    async def _forward_packet(self, packet: Packet) -> None:
        """转发数据包"""
        # 递减TTL
        packet.ttl -= 1
        if packet.ttl <= 0:
            self.logger.debug(f"Packet {packet.packet_id} TTL expired")
            return

        # 根据数据包类型处理
        if packet.packet_type == PacketType.CONTROL:
            # 控制平面数据包，交给控制平面处理
            await self._handle_control_packet(packet)
            return

        # 学习源MAC地址
        self._learn_mac_address(
            packet.source_mac,
            packet.source_switch_id,  # 实际应该是入接口
        )

        # 检查是否是发送给自己的
        if packet.destination_switch_id == self.switch_id:
            await self._handle_local_packet(packet)
            return

        # 路由查找
        outgoing_interface, next_hop = self._route_lookup(packet)
        
        if outgoing_interface:
            # 更新接口统计
            if outgoing_interface in self.interfaces:
                self.interfaces[outgoing_interface].output_packets += 1
            
            self.logger.debug(
                f"Forwarding packet {packet.packet_id} to {packet.destination_ip} "
                f"via interface {outgoing_interface}"
            )
        else:
            # 没有找到路由，丢弃
            self.logger.debug(
                f"No route found for packet {packet.packet_id} to {packet.destination_ip}"
            )

    def _learn_mac_address(self, mac_address: str, interface: str) -> None:
        """学习MAC地址"""
        if mac_address not in self.mac_address_table:
            entry = MacAddressTableEntry(
                mac_address=mac_address,
                interface=interface,
            )
            self.mac_address_table[mac_address] = entry
            self.logger.debug(f"Learned MAC address {mac_address} on {interface}")
        else:
            # 更新时间戳
            self.mac_address_table[mac_address].timestamp = time.time()

    def _route_lookup(self, packet: Packet) -> Tuple[Optional[str], Optional[str]]:
        """
        路由查找
        返回(出接口, 下一跳)
        """
        destination = packet.destination_ip
        
        # 最长前缀匹配（简化版本）
        best_match = None
        longest_prefix = -1
        
        for dest_prefix, route in self.routing_table.items():
            # 简化的前缀匹配
            if destination.startswith(dest_prefix):
                prefix_len = len(dest_prefix)
                if prefix_len > longest_prefix:
                    longest_prefix = prefix_len
                    best_match = route
        
        if best_match:
            # 确定出接口
            if best_match.is_ecmp and best_match.ecmp_paths:
                # ECMP负载均衡
                # 简化：随机选择一个路径
                import random
                ecmp_path = random.choice(best_match.ecmp_paths)
                return ecmp_path.get("interface"), ecmp_path.get("next_hop")
            else:
                return best_match.interface, best_match.next_hop
        
        # 默认路由
        if "0.0.0.0" in self.routing_table:
            default_route = self.routing_table["0.0.0.0"]
            return default_route.interface, default_route.next_hop
        
        return None, None

    async def _handle_control_packet(self, packet: Packet) -> None:
        """处理控制平面数据包"""
        self.logger.debug(
            f"Received control packet {packet.packet_id} from {packet.source_ip}"
        )
        # 实际环境中会通过IPC发送到控制平面

    async def _handle_local_packet(self, packet: Packet) -> None:
        """处理发送给本机的数据包"""
        self.logger.debug(
            f"Received local packet {packet.packet_id} from {packet.source_ip}"
        )
        # 根据协议类型处理

    async def receive_packet(self, packet: Packet, ingress_interface: str) -> None:
        """接收数据包"""
        # 更新入接口统计
        if ingress_interface in self.interfaces:
            self.interfaces[ingress_interface].input_packets += 1
        
        # 添加到缓冲区
        self.packet_buffer.append(packet)
        self.logger.debug(
            f"Received packet {packet.packet_id} on interface {ingress_interface}"
        )

    def get_interface_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取接口统计"""
        return {
            name: {
                "speed": iface.speed,
                "status": iface.status,
                "input_packets": iface.input_packets,
                "output_packets": iface.output_packets,
                "input_errors": iface.input_errors,
                "output_errors": iface.output_errors,
            }
            for name, iface in self.interfaces.items()
        }

    def get_mac_table_size(self) -> int:
        """获取MAC地址表大小"""
        return len(self.mac_address_table)

    def get_routing_table_size(self) -> int:
        """获取路由表大小"""
        return len(self.routing_table)


class ControlPlane:
    """
    控制平面实现
    负责路由协议、拓扑发现等功能
    与数据平面完全隔离
    """

    def __init__(
        self,
        switch_id: str,
        switch_type: SwitchType,
        ip_address: str,
        mac_address: str,
    ):
        self.switch_id = switch_id
        self.switch_type = switch_type
        self.ip_address = ip_address
        self.mac_address = mac_address
        self.routing_protocol: Optional[LinkStateRouting] = None
        self.routing_table: RoutingTable = RoutingTable(switch_id=switch_id)
        self.neighbors: Set[str] = set()
        self.logger = logging.getLogger(f"{switch_id}-controlplane")
        self.running = False
        self._control_tasks: List[asyncio.Task] = []

        # 与数据平面通信的回调
        self.send_to_dataplane_callback = None
        self.receive_from_dataplane_callback = None

    async def start(self) -> None:
        """启动控制平面"""
        self.running = True
        
        # 初始化路由协议
        self.routing_protocol = LinkStateRouting(
            router_id=self.switch_id,
            router_ip=self.ip_address,
            area_id=0,
        )
        
        # 设置LSA通信回调
        self.routing_protocol.send_lsa_callback = self._send_lsa_to_neighbors
        self.routing_protocol.receive_lsa_callback = self._receive_lsa
        
        await self.routing_protocol.start()
        
        self.logger.info("Control plane started")

    async def stop(self) -> None:
        """停止控制平面"""
        self.running = False
        
        if self.routing_protocol:
            await self.routing_protocol.stop()
        
        # 取消所有任务
        for task in self._control_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Control plane stopped")

    async def _send_lsa_to_neighbors(self, lsa: LinkStateAdvertisement) -> None:
        """发送LSA到邻居"""
        for neighbor_id in self.neighbors:
            self.logger.debug(
                f"Would send LSA {lsa.lsa_id} to neighbor {neighbor_id}"
            )
            # 实际环境中会通过数据平面发送

    async def _receive_lsa(
        self, lsa: LinkStateAdvertisement, source_router: str
    ) -> None:
        """接收LSA"""
        if self.routing_protocol:
            await self.routing_protocol.receive_lsa(lsa, source_router)

    def add_neighbor(self, neighbor_id: str) -> None:
        """添加邻居"""
        if neighbor_id not in self.neighbors:
            self.neighbors.add(neighbor_id)
            self.logger.info(f"Added neighbor: {neighbor_id}")

    def remove_neighbor(self, neighbor_id: str) -> None:
        """移除邻居"""
        if neighbor_id in self.neighbors:
            self.neighbors.remove(neighbor_id)
            self.logger.info(f"Removed neighbor: {neighbor_id}")

    async def generate_router_lsa(self, links: List[Dict[str, Any]]) -> None:
        """生成路由器LSA"""
        if self.routing_protocol:
            await self.routing_protocol.generate_router_lsa(links)

    def get_routing_table(self) -> RoutingTable:
        """获取路由表"""
        return self.routing_table

    def update_routing_table(self, routes: Dict[str, Route]) -> None:
        """更新路由表"""
        for destination, route in routes.items():
            self.routing_table.add_route(route)
        self.logger.debug(f"Updated routing table with {len(routes)} routes")

    def get_status(self) -> Dict[str, Any]:
        """获取控制平面状态"""
        protocol_status = {}
        if self.routing_protocol:
            protocol_status = self.routing_protocol.get_status()
        
        return {
            "switch_id": self.switch_id,
            "switch_type": self.switch_type.value,
            "ip_address": self.ip_address,
            "running": self.running,
            "neighbors": list(self.neighbors),
            "routing_table_size": len(self.routing_table.routes),
            "protocol_status": protocol_status,
        }


class SimulatedSwitch:
    """
    模拟交换机
    整合控制平面和数据平面，实现完整的交换机功能
    """

    def __init__(
        self,
        switch_id: str,
        name: str,
        switch_type: SwitchType,
        ip_address: str,
        mac_address: str,
    ):
        self.switch_id = switch_id
        self.name = name
        self.switch_type = switch_type
        self.ip_address = ip_address
        self.mac_address = mac_address
        
        # 创建控制平面和数据平面（完全隔离）
        self.control_plane = ControlPlane(
            switch_id=switch_id,
            switch_type=switch_type,
            ip_address=ip_address,
            mac_address=mac_address,
        )
        
        self.data_plane = DataPlane(
            switch_id=switch_id,
            mac_address=mac_address,
        )
        
        # 建立控制平面和数据平面之间的通信通道
        self._setup_inter_plane_communication()
        
        self.logger = logging.getLogger(switch_id)
        self.running = False

    def _setup_inter_plane_communication(self) -> None:
        """建立控制平面和数据平面之间的通信"""
        # 控制平面 -> 数据平面
        self.control_plane.send_to_dataplane_callback = self._control_to_data
        
        # 数据平面 -> 控制平面
        # 实际环境中会通过IPC或消息队列实现

    async def _control_to_data(self, message: Dict[str, Any]) -> None:
        """控制平面到数据平面的通信"""
        message_type = message.get("type")
        
        if message_type == "update_routes":
            routes = message.get("routes", {})
            self.data_plane.update_routing_table(routes)
            self.logger.debug("Updated data plane routing table from control plane")

    async def start(self) -> None:
        """启动交换机"""
        self.running = True
        
        # 启动数据平面
        await self.data_plane.start()
        
        # 启动控制平面
        await self.control_plane.start()
        
        self.logger.info(f"Switch {self.switch_id} started")

    async def stop(self) -> None:
        """停止交换机"""
        self.running = False
        
        # 停止控制平面
        await self.control_plane.stop()
        
        # 停止数据平面
        await self.data_plane.stop()
        
        self.logger.info(f"Switch {self.switch_id} stopped")

    def add_interface(
        self,
        name: str,
        speed: int,
        status: str,
        ip_address: str,
        mac_address: str,
    ) -> None:
        """添加网络接口"""
        interface = Interface(
            name=name,
            speed=speed,
            status=status,
            ip_address=ip_address,
            mac_address=mac_address,
        )
        self.data_plane.add_interface(interface)
        self.logger.debug(f"Added interface {name}")

    def connect_to(
        self,
        other_switch: 'SimulatedSwitch',
        local_interface: str,
        remote_interface: str,
    ) -> None:
        """连接到另一个交换机"""
        # 更新本地接口
        if local_interface in self.data_plane.interfaces:
            self.data_plane.interfaces[local_interface].connected_to = (
                other_switch.switch_id,
                remote_interface,
            )
        
        # 更新远程接口
        if remote_interface in other_switch.data_plane.interfaces:
            other_switch.data_plane.interfaces[remote_interface].connected_to = (
                self.switch_id,
                local_interface,
            )
        
        # 添加邻居关系
        self.control_plane.add_neighbor(other_switch.switch_id)
        other_switch.control_plane.add_neighbor(self.switch_id)
        
        self.logger.info(
            f"Connected {self.switch_id}:{local_interface} to "
            f"{other_switch.switch_id}:{remote_interface}"
        )

    async def send_packet(
        self,
        packet: Packet,
        egress_interface: str,
    ) -> None:
        """发送数据包"""
        if egress_interface not in self.data_plane.interfaces:
            self.logger.warning(f"Interface {egress_interface} not found")
            return
        
        interface = self.data_plane.interfaces[egress_interface]
        if interface.connected_to is None:
            self.logger.warning(f"Interface {egress_interface} not connected")
            return
        
        # 实际环境中会通过网络发送
        # 这里简化为直接调用目标交换机的receive_packet
        destination_switch_id, destination_interface = interface.connected_to
        
        self.logger.debug(
            f"Sending packet {packet.packet_id} to {destination_switch_id}"
        )
        
        # 更新统计
        interface.output_packets += 1

    async def receive_packet(
        self,
        packet: Packet,
        ingress_interface: str,
    ) -> None:
        """接收数据包"""
        await self.data_plane.receive_packet(packet, ingress_interface)

    def update_routing_table(self, routes: Dict[str, Route]) -> None:
        """
        更新路由表（由控制器调用）
        同时更新控制平面和数据平面的路由表
        """
        # 更新控制平面路由表
        self.control_plane.update_routing_table(routes)
        
        # 更新数据平面路由表
        self.data_plane.update_routing_table(routes)
        
        self.logger.info(f"Updated routing table with {len(routes)} routes")

    def get_status(self) -> Dict[str, Any]:
        """获取交换机状态"""
        return {
            "switch_id": self.switch_id,
            "name": self.name,
            "switch_type": self.switch_type.value,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "running": self.running,
            "control_plane": self.control_plane.get_status(),
            "data_plane": {
                "interfaces": self.data_plane.get_interface_stats(),
                "mac_table_size": self.data_plane.get_mac_table_size(),
                "routing_table_size": self.data_plane.get_routing_table_size(),
            },
        }

    def to_model(self) -> Switch:
        """转换为Switch模型"""
        return Switch(
            switch_id=self.switch_id,
            name=self.name,
            switch_type=self.switch_type,
            ip_address=self.ip_address,
            mac_address=self.mac_address,
            interfaces=[
                {
                    "name": name,
                    "speed": iface.speed,
                    "status": iface.status,
                    "ip_address": iface.ip_address,
                    "mac_address": iface.mac_address,
                }
                for name, iface in self.data_plane.interfaces.items()
            ],
            neighbors=list(self.control_plane.neighbors),
            is_active=self.running,
        )
