import os

class InspectionConfig:
    # OpenStack配置
    OPENSTACK_AUTH_URL = os.environ.get('OPENSTACK_AUTH_URL', 'http://openstack-controller:5000/v3')
    OPENSTACK_USERNAME = os.environ.get('OPENSTACK_USERNAME', 'admin')
    OPENSTACK_PASSWORD = os.environ.get('OPENSTACK_PASSWORD', 'password')
    OPENSTACK_PROJECT_NAME = os.environ.get('OPENSTACK_PROJECT_NAME', 'admin')
    OPENSTACK_USER_DOMAIN_NAME = os.environ.get('OPENSTACK_USER_DOMAIN_NAME', 'Default')
    OPENSTACK_PROJECT_DOMAIN_NAME = os.environ.get('OPENSTACK_PROJECT_DOMAIN_NAME', 'Default')
    OPENSTACK_REGION_NAME = os.environ.get('OPENSTACK_REGION_NAME', 'RegionOne')
    
    # Kubernetes配置
    KUBECONFIG_PATH = os.environ.get('KUBECONFIG_PATH', '~/.kube/config')
    KUBERNETES_API_SERVER = os.environ.get('KUBERNETES_API_SERVER', None)
    KUBERNETES_TOKEN = os.environ.get('KUBERNETES_TOKEN', None)
    
    # 数据库配置（支持MySQL/PostgreSQL）
    DATABASE_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@localhost/cloud_inspection')
    # 或者使用PostgreSQL: 'postgresql://user:password@localhost/cloud_inspection'
    
    # 巡检配置
    MAX_CONCURRENT_HOSTS = int(os.environ.get('MAX_CONCURRENT_HOSTS', 100))  # 每批次并发数
    HOSTS_PER_BATCH = int(os.environ.get('HOSTS_PER_BATCH', 100))  # 每批处理的主机数
    HOST_INSPECTION_TIMEOUT = int(os.environ.get('HOST_INSPECTION_TIMEOUT', 120))  # 单台主机巡检超时时间（秒）
    RETRY_COUNT = int(os.environ.get('RETRY_COUNT', 3))  # 失败重试次数
    RETRY_DELAY = int(os.environ.get('RETRY_DELAY', 5))  # 重试延迟（秒）
    
    # 告警系统配置
    ALERT_MANAGER_URL = os.environ.get('ALERT_MANAGER_URL', 'http://alertmanager:9093/api/v1/alerts')
    PROMETHEUS_URL = os.environ.get('PROMETHEUS_URL', 'http://prometheus:9090/api/v1/query')
    
    # 资源监控配置
    RESOURCE_METRICS_RETENTION_DAYS = int(os.environ.get('RESOURCE_METRICS_RETENTION_DAYS', 30))  # 历史数据保留天数
    PREDICTION_HISTORY_DAYS = int(os.environ.get('PREDICTION_HISTORY_DAYS', 7))  # 预测使用的历史天数
    PREDICTION_FORECAST_DAYS = int(os.environ.get('PREDICTION_FORECAST_DAYS', 3))  # 预测未来天数
    
    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'cloud_inspection.log')
    LOG_MAX_SIZE = int(os.environ.get('LOG_MAX_SIZE', 10 * 1024 * 1024))  # 10MB
    LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', 5))  # 保留5个备份
    
    def __init__(self):
        self._validate_config()
    
    def _validate_config(self):
        """验证必要的配置项"""
        required_configs = [
            ('OPENSTACK_AUTH_URL', self.OPENSTACK_AUTH_URL),
            ('OPENSTACK_USERNAME', self.OPENSTACK_USERNAME),
            ('OPENSTACK_PASSWORD', self.OPENSTACK_PASSWORD),
        ]
        
        missing_configs = [name for name, value in required_configs if not value]
        
        if missing_configs:
            raise ValueError(f"Missing required configuration: {', '.join(missing_configs)}")
        
        # 验证并发配置
        if self.MAX_CONCURRENT_HOSTS <= 0:
            raise ValueError("MAX_CONCURRENT_HOSTS must be greater than 0")
        
        if self.HOSTS_PER_BATCH <= 0:
            raise ValueError("HOSTS_PER_BATCH must be greater than 0")
        
        # 确保每批处理的主机数不超过最大并发数
        if self.HOSTS_PER_BATCH > self.MAX_CONCURRENT_HOSTS * 10:
            raise ValueError("HOSTS_PER_BATCH should not be more than 10 times MAX_CONCURRENT_HOSTS")
