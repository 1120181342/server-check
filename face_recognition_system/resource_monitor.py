import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from inspection_config import InspectionConfig

logger = logging.getLogger(__name__)


class ResourceMonitor:
    """资源监控模块，用于获取CPU、内存、磁盘等资源水位"""
    
    # 资源水位阈值定义
    CPU_WARNING_THRESHOLD = 70.0  # CPU警告阈值（百分比）
    CPU_CRITICAL_THRESHOLD = 90.0  # CPU严重阈值（百分比）
    
    MEMORY_WARNING_THRESHOLD = 75.0  # 内存警告阈值（百分比）
    MEMORY_CRITICAL_THRESHOLD = 90.0  # 内存严重阈值（百分比）
    
    DISK_WARNING_THRESHOLD = 80.0  # 磁盘警告阈值（百分比）
    DISK_CRITICAL_THRESHOLD = 90.0  # 磁盘严重阈值（百分比）
    
    def __init__(self, config: InspectionConfig):
        """初始化资源监控模块
        
        Args:
            config: 配置对象
        """
        self.config = config
        self._session: Optional[requests.Session] = None
    
    def _get_session(self) -> requests.Session:
        """获取HTTP会话（带重试机制）
        
        Returns:
            requests会话对象
        """
        if self._session is None:
            self._session = requests.Session()
            
            retry_strategy = Retry(
                total=self.config.RETRY_COUNT,
                backoff_factor=self.config.RETRY_DELAY,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        
        return self._session
    
    def _query_prometheus(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """执行Prometheus查询
        
        Args:
            query: PromQL查询语句
            
        Returns:
            查询结果列表
        """
        session = self._get_session()
        prometheus_url = self.config.PROMETHEUS_URL
        
        try:
            response = session.get(
                prometheus_url,
                params={'query': query},
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data', {}).get('result', [])
            else:
                logger.warning(f"Prometheus query failed: {data.get('error')}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to query Prometheus: {str(e)}")
            return None
    
    def get_cpu_usage(self, instance: str = None) -> List[Dict[str, Any]]:
        """获取CPU使用率
        
        Args:
            instance: 实例标识（IP:端口），如果为None则获取所有实例
            
        Returns:
            CPU使用率信息列表
        """
        # PromQL查询：计算最近5分钟的平均CPU使用率
        query = '100 - (avg by (instance) (irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)'
        
        if instance:
            query = f'100 - (avg by (instance) (irate(node_cpu_seconds_total{{mode="idle", instance="{instance}"}}[5m])) * 100)'
        
        results = self._query_prometheus(query)
        
        if not results:
            return []
        
        cpu_usages = []
        for result in results:
            instance_name = result.get('metric', {}).get('instance', '')
            value = result.get('value', [])
            
            if len(value) >= 2:
                try:
                    usage_percent = float(value[1])
                    
                    # 确定水位状态
                    status = self._determine_status(
                        usage_percent,
                        self.CPU_WARNING_THRESHOLD,
                        self.CPU_CRITICAL_THRESHOLD
                    )
                    
                    cpu_usages.append({
                        'instance': instance_name,
                        'metric': 'cpu_usage_percent',
                        'value': round(usage_percent, 2),
                        'unit': '%',
                        'status': status,
                        'warning_threshold': self.CPU_WARNING_THRESHOLD,
                        'critical_threshold': self.CPU_CRITICAL_THRESHOLD,
                        'timestamp': datetime.now()
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse CPU usage value: {e}")
        
        return cpu_usages
    
    def get_memory_usage(self, instance: str = None) -> List[Dict[str, Any]]:
        """获取内存使用率
        
        Args:
            instance: 实例标识
            
        Returns:
            内存使用率信息列表
        """
        # PromQL查询：计算内存使用率
        query = '(1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)) * 100'
        
        if instance:
            query = f'(1 - (node_memory_MemAvailable_bytes{{instance="{instance}"}} / node_memory_MemTotal_bytes{{instance="{instance}"}})) * 100'
        
        results = self._query_prometheus(query)
        
        if not results:
            return []
        
        memory_usages = []
        for result in results:
            instance_name = result.get('metric', {}).get('instance', '')
            value = result.get('value', [])
            
            if len(value) >= 2:
                try:
                    usage_percent = float(value[1])
                    
                    status = self._determine_status(
                        usage_percent,
                        self.MEMORY_WARNING_THRESHOLD,
                        self.MEMORY_CRITICAL_THRESHOLD
                    )
                    
                    memory_usages.append({
                        'instance': instance_name,
                        'metric': 'memory_usage_percent',
                        'value': round(usage_percent, 2),
                        'unit': '%',
                        'status': status,
                        'warning_threshold': self.MEMORY_WARNING_THRESHOLD,
                        'critical_threshold': self.MEMORY_CRITICAL_THRESHOLD,
                        'timestamp': datetime.now()
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse memory usage value: {e}")
        
        return memory_usages
    
    def get_disk_usage(self, instance: str = None) -> List[Dict[str, Any]]:
        """获取磁盘使用率
        
        Args:
            instance: 实例标识
            
        Returns:
            磁盘使用率信息列表（每个挂载点一个条目）
        """
        # PromQL查询：计算磁盘使用率（排除临时文件系统）
        query = '''
        100 - (
            (node_filesystem_avail_bytes{fstype!~"tmpfs|sysfs|procfs|devtmpfs|debugfs|securityfs|pstore|efivarfs|bpf|mqueue|hugetlbfs"} * 100) 
            / node_filesystem_size_bytes{fstype!~"tmpfs|sysfs|procfs|devtmpfs|debugfs|securityfs|pstore|efivarfs|bpf|mqueue|hugetlbfs"}
        )
        '''
        
        if instance:
            query = f'''
            100 - (
                (node_filesystem_avail_bytes{{instance="{instance}", fstype!~"tmpfs|sysfs|procfs|devtmpfs|debugfs|securityfs|pstore|efivarfs|bpf|mqueue|hugetlbfs"}} * 100) 
                / node_filesystem_size_bytes{{instance="{instance}", fstype!~"tmpfs|sysfs|procfs|devtmpfs|debugfs|securityfs|pstore|efivarfs|bpf|mqueue|hugetlbfs"}}
            )
            '''
        
        results = self._query_prometheus(query)
        
        if not results:
            return []
        
        disk_usages = []
        for result in results:
            metric = result.get('metric', {})
            instance_name = metric.get('instance', '')
            mountpoint = metric.get('mountpoint', '')
            fstype = metric.get('fstype', '')
            value = result.get('value', [])
            
            if len(value) >= 2:
                try:
                    usage_percent = float(value[1])
                    
                    # 过滤掉无效值
                    if usage_percent < 0 or usage_percent > 100:
                        continue
                    
                    status = self._determine_status(
                        usage_percent,
                        self.DISK_WARNING_THRESHOLD,
                        self.DISK_CRITICAL_THRESHOLD
                    )
                    
                    disk_usages.append({
                        'instance': instance_name,
                        'mountpoint': mountpoint,
                        'fstype': fstype,
                        'metric': 'disk_usage_percent',
                        'value': round(usage_percent, 2),
                        'unit': '%',
                        'status': status,
                        'warning_threshold': self.DISK_WARNING_THRESHOLD,
                        'critical_threshold': self.DISK_CRITICAL_THRESHOLD,
                        'timestamp': datetime.now()
                    })
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse disk usage value: {e}")
        
        return disk_usages
    
    def get_network_stats(self, instance: str = None) -> List[Dict[str, Any]]:
        """获取网络统计信息
        
        Args:
            instance: 实例标识
            
        Returns:
            网络统计信息列表
        """
        # 查询网络接收字节数速率
        rx_query = 'rate(node_network_receive_bytes_total[5m])'
        # 查询网络发送字节数速率
        tx_query = 'rate(node_network_transmit_bytes_total[5m])'
        
        if instance:
            rx_query = f'rate(node_network_receive_bytes_total{{instance="{instance}"}}[5m])'
            tx_query = f'rate(node_network_transmit_bytes_total{{instance="{instance}"}}[5m])'
        
        rx_results = self._query_prometheus(rx_query) or []
        tx_results = self._query_prometheus(tx_query) or []
        
        # 创建一个字典来合并收发数据
        network_stats = {}
        
        # 处理接收数据
        for result in rx_results:
            metric = result.get('metric', {})
            instance_name = metric.get('instance', '')
            device = metric.get('device', '')
            value = result.get('value', [])
            
            if len(value) >= 2 and device and device != 'lo':  # 排除回环接口
                key = f"{instance_name}_{device}"
                if key not in network_stats:
                    network_stats[key] = {
                        'instance': instance_name,
                        'device': device,
                        'timestamp': datetime.now()
                    }
                try:
                    network_stats[key]['rx_bytes_per_second'] = float(value[1])
                except (ValueError, TypeError):
                    network_stats[key]['rx_bytes_per_second'] = 0
        
        # 处理发送数据
        for result in tx_results:
            metric = result.get('metric', {})
            instance_name = metric.get('instance', '')
            device = metric.get('device', '')
            value = result.get('value', [])
            
            if len(value) >= 2 and device and device != 'lo':
                key = f"{instance_name}_{device}"
                if key not in network_stats:
                    network_stats[key] = {
                        'instance': instance_name,
                        'device': device,
                        'timestamp': datetime.now()
                    }
                try:
                    network_stats[key]['tx_bytes_per_second'] = float(value[1])
                except (ValueError, TypeError):
                    network_stats[key]['tx_bytes_per_second'] = 0
        
        # 转换为列表并添加额外信息
        stats_list = []
        for stats in network_stats.values():
            rx = stats.get('rx_bytes_per_second', 0)
            tx = stats.get('tx_bytes_per_second', 0)
            
            stats_list.append({
                **stats,
                'rx_kbps': round(rx / 1024, 2),
                'tx_kbps': round(tx / 1024, 2),
                'rx_mbps': round(rx / (1024 * 1024), 2),
                'tx_mbps': round(tx / (1024 * 1024), 2)
            })
        
        return stats_list
    
    def get_all_resource_metrics(self, instance: str = None) -> Dict[str, Any]:
        """获取所有资源指标
        
        Args:
            instance: 实例标识
            
        Returns:
            包含所有资源指标的字典
        """
        logger.info(f"Fetching all resource metrics for instance: {instance or 'all'}")
        
        cpu_usage = self.get_cpu_usage(instance)
        memory_usage = self.get_memory_usage(instance)
        disk_usage = self.get_disk_usage(instance)
        network_stats = self.get_network_stats(instance)
        
        # 汇总状态
        all_metrics = cpu_usage + memory_usage + disk_usage
        has_critical = any(m.get('status') == 'critical' for m in all_metrics)
        has_warning = any(m.get('status') == 'warning' for m in all_metrics)
        
        overall_status = 'normal'
        if has_critical:
            overall_status = 'critical'
        elif has_warning:
            overall_status = 'warning'
        
        return {
            'timestamp': datetime.now(),
            'instance': instance,
            'overall_status': overall_status,
            'cpu_usage': cpu_usage,
            'memory_usage': memory_usage,
            'disk_usage': disk_usage,
            'network_stats': network_stats,
            'summary': {
                'total_metrics': len(all_metrics),
                'critical_count': sum(1 for m in all_metrics if m.get('status') == 'critical'),
                'warning_count': sum(1 for m in all_metrics if m.get('status') == 'warning'),
                'normal_count': sum(1 for m in all_metrics if m.get('status') == 'normal')
            }
        }
    
    def get_resource_metrics_for_servers(self, server_ips: List[str]) -> Dict[str, Dict[str, Any]]:
        """获取多个服务器的资源指标
        
        Args:
            server_ips: 服务器IP列表
            
        Returns:
            以IP为键的资源指标字典
        """
        results = {}
        
        for ip in server_ips:
            # 尝试使用不同的端口格式查询
            instance_formats = [
                f"{ip}:9100",  # 默认node_exporter端口
                f"{ip}:8080",
                ip
            ]
            
            metrics = None
            for instance_format in instance_formats:
                try:
                    metrics = self.get_all_resource_metrics(instance_format)
                    # 检查是否有有效数据
                    if (metrics.get('cpu_usage') or 
                        metrics.get('memory_usage') or 
                        metrics.get('disk_usage')):
                        break
                except Exception as e:
                    logger.debug(f"Failed to get metrics for {instance_format}: {e}")
                    continue
            
            results[ip] = metrics or {
                'timestamp': datetime.now(),
                'instance': ip,
                'overall_status': 'unknown',
                'error': 'Failed to retrieve metrics'
            }
        
        return results
    
    def _determine_status(self, value: float, 
                          warning_threshold: float, 
                          critical_threshold: float) -> str:
        """根据值和阈值确定状态
        
        Args:
            value: 当前值
            warning_threshold: 警告阈值
            critical_threshold: 严重阈值
            
        Returns:
            状态字符串：normal, warning, critical
        """
        if value >= critical_threshold:
            return 'critical'
        elif value >= warning_threshold:
            return 'warning'
        else:
            return 'normal'
    
    def close(self):
        """关闭HTTP会话"""
        if self._session:
            self._session.close()
            self._session = None
            logger.info("Resource monitor session closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
