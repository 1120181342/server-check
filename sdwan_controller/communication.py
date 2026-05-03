"""
通信模块
实现控制平面与数据平面的隔离通信机制
使用异步消息队列和安全通道
"""

import asyncio
import json
import time
import uuid
import logging
import zlib
from typing import Dict, List, Optional, Any, Callable, Awaitable
from dataclasses import dataclass, field, asdict
from enum import Enum
from abc import ABC, abstractmethod

from .config import COMMUNICATION_CONFIG, PERFORMANCE_CONFIG


class MessageType(Enum):
    """消息类型枚举"""
    # 控制平面 -> 数据平面
    ROUTE_UPDATE = "route_update"
    FLOW_INSTALL = "flow_install"
    FLOW_REMOVE = "flow_remove"
    TOPOLOGY_REQUEST = "topology_request"
    CONFIG_UPDATE = "config_update"
    HEARTBEAT = "heartbeat"
    
    # 数据平面 -> 控制平面
    PACKET_IN = "packet_in"
    TOPOLOGY_REPORT = "topology_report"
    STATISTICS_REPORT = "statistics_report"
    EVENT_NOTIFICATION = "event_notification"
    HEARTBEAT_ACK = "heartbeat_ack"
    
    # 通用
    ACK = "ack"
    NACK = "nack"
    ERROR = "error"


class MessagePriority(Enum):
    """消息优先级枚举"""
    CRITICAL = 0  # 最高优先级（如网络故障）
    HIGH = 1      # 高优先级（如路由更新）
    NORMAL = 2    # 正常优先级
    LOW = 3       # 低优先级（如统计报告）


@dataclass
class Message:
    """消息数据结构"""
    message_id: str
    message_type: MessageType
    source: str
    destination: str
    payload: Dict[str, Any]
    priority: MessagePriority = MessagePriority.NORMAL
    timestamp: float = field(default_factory=time.time)
    ttl: int = 64
    correlation_id: Optional[str] = None

    def to_bytes(self) -> bytes:
        """序列化为字节"""
        data = {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "source": self.source,
            "destination": self.destination,
            "payload": self.payload,
            "priority": self.priority.value,
            "timestamp": self.timestamp,
            "ttl": self.ttl,
            "correlation_id": self.correlation_id,
        }
        
        json_str = json.dumps(data)
        
        # 压缩（如果启用）
        if COMMUNICATION_CONFIG.get("compression_enabled", True):
            compressed = zlib.compress(json_str.encode("utf-8"))
            return compressed
        
        return json_str.encode("utf-8")

    @classmethod
    def from_bytes(cls, data: bytes) -> 'Message':
        """从字节反序列化"""
        # 尝试解压缩
        try:
            decompressed = zlib.decompress(data)
            json_str = decompressed.decode("utf-8")
        except zlib.error:
            json_str = data.decode("utf-8")
        
        data_dict = json.loads(json_str)
        
        return cls(
            message_id=data_dict["message_id"],
            message_type=MessageType(data_dict["message_type"]),
            source=data_dict["source"],
            destination=data_dict["destination"],
            payload=data_dict["payload"],
            priority=MessagePriority(data_dict.get("priority", 2)),
            timestamp=data_dict.get("timestamp", time.time()),
            ttl=data_dict.get("ttl", 64),
            correlation_id=data_dict.get("correlation_id"),
        )

    def is_expired(self) -> bool:
        """检查消息是否过期"""
        current_age = time.time() - self.timestamp
        return current_age > COMMUNICATION_CONFIG.get("message_timeout", 5.0)


