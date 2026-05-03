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
