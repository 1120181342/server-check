import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import os

try:
    from kubernetes import client, config
    from kubernetes.client import CoreV1Api, AppsV1Api, CustomObjectsApi
    from kubernetes.client.rest import ApiException
    KUBERNETES_AVAILABLE = True
except ImportError:
    KUBERNETES_AVAILABLE = False

from inspection_config import InspectionConfig

logger = logging.getLogger(__name__)


class KubernetesClient:
    """Kubernetes API客户端，用于获取容器化部署信息"""
    
    def __init__(self, config: InspectionConfig):
        """初始化Kubernetes客户端
        
        Args:
            config: 配置对象
        """
        if not KUBERNETES_AVAILABLE:
            raise ImportError("Kubernetes client is not installed. Please install it with 'pip install kubernetes'")
        
        self.config = config
        self._core_api: Optional[CoreV1Api] = None
        self._apps_api: Optional[AppsV1Api] = None
        self._custom_api: Optional[CustomObjectsApi] = None
    
    def _load_config(self):
        """加载Kubernetes配置"""
        try:
            # 首先尝试从kubeconfig文件加载
            kubeconfig_path = os.path.expanduser(self.config.KUBECONFIG_PATH)
            if os.path.exists(kubeconfig_path):
                logger.info(f"Loading Kubernetes config from {kubeconfig_path}")
                config.load_kube_config(config_file=kubeconfig_path)
            else:
                # 尝试从集群内部加载（在Pod中运行时）
                logger.info("Loading Kubernetes config from cluster...")
                config.load_incluster_config()
            
            logger.info("Successfully configured Kubernetes client")
            
        except Exception as e:
            logger.error(f"Failed to load Kubernetes config: {str(e)}")
            raise
    
    def _get_core_api(self) -> CoreV1Api:
        """获取Core V1 API客户端
        
        Returns:
            CoreV1Api对象
        """
        if self._core_api is None:
            self._load_config()
            self._core_api = client.CoreV1Api()
        return self._core_api
    
    def _get_apps_api(self) -> AppsV1Api:
        """获取Apps V1 API客户端
        
        Returns:
            AppsV1Api对象
        """
        if self._apps_api is None:
            self._load_config()
            self._apps_api = client.AppsV1Api()
        return self._apps_api
    
    def _get_custom_api(self) -> CustomObjectsApi:
        """获取Custom Objects API客户端
        
        Returns:
            CustomObjectsApi对象
        """
        if self._custom_api is None:
            self._load_config()
            self._custom_api = client.CustomObjectsApi()
        return self._custom_api
    
    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """获取所有Kubernetes节点信息
        
        Returns:
            节点信息列表
        """
        core_api = self._get_core_api()
        logger.info("Fetching all Kubernetes nodes...")
        
        try:
            nodes = core_api.list_node()
            logger.info(f"Found {len(nodes.items)} Kubernetes nodes")
            
            node_list = []
            for node in nodes.items:
                node_info = self._parse_node_info(node)
                node_list.append(node_info)
            
            return node_list
            
        except ApiException as e:
            logger.error(f"Kubernetes API error when fetching nodes: {e.status} - {e.reason}")
            raise
        except Exception as e:
            logger.error(f"Failed to fetch Kubernetes nodes: {str(e)}")
            raise
    
    def get_node_by_name(self, node_name: str) -> Optional[Dict[str, Any]]:
        """根据名称获取Kubernetes节点
        
        Args:
            node_name: 节点名称
            
        Returns:
            节点信息，如果不存在则返回None
        """
        core_api = self._get_core_api()
        
        try:
            node = core_api.read_node(node_name)
            return self._parse_node_info(node)
        except ApiException as e:
            if e.status == 404:
                logger.warning(f"Kubernetes node {node_name} not found")
                return None
            else:
                logger.error(f"Kubernetes API error: {e.status} - {e.reason}")
                raise
        except Exception as e:
            logger.error(f"Failed to get node {node_name}: {str(e)}")
            raise
    
    def get_node_pods(self, node_name: str) -> List[Dict[str, Any]]:
        """获取运行在特定节点上的所有Pod
        
        Args:
            node_name: 节点名称
            
        Returns:
            Pod信息列表
        """
        core_api = self._get_core_api()
        
        try:
            field_selector = f"spec.nodeName={node_name}"
            pods = core_api.list_pod_for_all_namespaces(field_selector=field_selector)
            
            pod_list = []
            for pod in pods.items:
                pod_info = self._parse_pod_info(pod)
                pod_list.append(pod_info)
            
            return pod_list
            
        except Exception as e:
            logger.error(f"Failed to get pods for node {node_name}: {str(e)}")
            return []
    
    def get_node_metrics(self, node_name: str) -> Optional[Dict[str, Any]]:
        """获取节点的资源使用指标（需要metrics-server）
        
        Args:
            node_name: 节点名称
            
        Returns:
            节点指标信息，如果无法获取则返回None
        """
        custom_api = self._get_custom_api()
        
        try:
            metrics = custom_api.list_cluster_custom_object(
                group="metrics.k8s.io",
                version="v1beta1",
                plural="nodes",
                field_selector=f"metadata.name={node_name}"
            )
            
            if metrics.get('items') and len(metrics['items']) > 0:
                node_metric = metrics['items'][0]
                return self._parse_node_metrics(node_metric)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to get metrics for node {node_name}: {str(e)}")
            return None
    
    def get_deployments(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """获取Deployment信息
        
        Args:
            namespace: 命名空间，默认default
            
        Returns:
            Deployment信息列表
        """
        apps_api = self._get_apps_api()
        
        try:
            deployments = apps_api.list_namespaced_deployment(namespace=namespace)
            
            deployment_list = []
            for deploy in deployments.items:
                deploy_info = {
                    'name': deploy.metadata.name,
                    'namespace': deploy.metadata.namespace,
                    'replicas': deploy.spec.replicas,
                    'ready_replicas': deploy.status.ready_replicas or 0,
                    'updated_replicas': deploy.status.updated_replicas or 0,
                    'available_replicas': deploy.status.available_replicas or 0,
                    'creation_timestamp': deploy.metadata.creation_timestamp,
                    'labels': deploy.metadata.labels or {},
                    'annotations': deploy.metadata.annotations or {}
                }
                deployment_list.append(deploy_info)
            
            return deployment_list
            
        except Exception as e:
            logger.error(f"Failed to get deployments: {str(e)}")
            return []
    
    def get_all_pods(self, namespace: str = "default") -> List[Dict[str, Any]]:
        """获取所有Pod信息
        
        Args:
            namespace: 命名空间，默认default
            
        Returns:
            Pod信息列表
        """
        core_api = self._get_core_api()
        
        try:
            if namespace == "all":
                pods = core_api.list_pod_for_all_namespaces()
            else:
                pods = core_api.list_namespaced_pod(namespace=namespace)
            
            pod_list = []
            for pod in pods.items:
                pod_info = self._parse_pod_info(pod)
                pod_list.append(pod_info)
            
            return pod_list
            
        except Exception as e:
            logger.error(f"Failed to get pods: {str(e)}")
            return []
    
    def _parse_node_info(self, node) -> Dict[str, Any]:
        """解析Kubernetes节点信息
        
        Args:
            node: Kubernetes节点对象
            
        Returns:
            包含节点信息的字典
        """
        # 解析节点状态
        status = "Unknown"
        node_status = node.status
        if node_status and node_status.conditions:
            for condition in node_status.conditions:
                if condition.type == "Ready":
                    if condition.status == "True":
                        status = "Ready"
                    elif condition.status == "False":
                        status = "NotReady"
                    else:
                        status = "Unknown"
                    break
        
        # 解析节点容量和可分配资源
        capacity = {}
        allocatable = {}
        if node_status:
            if node_status.capacity:
                capacity = {
                    'cpu': str(node_status.capacity.get('cpu', '0')),
                    'memory': str(node_status.capacity.get('memory', '0')),
                    'pods': str(node_status.capacity.get('pods', '0'))
                }
            if node_status.allocatable:
                allocatable = {
                    'cpu': str(node_status.allocatable.get('cpu', '0')),
                    'memory': str(node_status.allocatable.get('memory', '0')),
                    'pods': str(node_status.allocatable.get('pods', '0'))
                }
        
        # 解析节点信息
        node_info = {
            'name': node.metadata.name,
            'uid': node.metadata.uid,
            'status': status,
            'creation_timestamp': node.metadata.creation_timestamp,
            
            # 资源信息
            'capacity': capacity,
            'allocatable': allocatable,
            
            # 标签和注解
            'labels': node.metadata.labels or {},
            'annotations': node.metadata.annotations or {},
            
            # 节点地址
            'addresses': [],
            
            # 节点信息
            'node_info': {}
        }
        
        # 解析节点地址
        if node_status and node_status.addresses:
            for addr in node_status.addresses:
                node_info['addresses'].append({
                    'type': addr.type,
                    'address': addr.address
                })
        
        # 解析节点详细信息
        if node_status and node_status.node_info:
            node_info['node_info'] = {
                'architecture': node_status.node_info.architecture,
                'container_runtime_version': node_status.node_info.container_runtime_version,
                'kernel_version': node_status.node_info.kernel_version,
                'kube_proxy_version': node_status.node_info.kube_proxy_version,
                'kubelet_version': node_status.node_info.kubelet_version,
                'operating_system': node_status.node_info.operating_system,
                'os_image': node_status.node_info.os_image
            }
        
        # 获取污点信息
        if node.spec and node.spec.taints:
            node_info['taints'] = [
                {
                    'key': taint.key,
                    'value': taint.value,
                    'effect': taint.effect
                }
                for taint in node.spec.taints
            ]
        else:
            node_info['taints'] = []
        
        return node_info
    
    def _parse_pod_info(self, pod) -> Dict[str, Any]:
        """解析Kubernetes Pod信息
        
        Args:
            pod: Kubernetes Pod对象
            
        Returns:
            包含Pod信息的字典
        """
        pod_info = {
            'name': pod.metadata.name,
            'namespace': pod.metadata.namespace,
            'uid': pod.metadata.uid,
            'status': pod.status.phase if pod.status else 'Unknown',
            'node_name': pod.spec.node_name if pod.spec else None,
            'creation_timestamp': pod.metadata.creation_timestamp,
            
            # 标签和注解
            'labels': pod.metadata.labels or {},
            'annotations': pod.metadata.annotations or {},
            
            # 容器信息
            'containers': [],
            'init_containers': [],
            
            # 资源请求和限制
            'resources': {
                'requests': {},
                'limits': {}
            }
        }
        
        # 解析容器信息
        if pod.spec:
            # 主容器
            if pod.spec.containers:
                for container in pod.spec.containers:
                    container_info = {
                        'name': container.name,
                        'image': container.image,
                        'image_pull_policy': container.image_pull_policy
                    }
                    
                    # 资源请求和限制
                    if container.resources:
                        container_info['resources'] = {
                            'requests': {},
                            'limits': {}
                        }
                        if container.resources.requests:
                            container_info['resources']['requests'] = {
                                'cpu': str(container.resources.requests.get('cpu', '0')),
                                'memory': str(container.resources.requests.get('memory', '0'))
                            }
                        if container.resources.limits:
                            container_info['resources']['limits'] = {
                                'cpu': str(container.resources.limits.get('cpu', '0')),
                                'memory': str(container.resources.limits.get('memory', '0'))
                            }
                    
                    pod_info['containers'].append(container_info)
            
            # Init容器
            if pod.spec.init_containers:
                for container in pod.spec.init_containers:
                    pod_info['init_containers'].append({
                        'name': container.name,
                        'image': container.image
                    })
        
        # 解析Pod状态
        if pod.status:
            pod_info['host_ip'] = pod.status.host_ip
            pod_info['pod_ip'] = pod.status.pod_ip
            pod_info['start_time'] = pod.status.start_time
            
            # 容器状态
            if pod.status.container_statuses:
                pod_info['container_statuses'] = []
                for cs in pod.status.container_statuses:
                    pod_info['container_statuses'].append({
                        'name': cs.name,
                        'ready': cs.ready,
                        'restart_count': cs.restart_count,
                        'state': str(cs.state)
                    })
        
        return pod_info
    
    def _parse_node_metrics(self, metrics: Dict) -> Dict[str, Any]:
        """解析节点指标数据
        
        Args:
            metrics: 指标数据字典
            
        Returns:
            解析后的指标信息
        """
        usage = metrics.get('usage', {})
        
        return {
            'name': metrics.get('metadata', {}).get('name'),
            'timestamp': metrics.get('timestamp'),
            'window': metrics.get('window'),
            'usage': {
                'cpu': usage.get('cpu', '0'),
                'memory': usage.get('memory', '0')
            }
        }
    
    def close(self):
        """清理资源"""
        self._core_api = None
        self._apps_api = None
        self._custom_api = None
        logger.info("Kubernetes client resources cleared")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