class MessageQueue:
    """
    优先级消息队列
    用于控制平面和数据平面之间的异步通信
    """

    def __init__(self, name: str, max_size: int = 10000):
        self.name = name
        self.max_size = max_size
        
        # 按优先级划分的队列
        self._queues: Dict[MessagePriority, asyncio.Queue] = {
            MessagePriority.CRITICAL: asyncio.Queue(maxsize=max_size // 4),
            MessagePriority.HIGH: asyncio.Queue(maxsize=max_size // 4),
            MessagePriority.NORMAL: asyncio.Queue(maxsize=max_size // 4),
            MessagePriority.LOW: asyncio.Queue(maxsize=max_size // 4),
        }
        
        self._total_messages = 0
        self._dropped_messages = 0
        self.logger = logging.getLogger(f"queue-{name}")

    async def put(self, message: Message) -> bool:
        """
        放入消息到队列
        按优先级处理
        """
        if message.is_expired():
            self.logger.debug(f"Dropping expired message {message.message_id}")
            return False
        
        queue = self._queues[message.priority]
        
        try:
            queue.put_nowait(message)
            self._total_messages += 1
            return True
        except asyncio.QueueFull:
            # 队列已满，根据优先级处理
            if message.priority in (MessagePriority.CRITICAL, MessagePriority.HIGH):
                # 高优先级消息，尝试丢弃低优先级消息腾出空间
                await self._drop_low_priority_messages()
                try:
                    queue.put_nowait(message)
                    self._total_messages += 1
                    return True
                except asyncio.QueueFull:
                    pass
            
            self._dropped_messages += 1
            self.logger.warning(
                f"Queue full, dropping message {message.message_id} "
                f"(priority: {message.priority.value})"
            )
            return False

    async def _drop_low_priority_messages(self, count: int = 10) -> None:
        """丢弃低优先级消息以腾出空间"""
        for priority in [MessagePriority.LOW, MessagePriority.NORMAL]:
            queue = self._queues[priority]
            for _ in range(count):
                try:
                    queue.get_nowait()
                    self._dropped_messages += 1
                except asyncio.QueueEmpty:
                    break

    async def get(self, timeout: Optional[float] = None) -> Optional[Message]:
        """
        从队列获取消息
        按优先级顺序获取
        """
        # 按优先级顺序检查队列
        for priority in [
            MessagePriority.CRITICAL,
            MessagePriority.HIGH,
            MessagePriority.NORMAL,
            MessagePriority.LOW,
        ]:
            queue = self._queues[priority]
            try:
                if timeout is not None:
                    message = await asyncio.wait_for(queue.get(), timeout=timeout)
                else:
                    message = queue.get_nowait()
                
                # 检查是否过期
                if message.is_expired():
                    self.logger.debug(f"Skipping expired message {message.message_id}")
                    continue
                
                return message
            except (asyncio.QueueEmpty, asyncio.TimeoutError):
                continue
        
        return None

    def get_stats(self) -> Dict[str, Any]:
        """获取队列统计"""
        queue_sizes = {
            priority.value: queue.qsize()
            for priority, queue in self._queues.items()
        }
        
        return {
            "name": self.name,
            "total_messages": self._total_messages,
            "dropped_messages": self._dropped_messages,
            "queue_sizes": queue_sizes,
            "total_current": sum(self._queues[p].qsize() for p in self._queues),
        }


class ControlPlaneChannel:
    """
    控制平面通信通道
    负责控制器与交换机控制平面之间的通信
    """

    def __init__(self, controller_id: str):
        self.controller_id = controller_id
        self._outgoing_queue = MessageQueue(f"{controller_id}-outgoing")
        self._incoming_queue = MessageQueue(f"{controller_id}-incoming")
        self._message_handlers: Dict[MessageType, Callable[[Message], Awaitable[None]]] = {}
        self.running = False
        self._receive_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(f"control-channel-{controller_id}")

    async def start(self) -> None:
        """启动控制平面通道"""
        self.running = True
        self._receive_task = asyncio.create_task(self._receive_loop())
        self.logger.info("Control plane channel started")

    async def stop(self) -> None:
        """停止控制平面通道"""
        self.running = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Control plane channel stopped")

    async def _receive_loop(self) -> None:
        """消息接收循环"""
        while self.running:
            try:
                message = await self._incoming_queue.get(timeout=1.0)
                if message:
                    await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(0.1)

    async def _handle_message(self, message: Message) -> None:
        """处理接收到的消息"""
        handler = self._message_handlers.get(message.message_type)
        
        if handler:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(
                    f"Error handling message {message.message_id}: {e}"
                )
                # 发送错误响应
                await self.send_nack(message, str(e))
        else:
            self.logger.warning(
                f"No handler for message type {message.message_type}"
            )

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Message], Awaitable[None]],
    ) -> None:
        """注册消息处理器"""
        self._message_handlers[message_type] = handler
        self.logger.debug(f"Registered handler for {message_type.value}")

    def unregister_handler(self, message_type: MessageType) -> None:
        """注销消息处理器"""
        if message_type in self._message_handlers:
            del self._message_handlers[message_type]
            self.logger.debug(f"Unregistered handler for {message_type.value}")

    async def send_message(
        self,
        destination: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
        correlation_id: Optional[str] = None,
    ) -> str:
        """发送消息"""
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            source=self.controller_id,
            destination=destination,
            payload=payload,
            priority=priority,
            correlation_id=correlation_id,
        )
        
        success = await self._outgoing_queue.put(message)
        
        if success:
            self.logger.debug(
                f"Sent message {message.message_id} to {destination} "
                f"(type: {message_type.value})"
            )
        else:
            self.logger.warning(
                f"Failed to send message to {destination} (type: {message_type.value})"
            )
        
        return message.message_id

    async def send_ack(
        self, original_message: Message, additional_payload: Optional[Dict[str, Any]] = None
    ) -> None:
        """发送确认消息"""
        payload = {"status": "ok"}
        if additional_payload:
            payload.update(additional_payload)
        
        await self.send_message(
            destination=original_message.source,
            message_type=MessageType.ACK,
            payload=payload,
            priority=MessagePriority.HIGH,
            correlation_id=original_message.message_id,
        )

    async def send_nack(
        self, original_message: Message, error_message: str
    ) -> None:
        """发送否定确认消息"""
        await self.send_message(
            destination=original_message.source,
            message_type=MessageType.NACK,
            payload={"error": error_message},
            priority=MessagePriority.HIGH,
            correlation_id=original_message.message_id,
        )

    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """接收消息"""
        return await self._incoming_queue.get(timeout=timeout)

    def get_stats(self) -> Dict[str, Any]:
        """获取通道统计"""
        return {
            "controller_id": self.controller_id,
            "running": self.running,
            "outgoing_queue": self._outgoing_queue.get_stats(),
            "incoming_queue": self._incoming_queue.get_stats(),
            "registered_handlers": [mt.value for mt in self._message_handlers.keys()],
        }


