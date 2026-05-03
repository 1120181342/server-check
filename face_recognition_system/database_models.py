import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
from contextlib import contextmanager

try:
    from sqlalchemy import (
        create_engine, Column, Integer, String, Float, DateTime,
        Text, Boolean, ForeignKey, Index
    )
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship, Session
    from sqlalchemy.dialects.mysql import LONGTEXT
    from sqlalchemy.sql import func
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    SQLALCHEMY_AVAILABLE = False

from inspection_config import InspectionConfig

logger = logging.getLogger(__name__)

if SQLALCHEMY_AVAILABLE:
    Base = declarative_base()
else:
    Base = object


class Server(Base):
    """服务器基本信息表"""
    __tablename__ = 'servers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), index=True)
    status = Column(String(50), default='unknown')
    
    # OpenStack信息
    openstack_flavor_id = Column(String(255))
    openstack_flavor_name = Column(String(255))
    openstack_image_id = Column(String(255))
    openstack_image_name = Column(String(255))
    openstack_availability_zone = Column(String(255))
    openstack_host_id = Column(String(255))
    openstack_hypervisor_hostname = Column(String(255))
    
    # 规格信息
    vcpus = Column(Integer)
    ram_mb = Column(Integer)
    disk_gb = Column(Integer)
    
    # 网络信息（JSON存储）
    networks_json = Column(Text)
    
    # Kubernetes信息
    k8s_node_name = Column(String(255), index=True)
    k8s_status = Column(String(50))
    
    # 元数据（JSON存储）
    metadata_json = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    first_seen_at = Column(DateTime)
    last_seen_at = Column(DateTime)
    
    # 关系
    inspection_records = relationship('InspectionRecord', back_populates='server', lazy='dynamic')
    resource_metrics = relationship('ResourceMetric', back_populates='server', lazy='dynamic')
    alerts = relationship('Alert', back_populates='server', lazy='dynamic')
    
    __table_args__ = (
        Index('idx_server_status', 'status'),
        Index('idx_k8s_node_name', 'k8s_node_name'),
    )


class InspectionRecord(Base):
    """巡检记录表"""
    __tablename__ = 'inspection_records'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(255), ForeignKey('servers.server_id'), nullable=False, index=True)
    inspection_task_id = Column(String(255), index=True)
    
    # 巡检状态
    status = Column(String(50), default='pending')  # pending, running, completed, failed, timeout
    overall_status = Column(String(50), default='unknown')  # normal, warning, critical, unknown
    
    # 执行时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # 重试信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # 详细结果（JSON存储）
    result_json = Column(Text)  # 存储完整的巡检结果
    error_message = Column(Text)
    
    # 关联
    server = relationship('Server', back_populates='inspection_records')
    
    __table_args__ = (
        Index('idx_inspection_server_status', 'server_id', 'status'),
        Index('idx_inspection_created', 'started_at'),
    )


class ResourceMetric(Base):
    """资源指标历史表"""
    __tablename__ = 'resource_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(255), ForeignKey('servers.server_id'), nullable=False, index=True)
    inspection_record_id = Column(Integer, ForeignKey('inspection_records.id'), nullable=True)
    
    # 指标信息
    metric_name = Column(String(100), nullable=False, index=True)  # cpu_usage_percent, memory_usage_percent, disk_usage_percent
    metric_type = Column(String(50))  # cpu, memory, disk, network
    
    # 数值
    value = Column(Float, nullable=False)
    unit = Column(String(20), default='%')
    
    # 状态
    status = Column(String(20), default='normal')  # normal, warning, critical
    warning_threshold = Column(Float)
    critical_threshold = Column(Float)
    
    # 额外信息（JSON存储）
    labels_json = Column(Text)  # 例如磁盘挂载点、网络接口等
    
    # 时间戳
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    collected_at = Column(DateTime)
    
    # 关联
    server = relationship('Server', back_populates='resource_metrics')
    
    __table_args__ = (
        Index('idx_metric_server_time', 'server_id', 'metric_name', 'timestamp'),
        Index('idx_metric_status', 'status'),
    )


