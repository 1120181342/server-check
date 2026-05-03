import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from inspection_config import InspectionConfig

logger = logging.getLogger(__name__)


class AlertSystemClient:
    """告警系统客户端，用于获取活跃告警信息"""
    
    # 告警严重级别定义
    SEVERITY_CRITICAL = "critical"
    SEVERITY_WARNING = "warning"
    SEVERITY_INFO = "info"
    
    def __init__(self, config: InspectionConfig):
        """初始化告警系统客户端
        
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
            
            # 配置重试策略
            retry_strategy = Retry(
                total=self.config.RETRY_COUNT,
                backoff_factor=self.config.RETRY_DELAY,
                status_forcelist=[429, 500, 502, 503, 504]
            )
            
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self._session.mount("http://", adapter)
            self._session.mount("https://", adapter)
        
        return self._session
    
    def get_alerts_from_alertmanager(self, 
                                      active_only: bool = True,
                                      severity_filter: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """从AlertManager获取告警
        
        Args:
            active_only: 是否只获取活跃告警
            severity_filter: 严重级别过滤器，如 ["critical", "warning"]
            
        Returns:
            告警信息列表
        """
        session = self._get_session()
        alertmanager_url = self.config.ALERT_MANAGER_URL
        
        logger.info(f"Fetching alerts from AlertManager: {alertmanager_url}")
        
        try:
            # 构建查询参数
            params = {}
            if active_only:
                params['active'] = 'true'
            
            response = session.get(alertmanager_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            alerts = data.get('data', [])
            
            logger.info(f"Retrieved {len(alerts)} alerts from AlertManager")
            
            # 解析告警
            parsed_alerts = []
            for alert in alerts:
                parsed_alert = self._parse_alertmanager_alert(alert)
                
                # 应用严重级别过滤
                if severity_filter and parsed_alert.get('severity') not in severity_filter:
                    continue
                
                parsed_alerts.append(parsed_alert)
            
            return parsed_alerts
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch alerts from AlertManager: {str(e)}")
            return []
    
    def query_prometheus(self, query: str, 
                          time: Optional[datetime] = None) -> Optional[Dict[str, Any]]:
        """执行Prometheus查询
        
        Args:
            query: PromQL查询语句
            time: 查询时间点，默认为当前时间
            
        Returns:
            查询结果
        """
        session = self._get_session()
        prometheus_url = self.config.PROMETHEUS_URL
        
        params = {'query': query}
        if time:
            params['time'] = time.timestamp()
        
        try:
            response = session.get(prometheus_url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            if data.get('status') == 'success':
                return data.get('data')
            else:
                logger.warning(f"Prometheus query failed: {data.get('error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to query Prometheus: {str(e)}")
            return None
    
    def get_alerts_for_server(self, server_id: str, 
                               server_name: str = None,
                               server_ips: List[str] = None) -> List[Dict[str, Any]]:
        """获取特定云主机的告警
        
        Args:
            server_id: 云主机ID
            server_name: 云主机名称
            server_ips: 云主机IP地址列表
            
        Returns:
            与该主机相关的告警列表
        """
        all_alerts = self.get_alerts_from_alertmanager()
        related_alerts = []
        
        for alert in all_alerts:
            # 检查告警是否与该主机相关
            labels = alert.get('labels', {})
            
            # 检查可能的标识符
            identifiers = [
                labels.get('instance', ''),
                labels.get('hostname', ''),
                labels.get('node', ''),
                labels.get('server', ''),
                labels.get('server_id', ''),
                str(alert.get('annotations', {}).get('hostname', '')),
                str(alert.get('annotations', {}).get('instance', ''))
            ]
            
            # 检查是否匹配
            is_related = False
            
            # 检查服务器ID
            if server_id and server_id in str(labels.get('server_id', '')):
                is_related = True
            
            # 检查服务器名称
            if server_name and not is_related:
                for identifier in identifiers:
                    if server_name.lower() in identifier.lower():
                        is_related = True
                        break
            
            # 检查IP地址
            if server_ips and not is_related:
                for ip in server_ips:
                    for identifier in identifiers:
                        if ip in identifier:
                            is_related = True
                            break
                    if is_related:
                        break
            
            if is_related:
                related_alerts.append(alert)
        
        logger.info(f"Found {len(related_alerts)} alerts for server {server_id}")
        return related_alerts
    
    def get_alerts_by_severity(self, severity: str) -> List[Dict[str, Any]]:
        """按严重级别获取告警
        
        Args:
            severity: 严重级别（critical, warning, info）
            
        Returns:
            告警列表
        """
        return self.get_alerts_from_alertmanager(severity_filter=[severity])
    
    def get_critical_alerts(self) -> List[Dict[str, Any]]:
        """获取严重告警
        
        Returns:
            严重告警列表
        """
        return self.get_alerts_by_severity(self.SEVERITY_CRITICAL)
    
    def get_warning_alerts(self) -> List[Dict[str, Any]]:
        """获取警告告警
        
        Returns:
            警告告警列表
        """
        return self.get_alerts_by_severity(self.SEVERITY_WARNING)
    
    def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计信息
        
        Returns:
            告警统计信息
        """
        all_alerts = self.get_alerts_from_alertmanager()
        
        stats = {
            'total': len(all_alerts),
            'critical': 0,
            'warning': 0,
            'info': 0,
            'by_alertname': {},
            'by_severity': {
                'critical': [],
                'warning': [],
                'info': [],
                'unknown': []
            }
        }
        
        for alert in all_alerts:
            severity = alert.get('severity', 'unknown')
            alertname = alert.get('alertname', 'Unknown')
            
            # 统计严重级别
            if severity == self.SEVERITY_CRITICAL:
                stats['critical'] += 1
                stats['by_severity']['critical'].append(alert)
            elif severity == self.SEVERITY_WARNING:
                stats['warning'] += 1
                stats['by_severity']['warning'].append(alert)
            elif severity == self.SEVERITY_INFO:
                stats['info'] += 1
                stats['by_severity']['info'].append(alert)
            else:
                stats['by_severity']['unknown'].append(alert)
            
            # 统计告警名称
            if alertname not in stats['by_alertname']:
                stats['by_alertname'][alertname] = 0
            stats['by_alertname'][alertname] += 1
        
        return stats
    
    def _parse_alertmanager_alert(self, alert: Dict[str, Any]) -> Dict[str, Any]:
        """解析AlertManager告警格式
        
        Args:
            alert: AlertManager原始告警数据
            
        Returns:
            标准化的告警信息
        """
        labels = alert.get('labels', {})
        annotations = alert.get('annotations', {})
        
        # 解析时间
        starts_at = self._parse_datetime(alert.get('startsAt'))
        ends_at = self._parse_datetime(alert.get('endsAt')) if alert.get('endsAt') else None
        
        # 确定严重级别
        severity = labels.get('severity', 'unknown').lower()
        
        return {
            'alertname': labels.get('alertname', 'Unknown'),
            'severity': severity,
            'status': alert.get('status', 'unknown'),
            
            # 标签
            'labels': labels,
            'instance': labels.get('instance', ''),
            'job': labels.get('job', ''),
            'node': labels.get('node', ''),
            'namespace': labels.get('namespace', ''),
            'pod': labels.get('pod', ''),
            'container': labels.get('container', ''),
            
            # 注解
            'annotations': annotations,
            'summary': annotations.get('summary', ''),
            'description': annotations.get('description', ''),
            'message': annotations.get('message', '') or annotations.get('summary', ''),
            
            # 时间
            'starts_at': starts_at,
            'ends_at': ends_at,
            'duration_seconds': (datetime.now() - starts_at).total_seconds() if starts_at else None,
            
            # 生成器URL
            'generator_url': alert.get('generatorURL', ''),
            
            # 指纹（用于唯一标识）
            'fingerprint': alert.get('fingerprint', '')
        }
    
    def _parse_datetime(self, datetime_str: str) -> Optional[datetime]:
        """解析日期时间字符串
        
        Args:
            datetime_str: 日期时间字符串（ISO 8601格式）
            
        Returns:
            datetime对象
        """
        if not datetime_str:
            return None
        
        try:
            # AlertManager使用ISO 8601格式，如 2024-01-15T10:30:00.123Z
            from dateutil import parser
            return parser.parse(datetime_str)
        except Exception:
            try:
                # 尝试手动解析
                if datetime_str.endswith('Z'):
                    datetime_str = datetime_str[:-1] + '+00:00'
                from datetime import datetime
                return datetime.fromisoformat(datetime_str)
            except Exception:
                return None
    
    def format_alert_for_display(self, alert: Dict[str, Any]) -> str:
        """格式化告警用于显示
        
        Args:
            alert: 告警信息
            
        Returns:
            格式化的告警字符串
        """
        severity_icon = {
            'critical': '🔴',
            'warning': '🟡',
            'info': '🔵',
            'unknown': '⚪'
        }.get(alert.get('severity', 'unknown'), '⚪')
        
        lines = [
            f"{severity_icon} [{alert['severity'].upper()}] {alert['alertname']}",
            f"   Status: {alert.get('status', 'unknown')}",
            f"   Instance: {alert.get('instance', 'N/A')}",
            f"   Started: {alert.get('starts_at', 'N/A')}",
        ]
        
        if alert.get('duration_seconds'):
            duration = int(alert['duration_seconds'])
            hours = duration // 3600
            minutes = (duration % 3600) // 60
            lines.append(f"   Duration: {hours}h {minutes}m")
        
        if alert.get('message'):
            lines.append(f"   Message: {alert['message']}")
        
        return '\n'.join(lines)
    
    def close(self):
        """关闭HTTP会话"""
        if self._session:
            self._session.close()
            self._session = None
            logger.info("Alert system client session closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
