import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import openstack
from openstack.connection import Connection
from openstack.compute.v2.server import Server

from inspection_config import InspectionConfig

logger = logging.getLogger(__name__)


class OpenStackClient:
    """OpenStack API客户端，用于获取云主机信息"""
    
    def __init__(self, config: InspectionConfig):
        """初始化OpenStack客户端
        
        Args:
            config: 配置对象
        """
        self.config = config
        self._connection: Optional[Connection] = None
    
    def _get_connection(self) -> Connection:
        """获取OpenStack连接（单例模式）
        
        Returns:
            OpenStack连接对象
        """
        if self._connection is None:
            logger.info("Connecting to OpenStack...")
            try:
                self._connection = openstack.connect(
                    auth_url=self.config.OPENSTACK_AUTH_URL,
                    username=self.config.OPENSTACK_USERNAME,
                    password=self.config.OPENSTACK_PASSWORD,
                    project_name=self.config.OPENSTACK_PROJECT_NAME,
                    user_domain_name=self.config.OPENSTACK_USER_DOMAIN_NAME,
                    project_domain_name=self.config.OPENSTACK_PROJECT_DOMAIN_NAME,
                    region_name=self.config.OPENSTACK_REGION_NAME
                )
                logger.info("Successfully connected to OpenStack")
            except Exception as e:
                logger.error(f"Failed to connect to OpenStack: {str(e)}")
                raise
        
        return self._connection
    
    def get_all_servers(self) -> List[Server]:
        """获取所有云主机列表
        
        Returns:
            云主机列表
        """
        conn = self._get_connection()
        logger.info("Fetching all servers from OpenStack...")
        
        try:
            servers = list(conn.compute.servers())
            logger.info(f"Found {len(servers)} servers in OpenStack")
            return servers
        except Exception as e:
            logger.error(f"Failed to fetch servers: {str(e)}")
            raise
    
    def get_server_by_id(self, server_id: str) -> Optional[Server]:
        """根据ID获取云主机
        
        Args:
            server_id: 云主机ID
            
        Returns:
            云主机对象，如果不存在则返回None
        """
        conn = self._get_connection()
        try:
            server = conn.compute.get_server(server_id)
            return server
        except Exception as e:
            logger.warning(f"Failed to get server {server_id}: {str(e)}")
            return None
    
    def get_server_details(self, server: Server) -> Dict[str, Any]:
        """获取云主机详细信息
        
        Args:
            server: 云主机对象
            
        Returns:
            包含云主机详细信息的字典
        """
        conn = self._get_connection()
        
        try:
            # 获取完整的服务器详情
            server_details = conn.compute.get_server(server.id)
            
            # 获取规格信息
            flavor_id = server_details.flavor['id']
            flavor = conn.compute.get_flavor(flavor_id)
            
            # 获取镜像信息
            image_id = server_details.image['id'] if server_details.image else None
            image_name = None
            if image_id:
                try:
                    image = conn.image.get_image(image_id)
                    image_name = image.name
                except Exception:
                    image_name = "Unknown"
            
            # 解析网络信息
            networks = {}
            addresses = server_details.addresses if hasattr(server_details, 'addresses') else {}
            for network_name, network_addresses in addresses.items():
                networks[network_name] = []
                for addr in network_addresses:
                    networks[network_name].append({
                        'version': addr.get('version'),
                        'address': addr.get('addr'),
                        'type': 'floating' if addr.get('OS-EXT-IPS:type') == 'floating' else 'fixed'
                    })
            
            # 构建详细信息
            server_info = {
                'server_id': server_details.id,
                'name': server_details.name,
                'status': server_details.status,
                'created_at': self._parse_datetime(server_details.created_at),
                'updated_at': self._parse_datetime(server_details.updated_at) if hasattr(server_details, 'updated_at') else None,
                'launched_at': self._parse_datetime(server_details.launched_at) if hasattr(server_details, 'launched_at') else None,
                
                # 规格信息
                'flavor': {
                    'id': flavor.id,
                    'name': flavor.name,
                    'vcpus': flavor.vcpus,
                    'ram_mb': flavor.ram,
                    'disk_gb': flavor.disk,
                    'ephemeral_gb': flavor.ephemeral if hasattr(flavor, 'ephemeral') else 0,
                    'swap_mb': flavor.swap if hasattr(flavor, 'swap') else 0
                },
                
                # 镜像信息
                'image': {
                    'id': image_id,
                    'name': image_name
                },
                
                # 网络信息
                'networks': networks,
                
                # 额外信息
                'host_id': server_details.host_id if hasattr(server_details, 'host_id') else None,
                'hypervisor_hostname': server_details.hypervisor_hostname if hasattr(server_details, 'hypervisor_hostname') else None,
                'availability_zone': server_details.availability_zone if hasattr(server_details, 'availability_zone') else None,
                'tenant_id': server_details.tenant_id if hasattr(server_details, 'tenant_id') else None,
                'user_id': server_details.user_id if hasattr(server_details, 'user_id') else None,
                
                # 元数据
                'metadata': server_details.metadata if hasattr(server_details, 'metadata') else {},
                
                # 扩展属性
                'power_state': server_details.power_state if hasattr(server_details, 'power_state') else None,
                'task_state': server_details.task_state if hasattr(server_details, 'task_state') else None,
                'vm_state': server_details.vm_state if hasattr(server_details, 'vm_state') else None
            }
            
            return server_info
            
        except Exception as e:
            logger.error(f"Failed to get server details for {server.id}: {str(e)}")
            # 返回基本信息
            return {
                'server_id': server.id,
                'name': server.name,
                'status': server.status,
                'created_at': self._parse_datetime(server.created_at) if hasattr(server, 'created_at') else None,
                'error': str(e)
            }
    
    def get_servers_with_details(self, server_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """获取多个云主机的详细信息
        
        Args:
            server_ids: 云主机ID列表，如果为None则获取所有云主机
            
        Returns:
            云主机详细信息列表
        """
        if server_ids:
            servers = []
            for server_id in server_ids:
                server = self.get_server_by_id(server_id)
                if server:
                    servers.append(server)
        else:
            servers = self.get_all_servers()
        
        results = []
        for server in servers:
            details = self.get_server_details(server)
            results.append(details)
        
        return results
    
    def get_server_ips(self, server: Server) -> List[str]:
        """获取云主机的所有IP地址
        
        Args:
            server: 云主机对象
            
        Returns:
            IP地址列表
        """
        ips = []
        addresses = server.addresses if hasattr(server, 'addresses') else {}
        
        for network_name, network_addresses in addresses.items():
            for addr in network_addresses:
                ip = addr.get('addr')
                if ip:
                    ips.append(ip)
        
        return ips
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析OpenStack日期时间字符串
        
        Args:
            datetime_str: 日期时间字符串
            
        Returns:
            datetime对象，如果解析失败则返回None
        """
        if not datetime_str:
            return None
        
        # OpenStack使用ISO 8601格式
        try:
            # 尝试多种格式
            formats = [
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(datetime_str, fmt)
                except ValueError:
                    continue
            
            # 如果所有格式都失败，尝试使用dateutil
            from dateutil import parser
            return parser.parse(datetime_str)
            
        except Exception:
            return None
    
    def close(self):
        """关闭OpenStack连接"""
        if self._connection:
            self._connection.close()
            self._connection = None
            logger.info("OpenStack connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
