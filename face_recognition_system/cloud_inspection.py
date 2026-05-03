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
    from predictor import TimeSeriesPredictor
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
                    
                    # 保存整体预测
                    if 'overall_prediction' in prediction_result:
                        overall = prediction_result['overall_prediction']
                        overall['server_id'] = server_id
                        overall['metric_name'] = 'overall'
                        self.db_manager.save_prediction_result(overall)
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
        
        Args:
            server_id: 服务器ID
            
        Returns:
            预测结果字典
        """
        if not self.db_manager:
            logger.warning("No database manager, skipping prediction")
            return {'error': 'No database available'}
        
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
        
        # 执行整体预测
        if history_metrics:
            # 定义阈值
            thresholds = {
                'cpu_usage_percent': {'warning': 70.0, 'critical': 90.0},
                'memory_usage_percent': {'warning': 75.0, 'critical': 90.0},
                'disk_usage_percent': {'warning': 80.0, 'critical': 90.0}
            }
            
            overall_prediction = self.predictor.predict_host_status(
                server_id=server_id,
                history_metrics=history_metrics,
                thresholds=thresholds
            )
            
            return {
                'metric_predictions': metric_predictions,
                'overall_prediction': overall_prediction,
                'history_data_points': {k: len(v) for k, v in history_metrics.items()}
            }
        else:
            return {
                'error': 'Insufficient history data for prediction',
                'metric_predictions': {},
                'overall_prediction': None
            }
    
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
        overall_prediction = prediction.get('overall_prediction', {})
        prediction_status = overall_prediction.get('overall_status', 'unknown')
        
        if prediction_status == 'critical':
            statuses.append('critical')
        elif prediction_status == 'warning':
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
