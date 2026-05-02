"""
SD-WAN局域网控制器
一个高性能的SD-WAN控制器，支持20台交换机的网络
"""

__version__ = "1.0.0"
__author__ = "SD-WAN Controller Team"

from .config import (
    NETWORK_TOPOLOGY,
    LINK_PARAMS,
    ROUTING_PROTOCOL,
    PERFORMANCE_CONFIG,
    COMMUNICATION_CONFIG,
    LOGGING_CONFIG,
)
from .models import (
    Switch,
    Link,
    Route,
    Topology,
    RoutingTable,
    SwitchType,
    LinkStatus,
    RouteType,
    Path,
)
from .core_controller import (
    CoreController,
    TopologyDiscovery,
    RouteCalculator,
    PathOptimizer,
)
from .routing_protocol import (
    LinkStateRouting,
    HelloProtocol,
    LinkStateDatabase,
    HelloPacket,
    LinkStateAdvertisement,
    HelloState,
    LSA,
    Neighbor,
)
from .switch_simulator import (
    SimulatedSwitch,
    ControlPlane,
    DataPlane,
    Packet,
    Interface,
    MacAddressTableEntry,
    PacketType,
)
from .communication import (
    Message,
    MessageQueue,
    ControlPlaneChannel,
    DataPlaneChannel,
    ChannelBroker,
    MessageType,
    MessagePriority,
)
from .performance_optimizer import (
    IncrementalRouteCalculator,
    HierarchicalRouteCalculator,
    ParallelRouteCalculator,
    RouteCache,
    RouteCacheEntry,
    timed_operation,
)

__all__ = [
    # 配置
    "NETWORK_TOPOLOGY",
    "LINK_PARAMS",
    "ROUTING_PROTOCOL",
    "PERFORMANCE_CONFIG",
    "COMMUNICATION_CONFIG",
    "LOGGING_CONFIG",
    
    # 模型
    "Switch",
    "Link",
    "Route",
    "Topology",
    "RoutingTable",
    "SwitchType",
    "LinkStatus",
    "RouteType",
    "Path",
    
    # 核心控制器
    "CoreController",
    "TopologyDiscovery",
    "RouteCalculator",
    "PathOptimizer",
    
    # 路由协议
    "LinkStateRouting",
    "HelloProtocol",
    "LinkStateDatabase",
    "HelloPacket",
    "LinkStateAdvertisement",
    "HelloState",
    "LSA",
    "Neighbor",
    
    # 交换机模拟器
    "SimulatedSwitch",
    "ControlPlane",
    "DataPlane",
    "Packet",
    "Interface",
    "MacAddressTableEntry",
    "PacketType",
    
    # 通信
    "Message",
    "MessageQueue",
    "ControlPlaneChannel",
    "DataPlaneChannel",
    "ChannelBroker",
    "MessageType",
    "MessagePriority",
    
    # 性能优化
    "IncrementalRouteCalculator",
    "HierarchicalRouteCalculator",
    "ParallelRouteCalculator",
    "RouteCache",
    "RouteCacheEntry",
    "timed_operation",
]