class DataPlaneChannel:
    """
    数据平面通信通道
    负责交换机数据平面与控制平面之间的通信
    """

    def __init__(self, switch_id: str):
        self.switch_id = switch_id
        self._outgoing_queue = MessageQueue(f"{switch_id}-outgoing")
        self._incoming_queue = MessageQueue(f"{switch_id}-incoming")
        self._message_handlers: Dict[MessageType, Callable[[Message], Awaitable[None]]] = {}
        self.running = False
        self._receive_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger(f"data-channel-{switch_id}")

    async def start(self) -> None:
        """启动数据平面通道"""
        self.running = True
        self._receive_task = asyncio.create_task(self._receive_loop())
        self.logger.info("Data plane channel started")

    async def stop(self) -> None:
        """停止数据平面通道"""
        self.running = False
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Data plane channel stopped")

    async def _receive_loop(self) -> None:
        """消息接收循环"""
        while self.running:
            try:
                message = await self._incoming_queue.get(timeout=1.0)
                if message:
                    await self._handle_message(message)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in receive loop: {e}")
                await asyncio.sleep(0.1)

    async def _handle_message(self, message: Message) -> None:
        """处理接收到的消息"""
        handler = self._message_handlers.get(message.message_type)
        
        if handler:
            try:
                await handler(message)
            except Exception as e:
                self.logger.error(
                    f"Error handling message {message.message_id}: {e}"
                )
        else:
            self.logger.warning(
                f"No handler for message type {message.message_type}"
            )

    def register_handler(
        self,
        message_type: MessageType,
        handler: Callable[[Message], Awaitable[None]],
    ) -> None:
        """注册消息处理器"""
        self._message_handlers[message_type] = handler
        self.logger.debug(f"Registered handler for {message_type.value}")

    async def send_message(
        self,
        destination: str,
        message_type: MessageType,
        payload: Dict[str, Any],
        priority: MessagePriority = MessagePriority.NORMAL,
    ) -> str:
        """发送消息到控制平面"""
        message = Message(
            message_id=str(uuid.uuid4()),
            message_type=message_type,
            source=self.switch_id,
            destination=destination,
            payload=payload,
            priority=priority,
        )
        
        success = await self._outgoing_queue.put(message)
        
        if success:
            self.logger.debug(
                f"Sent message {message.message_id} to {destination} "
                f"(type: {message_type.value})"
            )
        
        return message.message_id

    async def receive_message(self, timeout: Optional[float] = None) -> Optional[Message]:
        """接收消息"""
        return await self._incoming_queue.get(timeout=timeout)

    def get_stats(self) -> Dict[str, Any]:
        """获取通道统计"""
        return {
            "switch_id": self.switch_id,
            "running": self.running,
            "outgoing_queue": self._outgoing_queue.get_stats(),
            "incoming_queue": self._incoming_queue.get_stats(),
        }


