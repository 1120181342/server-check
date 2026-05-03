import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
import math

logger = logging.getLogger(__name__)


class TimeSeriesPredictor:
    """时间序列预测器，使用简单时间序列预测算法"""
    
    # 预测置信度阈值
    HIGH_CONFIDENCE_THRESHOLD = 0.8
    MEDIUM_CONFIDENCE_THRESHOLD = 0.6
    
    def __init__(self, 
                 history_days: int = 7,
                 forecast_days: int = 3,
                 window_size: int = 5):
        """初始化预测器
        
        Args:
            history_days: 使用的历史数据天数
            forecast_days: 预测的未来天数
            window_size: 移动平均窗口大小
        """
        self.history_days = history_days
        self.forecast_days = forecast_days
        self.window_size = window_size
        
        logger.info(f"TimeSeriesPredictor initialized: history_days={history_days}, "
                   f"forecast_days={forecast_days}, window_size={window_size}")
    
    def simple_moving_average(self, data: List[float]) -> List[float]:
        """计算简单移动平均 (SMA)
        
        Args:
            data: 原始数据列表
            
        Returns:
            移动平均结果列表
        """
        if len(data) < self.window_size:
            return []
        
        result = []
        window = deque(maxlen=self.window_size)
        
        for i, value in enumerate(data):
            window.append(value)
            if i >= self.window_size - 1:
                result.append(sum(window) / self.window_size)
        
        return result
    
    def exponential_moving_average(self, data: List[float], 
                                    alpha: float = 0.3) -> List[float]:
        """计算指数移动平均 (EMA)
        
        Args:
            data: 原始数据列表
            alpha: 平滑因子 (0 < alpha < 1)
            
        Returns:
            指数移动平均结果列表
        """
        if not data:
            return []
        
        result = [data[0]]
        
        for i in range(1, len(data)):
            ema = alpha * data[i] + (1 - alpha) * result[i-1]
            result.append(ema)
        
        return result
    
    def calculate_trend(self, data: List[float]) -> Tuple[float, float]:
        """计算数据趋势（斜率和截距）
        
        使用最小二乘法计算线性回归
        y = mx + b，其中m是斜率，b是截距
        
        Args:
            data: 数据列表
            
        Returns:
            (斜率, 截距) 元组
        """
        if len(data) < 2:
            return (0.0, data[0] if data else 0.0)
        
        n = len(data)
        x = list(range(n))
        
        sum_x = sum(x)
        sum_y = sum(data)
        sum_xy = sum(xi * yi for xi, yi in zip(x, data))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        denominator = n * sum_x2 - sum_x ** 2
        
        if denominator == 0:
            return (0.0, sum_y / n)
        
        slope = (n * sum_xy - sum_x * sum_y) / denominator
        intercept = (sum_y - slope * sum_x) / n
        
        return (slope, intercept)
    
    def predict_using_trend(self, 
                            history_data: List[float], 
                            steps: int = None) -> Dict[str, Any]:
        """使用趋势进行预测
        
        Args:
            history_data: 历史数据列表
            steps: 预测步数，默认为forecast_days
            
        Returns:
            包含预测结果的字典
        """
        if steps is None:
            steps = self.forecast_days
        
        if len(history_data) < 2:
            logger.warning("Insufficient data for trend prediction")
            return {
                'predicted_values': [],
                'trend': 'unknown',
                'confidence': 0.0,
                'method': 'trend'
            }
        
        # 计算趋势
        slope, intercept = self.calculate_trend(history_data)
        
        # 确定趋势方向
        if abs(slope) < 0.001:
            trend = 'stable'
        elif slope > 0:
            trend = 'increasing'
        else:
            trend = 'decreasing'
        
        # 生成预测值
        predictions = []
        n = len(history_data)
        
        for i in range(1, steps + 1):
            predicted_value = slope * (n + i - 1) + intercept
            # 确保预测值不会为负数
            predicted_value = max(0, predicted_value)
            predictions.append(predicted_value)
        
        # 计算置信度（基于数据的方差）
        variance = self._calculate_variance(history_data)
        mean_value = sum(history_data) / len(history_data) if history_data else 0
        
        if mean_value == 0:
            confidence = 0.5
        else:
            normalized_variance = variance / (mean_value ** 2) if mean_value != 0 else 1.0
            confidence = max(0.3, min(0.95, 1.0 - normalized_variance))
        
        return {
            'predicted_values': predictions,
            'trend': trend,
            'slope': slope,
            'intercept': intercept,
            'confidence': confidence,
            'method': 'trend',
            'variance': variance
        }
    
    def predict_using_ema(self, 
                               history_data: List[float],
                               steps: int = None,
                               alpha: float = 0.3) -> Dict[str, Any]:
        """使用指数移动平均进行预测
        
        Args:
            history_data: 历史数据列表
            steps: 预测步数
            alpha: 平滑因子
            
        Returns:
            包含预测结果的字典
        """
        if steps is None:
            steps = self.forecast_days
        
        if not history_data:
            return {
                'predicted_values': [],
                'trend': 'unknown',
                'confidence': 0.0,
                'method': 'ema'
            }
        
        # 计算EMA
        ema_values = self.exponential_moving_average(history_data, alpha)
        
        # 使用最后的EMA值作为基准进行预测
        # 对于简单的EMA预测，我们假设未来的值将保持在最后的EMA值附近
        # 或者可以结合趋势信息
        
        if len(ema_values) >= 2:
            # 计算EMA的趋势
            ema_slope, _ = self.calculate_trend(ema_values[-self.window_size:])
            
            # 生成预测值
            predictions = []
            last_ema = ema_values[-1]
            
            for i in range(1, steps + 1):
                # 结合趋势和最后的EMA
                predicted_value = last_ema + ema_slope * i
                predicted_value = max(0, predicted_value)
                predictions.append(predicted_value)
            
            # 确定趋势
            if abs(ema_slope) < 0.001:
                trend = 'stable'
            elif ema_slope > 0:
                trend = 'increasing'
            else:
                trend = 'decreasing'
            
            variance = self._calculate_variance(history_data)
            mean_value = sum(history_data) / len(history_data)
            normalized_variance = variance / (mean_value ** 2) if mean_value != 0 else 1.0
            confidence = max(0.3, min(0.95, 1.0 - normalized_variance * 0.5))
            
            return {
                'predicted_values': predictions,
                'trend': trend,
                'ema_slope': ema_slope,
                'last_ema': last_ema,
                'confidence': confidence,
                'method': 'ema',
                'ema_values': ema_values
            }
        
        # 如果数据不足，使用简单预测
        last_value = history_data[-1]
        predictions = [last_value] * steps
        
        return {
            'predicted_values': predictions,
            'trend': 'stable',
            'confidence': 0.5,
            'method': 'simple',
            'last_value': last_value
        }
    
    def predict_combined(self, 
                         history_data: List[float],
                         steps: int = None) -> Dict[str, Any]:
        """组合多种方法进行预测
        
        结合趋势预测和EMA预测，给出综合预测
        
        Args:
            history_data: 历史数据列表
            steps: 预测步数
            
        Returns:
            包含综合预测结果的字典
        """
        if steps is None:
            steps = self.forecast_days
        
        if len(history_data) < 3:
            # 数据不足，返回简单预测
            return self.predict_using_ema(history_data, steps)
        
        # 获取两种方法的预测
        trend_prediction = self.predict_using_trend(history_data, steps)
        ema_prediction = self.predict_using_ema(history_data, steps)
        
        # 计算加权平均
        # 根据置信度分配权重
        trend_weight = trend_prediction.get('confidence', 0.5)
        ema_weight = ema_prediction.get('confidence', 0.5)
        
        total_weight = trend_weight + ema_weight
        if total_weight == 0:
            total_weight = 1.0
            trend_weight = 0.5
            ema_weight = 0.5
        
        # 合并预测值
        trend_values = trend_prediction.get('predicted_values', [])
        ema_values = ema_prediction.get('predicted_values', [])
        
        combined_predictions = []
        for i in range(steps):
            t_val = trend_values[i] if i < len(trend_values) else 0
            e_val = ema_values[i] if i < len(ema_values) else 0
            
            combined = (t_val * trend_weight + e_val * ema_weight) / total_weight
            combined_predictions.append(combined)
        
        # 确定综合趋势
        trend_trend = trend_prediction.get('trend', 'unknown')
        ema_trend = ema_prediction.get('trend', 'unknown')
        
        if trend_trend == ema_trend:
            combined_trend = trend_trend
        elif trend_trend == 'stable' or ema_trend == 'stable':
            # 如果其中一个是稳定，取另一个
            combined_trend = ema_trend if trend_trend == 'stable' else trend_trend
        else:
            # 趋势不一致，根据置信度选择
            combined_trend = trend_trend if trend_weight >= ema_weight else ema_trend
        
        # 计算综合置信度
        combined_confidence = (trend_weight * trend_prediction.get('confidence', 0) + 
                               ema_weight * ema_prediction.get('confidence', 0)) / total_weight
        
        return {
            'predicted_values': combined_predictions,
            'trend': combined_trend,
            'confidence': combined_confidence,
            'method': 'combined',
            'trend_prediction': trend_prediction,
            'ema_prediction': ema_prediction,
            'weights': {
                'trend_weight': trend_weight / total_weight,
                'ema_weight': ema_weight / total_weight
            }
        }
    
    def predict_resource_usage(self,
                           history_data: List[Dict[str, Any]],
                           metric_name: str = 'usage',
                           steps: int = None) -> Dict[str, Any]:
        """预测资源使用情况
        
        Args:
            history_data: 历史数据列表，每个元素包含 'timestamp' 和 'value'
            metric_name: 指标名称
            steps: 预测步数
            
        Returns:
            包含预测结果的字典
        """
        if not history_data:
            logger.warning("No history data provided")
            return {
                'metric': metric_name,
                'predicted_values': [],
                'trend': 'unknown',
                'confidence': 0.0,
                'error': 'No history data'
            }
        
        # 提取数值数据
        values = [d.get('value', 0) for d in history_data]
        
        # 使用组合方法预测
        prediction = self.predict_combined(values, steps)
        
        # 生成预测时间点
        last_timestamp = history_data[-1].get('timestamp', datetime.now())
        if isinstance(last_timestamp, str):
            try:
                from dateutil import parser
                last_timestamp = parser.parse(last_timestamp)
            except:
                last_timestamp = datetime.now()
        
        predicted_timestamps = []
        for i in range(1, (steps or self.forecast_days) + 1):
            predicted_timestamps.append(last_timestamp + timedelta(days=i))
        
        # 构建预测结果
        result = {
            'metric': metric_name,
            'predicted_values': prediction.get('predicted_values', []),
            'predicted_timestamps': predicted_timestamps,
            'trend': prediction.get('trend', 'unknown'),
            'confidence': prediction.get('confidence', 0.0),
            'method': prediction.get('method', 'combined'),
            'history_data_points': len(history_data),
            'forecast_days': steps or self.forecast_days
        }
        
        return result
    
    def predict_host_status(self,
                           server_id: str,
                           history_metrics: Dict[str, List[Dict[str, Any]]],
                           thresholds: Dict[str, Dict[str, float]] = None) -> Dict[str, Any]:
        """预测主机未来状态
        
        基于历史资源指标预测主机是否会超过阈值
        
        Args:
            server_id: 服务器ID
            history_metrics: 历史指标数据，格式为 {metric_name: [{'timestamp': ..., 'value': ...}]}
            thresholds: 阈值配置，格式为 {metric_name: {'warning': 70, 'critical': 90}}
            
        Returns:
            包含主机状态预测的字典
        """
        if thresholds is None:
            # 默认阈值
            thresholds = {
                'cpu_usage_percent': {'warning': 70.0, 'critical': 90.0},
                'memory_usage_percent': {'warning': 75.0, 'critical': 90.0},
                'disk_usage_percent': {'warning': 80.0, 'critical': 90.0}
            }
        
        predictions = {}
        overall_status = 'normal'
        has_warnings = []
        has_criticals = []
        
        for metric_name, history_data in history_metrics.items():
            if not history_data:
                continue
            
            # 获取阈值
            metric_thresholds = thresholds.get(metric_name, {})
            warning_threshold = metric_thresholds.get('warning', 70.0)
            critical_threshold = metric_thresholds.get('critical', 90.0)
            
            # 预测
            prediction = self.predict_resource_usage(history_data, metric_name)
            predictions[metric_name] = prediction
            
            # 检查预测值是否会超过阈值
            predicted_values = prediction.get('predicted_values', [])
            
            for i, value in enumerate(predicted_values):
                day_offset = i + 1
                
                if value >= critical_threshold:
                    has_criticals.append({
                        'metric': metric_name,
                        'day': day_offset,
                        'predicted_value': round(value, 2),
                        'threshold': critical_threshold
                    })
                elif value >= warning_threshold:
                    has_warnings.append({
                        'metric': metric_name,
                        'day': day_offset,
                        'predicted_value': round(value, 2),
                        'threshold': warning_threshold
                    })
        
        # 确定整体状态
        if has_criticals:
            overall_status = 'critical'
        elif has_warnings:
            overall_status = 'warning'
        
        # 计算风险评分
        risk_score = self._calculate_risk_score(has_warnings, has_criticals)
        
        result = {
            'server_id': server_id,
            'prediction_timestamp': datetime.now(),
            'overall_status': overall_status,
            'risk_score': risk_score,
            'predictions': predictions,
            'warnings': has_warnings,
            'criticals': has_criticals,
            'recommendation': self._generate_recommendation(overall_status, has_warnings, has_criticals)
        }
        
        return result
    
    def _calculate_variance(self, data: List[float]) -> float:
        """计算方差
        
        Args:
            data: 数据列表
            
        Returns:
            方差值
        """
        if len(data) < 2:
            return 0.0
        
        mean = sum(data) / len(data)
        variance = sum((x - mean) ** 2 for x in data) / len(data)
        
        return variance
    
    def _calculate_risk_score(self, 
                          warnings: List[Dict], 
                          criticals: List[Dict]) -> float:
        """计算风险评分
        
        Args:
            warnings: 警告列表
            criticals: 严重告警列表
            
        Returns:
            风险评分 (0-100)
        """
        score = 0.0
        
        # 严重告警的权重更高
        for critical in criticals:
            day = critical.get('day', 1)
            # 越早发生的风险越高
            day_factor = max(0.3, 1.0 - (day - 1) * 0.1)
            score += 20.0 * day_factor
        
        for warning in warnings:
            day = warning.get('day', 1)
            day_factor = max(0.3, 1.0 - (day - 1) * 0.1)
            score += 5.0 * day_factor
        
        return min(100.0, score)
    
    def _generate_recommendation(self,
                                 overall_status: str,
                                 warnings: List[Dict],
                                 criticals: List[Dict]) -> str:
        """生成建议
        
        Args:
            overall_status: 整体状态
            warnings: 警告列表
            criticals: 严重告警列表
            
        Returns:
            建议文本
        """
        if overall_status == 'normal':
            return "主机状态正常，建议继续监控。"
        
        recommendations = []
        
        if criticals:
            metrics = set(c['metric'] for c in criticals)
            days = set(f"第{c['day']}天" for c in criticals)
            recommendations.append(
                f"严重风险：预计在 {', '.join(days)} 内，以下指标将超过临界阈值：{', '.join(metrics)}。建议立即关注并采取措施。"
            )
        
        if warnings:
            metrics = set(w['metric'] for w in warnings)
            days = set(f"第{w['day']}天" for w in warnings)
            recommendations.append(
                f"警告：预计在 {', '.join(days)} 内，以下指标将超过警告阈值：{', '.join(metrics)}。建议密切关注资源使用情况。"
            )
        
        return ' '.join(recommendations)


