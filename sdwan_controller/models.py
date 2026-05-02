"""
SD-WAN控制器核心数据模型
定义交换机、链路、拓扑和路由相关的数据结构
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid


class SwitchType(Enum):
    """交换机类型枚举"""
    CORE = "core"
    ACCESS = "access"
    POP = "pop"


class LinkStatus(Enum):
    """链路状态枚举"""
    UP = "up"
    DOWN = "down"
    UNKNOWN = "unknown"


class RouteType(Enum):
    """路由类型枚举"""
    DIRECT = "direct"
    STATIC = "static"
    DYNAMIC = "dynamic"


@dataclass
class Switch:
    """交换机数据模型"""
    switch_id: str
    name: str
    switch_type: SwitchType
    ip_address: str
    mac_address: str
    interfaces: List[Dict[str, Any]] = field(default_factory=list)
    neighbors: List[str] = field(default_factory=list)
    is_active: bool = True
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "switch_id": self.switch_id,
            "name": self.name,
            "switch_type": self.switch_type.value,
            "ip_address": self.ip_address,
            "mac_address": self.mac_address,
            "interfaces": self.interfaces,
            "neighbors": self.neighbors,
            "is_active": self.is_active,
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Switch':
        """从字典创建交换机实例"""
        return cls(
            switch_id=data["switch_id"],
            name=data["name"],
            switch_type=SwitchType(data["switch_type"]),
            ip_address=data["ip_address"],
            mac_address=data["mac_address"],
            interfaces=data.get("interfaces", []),
            neighbors=data.get("neighbors", []),
            is_active=data.get("is_active", True),
            last_updated=datetime.fromisoformat(data["last_updated"])
            if "last_updated" in data
            else datetime.now(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Link:
    """链路数据模型"""
    link_id: str
    source_switch_id: str
    destination_switch_id: str
    source_interface: str
    destination_interface: str
    cost: int
    bandwidth: int
    latency: float
    status: LinkStatus = LinkStatus.UP
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "link_id": self.link_id,
            "source_switch_id": self.source_switch_id,
            "destination_switch_id": self.destination_switch_id,
            "source_interface": self.source_interface,
            "destination_interface": self.destination_interface,
            "cost": self.cost,
            "bandwidth": self.bandwidth,
            "latency": self.latency,
            "status": self.status.value,
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Link':
        """从字典创建链路实例"""
        return cls(
            link_id=data["link_id"],
            source_switch_id=data["source_switch_id"],
            destination_switch_id=data["destination_switch_id"],
            source_interface=data["source_interface"],
            destination_interface=data["destination_interface"],
            cost=data["cost"],
            bandwidth=data["bandwidth"],
            latency=data["latency"],
            status=LinkStatus(data["status"]),
            last_updated=datetime.fromisoformat(data["last_updated"])
            if "last_updated" in data
            else datetime.now(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Route:
    """路由数据模型"""
    route_id: str
    destination: str
    next_hop: str
    cost: int
    route_type: RouteType
    interface: str
    is_ecmp: bool = False
    ecmp_paths: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "route_id": self.route_id,
            "destination": self.destination,
            "next_hop": self.next_hop,
            "cost": self.cost,
            "route_type": self.route_type.value,
            "interface": self.interface,
            "is_ecmp": self.is_ecmp,
            "ecmp_paths": self.ecmp_paths,
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Route':
        """从字典创建路由实例"""
        return cls(
            route_id=data["route_id"],
            destination=data["destination"],
            next_hop=data["next_hop"],
            cost=data["cost"],
            route_type=RouteType(data["route_type"]),
            interface=data["interface"],
            is_ecmp=data.get("is_ecmp", False),
            ecmp_paths=data.get("ecmp_paths", []),
            last_updated=datetime.fromisoformat(data["last_updated"])
            if "last_updated" in data
            else datetime.now(),
            metadata=data.get("metadata", {}),
        )


@dataclass
class Topology:
    """网络拓扑数据模型"""
    topology_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    switches: Dict[str, Switch] = field(default_factory=dict)
    links: Dict[str, Link] = field(default_factory=dict)
    adjacency_matrix: Dict[str, Dict[str, int]] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_switch(self, switch: Switch) -> None:
        """添加交换机到拓扑"""
        self.switches[switch.switch_id] = switch
        if switch.switch_id not in self.adjacency_matrix:
            self.adjacency_matrix[switch.switch_id] = {}
        self.last_updated = datetime.now()

    def remove_switch(self, switch_id: str) -> None:
        """从拓扑中移除交换机"""
        if switch_id in self.switches:
            del self.switches[switch_id]
        if switch_id in self.adjacency_matrix:
            del self.adjacency_matrix[switch_id]
        # 移除所有相关链路
        links_to_remove = [
            link_id
            for link_id, link in self.links.items()
            if link.source_switch_id == switch_id
            or link.destination_switch_id == switch_id
        ]
        for link_id in links_to_remove:
            self.remove_link(link_id)
        self.last_updated = datetime.now()

    def add_link(self, link: Link) -> None:
        """添加链路到拓扑"""
        self.links[link.link_id] = link
        # 更新邻接矩阵
        if link.source_switch_id not in self.adjacency_matrix:
            self.adjacency_matrix[link.source_switch_id] = {}
        self.adjacency_matrix[link.source_switch_id][
            link.destination_switch_id
        ] = link.cost
        # 添加反向链路
        if link.destination_switch_id not in self.adjacency_matrix:
            self.adjacency_matrix[link.destination_switch_id] = {}
        self.adjacency_matrix[link.destination_switch_id][
            link.source_switch_id
        ] = link.cost
        self.last_updated = datetime.now()

    def remove_link(self, link_id: str) -> None:
        """从拓扑中移除链路"""
        if link_id in self.links:
            link = self.links[link_id]
            # 从邻接矩阵中移除
            if (
                link.source_switch_id in self.adjacency_matrix
                and link.destination_switch_id
                in self.adjacency_matrix[link.source_switch_id]
            ):
                del self.adjacency_matrix[link.source_switch_id][
                    link.destination_switch_id
                ]
            if (
                link.destination_switch_id in self.adjacency_matrix
                and link.source_switch_id
                in self.adjacency_matrix[link.destination_switch_id]
            ):
                del self.adjacency_matrix[link.destination_switch_id][
                    link.source_switch_id
                ]
            del self.links[link_id]
            self.last_updated = datetime.now()

    def get_switch(self, switch_id: str) -> Optional[Switch]:
        """获取指定交换机"""
        return self.switches.get(switch_id)

    def get_link(self, link_id: str) -> Optional[Link]:
        """获取指定链路"""
        return self.links.get(link_id)

    def get_links_by_switch(self, switch_id: str) -> List[Link]:
        """获取与指定交换机相关的所有链路"""
        return [
            link
            for link in self.links.values()
            if link.source_switch_id == switch_id
            or link.destination_switch_id == switch_id
        ]

    def get_active_switches(self) -> List[Switch]:
        """获取所有活跃的交换机"""
        return [switch for switch in self.switches.values() if switch.is_active]

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "topology_id": self.topology_id,
            "switches": {
                switch_id: switch.to_dict()
                for switch_id, switch in self.switches.items()
            },
            "links": {
                link_id: link.to_dict() for link_id, link in self.links.items()
            },
            "adjacency_matrix": self.adjacency_matrix,
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Topology':
        """从字典创建拓扑实例"""
        topology = cls(
            topology_id=data["topology_id"],
            last_updated=datetime.fromisoformat(data["last_updated"])
            if "last_updated" in data
            else datetime.now(),
        )
        # 重建交换机
        for switch_id, switch_data in data.get("switches", {}).items():
            topology.add_switch(Switch.from_dict(switch_data))
        # 重建链路
        for link_id, link_data in data.get("links", {}).items():
            topology.add_link(Link.from_dict(link_data))
        return topology


@dataclass
class RoutingTable:
    """路由表数据模型"""
    switch_id: str
    routes: Dict[str, Route] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def add_route(self, route: Route) -> None:
        """添加路由到路由表"""
        self.routes[route.destination] = route
        self.last_updated = datetime.now()

    def remove_route(self, destination: str) -> None:
        """从路由表中移除路由"""
        if destination in self.routes:
            del self.routes[destination]
            self.last_updated = datetime.now()

    def get_route(self, destination: str) -> Optional[Route]:
        """获取到指定目的地的路由"""
        return self.routes.get(destination)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "switch_id": self.switch_id,
            "routes": {
                dest: route.to_dict() for dest, route in self.routes.items()
            },
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoutingTable':
        """从字典创建路由表实例"""
        routing_table = cls(
            switch_id=data["switch_id"],
            last_updated=datetime.fromisoformat(data["last_updated"])
            if "last_updated" in data
            else datetime.now(),
        )
        # 重建路由
        for dest, route_data in data.get("routes", {}).items():
            routing_table.add_route(Route.from_dict(route_data))
        return routing_table