class Alert(Base):
    """告警记录表"""
    __tablename__ = 'alerts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(255), ForeignKey('servers.server_id'), nullable=True, index=True)
    inspection_record_id = Column(Integer, ForeignKey('inspection_records.id'), nullable=True)
    
    # 告警基本信息
    alertname = Column(String(255), nullable=False, index=True)
    severity = Column(String(50), index=True)  # critical, warning, info
    status = Column(String(50))  # firing, resolved, suppressed
    
    # 标识信息
    instance = Column(String(255), index=True)
    job = Column(String(255))
    node = Column(String(255))
    namespace = Column(String(255))
    pod = Column(String(255))
    container = Column(String(255))
    
    # 描述信息
    summary = Column(Text)
    description = Column(Text)
    message = Column(Text)
    
    # 标签和注解（JSON存储）
    labels_json = Column(Text)
    annotations_json = Column(Text)
    
    # 时间
    starts_at = Column(DateTime, index=True)
    ends_at = Column(DateTime)
    duration_seconds = Column(Float)
    
    # 来源
    source = Column(String(50))  # alertmanager, prometheus, custom
    fingerprint = Column(String(255), unique=True, index=True)
    generator_url = Column(Text)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联
    server = relationship('Server', back_populates='alerts')


class PredictionResult(Base):
    """预测结果表"""
    __tablename__ = 'prediction_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    server_id = Column(String(255), ForeignKey('servers.server_id'), nullable=False, index=True)
    
    # 预测信息
    metric_name = Column(String(100), index=True)
    prediction_method = Column(String(50))  # trend, ema, combined
    
    # 预测值（JSON存储）
    predicted_values_json = Column(Text)  # 存储预测值列表
    predicted_timestamps_json = Column(Text)  # 存储预测时间点列表
    
    # 趋势和置信度
    trend = Column(String(20))  # increasing, decreasing, stable, unknown
    confidence = Column(Float)
    slope = Column(Float)
    
    # 风险评估
    overall_status = Column(String(20))  # normal, warning, critical
    risk_score = Column(Float)
    
    # 警告和严重预测（JSON存储）
    warnings_json = Column(Text)
    criticals_json = Column(Text)
    recommendation = Column(Text)
    
    # 历史数据信息
    history_data_points = Column(Integer)
    forecast_days = Column(Integer)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    __table_args__ = (
        Index('idx_prediction_server_time', 'server_id', 'created_at'),
        Index('idx_prediction_status', 'overall_status'),
    )


class InspectionBatch(Base):
    """巡检批次表"""
    __tablename__ = 'inspection_batches'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    batch_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # 批次信息
    total_servers = Column(Integer, default=0)
    completed_servers = Column(Integer, default=0)
    failed_servers = Column(Integer, default=0)
    timeout_servers = Column(Integer, default=0)
    
    # 执行状态
    status = Column(String(50), default='pending')  # pending, running, completed, failed
    
    # 时间
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    total_duration_seconds = Column(Float)
    average_duration_seconds = Column(Float)
    
    # 配置
    max_workers = Column(Integer)
    task_timeout_seconds = Column(Integer)
    
    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_batch_created', 'created_at'),
    )