class ChannelBroker:
    """
    通道代理
    负责在控制平面通道和数据平面通道之间路由消息
    实现控制平面和数据平面的完全隔离
    """

    def __init__(self):
        self._control_channels: Dict[str, ControlPlaneChannel] = {}
        self._data_channels: Dict[str, DataPlaneChannel] = {}
        self.running = False
        self._routing_task: Optional[asyncio.Task] = None
        self.logger = logging.getLogger("channel-broker")

    async def start(self) -> None:
        """启动通道代理"""
        self.running = True
        self._routing_task = asyncio.create_task(self._routing_loop())
        self.logger.info("Channel broker started")

    async def stop(self) -> None:
        """停止通道代理"""
        self.running = False
        if self._routing_task:
            self._routing_task.cancel()
            try:
                await self._routing_task
            except asyncio.CancelledError:
                pass
        
        # 停止所有通道
        for channel in self._control_channels.values():
            await channel.stop()
        for channel in self._data_channels.values():
            await channel.stop()
        
        self.logger.info("Channel broker stopped")

    def register_control_channel(self, channel: ControlPlaneChannel) -> None:
        """注册控制平面通道"""
        self._control_channels[channel.controller_id] = channel
        self.logger.info(f"Registered control channel: {channel.controller_id}")

    def register_data_channel(self, channel: DataPlaneChannel) -> None:
        """注册数据平面通道"""
        self._data_channels[channel.switch_id] = channel
        self.logger.info(f"Registered data channel: {channel.switch_id}")

    async def _routing_loop(self) -> None:
        """消息路由循环"""
        while self.running:
            try:
                # 路由控制平面 -> 数据平面的消息
                for controller_id, control_channel in self._control_channels.items():
                    message = await control_channel._outgoing_queue.get(timeout=0.1)
                    if message:
                        await self._route_to_data_plane(message)
                
                # 路由数据平面 -> 控制平面的消息
                for switch_id, data_channel in self._data_channels.items():
                    message = await data_channel._outgoing_queue.get(timeout=0.1)
                    if message:
                        await self._route_to_control_plane(message)
                
                await asyncio.sleep(0.001)
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                self.logger.error(f"Error in routing loop: {e}")
                await asyncio.sleep(0.1)

    async def _route_to_data_plane(self, message: Message) -> None:
        """路由消息到数据平面"""
        if message.destination in self._data_channels:
            data_channel = self._data_channels[message.destination]
            success = await data_channel._incoming_queue.put(message)
            if success:
                self.logger.debug(
                    f"Routed message {message.message_id} from "
                    f"{message.source} to data plane {message.destination}"
                )
            else:
                self.logger.warning(
                    f"Failed to route message to data plane {message.destination}"
                )
        else:
            self.logger.warning(
                f"Data channel {message.destination} not found"
            )

    async def _route_to_control_plane(self, message: Message) -> None:
        """路由消息到控制平面"""
        if message.destination in self._control_channels:
            control_channel = self._control_channels[message.destination]
            success = await control_channel._incoming_queue.put(message)
            if success:
                self.logger.debug(
                    f"Routed message {message.message_id} from "
                    f"{message.source} to control plane {message.destination}"
                )
            else:
                self.logger.warning(
                    f"Failed to route message to control plane {message.destination}"
                )
        else:
            # 如果没有指定目标控制平面，广播到所有控制平面
            for control_channel in self._control_channels.values():
                await control_channel._incoming_queue.put(message)

    def get_stats(self) -> Dict[str, Any]:
        """获取代理统计"""
        return {
            "running": self.running,
            "control_channels": list(self._control_channels.keys()),
            "data_channels": list(self._data_channels.keys()),
            "control_channel_count": len(self._control_channels),
            "data_channel_count": len(self._data_channels),
        }
