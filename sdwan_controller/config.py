"""
SD-WAN控制器配置文件
定义网络拓扑、协议参数和性能配置
"""

# 网络拓扑配置
NETWORK_TOPOLOGY = {
    "core_switches": 2,      # 核心交换机数量
    "access_switches": 10,    # 接入交换机数量
    "pop_switches": 8,         # POP交换机数量
    "total_switches": 20,      # 总交换机数量
}

# 交换机类型枚举
SWITCH_TYPES = {
    "CORE": "core",
    "ACCESS": "access",
    "POP": "pop",
}

# 链路参数配置
LINK_PARAMS = {
    "core_core_cost": 1,           # 核心-核心链路开销
    "core_access_cost": 5,         # 核心-接入链路开销
    "core_pop_cost": 3,             # 核心-POP链路开销
    "access_access_cost": 10,         # 接入-接入链路开销（用于冗余）
    "pop_access_cost": 7,             # POP-接入链路开销
    "pop_pop_cost": 5,                 # POP-POP链路开销
}

# 路由协议配置
ROUTING_PROTOCOL = {
    "protocol_type": "link_state",     # 使用链路状态协议（类似OSPF/IS-IS）
    "hello_interval": 10,              # Hello包发送间隔（秒）
    "dead_interval": 40,               # 邻居失效时间（秒）
    "lsa_refresh_time": 1800,          # LSA刷新时间（秒）
    "max_lsa_age": 3600,              # LSA最大老化时间（秒）
    "ecmp_enabled": True,              # 启用等价多路径
    "max_ecmp_paths": 4,              # 最大ECMP路径数
}

# 性能配置
PERFORMANCE_CONFIG = {
    "max_computation_time": 1.0,      # 单次最大计算时间（秒）
    "route_calculation_timeout": 0.9,  # 路由计算超时时间（秒）
    "topology_update_batch": True,    # 启用拓扑更新批处理
    "batch_size": 50,                  # 批处理大小
    "cache_enabled": True,              # 启用路由缓存
    "cache_ttl": 60,                     # 缓存TTL（秒）
}

# 通信配置
COMMUNICATION_CONFIG = {
    "control_plane_port": 8080,       # 控制平面端口
    "data_plane_port": 8081,             # 数据平面端口
    "use_asyncio": True,                  # 使用asyncio进行异步通信
    "message_timeout": 5.0,              # 消息超时时间（秒）
    "max_message_size": 65536,           # 最大消息大小（字节）
    "compression_enabled": True,         # 启用消息压缩
}

# 日志配置
LOGGING_CONFIG = {
    "level": "INFO",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    "file": "sdwan_controller.log",
}
