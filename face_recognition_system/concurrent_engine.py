import logging
from typing import List, Dict, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class InspectionTask:
    """巡检任务数据类"""
    task_id: str
    server_id: str
    server_name: Optional[str] = None
    server_ips: List[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    priority: int = 0
    retries: int = 0
    max_retries: int = 3
    timeout_seconds: int = 120
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


class ConcurrentInspectionEngine:
    """并发巡检引擎，支持大批量主机的并发巡检"""
    
    def __init__(self,
                 max_workers: int = 100,
                 task_timeout_seconds: int = 120,
                 max_retries: int = 3,
                 retry_delay_seconds: int = 5,
                 progress_callback: Optional[Callable] = None):
        """初始化并发巡检引擎
        
        Args:
            max_workers: 最大工作线程数
            task_timeout_seconds: 单任务超时时间（秒）
            max_retries: 最大重试次数
            retry_delay_seconds: 重试延迟（秒）
            progress_callback: 进度回调函数
        """
        self.max_workers = max_workers
        self.task_timeout_seconds = task_timeout_seconds
        self.max_retries = max_retries
        self.retry_delay_seconds = retry_delay_seconds
        self.progress_callback = progress_callback
        
        # 任务队列
        self.task_queue: queue.Queue = queue.Queue()
        self.tasks: Dict[str, InspectionTask] = {}
        self.task_lock = threading.Lock()
        
        # 统计信息
        self._stats = {
            'total_tasks': 0,
            'completed_tasks': 0,
            'failed_tasks': 0,
            'timeout_tasks': 0,
            'retried_tasks': 0
        }
        self._stats_lock = threading.Lock()
        
        # 控制标志
        self._running = False
        self._shutdown = False
        
        logger.info(f"ConcurrentInspectionEngine initialized with max_workers={max_workers}, "
                   f"task_timeout={task_timeout_seconds}s, max_retries={max_retries}")
    
    def create_task(self,
                   server_id: str,
                   server_name: str = None,
                   server_ips: List[str] = None,
                   priority: int = 0,
                   timeout_seconds: int = None) -> str:
        """创建巡检任务
        
        Args:
            server_id: 服务器ID
            server_name: 服务器名称
            server_ips: 服务器IP列表
            priority: 任务优先级（越高越先执行）
            timeout_seconds: 超时时间，默认使用全局配置
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        
        task = InspectionTask(
            task_id=task_id,
            server_id=server_id,
            server_name=server_name,
            server_ips=server_ips or [],
            priority=priority,
            max_retries=self.max_retries,
            timeout_seconds=timeout_seconds or self.task_timeout_seconds
        )
        
        with self.task_lock:
            self.tasks[task_id] = task
        
        # 放入队列（优先级通过负数实现，因为queue.PriorityQueue是最小堆）
        # 这里使用简单的FIFO队列，如果需要优先级可以改用PriorityQueue
        self.task_queue.put(task)
        
        logger.debug(f"Created task {task_id} for server {server_id}")
        
        return task_id
    
    def create_tasks_batch(self,
                          servers: List[Dict[str, Any]],
                          priority: int = 0) -> List[str]:
        """批量创建任务
        
        Args:
            servers: 服务器列表，每个元素包含 server_id, server_name, server_ips
            priority: 任务优先级
            
        Returns:
            任务ID列表
        """
        task_ids = []
        
        for server in servers:
            task_id = self.create_task(
                server_id=server.get('server_id'),
                server_name=server.get('server_name'),
                server_ips=server.get('server_ips', []),
                priority=priority
            )
            task_ids.append(task_id)
        
        logger.info(f"Created {len(task_ids)} tasks in batch")
        
        return task_ids
    
    def get_task(self, task_id: str) -> Optional[InspectionTask]:
        """获取任务信息
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象，如果不存在则返回None
        """
        with self.task_lock:
            return self.tasks.get(task_id)
    
    def get_all_tasks(self) -> List[InspectionTask]:
        """获取所有任务
        
        Returns:
            任务列表
        """
        with self.task_lock:
            return list(self.tasks.values())
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        with self._stats_lock:
            stats = self._stats.copy()
        
        # 添加当前状态的任务统计
        status_counts = {}
        with self.task_lock:
            for task in self.tasks.values():
                status = task.status.value
                if status not in status_counts:
                    status_counts[status] = 0
                status_counts[status] += 1
        
        stats['status_counts'] = status_counts
        
        # 计算进度
        total = stats['total_tasks']
        if total > 0:
            stats['progress_percent'] = round(
                (stats['completed_tasks'] + stats['failed_tasks'] + stats['timeout_tasks']) / total * 100,
                2
            )
        else:
            stats['progress_percent'] = 0.0
        
        return stats
    
    def _execute_task(self,
                     task: InspectionTask,
                     inspection_func: Callable) -> InspectionTask:
        """执行单个任务
        
        Args:
            task: 任务对象
            inspection_func: 巡检函数
            
        Returns:
            更新后的任务对象
        """
        task.started_at = datetime.now()
        task.status = TaskStatus.RUNNING
        
        logger.debug(f"Starting task {task.task_id} for server {task.server_id}")
        
        try:
            # 执行巡检函数
            result = inspection_func(
                server_id=task.server_id,
                server_name=task.server_name,
                server_ips=task.server_ips
            )
            
            task.result = result
            task.status = TaskStatus.COMPLETED
            
            with self._stats_lock:
                self._stats['completed_tasks'] += 1
            
            logger.debug(f"Task {task.task_id} completed successfully")
            
        except TimeoutError as e:
            task.error = f"Task timeout: {str(e)}"
            task.status = TaskStatus.TIMEOUT
            
            with self._stats_lock:
                self._stats['timeout_tasks'] += 1
            
            logger.warning(f"Task {task.task_id} timeout: {str(e)}")
            
        except Exception as e:
            task.error = f"Task failed: {str(e)}"
            
            # 检查是否可以重试
            if task.retries < task.max_retries:
                task.retries += 1
                with self._stats_lock:
                    self._stats['retried_tasks'] += 1
                logger.warning(f"Task {task.task_id} failed, will retry ({task.retries}/{task.max_retries}): {str(e)}")
                # 重新入队
                task.status = TaskStatus.PENDING
                self.task_queue.put(task)
                return task
            else:
                task.status = TaskStatus.FAILED
                with self._stats_lock:
                    self._stats['failed_tasks'] += 1
                logger.error(f"Task {task.task_id} failed after {task.max_retries} retries: {str(e)}")
        
        finally:
            task.completed_at = datetime.now()
            if task.started_at and task.completed_at:
                task.duration_seconds = (task.completed_at - task.started_at).total_seconds()
        
        return task
    
    def run(self,
           inspection_func: Callable,
           server_batch: List[Dict[str, Any]] = None,
           batch_size: int = 100,
           batch_delay_seconds: int = 2) -> Dict[str, Any]:
        """运行巡检引擎
        
        Args:
            inspection_func: 巡检函数，接收 server_id, server_name, server_ips 参数
            server_batch: 服务器列表，如果为None则使用已创建的任务
            batch_size: 每批处理的服务器数量
            batch_delay_seconds: 批次之间的延迟（秒）
            
        Returns:
            执行结果汇总
        """
        if server_batch:
            # 分批创建任务
            total_servers = len(server_batch)
            logger.info(f"Starting inspection for {total_servers} servers, batch size={batch_size}")
            
            for i in range(0, total_servers, batch_size):
                batch = server_batch[i:i + batch_size]
                self.create_tasks_batch(batch)
                
                # 如果不是第一批，等待一段时间
                if i > 0 and batch_delay_seconds > 0:
                    time.sleep(batch_delay_seconds)
        
        with self._stats_lock:
            self._stats['total_tasks'] = len(self.tasks)
        
        logger.info(f"Starting execution of {self._stats['total_tasks']} tasks with {self.max_workers} workers")
        
        self._running = True
        
        try:
            # 使用线程池执行任务
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # 提交所有任务
                future_to_task = {}
                
                while not self.task_queue.empty() and not self._shutdown:
                    try:
                        task = self.task_queue.get(timeout=1)
                        
                        # 跳过已取消的任务
                        if task.status == TaskStatus.CANCELLED:
                            continue
                        
                        # 提交任务到线程池
                        future = executor.submit(
                            self._execute_task,
                            task,
                            inspection_func
                        )
                        future_to_task[future] = task
                        
                    except queue.Empty:
                        continue
                
                # 等待所有任务完成
                for future in as_completed(future_to_task):
                    task = future_to_task[future]
                    
                    try:
                        # 获取结果（已经在_execute_task中处理了异常）
                        completed_task = future.result(timeout=task.timeout_seconds + 10)
                        
                        # 更新任务状态
                        with self.task_lock:
                            self.tasks[completed_task.task_id] = completed_task
                        
                        # 调用进度回调
                        if self.progress_callback:
                            stats = self.get_statistics()
                            self.progress_callback(stats)
                            
                    except TimeoutError:
                        # 任务超时
                        with self.task_lock:
                            self.tasks[task.task_id].status = TaskStatus.TIMEOUT
                            self.tasks[task.task_id].error = "Future timeout"
                        with self._stats_lock:
                            self._stats['timeout_tasks'] += 1
                        logger.error(f"Future timeout for task {task.task_id}")
                    
                    except Exception as e:
                        logger.error(f"Error processing task {task.task_id}: {str(e)}")
        
        finally:
            self._running = False
        
        # 生成结果汇总
        results = self._generate_results_summary()
        
        logger.info(f"Inspection completed: {results['summary']['completed']} completed, "
                   f"{results['summary']['failed']} failed, {results['summary']['timeout']} timeout")
        
        return results
    
    def _generate_results_summary(self) -> Dict[str, Any]:
        """生成结果汇总
        
        Returns:
            结果汇总字典
        """
        completed_tasks = []
        failed_tasks = []
        timeout_tasks = []
        
        with self.task_lock:
            for task in self.tasks.values():
                task_dict = {
                    'task_id': task.task_id,
                    'server_id': task.server_id,
                    'server_name': task.server_name,
                    'status': task.status.value,
                    'duration_seconds': task.duration_seconds,
                    'retries': task.retries,
                    'error': task.error
                }
                
                if task.status == TaskStatus.COMPLETED:
                    task_dict['result'] = task.result
                    completed_tasks.append(task_dict)
                elif task.status == TaskStatus.FAILED:
                    failed_tasks.append(task_dict)
                elif task.status == TaskStatus.TIMEOUT:
                    timeout_tasks.append(task_dict)
        
        # 计算总体统计
        total_duration = sum(
            t.duration_seconds for t in self.tasks.values() 
            if t.duration_seconds is not None
        )
        avg_duration = total_duration / len(completed_tasks) if completed_tasks else 0
        
        return {
            'timestamp': datetime.now(),
            'summary': {
                'total': len(self.tasks),
                'completed': len(completed_tasks),
                'failed': len(failed_tasks),
                'timeout': len(timeout_tasks),
                'total_duration_seconds': round(total_duration, 2),
                'average_duration_seconds': round(avg_duration, 2)
            },
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'timeout_tasks': timeout_tasks,
            'statistics': self.get_statistics()
        }
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            是否成功取消
        """
        with self.task_lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
                    logger.info(f"Task {task_id} cancelled")
                    return True
        
        return False
    
    def cancel_all_tasks(self):
        """取消所有待处理任务"""
        with self.task_lock:
            for task in self.tasks.values():
                if task.status == TaskStatus.PENDING:
                    task.status = TaskStatus.CANCELLED
        
        logger.info("All pending tasks cancelled")
    
    def shutdown(self, wait: bool = True):
        """关闭引擎
        
        Args:
            wait: 是否等待当前任务完成
        """
        logger.info("Shutting down inspection engine...")
        self._shutdown = True
        
        if wait:
            # 等待当前运行的任务完成
            while self._running:
                time.sleep(0.5)
        
        logger.info("Inspection engine shutdown complete")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.shutdown(wait=True)


class BatchProgressTracker:
    """批量进度跟踪器"""
    
    def __init__(self, 
                 total_batches: int,
                 log_interval: int = 1):
        """初始化进度跟踪器
        
        Args:
            total_batches: 总批次数
            log_interval: 日志间隔（批次）
        """
        self.total_batches = total_batches
        self.log_interval = log_interval
        self.current_batch = 0
        self.start_time = datetime.now()
        
        # 每个批次的统计
        self.batch_stats = []
        
        logger.info(f"BatchProgressTracker initialized for {total_batches} batches")
    
    def start_batch(self, batch_number: int, batch_size: int):
        """记录批次开始
        
        Args:
            batch_number: 批次号
            batch_size: 批次大小
        """
        self.current_batch = batch_number
        
        self.batch_stats.append({
            'batch_number': batch_number,
            'batch_size': batch_size,
            'start_time': datetime.now(),
            'completed': 0,
            'failed': 0
        })
        
        if batch_number % self.log_interval == 0 or batch_number == self.total_batches:
            elapsed = (datetime.now() - self.start_time).total_seconds()
            progress = batch_number / self.total_batches * 100
            
            logger.info(
                f"Starting batch {batch_number}/{self.total_batches} "
                f"({batch_size} servers), progress: {progress:.1f}%, "
                f"elapsed: {elapsed:.1f}s"
            )
    
    def update_batch_progress(self, stats: Dict[str, Any]):
        """更新批次进度
        
        Args:
            stats: 统计信息
        """
        if self.batch_stats:
            current = self.batch_stats[-1]
            current['completed'] = stats.get('completed_tasks', 0)
            current['failed'] = stats.get('failed_tasks', 0) + stats.get('timeout_tasks', 0)
    
    def end_batch(self):
        """记录批次结束"""
        if self.batch_stats:
            current = self.batch_stats[-1]
            current['end_time'] = datetime.now()
            current['duration'] = (current['end_time'] - current['start_time']).total_seconds()
            
            # 计算平均时间
            if current['completed'] + current['failed'] > 0:
                current['avg_time_per_server'] = current['duration'] / (current['completed'] + current['failed'])
            else:
                current['avg_time_per_server'] = 0
            
            logger.info(
                f"Batch {current['batch_number']} completed: "
                f"{current['completed']} completed, {current['failed']} failed, "
                f"duration: {current['duration']:.2f}s, "
                f"avg: {current['avg_time_per_server']:.2f}s/server"
            )
    
    def get_overall_stats(self) -> Dict[str, Any]:
        """获取整体统计
        
        Returns:
            整体统计信息
        """
        total_completed = sum(b['completed'] for b in self.batch_stats)
        total_failed = sum(b['failed'] for b in self.batch_stats)
        total_duration = (datetime.now() - self.start_time).total_seconds()
        
        # 预计剩余时间
        if self.current_batch > 0:
            avg_batch_duration = total_duration / self.current_batch
            remaining_batches = self.total_batches - self.current_batch
            estimated_remaining = avg_batch_duration * remaining_batches
        else:
            estimated_remaining = None
        
        return {
            'total_batches': self.total_batches,
            'current_batch': self.current_batch,
            'total_completed': total_completed,
            'total_failed': total_failed,
            'total_duration_seconds': round(total_duration, 2),
            'estimated_remaining_seconds': round(estimated_remaining, 2) if estimated_remaining else None,
            'progress_percent': round(self.current_batch / self.total_batches * 100, 2) if self.total_batches > 0 else 0.0
        }
