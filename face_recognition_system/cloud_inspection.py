#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
OpenStack云资源池服务器巡检脚本
支持并发巡检1000台主机，平均每台执行时间约2分钟

功能：
1. 云主机基本配置信息采集
2. 活跃告警信息获取
3. 资源水位监控
4. 未来主机状态预测分析
"""

import logging
import sys
import argparse
import json
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cloud_inspection.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

# 导入模块
try:
    from inspection_config import InspectionConfig
    from openstack_client import OpenStackClient
    from kubernetes_client import KubernetesClient
    from alert_system_client import AlertSystemClient
    from resource_monitor import ResourceMonitor
    from predictor import TimeSeriesPredictor, AlertPredictor
    from concurrent_engine import ConcurrentInspectionEngine, BatchProgressTracker
    from database_models import DatabaseManager
    MODULES_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    MODULES_AVAILABLE = False


class CloudInspectionSystem:
    """云资源池巡检系统"""
    
    def __init__(self, config: InspectionConfig = None):
        """初始化巡检系统
        
        Args:
            config: 配置对象
        """
        if config is None:
            config = InspectionConfig()
        
        self.config = config
        
        # 初始化组件
        self.openstack_client: Optional[OpenStackClient] = None
        self.k8s_client: Optional[KubernetesClient] = None
        self.alert_client: Optional[AlertSystemClient] = None
        self.resource_monitor: Optional[ResourceMonitor] = None
        self.predictor: Optional[TimeSeriesPredictor] = None
        self.alert_predictor: Optional[AlertPredictor] = None
        self.db_manager: Optional[DatabaseManager] = None
        
        self._initialized = False
    
    def initialize(self):
        """初始化所有组件"""
        if self._initialized:
            return
        
        logger.info("Initializing Cloud Inspection System...")
        
        # 初始化数据库管理器
        try:
            self.db_manager = DatabaseManager(self.config)
            self.db_manager.create_tables()
            logger.info("Database manager initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize database manager: {e}")
            logger.warning("Database operations will be skipped")
        
        # 初始化预测器
        self.predictor = TimeSeriesPredictor(
            history_days=self.config.PREDICTION_HISTORY_DAYS,
            forecast_days=self.config.PREDICTION_FORECAST_DAYS
        )
        logger.info("Predictor initialized")
        
        # 初始化告警预测器
        self.alert_predictor = AlertPredictor(
            history_days=14,  # 使用14天的历史告警数据
            forecast_days=self.config.PREDICTION_FORECAST_DAYS
        )
        logger.info("Alert Predictor initialized")
        
        self._initialized = True
        logger.info("Cloud Inspection System initialized successfully")
    
    def _get_openstack_client(self) -> OpenStackClient:
        """获取OpenStack客户端（延迟初始化）"""
        if self.openstack_client is None:
            self.openstack_client = OpenStackClient(self.config)
        return self.openstack_client
    
    def _get_k8s_client(self) -> KubernetesClient:
        """获取Kubernetes客户端（延迟初始化）"""
        if self.k8s_client is None:
            self.k8s_client = KubernetesClient(self.config)
        return self.k8s_client
    
    def _get_alert_client(self) -> AlertSystemClient:
        """获取告警系统客户端（延迟初始化）"""
        if self.alert_client is None:
            self.alert_client = AlertSystemClient(self.config)
        return self.alert_client
    
    def _get_resource_monitor(self) -> ResourceMonitor:
        """获取资源监控器（延迟初始化）"""
        if self.resource_monitor is None:
            self.resource_monitor = ResourceMonitor(self.config)
        return self.resource_monitor
    
    def inspect_single_server(self,
                              server_id: str,
                              server_name: str = None,
                              server_ips: List[str] = None) -> Dict[str, Any]:
        """巡检单台服务器
        
        Args:
            server_id: 服务器ID
            server_name: 服务器名称
            server_ips: 服务器IP列表
            
        Returns:
            巡检结果字典
        """
        start_time = datetime.now()
        logger.info(f"Starting inspection for server: {server_id} ({server_name})")
        
        result = {
            'server_id': server_id,
            'server_name': server_name,
            'server_ips': server_ips or [],
            'inspection_start_time': start_time,
            'status': 'running',
            'components': {}
        }
        
        try:
            # 1. 获取OpenStack基本信息
            try:
                openstack_client = self._get_openstack_client()
                server = openstack_client.get_server_by_id(server_id)
                
                if server:
                    server_details = openstack_client.get_server_details(server)
                    result['components']['openstack'] = {
                        'status': 'success',
                        'data': server_details
                    }
                    
                    # 保存到数据库
                    if self.db_manager:
                        self.db_manager.save_server(server_details)
                else:
                    result['components']['openstack'] = {
                        'status': 'not_found',
                        'error': f'Server {server_id} not found in OpenStack'
                    }
            except Exception as e:
                logger.error(f"Failed to get OpenStack info for {server_id}: {e}")
                result['components']['openstack'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # 2. 获取Kubernetes信息
            try:
                k8s_client = self._get_k8s_client()
                
                # 尝试通过IP或名称查找节点
                k8s_node = None
                
                # 首先尝试通过名称查找
                if server_name:
                    k8s_node = k8s_client.get_node_by_name(server_name)
                
                # 如果没有找到，尝试通过IP查找
                if not k8s_node and server_ips:
                    all_nodes = k8s_client.get_all_nodes()
                    for node in all_nodes:
                        node_addresses = node.get('addresses', [])
                        node_ips = [addr.get('address') for addr in node_addresses if addr.get('type') in ['InternalIP', 'ExternalIP']]
                        
                        for server_ip in server_ips:
                            if server_ip in node_ips:
                                k8s_node = node
                                break
                        if k8s_node:
                            break
                
                if k8s_node:
                    # 获取该节点上的Pod
                    node_pods = k8s_client.get_node_pods(k8s_node.get('name', ''))
                    
                    # 获取节点指标
                    node_metrics = k8s_client.get_node_metrics(k8s_node.get('name', ''))
                    
                    result['components']['kubernetes'] = {
                        'status': 'success',
                        'node_info': k8s_node,
                        'pods_count': len(node_pods),
                        'pods': node_pods[:10],  # 只保存前10个Pod的详细信息
                        'metrics': node_metrics
                    }
                else:
                    result['components']['kubernetes'] = {
                        'status': 'not_found',
                        'error': f'Kubernetes node not found for server {server_id}'
                    }
            except Exception as e:
                logger.error(f"Failed to get Kubernetes info for {server_id}: {e}")
                result['components']['kubernetes'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # 3. 获取告警信息
            try:
                alert_client = self._get_alert_client()
                server_alerts = alert_client.get_alerts_for_server(
                    server_id=server_id,
                    server_name=server_name,
                    server_ips=server_ips
                )
                
                result['components']['alerts'] = {
                    'status': 'success',
                    'count': len(server_alerts),
                    'alerts': server_alerts
                }
                
                # 保存告警到数据库
                if self.db_manager and server_alerts:
                    for alert in server_alerts:
                        alert['server_id'] = server_id
                        self.db_manager.save_alert(alert)
            except Exception as e:
                logger.error(f"Failed to get alerts for {server_id}: {e}")
                result['components']['alerts'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # 4. 获取资源监控信息
            try:
                resource_monitor = self._get_resource_monitor()
                
                resource_metrics = {}
                if server_ips:
                    # 获取所有相关IP的资源指标
                    metrics_result = resource_monitor.get_resource_metrics_for_servers(server_ips)
                    
                    # 合并所有IP的指标
                    all_cpu = []
                    all_memory = []
                    all_disk = []
                    all_network = []
                    
                    for ip, metrics in metrics_result.items():
                        if metrics:
                            if 'cpu_usage' in metrics:
                                all_cpu.extend(metrics['cpu_usage'])
                            if 'memory_usage' in metrics:
                                all_memory.extend(metrics['memory_usage'])
                            if 'disk_usage' in metrics:
                                all_disk.extend(metrics['disk_usage'])
                            if 'network_stats' in metrics:
                                all_network.extend(metrics['network_stats'])
                    
                    resource_metrics = {
                        'cpu_usage': all_cpu,
                        'memory_usage': all_memory,
                        'disk_usage': all_disk,
                        'network_stats': all_network,
                        'overall_status': metrics.get('overall_status', 'unknown') if metrics else 'unknown'
                    }
                    
                    # 保存资源指标到数据库
                    if self.db_manager:
                        all_metrics = all_cpu + all_memory + all_disk
                        for metric in all_metrics:
                            metric['server_id'] = server_id
                            self.db_manager.save_resource_metric(metric)
                
                result['components']['resources'] = {
                    'status': 'success' if resource_metrics else 'no_data',
                    'metrics': resource_metrics
                }
            except Exception as e:
                logger.error(f"Failed to get resource metrics for {server_id}: {e}")
                result['components']['resources'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # 5. 执行预测分析
            try:
                prediction_result = self._perform_prediction(server_id)
                result['components']['prediction'] = {
                    'status': 'success',
                    'prediction': prediction_result
                }
                
                # 保存预测结果到数据库
                if self.db_manager and prediction_result:
                    # 保存每个指标的预测结果
                    for metric_name, pred in prediction_result.get('metric_predictions', {}).items():
                        pred['server_id'] = server_id
                        pred['metric_name'] = metric_name
                        self.db_manager.save_prediction_result(pred)
                    
                    # 保存整体资源预测
                    if 'overall_resource_prediction' in prediction_result and prediction_result['overall_resource_prediction']:
                        overall_resource = prediction_result['overall_resource_prediction']
                        overall_resource['server_id'] = server_id
                        overall_resource['metric_name'] = 'overall_resource'
                        self.db_manager.save_prediction_result(overall_resource)
                    
                    # 保存告警预测结果
                    if 'alert_prediction' in prediction_result and prediction_result['alert_prediction']:
                        alert_pred = prediction_result['alert_prediction']
                        
                        # 使用专门的方法保存告警预测
                        if 'risk_assessment' in alert_pred:
                            # 提取风险评估信息保存
                            risk_assessment = alert_pred['risk_assessment']
                            risk_assessment['server_id'] = server_id
                            risk_assessment['metric_name'] = 'alert_prediction'
                            risk_assessment['overall_status'] = risk_assessment.get('overall_risk_level', 'low')
                            risk_assessment['risk_score'] = risk_assessment.get('risk_score', 0.0)
                            risk_assessment['forecast_days'] = alert_pred.get('forecast_days', 3)
                            
                            # 保存预测的告警列表
                            predictions = alert_pred.get('predictions', [])
                            if predictions:
                                risk_assessment['predicted_values'] = [
                                    {
                                        'alertname': p.get('alertname'),
                                        'severity': p.get('severity'),
                                        'confidence': p.get('confidence'),
                                        'sources': p.get('sources', [])
                                    }
                                    for p in predictions
                                ]
                            
                            self.db_manager.save_alert_prediction(risk_assessment)
            except Exception as e:
                logger.error(f"Failed to perform prediction for {server_id}: {e}")
                result['components']['prediction'] = {
                    'status': 'failed',
                    'error': str(e)
                }
            
            # 计算整体状态
            result['overall_status'] = self._calculate_overall_status(result)
            result['status'] = 'completed'
            
        except Exception as e:
            logger.error(f"Inspection failed for server {server_id}: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
            result['overall_status'] = 'unknown'
        
        finally:
            end_time = datetime.now()
            result['inspection_end_time'] = end_time
            result['duration_seconds'] = (end_time - start_time).total_seconds()
            
            logger.info(
                f"Inspection completed for server {server_id}: "
                f"status={result['status']}, "
                f"duration={result['duration_seconds']:.2f}s"
            )
        
        return result
    
    def _perform_prediction(self, server_id: str) -> Dict[str, Any]:
        """执行预测分析
        
        包括资源使用预测和告警预测
        
        Args:
            server_id: 服务器ID
            
        Returns:
            预测结果字典
        """
        if not self.db_manager:
            logger.warning("No database manager, skipping prediction")
            return {'error': 'No database available'}
        
        # ============================================
        # 1. 资源使用预测（现有功能）
        # ============================================
        
        # 获取历史指标数据
        metrics_to_predict = [
            'cpu_usage_percent',
            'memory_usage_percent',
            'disk_usage_percent'
        ]
        
        history_metrics = {}
        metric_predictions = {}
        
        for metric_name in metrics_to_predict:
            # 获取最近7天的历史数据
            history_data = self.db_manager.get_server_history_metrics(
                server_id=server_id,
                metric_name=metric_name,
                days=self.config.PREDICTION_HISTORY_DAYS
            )
            
            if history_data and len(history_data) >= 3:
                history_metrics[metric_name] = history_data
                
                # 执行预测
                prediction = self.predictor.predict_resource_usage(
                    history_data=history_data,
                    metric_name=metric_name
                )
                metric_predictions[metric_name] = prediction
        
        # 执行整体资源预测
        overall_resource_prediction = None
        if history_metrics:
            # 定义阈值
            thresholds = {
                'cpu_usage_percent': {'warning': 70.0, 'critical': 90.0},
                'memory_usage_percent': {'warning': 75.0, 'critical': 90.0},
                'disk_usage_percent': {'warning': 80.0, 'critical': 90.0}
            }
            
            overall_resource_prediction = self.predictor.predict_host_status(
                server_id=server_id,
                history_metrics=history_metrics,
                thresholds=thresholds
            )
        
        # ============================================
        # 2. 告警预测（新增功能）
        # ============================================
        
        alert_prediction = None
        
        try:
            # 获取历史告警数据（最近14天）
            history_alerts = self.db_manager.get_server_history_alerts(
                server_id=server_id,
                days=14  # 使用14天的历史告警数据进行预测
            )
            
            logger.info(f"Found {len(history_alerts)} historical alerts for server {server_id}")
            
            # 执行告警预测
            # 需要将资源预测结果转换为AlertPredictor需要的格式
            resource_predictions_for_alert = {}
            for metric_name, pred in metric_predictions.items():
                resource_predictions_for_alert[metric_name] = pred
            
            # 定义资源阈值用于告警预测
            resource_thresholds = {
                'cpu_usage_percent': {'warning': 70.0, 'critical': 90.0},
                'memory_usage_percent': {'warning': 75.0, 'critical': 90.0},
                'disk_usage_percent': {'warning': 80.0, 'critical': 90.0}
            }
            
            # 执行告警预测
            if self.alert_predictor:
                alert_prediction = self.alert_predictor.predict_server_alerts(
                    server_id=server_id,
                    history_alerts=history_alerts,
                    resource_predictions=resource_predictions_for_alert if resource_predictions_for_alert else None,
                    resource_thresholds=resource_thresholds,
                    steps=self.config.PREDICTION_FORECAST_DAYS
                )
                
                logger.info(f"Alert prediction completed for server {server_id}: "
                           f"risk_level={alert_prediction.get('risk_assessment', {}).get('overall_risk_level', 'unknown')}")
        
        except Exception as e:
            logger.error(f"Failed to perform alert prediction for server {server_id}: {e}")
            alert_prediction = {
                'error': str(e),
                'server_id': server_id,
                'prediction_timestamp': datetime.now()
            }
        
        # ============================================
        # 3. 整合结果
        # ============================================
        
        result = {
            'metric_predictions': metric_predictions,
            'overall_resource_prediction': overall_resource_prediction,
            'alert_prediction': alert_prediction,
            'history_data_points': {
                'resource_metrics': {k: len(v) for k, v in history_metrics.items()},
                'alerts_count': len(history_alerts) if 'history_alerts' in locals() else 0
            },
            'prediction_timestamp': datetime.now()
        }
        
        # 计算综合预测状态
        result['overall_prediction_status'] = self._calculate_combined_prediction_status(
            overall_resource_prediction,
            alert_prediction
        )
        
        return result
    
    def _calculate_combined_prediction_status(self,
                                               resource_prediction: Dict[str, Any],
                                               alert_prediction: Dict[str, Any]) -> str:
        """计算综合预测状态
        
        结合资源预测和告警预测，确定整体预测状态
        
        Args:
            resource_prediction: 资源预测结果
            alert_prediction: 告警预测结果
            
        Returns:
            综合状态: normal, warning, critical, unknown
        """
        statuses = []
        
        # 检查资源预测状态
        if resource_prediction:
            resource_status = resource_prediction.get('overall_status', 'unknown')
            if resource_status in ['critical', 'warning']:
                statuses.append(resource_status)
        
        # 检查告警预测状态
        if alert_prediction and 'risk_assessment' in alert_prediction:
            risk_level = alert_prediction['risk_assessment'].get('overall_risk_level', 'low')
            
            # 将风险级别映射到状态
            if risk_level == 'high':
                statuses.append('critical')
            elif risk_level == 'medium':
                statuses.append('warning')
        
        # 确定最终状态
        if 'critical' in statuses:
            return 'critical'
        elif 'warning' in statuses:
            return 'warning'
        elif statuses or (resource_prediction and resource_prediction.get('overall_status') == 'normal'):
            return 'normal'
        else:
            return 'unknown'
    
    def _calculate_overall_status(self, result: Dict[str, Any]) -> str:
        """计算整体状态
        
        Args:
            result: 巡检结果
            
        Returns:
            整体状态: normal, warning, critical, unknown
        """
        statuses = []
        
        # 检查告警
        alerts = result.get('components', {}).get('alerts', {})
        if alerts.get('count', 0) > 0:
            for alert in alerts.get('alerts', []):
                severity = alert.get('severity', '')
                if severity == 'critical':
                    return 'critical'
                elif severity == 'warning':
                    statuses.append('warning')
        
        # 检查资源状态
        resources = result.get('components', {}).get('resources', {}).get('metrics', {})
        overall_resource_status = resources.get('overall_status', 'unknown')
        
        if overall_resource_status == 'critical':
            return 'critical'
        elif overall_resource_status == 'warning':
            statuses.append('warning')
        
        # 检查预测状态
        prediction = result.get('components', {}).get('prediction', {}).get('prediction', {})
        
        # 检查综合预测状态（新字段）
        overall_prediction_status = prediction.get('overall_prediction_status', 'unknown')
        
        if overall_prediction_status == 'critical':
            statuses.append('critical')
        elif overall_prediction_status == 'warning':
            statuses.append('warning')
        
        # 也检查旧的字段以保持兼容性
        if overall_prediction_status == 'unknown':
            # 检查整体资源预测
            overall_resource_prediction = prediction.get('overall_resource_prediction', {})
            resource_prediction_status = overall_resource_prediction.get('overall_status', 'unknown')
            
            if resource_prediction_status == 'critical':
                statuses.append('critical')
            elif resource_prediction_status == 'warning':
                statuses.append('warning')
            
            # 检查告警预测
            alert_prediction = prediction.get('alert_prediction', {})
            if alert_prediction and 'risk_assessment' in alert_prediction:
                risk_level = alert_prediction['risk_assessment'].get('overall_risk_level', 'low')
                
                if risk_level == 'high':
                    statuses.append('critical')
                elif risk_level == 'medium':
                    statuses.append('warning')
        
        # 确定最终状态
        if 'critical' in statuses:
            return 'critical'
        elif 'warning' in statuses:
            return 'warning'
        elif statuses or overall_resource_status == 'normal':
            return 'normal'
        else:
            return 'unknown'
    
    def get_all_servers_from_openstack(self) -> List[Dict[str, Any]]:
        """从OpenStack获取所有服务器列表
        
        Returns:
            服务器列表，每个元素包含 server_id, server_name, server_ips
        """
        logger.info("Fetching all servers from OpenStack...")
        
        openstack_client = self._get_openstack_client()
        servers = openstack_client.get_all_servers()
        
        server_list = []
        for server in servers:
            server_ips = openstack_client.get_server_ips(server)
            
            server_list.append({
                'server_id': server.id,
                'server_name': server.name,
                'server_ips': server_ips
            })
        
        logger.info(f"Found {len(server_list)} servers in OpenStack")
        return server_list
    
    def run_inspection(self,
                      servers: List[Dict[str, Any]] = None,
                      max_workers: int = None,
                      batch_size: int = 100,
                      batch_delay: int = 2) -> Dict[str, Any]:
        """执行巡检
        
        Args:
            servers: 服务器列表，如果为None则从OpenStack获取
            max_workers: 最大并发数，默认使用配置中的值
            batch_size: 每批处理的服务器数量
            batch_delay: 批次之间的延迟（秒）
            
        Returns:
            巡检结果汇总
        """
        self.initialize()
        
        # 如果没有提供服务器列表，从OpenStack获取
        if servers is None:
            servers = self.get_all_servers_from_openstack()
        
        if not servers:
            logger.warning("No servers to inspect")
            return {
                'timestamp': datetime.now(),
                'total_servers': 0,
                'status': 'no_servers',
                'results': {}
            }
        
        total_servers = len(servers)
        logger.info(f"Starting inspection for {total_servers} servers")
        
        # 创建批次ID
        batch_id = str(uuid.uuid4())
        
        # 保存批次信息到数据库
        if self.db_manager:
            self.db_manager.save_inspection_batch({
                'batch_id': batch_id,
                'total_servers': total_servers,
                'status': 'running',
                'started_at': datetime.now(),
                'max_workers': max_workers or self.config.MAX_CONCURRENT_HOSTS,
                'task_timeout_seconds': self.config.HOST_INSPECTION_TIMEOUT
            })
        
        # 创建并发引擎
        engine = ConcurrentInspectionEngine(
            max_workers=max_workers or self.config.MAX_CONCURRENT_HOSTS,
            task_timeout_seconds=self.config.HOST_INSPECTION_TIMEOUT,
            max_retries=self.config.RETRY_COUNT,
            retry_delay_seconds=self.config.RETRY_DELAY
        )
        
        # 创建进度跟踪器
        total_batches = (total_servers + batch_size - 1) // batch_size
        progress_tracker = BatchProgressTracker(total_batches=total_batches)
        
        all_results = []
        
        try:
            # 分批处理
            for batch_num, i in enumerate(range(0, total_servers, batch_size), 1):
                batch = servers[i:i + batch_size]
                
                progress_tracker.start_batch(batch_num, len(batch))
                
                # 执行该批次
                batch_results = engine.run(
                    inspection_func=self.inspect_single_server,
                    server_batch=batch,
                    batch_size=len(batch),
                    batch_delay_seconds=0  # 批次内不需要延迟
                )
                
                all_results.append(batch_results)
                
                progress_tracker.end_batch()
                
                # 批次间延迟
                if batch_num < total_batches and batch_delay > 0:
                    logger.info(f"Waiting {batch_delay} seconds before next batch...")
                    time.sleep(batch_delay)
                
                # 定期清理旧数据
                if self.db_manager and batch_num % 10 == 0:
                    try:
                        self.db_manager.cleanup_old_data(
                            retention_days=self.config.RESOURCE_METRICS_RETENTION_DAYS
                        )
                    except Exception as e:
                        logger.warning(f"Failed to cleanup old data: {e}")
        
        finally:
            engine.shutdown(wait=True)
        
        # 汇总结果
        final_summary = self._summarize_results(all_results, total_servers)
        
        # 更新批次信息
        if self.db_manager:
            self.db_manager.save_inspection_batch({
                'batch_id': batch_id,
                'completed_servers': final_summary['summary']['completed'],
                'failed_servers': final_summary['summary']['failed'],
                'timeout_servers': final_summary['summary']['timeout'],
                'status': 'completed',
                'completed_at': datetime.now(),
                'total_duration_seconds': final_summary['summary']['total_duration_seconds'],
                'average_duration_seconds': final_summary['summary']['average_duration_seconds']
            })
        
        return final_summary
    
    def _summarize_results(self,
                           all_results: List[Dict[str, Any]],
                           total_servers: int) -> Dict[str, Any]:
        """汇总所有批次的结果
        
        Args:
            all_results: 所有批次的结果列表
            total_servers: 总服务器数
            
        Returns:
            汇总结果
        """
        total_completed = 0
        total_failed = 0
        total_timeout = 0
        all_completed_tasks = []
        all_failed_tasks = []
        all_timeout_tasks = []
        total_duration = 0.0
        
        for batch_result in all_results:
            summary = batch_result.get('summary', {})
            total_completed += summary.get('completed', 0)
            total_failed += summary.get('failed', 0)
            total_timeout += summary.get('timeout', 0)
            total_duration += summary.get('total_duration_seconds', 0)
            
            all_completed_tasks.extend(batch_result.get('completed_tasks', []))
            all_failed_tasks.extend(batch_result.get('failed_tasks', []))
            all_timeout_tasks.extend(batch_result.get('timeout_tasks', []))
        
        # 计算状态分布
        status_counts = {
            'normal': 0,
            'warning': 0,
            'critical': 0,
            'unknown': 0
        }
        
        for task in all_completed_tasks:
            result = task.get('result', {})
            overall_status = result.get('overall_status', 'unknown')
            if overall_status in status_counts:
                status_counts[overall_status] += 1
            else:
                status_counts['unknown'] += 1
        
        # 计算平均时间
        completed_count = len(all_completed_tasks)
        avg_duration = total_duration / completed_count if completed_count > 0 else 0
        
        return {
            'timestamp': datetime.now(),
            'summary': {
                'total': total_servers,
                'completed': total_completed,
                'failed': total_failed,
                'timeout': total_timeout,
                'total_duration_seconds': round(total_duration, 2),
                'average_duration_seconds': round(avg_duration, 2)
            },
            'status_distribution': status_counts,
            'completed_tasks': all_completed_tasks,
            'failed_tasks': all_failed_tasks,
            'timeout_tasks': all_timeout_tasks
        }
    
    def generate_report(self, results: Dict[str, Any], output_file: str = None) -> str:
        """生成巡检报告
        
        Args:
            results: 巡检结果
            output_file: 输出文件路径
            
        Returns:
            报告内容
        """
        summary = results.get('summary', {})
        status_dist = results.get('status_distribution', {})
        
        # 生成Markdown报告
        report_lines = [
            f"# OpenStack云资源池服务器巡检报告",
            f"",
            f"## 生成时间",
            f"{results.get('timestamp', datetime.now())}",
            f"",
            f"## 执行概况",
            f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 总服务器数 | {summary.get('total', 0)} |",
            f"| 巡检完成 | {summary.get('completed', 0)} |",
            f"| 巡检失败 | {summary.get('failed', 0)} |",
            f"| 巡检超时 | {summary.get('timeout', 0)} |",
            f"| 总耗时(秒) | {summary.get('total_duration_seconds', 0)} |",
            f"| 平均每台耗时(秒) | {summary.get('average_duration_seconds', 0)} |",
            f"",
            f"## 状态分布",
            f"",
            f"| 状态 | 数量 | 占比 |",
            f"|------|------|------|",
        ]
        
        total = summary.get('total', 1)
        for status, count in status_dist.items():
            percentage = round(count / total * 100, 2) if total > 0 else 0
            status_label = {
                'normal': '正常',
                'warning': '警告',
                'critical': '严重',
                'unknown': '未知'
            }.get(status, status)
            report_lines.append(f"| {status_label} | {count} | {percentage}% |")
        
        report_lines.extend([
            f"",
            f"## 详细结果",
            f"",
        ])
        
        # 添加严重和警告的服务器列表
        critical_servers = []
        warning_servers = []
        
        for task in results.get('completed_tasks', []):
            result = task.get('result', {})
            overall_status = result.get('overall_status', 'unknown')
            
            if overall_status == 'critical':
                critical_servers.append({
                    'server_id': task.get('server_id'),
                    'server_name': task.get('server_name'),
                    'duration': task.get('duration_seconds')
                })
            elif overall_status == 'warning':
                warning_servers.append({
                    'server_id': task.get('server_id'),
                    'server_name': task.get('server_name'),
                    'duration': task.get('duration_seconds')
                })
        
        if critical_servers:
            report_lines.extend([
                f"### 严重状态服务器 ({len(critical_servers)}台)",
                f"",
                f"| 服务器ID | 服务器名称 | 巡检耗时(秒) |",
                f"|----------|------------|--------------|",
            ])
            for s in critical_servers:
                report_lines.append(f"| {s['server_id']} | {s['server_name'] or '-'} | {s['duration'] or '-'} |")
            report_lines.append(f"")
        
        if warning_servers:
            report_lines.extend([
                f"### 警告状态服务器 ({len(warning_servers)}台)",
                f"",
                f"| 服务器ID | 服务器名称 | 巡检耗时(秒) |",
                f"|----------|------------|--------------|",
            ])
            for s in warning_servers:
                report_lines.append(f"| {s['server_id']} | {s['server_name'] or '-'} | {s['duration'] or '-'} |")
            report_lines.append(f"")
        
        # 添加失败的服务器列表
        failed_tasks = results.get('failed_tasks', []) + results.get('timeout_tasks', [])
        if failed_tasks:
            report_lines.extend([
                f"### 巡检失败服务器 ({len(failed_tasks)}台)",
                f"",
                f"| 服务器ID | 服务器名称 | 状态 | 错误信息 |",
                f"|----------|------------|------|----------|",
            ])
            for task in failed_tasks:
                error = task.get('error', '-')[:100] if task.get('error') else '-'
                report_lines.append(f"| {task.get('server_id')} | {task.get('server_name') or '-'} | {task.get('status')} | {error} |")
            report_lines.append(f"")
        
        # ============================================
        # 新增：告警预测信息
        # ============================================
        
        # 收集告警预测信息
        high_risk_servers = []
        medium_risk_servers = []
        predicted_alerts_summary = {}
        
        for task in results.get('completed_tasks', []):
            result = task.get('result', {})
            prediction = result.get('components', {}).get('prediction', {}).get('prediction', {})
            alert_prediction = prediction.get('alert_prediction', {})
            
            if alert_prediction and 'risk_assessment' in alert_prediction:
                risk_assessment = alert_prediction['risk_assessment']
                risk_level = risk_assessment.get('overall_risk_level', 'low')
                
                server_info = {
                    'server_id': task.get('server_id'),
                    'server_name': task.get('server_name'),
                    'risk_score': risk_assessment.get('risk_score', 0.0),
                    'critical_alerts_count': risk_assessment.get('critical_alerts_count', 0),
                    'warning_alerts_count': risk_assessment.get('warning_alerts_count', 0),
                    'recommendation': risk_assessment.get('recommendation', ''),
                    'predicted_alerts': alert_prediction.get('predictions', [])
                }
                
                if risk_level == 'high':
                    high_risk_servers.append(server_info)
                elif risk_level == 'medium':
                    medium_risk_servers.append(server_info)
                
                # 统计预测的告警类型
                for alert in alert_prediction.get('predictions', []):
                    alertname = alert.get('alertname', 'Unknown')
                    if alertname not in predicted_alerts_summary:
                        predicted_alerts_summary[alertname] = {
                            'count': 0,
                            'critical_count': 0,
                            'warning_count': 0,
                            'servers': []
                        }
                    
                    predicted_alerts_summary[alertname]['count'] += 1
                    if alert.get('severity') == 'critical':
                        predicted_alerts_summary[alertname]['critical_count'] += 1
                    elif alert.get('severity') == 'warning':
                        predicted_alerts_summary[alertname]['warning_count'] += 1
                    
                    if task.get('server_id') not in predicted_alerts_summary[alertname]['servers']:
                        predicted_alerts_summary[alertname]['servers'].append(task.get('server_id'))
        
        # 添加告警预测报告
        report_lines.extend([
            f"",
            f"## 告警预测分析",
            f"",
        ])
        
        # 告警预测统计
        total_high_risk = len(high_risk_servers)
        total_medium_risk = len(medium_risk_servers)
        
        report_lines.extend([
            f"### 预测风险统计",
            f"",
            f"| 风险级别 | 服务器数量 | 说明 |",
            f"|----------|------------|------|",
            f"| 高风险 | {total_high_risk} | 预测未来可能发生严重告警 |",
            f"| 中风险 | {total_medium_risk} | 预测未来可能发生警告告警 |",
            f"| 低风险 | {summary.get('completed', 0) - total_high_risk - total_medium_risk} | 预测无重大告警风险 |",
            f"",
        ])
        
        # 高风险服务器列表
        if high_risk_servers:
            report_lines.extend([
                f"### 高风险服务器 ({len(high_risk_servers)}台)",
                f"",
                f"| 服务器ID | 服务器名称 | 风险评分 | 预测严重告警 | 预测警告告警 |",
                f"|----------|------------|----------|--------------|--------------|",
            ])
            
            for s in high_risk_servers:
                report_lines.append(
                    f"| {s['server_id']} | {s['server_name'] or '-'} | {s['risk_score']} | "
                    f"{s['critical_alerts_count']} | {s['warning_alerts_count']} |"
                )
            
            # 添加高风险服务器的详细预测
            report_lines.append(f"")
            report_lines.append(f"#### 高风险服务器详细预测")
            report_lines.append(f"")
            
            for s in high_risk_servers[:5]:  # 只显示前5个的详细信息
                report_lines.append(f"**{s['server_name'] or s['server_id']}**")
                report_lines.append(f"")
                report_lines.append(f"- 风险评分: {s['risk_score']}")
                report_lines.append(f"- 建议: {s['recommendation']}")
                
                if s['predicted_alerts']:
                    report_lines.append(f"- 预测告警:")
                    for alert in s['predicted_alerts']:
                        severity_icon = '🔴' if alert.get('severity') == 'critical' else '🟡'
                        report_lines.append(
                            f"  - {severity_icon} {alert.get('alertname')} "
                            f"(置信度: {alert.get('confidence', 0):.2%}, 来源: {', '.join(alert.get('sources', []))})"
                        )
                
                report_lines.append(f"")
        
        # 中风险服务器列表
        if medium_risk_servers:
            report_lines.extend([
                f"### 中风险服务器 ({len(medium_risk_servers)}台)",
                f"",
                f"| 服务器ID | 服务器名称 | 风险评分 | 预测警告告警 |",
                f"|----------|------------|----------|--------------|",
            ])
            
            for s in medium_risk_servers:
                report_lines.append(
                    f"| {s['server_id']} | {s['server_name'] or '-'} | {s['risk_score']} | "
                    f"{s['warning_alerts_count']} |"
                )
            
            report_lines.append(f"")
        
        # 预测告警类型统计
        if predicted_alerts_summary:
            report_lines.extend([
                f"### 预测告警类型分布",
                f"",
                f"| 告警名称 | 预测发生次数 | 严重告警 | 警告告警 | 影响服务器数 |",
                f"|----------|--------------|----------|----------|--------------|",
            ])
            
            # 按影响服务器数排序
            sorted_alerts = sorted(
                predicted_alerts_summary.items(),
                key=lambda x: len(x[1]['servers']),
                reverse=True
            )
            
            for alertname, stats in sorted_alerts:
                report_lines.append(
                    f"| {alertname} | {stats['count']} | {stats['critical_count']} | "
                    f"{stats['warning_count']} | {len(stats['servers'])} |"
                )
            
            report_lines.append(f"")
        
        report_content = '\n'.join(report_lines)
        
        # 保存到文件
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Report saved to: {output_file}")
        
        return report_content
    
    def close(self):
        """关闭所有组件"""
        if self.openstack_client:
            self.openstack_client.close()
        
        if self.alert_client:
            self.alert_client.close()
        
        if self.resource_monitor:
            self.resource_monitor.close()
        
        if self.db_manager:
            self.db_manager.close()
        
        logger.info("Cloud Inspection System closed")
    
    def __enter__(self):
        self.initialize()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def main():
    """主函数"""
    if not MODULES_AVAILABLE:
        logger.error("Required modules are not available. Please check imports.")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(
        description='OpenStack云资源池服务器巡检脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 执行完整巡检
  python cloud_inspection.py --run
  
  # 指定并发数执行
  python cloud_inspection.py --run --max-workers 50
  
  # 生成报告
  python cloud_inspection.py --run --report inspection_report.md
  
  # 仅获取服务器列表
  python cloud_inspection.py --list-servers
        '''
    )
    
    parser.add_argument('--run', action='store_true', help='执行巡检')
    parser.add_argument('--list-servers', action='store_true', help='列出所有服务器')
    parser.add_argument('--max-workers', type=int, default=None, help='最大并发数')
    parser.add_argument('--batch-size', type=int, default=100, help='每批处理的服务器数量')
    parser.add_argument('--batch-delay', type=int, default=2, help='批次间延迟(秒)')
    parser.add_argument('--report', type=str, default=None, help='生成报告并保存到指定文件')
    parser.add_argument('--server-id', type=str, default=None, help='仅巡检指定的服务器ID')
    parser.add_argument('--config', type=str, default=None, help='配置文件路径(暂未实现)')
    parser.add_argument('--verbose', '-v', action='store_true', help='详细输出')
    
    args = parser.parse_args()
    
    # 设置日志级别
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 创建配置
    config = InspectionConfig()
    
    # 创建巡检系统
    inspection_system = CloudInspectionSystem(config)
    
    try:
        if args.list_servers:
            # 仅列出服务器
            inspection_system.initialize()
            servers = inspection_system.get_all_servers_from_openstack()
            
            print(f"\n共发现 {len(servers)} 台服务器:")
            print("-" * 80)
            print(f"{'服务器ID':<40} {'服务器名称':<30} {'IP地址'}")
            print("-" * 80)
            
            for server in servers:
                ips = ', '.join(server.get('server_ips', []))[:40]
                print(f"{server['server_id']:<40} {server['server_name'] or '-':<30} {ips}")
            
            return
        
        elif args.run or args.server_id:
            # 执行巡检
            with inspection_system as system:
                if args.server_id:
                    # 仅巡检指定服务器
                    logger.info(f"Inspecting single server: {args.server_id}")
                    
                    # 先从OpenStack获取服务器信息
                    try:
                        openstack_client = system._get_openstack_client()
                        server = openstack_client.get_server_by_id(args.server_id)
                        
                        if server:
                            server_ips = openstack_client.get_server_ips(server)
                            result = system.inspect_single_server(
                                server_id=args.server_id,
                                server_name=server.name,
                                server_ips=server_ips
                            )
                        else:
                            result = system.inspect_single_server(
                                server_id=args.server_id
                            )
                        
                        # 输出结果
                        print(f"\n巡检结果:")
                        print(json.dumps(result, indent=2, ensure_ascii=False, default=str))
                        
                    except Exception as e:
                        logger.error(f"Failed to inspect server: {e}")
                        raise
                
                else:
                    # 执行完整巡检
                    logger.info("Starting full inspection...")
                    
                    results = system.run_inspection(
                        max_workers=args.max_workers,
                        batch_size=args.batch_size,
                        batch_delay=args.batch_delay
                    )
                    
                    # 输出摘要
                    summary = results.get('summary', {})
                    print(f"\n巡检完成!")
                    print(f"总服务器数: {summary.get('total', 0)}")
                    print(f"完成: {summary.get('completed', 0)}")
                    print(f"失败: {summary.get('failed', 0)}")
                    print(f"超时: {summary.get('timeout', 0)}")
                    print(f"总耗时: {summary.get('total_duration_seconds', 0):.2f} 秒")
                    print(f"平均每台耗时: {summary.get('average_duration_seconds', 0):.2f} 秒")
                    
                    # 生成报告
                    if args.report:
                        system.generate_report(results, args.report)
                    
                    return results
        
        else:
            # 显示帮助
            parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("Inspection interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Inspection failed: {e}")
        raise


if __name__ == '__main__':
    main()