class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: InspectionConfig):
        """初始化数据库管理器
        
        Args:
            config: 配置对象
        """
        if not SQLALCHEMY_AVAILABLE:
            raise ImportError(
                "SQLAlchemy is not installed. "
                "Please install it with 'pip install sqlalchemy' "
                "and the appropriate database driver (pymysql for MySQL, psycopg2 for PostgreSQL)"
            )
        
        self.config = config
        self._engine = None
        self._SessionFactory = None
        
        self._initialize_engine()
    
    def _initialize_engine(self):
        """初始化数据库引擎"""
        database_url = self.config.DATABASE_URL
        
        logger.info(f"Initializing database connection: {database_url.split('@')[0] if '@' in database_url else database_url.split('/')[0]}...")
        
        # 配置连接池
        pool_params = {
            'pool_size': 20,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 3600,
            'echo': False
        }
        
        self._engine = create_engine(database_url, **pool_params)
        self._SessionFactory = sessionmaker(bind=self._engine)
        
        logger.info("Database engine initialized successfully")
    
    def create_tables(self):
        """创建所有数据表"""
        logger.info("Creating database tables...")
        Base.metadata.create_all(self._engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """删除所有数据表（谨慎使用）"""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(self._engine)
        logger.warning("All database tables dropped")
    
    @contextmanager
    def get_session(self) -> Session:
        """获取数据库会话（上下文管理器）
        
        Yields:
            SQLAlchemy会话对象
        """
        session = self._SessionFactory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            session.close()
    
    def save_server(self, server_info: Dict[str, Any], session: Session = None) -> Server:
        """保存服务器信息
        
        Args:
            server_info: 服务器信息字典
            session: 可选的数据库会话
            
        Returns:
            Server对象
        """
        def _save(session: Session):
            server_id = server_info.get('server_id')
            if not server_id:
                raise ValueError("server_id is required")
            
            # 检查是否已存在
            server = session.query(Server).filter_by(server_id=server_id).first()
            
            if not server:
                server = Server(server_id=server_id)
            
            # 更新字段
            server.name = server_info.get('name')
            server.status = server_info.get('status')
            
            # OpenStack信息
            if 'flavor' in server_info:
                flavor = server_info['flavor']
                server.openstack_flavor_id = flavor.get('id')
                server.openstack_flavor_name = flavor.get('name')
                server.vcpus = flavor.get('vcpus')
                server.ram_mb = flavor.get('ram_mb')
                server.disk_gb = flavor.get('disk_gb')
            
            if 'image' in server_info:
                image = server_info['image']
                server.openstack_image_id = image.get('id')
                server.openstack_image_name = image.get('name')
            
            server.openstack_availability_zone = server_info.get('availability_zone')
            server.openstack_host_id = server_info.get('host_id')
            server.openstack_hypervisor_hostname = server_info.get('hypervisor_hostname')
            
            # 网络信息
            if 'networks' in server_info:
                server.networks_json = json.dumps(server_info['networks'], ensure_ascii=False)
            
            # 元数据
            if 'metadata' in server_info:
                server.metadata_json = json.dumps(server_info['metadata'], ensure_ascii=False)
            
            # Kubernetes信息
            if 'k8s_node_name' in server_info:
                server.k8s_node_name = server_info.get('k8s_node_name')
            if 'k8s_status' in server_info:
                server.k8s_status = server_info.get('k8s_status')
            
            # 时间戳
            now = datetime.utcnow()
            server.last_seen_at = now
            if not server.first_seen_at:
                server.first_seen_at = now
            if 'created_at' in server_info and server_info.get('created_at'):
                server.created_at = server_info.get('created_at')
            
            session.add(server)
            session.flush()
            
            logger.debug(f"Saved server: {server_id}")
            return server
        
        if session:
            return _save(session)
        else:
            with self.get_session() as s:
                return _save(s)
    
    def save_inspection_record(self, 
                                record_info: Dict[str, Any],
                                session: Session = None) -> InspectionRecord:
        """保存巡检记录
        
        Args:
            record_info: 巡检记录信息
            session: 可选的数据库会话
            
        Returns:
            InspectionRecord对象
        """
        def _save(session: Session):
            record = InspectionRecord()
            
            record.server_id = record_info.get('server_id')
            record.inspection_task_id = record_info.get('inspection_task_id')
            record.status = record_info.get('status', 'unknown')
            record.overall_status = record_info.get('overall_status', 'unknown')
            record.started_at = record_info.get('started_at')
            record.completed_at = record_info.get('completed_at')
            record.duration_seconds = record_info.get('duration_seconds')
            record.retry_count = record_info.get('retry_count', 0)
            record.max_retries = record_info.get('max_retries', 3)
            
            if 'result' in record_info:
                record.result_json = json.dumps(record_info['result'], ensure_ascii=False)
            
            record.error_message = record_info.get('error_message')
            
            session.add(record)
            session.flush()
            
            logger.debug(f"Saved inspection record for server: {record.server_id}")
            return record
        
        if session:
            return _save(session)
        else:
            with self.get_session() as s:
                return _save(s)
    
    def save_resource_metric(self,
                             metric_info: Dict[str, Any],
                             session: Session = None) -> ResourceMetric:
        """保存资源指标
        
        Args:
            metric_info: 指标信息
            session: 可选的数据库会话
            
        Returns:
            ResourceMetric对象
        """
        def _save(session: Session):
            metric = ResourceMetric()
            
            metric.server_id = metric_info.get('server_id')
            metric.inspection_record_id = metric_info.get('inspection_record_id')
            metric.metric_name = metric_info.get('metric_name')
            metric.metric_type = metric_info.get('metric_type')
            metric.value = metric_info.get('value', 0.0)
            metric.unit = metric_info.get('unit', '%')
            metric.status = metric_info.get('status', 'normal')
            metric.warning_threshold = metric_info.get('warning_threshold')
            metric.critical_threshold = metric_info.get('critical_threshold')
            
            if 'labels' in metric_info:
                metric.labels_json = json.dumps(metric_info['labels'], ensure_ascii=False)
            
            metric.timestamp = metric_info.get('timestamp', datetime.utcnow())
            metric.collected_at = metric_info.get('collected_at')
            
            session.add(metric)
            session.flush()
            
            logger.debug(f"Saved resource metric: {metric.metric_name}={metric.value} for server {metric.server_id}")
            return metric
        
        if session:
            return _save(session)
        else:
            with self.get_session() as s:
                return _save(s)
    
    def save_alert(self,
                  alert_info: Dict[str, Any],
                  session: Session = None) -> Alert:
        """保存告警
        
        Args:
            alert_info: 告警信息
            session: 可选的数据库会话
            
        Returns:
            Alert对象
        """
        def _save(session: Session):
            fingerprint = alert_info.get('fingerprint')
            
            if fingerprint:
                # 检查是否已存在
                alert = session.query(Alert).filter_by(fingerprint=fingerprint).first()
            else:
                alert = None
            
            if not alert:
                alert = Alert()
            
            alert.server_id = alert_info.get('server_id')
            alert.inspection_record_id = alert_info.get('inspection_record_id')
            alert.alertname = alert_info.get('alertname')
            alert.severity = alert_info.get('severity')
            alert.status = alert_info.get('status')
            alert.instance = alert_info.get('instance')
            alert.job = alert_info.get('job')
            alert.node = alert_info.get('node')
            alert.namespace = alert_info.get('namespace')
            alert.pod = alert_info.get('pod')
            alert.container = alert_info.get('container')
            alert.summary = alert_info.get('summary')
            alert.description = alert_info.get('description')
            alert.message = alert_info.get('message')
            
            if 'labels' in alert_info:
                alert.labels_json = json.dumps(alert_info['labels'], ensure_ascii=False)
            if 'annotations' in alert_info:
                alert.annotations_json = json.dumps(alert_info['annotations'], ensure_ascii=False)
            
            alert.starts_at = alert_info.get('starts_at')
            alert.ends_at = alert_info.get('ends_at')
            alert.duration_seconds = alert_info.get('duration_seconds')
            alert.source = alert_info.get('source')
            alert.fingerprint = fingerprint
            alert.generator_url = alert_info.get('generator_url')
            
            session.add(alert)
            session.flush()
            
            logger.debug(f"Saved alert: {alert.alertname} (severity={alert.severity})")
            return alert
        
        if session:
            return _save(session)
        else:
            with self.get_session() as s:
                return _save(s)
    
    def save_prediction_result(self,
                               prediction_info: Dict[str, Any],
                               session: Session = None) -> PredictionResult:
        """保存预测结果
        
        Args:
            prediction_info: 预测结果信息
            session: 可选的数据库会话
            
        Returns:
            PredictionResult对象
        """
        def _save(session: Session):
            prediction = PredictionResult()
            
            prediction.server_id = prediction_info.get('server_id')
            prediction.metric_name = prediction_info.get('metric_name')
            prediction.prediction_method = prediction_info.get('method')
            prediction.trend = prediction_info.get('trend')
            prediction.confidence = prediction_info.get('confidence')
            prediction.slope = prediction_info.get('slope')
            prediction.overall_status = prediction_info.get('overall_status')
            prediction.risk_score = prediction_info.get('risk_score')
            prediction.recommendation = prediction_info.get('recommendation')
            prediction.history_data_points = prediction_info.get('history_data_points')
            prediction.forecast_days = prediction_info.get('forecast_days')
            
            if 'predicted_values' in prediction_info:
                prediction.predicted_values_json = json.dumps(
                    prediction_info['predicted_values'], ensure_ascii=False
                )
            if 'predicted_timestamps' in prediction_info:
                # 转换datetime为字符串
                timestamps = []
                for ts in prediction_info.get('predicted_timestamps', []):
                    if isinstance(ts, datetime):
                        timestamps.append(ts.isoformat())
                    else:
                        timestamps.append(str(ts))
                prediction.predicted_timestamps_json = json.dumps(timestamps, ensure_ascii=False)
            
            if 'warnings' in prediction_info:
                prediction.warnings_json = json.dumps(prediction_info['warnings'], ensure_ascii=False)
            if 'criticals' in prediction_info:
                prediction.criticals_json = json.dumps(prediction_info['criticals'], ensure_ascii=False)
            
            session.add(prediction)
            session.flush()
            
            logger.debug(f"Saved prediction result for server: {prediction.server_id}")
            return prediction
        
        if session:
            return _save(session)
        else:
            with self.get_session() as s:
                return _save(s)
    
    def save_inspection_batch(self,
                              batch_info: Dict[str, Any],
                              session: Session = None) -> InspectionBatch:
        """保存巡检批次
        
        Args:
            batch_info: 批次信息
            session: 可选的数据库会话
            
        Returns:
            InspectionBatch对象
        """
        def _save(session: Session):
            batch_id = batch_info.get('batch_id')
            
            if batch_id:
                batch = session.query(InspectionBatch).filter_by(batch_id=batch_id).first()
            else:
                batch = None
            
            if not batch:
                batch = InspectionBatch()
                if batch_id:
                    batch.batch_id = batch_id
            
            batch.total_servers = batch_info.get('total_servers', 0)
            batch.completed_servers = batch_info.get('completed_servers', 0)
            batch.failed_servers = batch_info.get('failed_servers', 0)
            batch.timeout_servers = batch_info.get('timeout_servers', 0)
            batch.status = batch_info.get('status', 'pending')
            batch.started_at = batch_info.get('started_at')
            batch.completed_at = batch_info.get('completed_at')
            batch.total_duration_seconds = batch_info.get('total_duration_seconds')
            batch.average_duration_seconds = batch_info.get('average_duration_seconds')
            batch.max_workers = batch_info.get('max_workers')
            batch.task_timeout_seconds = batch_info.get('task_timeout_seconds')
            
            session.add(batch)
            session.flush()
            
            logger.debug(f"Saved inspection batch: {batch.batch_id}")
            return batch
        
        if session:
            return _save(session)
        else:
            with self.get_session() as s:
                return _save(s)
    
    def get_server_history_metrics(self,
                                   server_id: str,
                                   metric_name: str,
                                   days: int = 7,
                                   session: Session = None) -> List[Dict[str, Any]]:
        """获取服务器的历史指标数据
        
        Args:
            server_id: 服务器ID
            metric_name: 指标名称
            days: 获取最近多少天的数据
            session: 可选的数据库会话
            
        Returns:
            历史指标列表，每个元素包含 timestamp 和 value
        """
        def _get(session: Session) -> List[Dict]:
            cutoff_time = datetime.utcnow() - timedelta(days=days)
            
            metrics = session.query(ResourceMetric).filter(
                ResourceMetric.server_id == server_id,
                ResourceMetric.metric_name == metric_name,
                ResourceMetric.timestamp >= cutoff_time
            ).order_by(ResourceMetric.timestamp).all()
            
            result = []
            for metric in metrics:
                result.append({
                    'timestamp': metric.timestamp,
                    'value': metric.value
                })
            
            return result
        
        if session:
            return _get(session)
        else:
            with self.get_session() as s:
                return _get(s)
    
    def get_all_servers(self, session: Session = None) -> List[Server]:
        """获取所有服务器
        
        Args:
            session: 可选的数据库会话
            
        Returns:
            服务器列表
        """
        def _get(session: Session) -> List[Server]:
            return session.query(Server).all()
        
        if session:
            return _get(session)
        else:
            with self.get_session() as s:
                return _get(s)
    
    def get_server_by_id(self, server_id: str, session: Session = None) -> Optional[Server]:
        """根据ID获取服务器
        
        Args:
            server_id: 服务器ID
            session: 可选的数据库会话
            
        Returns:
            服务器对象，如果不存在则返回None
        """
        def _get(session: Session) -> Optional[Server]:
            return session.query(Server).filter_by(server_id=server_id).first()
        
        if session:
            return _get(session)
        else:
            with self.get_session() as s:
                return _get(s)
    
    def cleanup_old_data(self,
                        retention_days: int = 30,
                        session: Session = None):
        """清理旧数据
        
        Args:
            retention_days: 保留天数
            session: 可选的数据库会话
        """
        def _cleanup(session: Session):
            cutoff_time = datetime.utcnow() - timedelta(days=retention_days)
            
            # 删除旧的资源指标
            deleted_metrics = session.query(ResourceMetric).filter(
                ResourceMetric.timestamp < cutoff_time
            ).delete()
            
            # 删除旧的预测结果
            deleted_predictions = session.query(PredictionResult).filter(
                PredictionResult.created_at < cutoff_time
            ).delete()
            
            # 删除旧的告警（保留resolved状态超过30天的）
            deleted_alerts = session.query(Alert).filter(
                Alert.updated_at < cutoff_time,
                Alert.status == 'resolved'
            ).delete()
            
            logger.info(
                f"Cleaned up old data: {deleted_metrics} metrics, "
                f"{deleted_predictions} predictions, {deleted_alerts} alerts"
            )
        
        if session:
            _cleanup(session)
        else:
            with self.get_session() as s:
                _cleanup(s)
    
    def close(self):
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            logger.info("Database connection closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