class AlertPredictor:
    """告警预测器，用于预测未来可能发生的告警"""
    
    # 告警严重级别权重
    SEVERITY_WEIGHTS = {
        'critical': 10.0,
        'warning': 3.0,
        'info': 1.0
    }
    
    # 常见告警与资源指标的映射
    ALERT_RESOURCE_MAPPING = {
        'HighCPU': ['cpu_usage_percent'],
        'HighMemory': ['memory_usage_percent'],
        'HighDiskUsage': ['disk_usage_percent'],
        'DiskFull': ['disk_usage_percent'],
        'HighNetworkTraffic': ['network_usage_percent'],
        'PodCrashLooping': ['kubernetes_pod_restarts'],
        'KubeNodeNotReady': ['kubernetes_node_status'],
        'TargetDown': ['service_availability'],
        'PrometheusTargetDown': ['service_availability']
    }
    
    def __init__(self,
                 history_days: int = 14,
                 forecast_days: int = 3,
                 confidence_threshold: float = 0.6):
        """初始化告警预测器
        
        Args:
            history_days: 使用的历史数据天数
            forecast_days: 预测的未来天数
            confidence_threshold: 置信度阈值
        """
        self.history_days = history_days
        self.forecast_days = forecast_days
        self.confidence_threshold = confidence_threshold
        
        logger.info(f"AlertPredictor initialized: history_days={history_days}, "
                   f"forecast_days={forecast_days}")
    
    def analyze_alert_patterns(self,
                               history_alerts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析告警历史模式
        
        Args:
            history_alerts: 历史告警列表，每个元素包含 alertname, severity, starts_at, ends_at
            
        Returns:
            告警模式分析结果
        """
        if not history_alerts:
            return {
                'total_alerts': 0,
                'patterns': {},
                'periodicity': {}
            }
        
        logger.info(f"Analyzing alert patterns from {len(history_alerts)} historical alerts")
        
        # 按告警名称分组统计
        alert_groups = {}
        for alert in history_alerts:
            alertname = alert.get('alertname', 'Unknown')
            if alertname not in alert_groups:
                alert_groups[alertname] = []
            alert_groups[alertname].append(alert)
        
        patterns = {}
        
        for alertname, alerts in alert_groups.items():
            # 按时间排序
            sorted_alerts = sorted(alerts, key=lambda x: x.get('starts_at', datetime.min))
            
            # 统计信息
            pattern_info = {
                'total_count': len(sorted_alerts),
                'severity_distribution': self._count_by_severity(sorted_alerts),
                'first_occurrence': sorted_alerts[0].get('starts_at') if sorted_alerts else None,
                'last_occurrence': sorted_alerts[-1].get('starts_at') if sorted_alerts else None,
                'time_intervals': [],
                'frequency_stats': {},
                'periodicity_score': 0.0
            }
            
            # 计算告警间隔
            if len(sorted_alerts) >= 2:
                intervals = []
                for i in range(1, len(sorted_alerts)):
                    prev = sorted_alerts[i-1].get('starts_at')
                    curr = sorted_alerts[i].get('starts_at')
                    if prev and curr:
                        if isinstance(prev, str):
                            try:
                                from dateutil import parser
                                prev = parser.parse(prev)
                            except:
                                continue
                        if isinstance(curr, str):
                            try:
                                from dateutil import parser
                                curr = parser.parse(curr)
                            except:
                                continue
                        
                        interval_hours = (curr - prev).total_seconds() / 3600
                        intervals.append(interval_hours)
                
                pattern_info['time_intervals'] = intervals
                
                if intervals:
                    # 计算频率统计
                    import statistics
                    pattern_info['frequency_stats'] = {
                        'mean_interval_hours': statistics.mean(intervals),
                        'median_interval_hours': statistics.median(intervals),
                        'min_interval_hours': min(intervals),
                        'max_interval_hours': max(intervals),
                        'std_dev_hours': statistics.stdev(intervals) if len(intervals) > 1 else 0.0
                    }
                    
                    # 计算周期性评分（基于间隔的标准差）
                    mean = pattern_info['frequency_stats']['mean_interval_hours']
                    std_dev = pattern_info['frequency_stats']['std_dev_hours']
                    if mean > 0:
                        cv = std_dev / mean  # 变异系数
                        pattern_info['periodicity_score'] = max(0.0, 1.0 - min(1.0, cv))
            
            patterns[alertname] = pattern_info
        
        # 检测周期性模式
        periodicity = self._detect_periodicity(patterns)
        
        return {
            'total_alerts': len(history_alerts),
            'unique_alert_types': len(alert_groups),
            'patterns': patterns,
            'periodicity': periodicity,
            'severity_summary': self._count_by_severity(history_alerts)
        }
    
    def _count_by_severity(self, alerts: List[Dict]) -> Dict[str, int]:
        """按严重级别统计告警数量
        
        Args:
            alerts: 告警列表
            
        Returns:
            按严重级别统计的字典
        """
        counts = {'critical': 0, 'warning': 0, 'info': 0, 'unknown': 0}
        
        for alert in alerts:
            severity = alert.get('severity', 'unknown').lower()
            if severity in counts:
                counts[severity] += 1
            else:
                counts['unknown'] += 1
        
        return counts
    
    def _detect_periodicity(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """检测周期性模式
        
        Args:
            patterns: 告警模式分析结果
            
        Returns:
            周期性检测结果
        """
        periodic_alerts = []
        
        for alertname, pattern in patterns.items():
            periodicity_score = pattern.get('periodicity_score', 0.0)
            freq_stats = pattern.get('frequency_stats', {})
            
            if periodicity_score >= 0.7:  # 高周期性
                periodic_alerts.append({
                    'alertname': alertname,
                    'periodicity_score': periodicity_score,
                    'mean_interval_hours': freq_stats.get('mean_interval_hours'),
                    'predicted_next_occurrence_hours': self._estimate_next_occurrence(freq_stats)
                })
        
        return {
            'periodic_alerts_count': len(periodic_alerts),
            'periodic_alerts': periodic_alerts
        }
    
    def _estimate_next_occurrence(self, freq_stats: Dict[str, float]) -> Optional[float]:
        """估计下一次发生的时间
        
        Args:
            freq_stats: 频率统计信息
            
        Returns:
            预计下一次发生的小时数（从现在开始）
        """
        if not freq_stats:
            return None
        
        mean = freq_stats.get('mean_interval_hours')
        median = freq_stats.get('median_interval_hours')
        std_dev = freq_stats.get('std_dev_hours', 0.0)
        
        if mean is None or median is None:
            return None
        
        # 使用中位数更稳健
        # 减去最近一次发生的时间（假设当前是最近一次发生后的时间点）
        # 这里简化处理，直接返回预计间隔的一部分
        estimated_hours = max(0, median - std_dev * 0.5)
        
        return estimated_hours
    
    def predict_alerts_by_frequency(self,
                                    history_alerts: List[Dict[str, Any]],
                                    steps: int = None) -> Dict[str, Any]:
        """基于历史频率预测告警
        
        Args:
            history_alerts: 历史告警列表
            steps: 预测步数（天数）
            
        Returns:
            基于频率的预测结果
        """
        if steps is None:
            steps = self.forecast_days
        
        if not history_alerts:
            return {
                'method': 'frequency',
                'predictions': [],
                'confidence': 0.0,
                'error': 'No history alerts'
            }
        
        # 分析告警模式
        pattern_analysis = self.analyze_alert_patterns(history_alerts)
        patterns = pattern_analysis.get('patterns', {})
        
        predictions = []
        
        for alertname, pattern in patterns.items():
            freq_stats = pattern.get('frequency_stats', {})
            periodicity_score = pattern.get('periodicity_score', 0.0)
            
            if not freq_stats or 'mean_interval_hours' not in freq_stats:
                continue
            
            mean_interval_hours = freq_stats['mean_interval_hours']
            mean_interval_days = mean_interval_hours / 24
            
            # 计算在预测期内可能发生的次数
            occurrences_in_forecast = steps / mean_interval_days if mean_interval_days > 0 else 0
            
            # 计算置信度
            confidence = min(0.95, periodicity_score * 0.8 + 0.2)
            
            # 估计每天发生的概率
            daily_probability = min(1.0, 1 / mean_interval_days) if mean_interval_days > 0 else 0
            
            # 预测每天是否可能发生
            daily_predictions = []
            for day in range(1, steps + 1):
                # 简化模型：假设事件发生概率与时间成正比
                # 实际上应该基于泊松分布或更复杂的模型
                probability = min(1.0, daily_probability * day * 0.5)
                
                # 考虑周期性
                if periodicity_score >= 0.7:
                    # 如果有高周期性，计算距离下一个周期的时间
                    next_occurrence_hours = self._estimate_next_occurrence(freq_stats)
                    if next_occurrence_hours is not None:
                        next_occurrence_days = next_occurrence_hours / 24
                        # 如果预测天数接近下一次发生时间，概率增加
                        day_diff = abs(day - next_occurrence_days)
                        if day_diff <= 1:  # 1天范围内
                            probability = max(probability, 0.7 + periodicity_score * 0.2)
                
                daily_predictions.append({
                    'day': day,
                    'probability': round(probability, 4),
                    'likely_to_occur': probability >= self.confidence_threshold
                })
            
            # 确定整体趋势
            total_count = pattern.get('total_count', 0)
            first_occurrence = pattern.get('first_occurrence')
            last_occurrence = pattern.get('last_occurrence')
            
            trend = 'stable'
            if first_occurrence and last_occurrence and total_count >= 3:
                # 简单的趋势判断：比较前半段和后半段的频率
                pass  # 简化实现
            
            predictions.append({
                'alertname': alertname,
                'severity': self._get_most_common_severity(pattern),
                'mean_interval_days': round(mean_interval_days, 2),
                'periodicity_score': round(periodicity_score, 4),
                'confidence': round(confidence, 4),
                'trend': trend,
                'daily_predictions': daily_predictions,
                'expected_occurrences_in_forecast': round(occurrences_in_forecast, 2)
            })
        
        # 按置信度排序
        predictions.sort(key=lambda x: x.get('confidence', 0), reverse=True)
        
        return {
            'method': 'frequency',
            'predictions': predictions,
            'pattern_analysis': pattern_analysis,
            'forecast_days': steps
        }
    
    def _get_most_common_severity(self, pattern: Dict[str, Any]) -> str:
        """获取最常见的严重级别
        
        Args:
            pattern: 告警模式
            
        Returns:
            最常见的严重级别
        """
        severity_dist = pattern.get('severity_distribution', {})
        if not severity_dist:
            return 'unknown'
        
        # 按权重排序
        severity_order = ['critical', 'warning', 'info', 'unknown']
        for severity in severity_order:
            if severity_dist.get(severity, 0) > 0:
                return severity
        
        return 'unknown'
    
    def predict_alerts_by_resource_trend(self,
                                         resource_predictions: Dict[str, Any],
                                         resource_thresholds: Dict[str, Dict[str, float]] = None) -> Dict[str, Any]:
        """基于资源趋势预测告警
        
        根据资源指标的预测趋势，推断可能触发的告警
        
        Args:
            resource_predictions: 资源预测结果，格式为 {metric_name: prediction_result}
            resource_thresholds: 资源阈值配置，格式为 {metric_name: {'warning': 70, 'critical': 90}}
            
        Returns:
            基于资源趋势的告警预测结果
        """
        if resource_thresholds is None:
            resource_thresholds = {
                'cpu_usage_percent': {'warning': 70.0, 'critical': 90.0},
                'memory_usage_percent': {'warning': 75.0, 'critical': 90.0},
                'disk_usage_percent': {'warning': 80.0, 'critical': 90.0}
            }
        
        predictions = []
        
        for metric_name, prediction in resource_predictions.items():
            if not prediction or 'predicted_values' not in prediction:
                continue
            
            predicted_values = prediction.get('predicted_values', [])
            predicted_timestamps = prediction.get('predicted_timestamps', [])
            trend = prediction.get('trend', 'unknown')
            confidence = prediction.get('confidence', 0.5)
            
            # 获取该指标的阈值
            thresholds = resource_thresholds.get(metric_name, {})
            warning_threshold = thresholds.get('warning', 70.0)
            critical_threshold = thresholds.get('critical', 90.0)
            
            # 确定可能触发的告警名称
            alertname = self._get_alertname_for_metric(metric_name)
            
            # 分析每个预测点
            daily_predictions = []
            has_warning = False
            has_critical = False
            
            for i, (value, timestamp) in enumerate(zip(predicted_values, predicted_timestamps)):
                day = i + 1
                
                prediction_status = 'normal'
                threshold_exceeded = None
                
                if value >= critical_threshold:
                    prediction_status = 'critical'
                    threshold_exceeded = critical_threshold
                    has_critical = True
                elif value >= warning_threshold:
                    prediction_status = 'warning'
                    threshold_exceeded = warning_threshold
                    has_warning = True
                
                daily_predictions.append({
                    'day': day,
                    'predicted_value': round(value, 2),
                    'threshold': threshold_exceeded,
                    'threshold_type': 'critical' if prediction_status == 'critical' else ('warning' if prediction_status == 'warning' else None),
                    'status': prediction_status,
                    'likely_to_trigger_alert': prediction_status in ['warning', 'critical'],
                    'timestamp': timestamp
                })
            
            # 如果有阈值被超过，生成告警预测
            if has_warning or has_critical:
                # 确定最高严重级别
                severity = 'critical' if has_critical else 'warning'
                
                # 计算置信度（结合资源预测的置信度和趋势）
                alert_confidence = confidence
                if trend == 'increasing':
                    alert_confidence = min(0.95, alert_confidence + 0.1)
                elif trend == 'decreasing':
                    alert_confidence = max(0.3, alert_confidence - 0.1)
                
                # 找到首次超过阈值的天数
                first_warning_day = None
                first_critical_day = None
                
                for dp in daily_predictions:
                    if dp['status'] == 'warning' and first_warning_day is None:
                        first_warning_day = dp['day']
                    if dp['status'] == 'critical' and first_critical_day is None:
                        first_critical_day = dp['day']
                
                predictions.append({
                    'alertname': alertname,
                    'related_metric': metric_name,
                    'severity': severity,
                    'confidence': round(alert_confidence, 4),
                    'trend': trend,
                    'first_warning_day': first_warning_day,
                    'first_critical_day': first_critical_day,
                    'daily_predictions': daily_predictions,
                    'warning_threshold': warning_threshold,
                    'critical_threshold': critical_threshold,
                    'source': 'resource_trend'
                })
        
        # 按严重级别和置信度排序
        def sort_key(p):
            severity_order = {'critical': 3, 'warning': 2, 'info': 1}
            return (-severity_order.get(p.get('severity', 'info'), 0), -p.get('confidence', 0))
        
        predictions.sort(key=sort_key)
        
        return {
            'method': 'resource_trend',
            'predictions': predictions,
            'forecast_days': len(predicted_values) if predictions and 'daily_predictions' in predictions[0] else 0
        }
    
    def _get_alertname_for_metric(self, metric_name: str) -> str:
        """根据资源指标获取对应的告警名称
        
        Args:
            metric_name: 资源指标名称
            
        Returns:
            告警名称
        """
        metric_alert_mapping = {
            'cpu_usage_percent': 'HighCPU',
            'memory_usage_percent': 'HighMemory',
            'disk_usage_percent': 'HighDiskUsage',
            'network_usage_percent': 'HighNetworkTraffic'
        }
        
        return metric_alert_mapping.get(metric_name, f'High{metric_name.title()}')
    
    def predict_combined_alerts(self,
                                history_alerts: List[Dict[str, Any]],
                                resource_predictions: Dict[str, Any] = None,
                                resource_thresholds: Dict[str, Dict[str, float]] = None,
                                steps: int = None) -> Dict[str, Any]:
        """组合多种方法进行告警预测
        
        结合频率预测和资源趋势预测，给出综合预测
        
        Args:
            history_alerts: 历史告警列表
            resource_predictions: 资源预测结果
            resource_thresholds: 资源阈值配置
            steps: 预测步数
            
        Returns:
            综合告警预测结果
        """
        if steps is None:
            steps = self.forecast_days
        
        # 获取两种方法的预测
        freq_prediction = self.predict_alerts_by_frequency(history_alerts, steps)
        
        resource_prediction = {'predictions': []}
        if resource_predictions:
            resource_prediction = self.predict_alerts_by_resource_trend(
                resource_predictions, resource_thresholds
            )
        
        # 合并预测结果
        combined_predictions = {}
        
        # 处理频率预测
        for pred in freq_prediction.get('predictions', []):
            alertname = pred['alertname']
            if alertname not in combined_predictions:
                combined_predictions[alertname] = {
                    'alertname': alertname,
                    'severity': pred.get('severity', 'warning'),
                    'sources': [],
                    'confidence_factors': []
                }
            
            combined_predictions[alertname]['sources'].append('frequency')
            combined_predictions[alertname]['frequency_prediction'] = pred
            combined_predictions[alertname]['confidence_factors'].append(
                ('frequency', pred.get('confidence', 0.5))
            )
        
        # 处理资源趋势预测
        for pred in resource_prediction.get('predictions', []):
            alertname = pred['alertname']
            if alertname not in combined_predictions:
                combined_predictions[alertname] = {
                    'alertname': alertname,
                    'severity': pred.get('severity', 'warning'),
                    'sources': [],
                    'confidence_factors': []
                }
            
            combined_predictions[alertname]['sources'].append('resource_trend')
            combined_predictions[alertname]['resource_prediction'] = pred
            combined_predictions[alertname]['confidence_factors'].append(
                ('resource_trend', pred.get('confidence', 0.5))
            )
        
        # 计算综合置信度和合并每日预测
        final_predictions = []
        
        for alertname, data in combined_predictions.items():
            sources = data['sources']
            confidence_factors = data['confidence_factors']
            
            # 计算加权置信度
            # 如果多种方法都预测了同一个告警，置信度会增加
            weights = {
                'frequency': 0.5,
                'resource_trend': 0.5
            }
            
            total_weight = 0
            weighted_confidence = 0
            
            for source, confidence in confidence_factors:
                weight = weights.get(source, 0.5)
                weighted_confidence += confidence * weight
                total_weight += weight
            
            if total_weight > 0:
                combined_confidence = weighted_confidence / total_weight
            else:
                combined_confidence = 0.5
            
            # 如果有多个来源，增加置信度
            if len(sources) > 1:
                combined_confidence = min(0.95, combined_confidence + 0.1)
            
            # 合并每日预测
            daily_predictions = self._merge_daily_predictions(data, steps)
            
            # 确定最终严重级别
            severity = self._determine_combined_severity(data)
            
            # 生成最终预测
            final_pred = {
                'alertname': alertname,
                'severity': severity,
                'confidence': round(combined_confidence, 4),
                'sources': sources,
                'daily_predictions': daily_predictions,
                'forecast_days': steps
            }
            
            # 添加详细信息
            if 'frequency_prediction' in data:
                final_pred['frequency_details'] = {
                    'mean_interval_days': data['frequency_prediction'].get('mean_interval_days'),
                    'periodicity_score': data['frequency_prediction'].get('periodicity_score')
                }
            
            if 'resource_prediction' in data:
                final_pred['resource_details'] = {
                    'related_metric': data['resource_prediction'].get('related_metric'),
                    'trend': data['resource_prediction'].get('trend'),
                    'first_warning_day': data['resource_prediction'].get('first_warning_day'),
                    'first_critical_day': data['resource_prediction'].get('first_critical_day')
                }
            
            final_predictions.append(final_pred)
        
        # 按严重级别和置信度排序
        def sort_key(p):
            severity_order = {'critical': 3, 'warning': 2, 'info': 1}
            return (-severity_order.get(p.get('severity', 'info'), 0), -p.get('confidence', 0))
        
        final_predictions.sort(key=sort_key)
        
        # 生成风险评估
        risk_assessment = self._generate_alert_risk_assessment(final_predictions)
        
        return {
            'method': 'combined',
            'predictions': final_predictions,
            'risk_assessment': risk_assessment,
            'forecast_days': steps,
            'frequency_prediction_count': len(freq_prediction.get('predictions', [])),
            'resource_prediction_count': len(resource_prediction.get('predictions', []))
        }
    
    def _merge_daily_predictions(self, data: Dict[str, Any], steps: int) -> List[Dict[str, Any]]:
        """合并每日预测
        
        Args:
            data: 预测数据
            steps: 预测步数
            
        Returns:
            合并后的每日预测
        """
        daily_predictions = []
        
        for day in range(1, steps + 1):
            day_data = {
                'day': day,
                'probability': 0.0,
                'likely_to_trigger_alert': False,
                'sources': [],
                'details': {}
            }
            
            max_probability = 0.0
            any_likely = False
            
            # 检查频率预测
            if 'frequency_prediction' in data:
                freq_daily = data['frequency_prediction'].get('daily_predictions', [])
                for fd in freq_daily:
                    if fd.get('day') == day:
                        prob = fd.get('probability', 0.0)
                        max_probability = max(max_probability, prob)
                        if fd.get('likely_to_occur'):
                            any_likely = True
                        day_data['sources'].append('frequency')
                        day_data['details']['frequency_probability'] = prob
                        break
            
            # 检查资源趋势预测
            if 'resource_prediction' in data:
                res_daily = data['resource_prediction'].get('daily_predictions', [])
                for rd in res_daily:
                    if rd.get('day') == day:
                        status = rd.get('status', 'normal')
                        if status == 'critical':
                            prob = 0.9
                        elif status == 'warning':
                            prob = 0.7
                        else:
                            prob = 0.1
                        
                        max_probability = max(max_probability, prob)
                        if rd.get('likely_to_trigger_alert'):
                            any_likely = True
                        day_data['sources'].append('resource_trend')
                        day_data['details']['resource_status'] = status
                        day_data['details']['resource_predicted_value'] = rd.get('predicted_value')
                        break
            
            # 如果有多个来源，增加概率
            if len(day_data['sources']) > 1:
                max_probability = min(0.95, max_probability + 0.1)
            
            day_data['probability'] = round(max_probability, 4)
            day_data['likely_to_trigger_alert'] = any_likely or max_probability >= self.confidence_threshold
            
            daily_predictions.append(day_data)
        
        return daily_predictions
    
    def _determine_combined_severity(self, data: Dict[str, Any]) -> str:
        """确定组合后的严重级别
        
        Args:
            data: 预测数据
            
        Returns:
            严重级别
        """
        severities = []
        
        if 'frequency_prediction' in data:
            severities.append(data['frequency_prediction'].get('severity', 'warning'))
        
        if 'resource_prediction' in data:
            severities.append(data['resource_prediction'].get('severity', 'warning'))
        
        # 取最高级别
        severity_order = ['critical', 'warning', 'info', 'unknown']
        for severity in severity_order:
            if severity in severities:
                return severity
        
        return 'warning'
    
    def _generate_alert_risk_assessment(self, predictions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """生成告警风险评估
        
        Args:
            predictions: 预测列表
            
        Returns:
            风险评估结果
        """
        if not predictions:
            return {
                'overall_risk_level': 'low',
                'risk_score': 0.0,
                'critical_alerts_count': 0,
                'warning_alerts_count': 0,
                'high_confidence_alerts': [],
                'recommendation': '无预测告警风险。'
            }
        
        # 统计
        critical_count = sum(1 for p in predictions if p.get('severity') == 'critical')
        warning_count = sum(1 for p in predictions if p.get('severity') == 'warning')
        
        # 高置信度告警
        high_confidence_alerts = [
            p for p in predictions 
            if p.get('confidence', 0) >= 0.7 and p.get('severity') in ['critical', 'warning']
        ]
        
        # 计算风险评分
        risk_score = 0.0
        for p in predictions:
            severity = p.get('severity', 'warning')
            confidence = p.get('confidence', 0.5)
            
            severity_weight = {
                'critical': 10.0,
                'warning': 3.0,
                'info': 1.0
            }.get(severity, 1.0)
            
            risk_score += severity_weight * confidence
        
        risk_score = min(100.0, risk_score)
        
        # 确定风险级别
        if risk_score >= 20.0 or critical_count >= 1:
            overall_risk = 'high'
        elif risk_score >= 5.0 or warning_count >= 2:
            overall_risk = 'medium'
        else:
            overall_risk = 'low'
        
        # 生成建议
        recommendation = self._generate_alert_recommendation(
            overall_risk, critical_count, warning_count, high_confidence_alerts
        )
        
        return {
            'overall_risk_level': overall_risk,
            'risk_score': round(risk_score, 2),
            'critical_alerts_count': critical_count,
            'warning_alerts_count': warning_count,
            'total_predicted_alerts': len(predictions),
            'high_confidence_alerts': [
                {
                    'alertname': p['alertname'],
                    'severity': p['severity'],
                    'confidence': p['confidence'],
                    'sources': p.get('sources', [])
                }
                for p in high_confidence_alerts
            ],
            'recommendation': recommendation
        }
    
    def _generate_alert_recommendation(self,
                                       overall_risk: str,
                                       critical_count: int,
                                       warning_count: int,
                                       high_confidence_alerts: List[Dict]) -> str:
        """生成告警预测建议
        
        Args:
            overall_risk: 整体风险级别
            critical_count: 严重告警数量
            warning_count: 警告告警数量
            high_confidence_alerts: 高置信度告警列表
            
        Returns:
            建议文本
        """
        if overall_risk == 'low':
            return "告警预测风险较低，建议继续监控系统状态。"
        
        recommendations = []
        
        if critical_count > 0:
            critical_alerts = [p['alertname'] for p in high_confidence_alerts if p['severity'] == 'critical']
            if critical_alerts:
                recommendations.append(
                    f"高风险预警：预计未来可能发生 {critical_count} 个严重告警，包括：{', '.join(critical_alerts[:3])}。建议立即检查相关系统。"
                )
            else:
                recommendations.append(
                    f"高风险预警：预计未来可能发生 {critical_count} 个严重告警。建议立即检查系统状态。"
                )
        
        if warning_count > 0:
            warning_alerts = [p['alertname'] for p in high_confidence_alerts if p['severity'] == 'warning']
            if warning_alerts:
                recommendations.append(
                    f"中等风险：预计未来可能发生 {warning_count} 个警告告警，包括：{', '.join(warning_alerts[:3])}。建议密切关注相关指标。"
                )
            else:
                recommendations.append(
                    f"中等风险：预计未来可能发生 {warning_count} 个警告告警。建议密切关注系统状态。"
                )
        
        if high_confidence_alerts:
            # 找出最早可能发生的告警
            earliest_day = None
            earliest_alert = None
            
            for alert in high_confidence_alerts:
                for daily in alert.get('daily_predictions', []):
                    if daily.get('likely_to_trigger_alert'):
                        day = daily.get('day')
                        if earliest_day is None or day < earliest_day:
                            earliest_day = day
                            earliest_alert = alert.get('alertname')
                        break
            
            if earliest_day and earliest_alert:
                recommendations.append(
                    f"最早可能在第 {earliest_day} 天触发告警：{earliest_alert}。建议提前做好准备。"
                )
        
        return ' '.join(recommendations)
    
    def predict_server_alerts(self,
                              server_id: str,
                              history_alerts: List[Dict[str, Any]],
                              resource_predictions: Dict[str, Any] = None,
                              resource_thresholds: Dict[str, Dict[str, float]] = None,
                              steps: int = None) -> Dict[str, Any]:
        """预测服务器可能发生的告警
        
        这是主方法，整合所有预测逻辑
        
        Args:
            server_id: 服务器ID
            history_alerts: 该服务器的历史告警列表
            resource_predictions: 资源预测结果
            resource_thresholds: 资源阈值配置
            steps: 预测步数
            
        Returns:
            完整的告警预测结果
        """
        logger.info(f"Predicting alerts for server: {server_id}")
        
        if steps is None:
            steps = self.forecast_days
        
        # 执行组合预测
        combined_prediction = self.predict_combined_alerts(
            history_alerts=history_alerts,
            resource_predictions=resource_predictions,
            resource_thresholds=resource_thresholds,
            steps=steps
        )
        
        # 构建最终结果
        result = {
            'server_id': server_id,
            'prediction_timestamp': datetime.now(),
            'forecast_days': steps,
            'history_alerts_count': len(history_alerts),
            'has_resource_predictions': resource_predictions is not None,
            **combined_prediction
        }
        
        return result
