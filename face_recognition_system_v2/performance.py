import time
import threading
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
from functools import wraps
from datetime import datetime


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout: float = 60.0
    success_threshold: int = 3
    timeout: float = 10.0


@dataclass
class CircuitMetrics:
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0


class CircuitBreaker:
    def __init__(self, config: Optional[CircuitBreakerConfig] = None, name: str = "default"):
        self.config = config or CircuitBreakerConfig()
        self.name = name
        self._state = CircuitState.CLOSED
        self._metrics = CircuitMetrics()
        self._lock = threading.Lock()
        self._last_open_time: Optional[float] = None
        
        logger.info(f"CircuitBreaker '{name}' initialized with threshold={config.failure_threshold if config else 5}")
    
    @property
    def state(self) -> CircuitState:
        return self._state
    
    def _check_recovery(self):
        if self._state == CircuitState.OPEN:
            elapsed = time.time() - self._last_open_time
            if elapsed >= self.config.recovery_timeout:
                self._state = CircuitState.HALF_OPEN
                logger.info(f"CircuitBreaker '{self.name}' transitioning to HALF_OPEN state after recovery timeout")
    
    def can_execute(self) -> bool:
        with self._lock:
            self._check_recovery()
            
            if self._state == CircuitState.OPEN:
                return False
            
            return True
    
    def record_success(self):
        with self._lock:
            self._metrics.total_requests += 1
            self._metrics.successful_requests += 1
            self._metrics.last_success_time = time.time()
            self._metrics.consecutive_failures = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._metrics.consecutive_successes += 1
                if self._metrics.consecutive_successes >= self.config.success_threshold:
                    self._state = CircuitState.CLOSED
                    self._metrics.consecutive_successes = 0
                    logger.info(f"CircuitBreaker '{self.name}' transitioning to CLOSED state after successful recovery")
            
            elif self._state == CircuitState.CLOSED:
                self._metrics.consecutive_successes += 1
    
    def record_failure(self, exception: Optional[Exception] = None):
        with self._lock:
            self._metrics.total_requests += 1
            self._metrics.failed_requests += 1
            self._metrics.last_failure_time = time.time()
            self._metrics.consecutive_failures += 1
            self._metrics.consecutive_successes = 0
            
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._last_open_time = time.time()
                logger.warning(f"CircuitBreaker '{self.name}' transitioning to OPEN state after failure in HALF_OPEN")
            
            elif self._state == CircuitState.CLOSED:
                if self._metrics.consecutive_failures >= self.config.failure_threshold:
                    self._state = CircuitState.OPEN
                    self._last_open_time = time.time()
                    logger.warning(f"CircuitBreaker '{self.name}' transitioning to OPEN state after {self._metrics.consecutive_failures} consecutive failures")
    
    def get_metrics(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'name': self.name,
                'state': self._state.value,
                'total_requests': self._metrics.total_requests,
                'successful_requests': self._metrics.successful_requests,
                'failed_requests': self._metrics.failed_requests,
                'consecutive_failures': self._metrics.consecutive_failures,
                'consecutive_successes': self._metrics.consecutive_successes,
                'last_failure_time': self._metrics.last_failure_time,
                'last_success_time': self._metrics.last_success_time,
                'config': {
                    'failure_threshold': self.config.failure_threshold,
                    'recovery_timeout': self.config.recovery_timeout,
                    'success_threshold': self.config.success_threshold
                }
            }
    
    def reset(self):
        with self._lock:
            self._state = CircuitState.CLOSED
            self._metrics = CircuitMetrics()
            self._last_open_time = None
            logger.info(f"CircuitBreaker '{self.name}' reset to CLOSED state")


class RateLimiter:
    def __init__(self, rate: float = 10.0, capacity: int = 20, name: str = "default"):
        self.rate = rate
        self.capacity = capacity
        self.name = name
        self._tokens = capacity
        self._last_update = time.time()
        self._lock = threading.Lock()
        
        logger.info(f"RateLimiter '{name}' initialized with rate={rate}/s, capacity={capacity}")
    
    def _refill(self):
        now = time.time()
        elapsed = now - self._last_update
        new_tokens = elapsed * self.rate
        self._tokens = min(self.capacity, self._tokens + new_tokens)
        self._last_update = now
    
    def acquire(self, tokens: int = 1, timeout: Optional[float] = None) -> bool:
        start_time = time.time()
        
        with self._lock:
            while True:
                self._refill()
                
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return True
                
                if timeout is not None:
                    elapsed = time.time() - start_time
                    if elapsed >= timeout:
                        return False
                
                wait_time = (tokens - self._tokens) / self.rate
                time.sleep(min(wait_time, 0.1))
    
    def try_acquire(self, tokens: int = 1) -> bool:
        with self._lock:
            self._refill()
            
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            
            return False
    
    def get_available_tokens(self) -> float:
        with self._lock:
            self._refill()
            return self._tokens


@dataclass
class PerformanceSample:
    timestamp: float
    value: float
    tag: str = ""


class PerformanceMonitor:
    def __init__(self, window_size: int = 100, name: str = "default"):
        self.window_size = window_size
        self.name = name
        self._samples: Dict[str, deque] = {}
        self._lock = threading.Lock()
        
        logger.info(f"PerformanceMonitor '{name}' initialized with window_size={window_size}")
    
    def record(self, metric_name: str, value: float, tag: str = ""):
        with self._lock:
            if metric_name not in self._samples:
                self._samples[metric_name] = deque(maxlen=self.window_size)
            
            self._samples[metric_name].append(
                PerformanceSample(timestamp=time.time(), value=value, tag=tag)
            )
    
    def get_stats(self, metric_name: str) -> Dict[str, Any]:
        with self._lock:
            if metric_name not in self._samples:
                return {
                    'count': 0,
                    'mean': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0
                }
            
            samples = [s.value for s in self._samples[metric_name]]
            
            if not samples:
                return {
                    'count': 0,
                    'mean': 0.0,
                    'min': 0.0,
                    'max': 0.0,
                    'p50': 0.0,
                    'p95': 0.0,
                    'p99': 0.0
                }
            
            samples_sorted = sorted(samples)
            n = len(samples_sorted)
            
            return {
                'count': n,
                'mean': sum(samples) / n,
                'min': samples_sorted[0],
                'max': samples_sorted[-1],
                'p50': samples_sorted[int(n * 0.5)],
                'p95': samples_sorted[int(n * 0.95)] if n > 1 else samples_sorted[-1],
                'p99': samples_sorted[int(n * 0.99)] if n > 1 else samples_sorted[-1]
            }
    
    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            result = {}
            for metric_name in self._samples:
                result[metric_name] = self.get_stats(metric_name)
            return result
    
    def clear(self, metric_name: Optional[str] = None):
        with self._lock:
            if metric_name:
                if metric_name in self._samples:
                    self._samples[metric_name].clear()
            else:
                self._samples.clear()


class HealthChecker:
    def __init__(self, check_interval: float = 30.0, name: str = "default"):
        self.check_interval = check_interval
        self.name = name
        self._checks: Dict[str, Callable[[], bool]] = {}
        self._statuses: Dict[str, bool] = {}
        self._last_check_times: Dict[str, float] = {}
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        
        logger.info(f"HealthChecker '{name}' initialized with interval={check_interval}s")
    
    def register_check(self, name: str, check_func: Callable[[], bool]):
        with self._lock:
            self._checks[name] = check_func
            self._statuses[name] = True
            self._last_check_times[name] = time.time()
    
    def unregister_check(self, name: str):
        with self._lock:
            if name in self._checks:
                del self._checks[name]
            if name in self._statuses:
                del self._statuses[name]
            if name in self._last_check_times:
                del self._last_check_times[name]
    
    def run_checks(self):
        with self._lock:
            for name, check_func in self._checks.items():
                try:
                    result = check_func()
                    self._statuses[name] = result
                    self._last_check_times[name] = time.time()
                    
                    if not result:
                        logger.warning(f"Health check '{name}' failed")
                except Exception as e:
                    logger.error(f"Health check '{name}' error: {e}")
                    self._statuses[name] = False
                    self._last_check_times[name] = time.time()
    
    def get_status(self) -> Dict[str, Any]:
        with self._lock:
            all_healthy = all(self._statuses.values()) if self._statuses else True
            
            details = []
            for name, healthy in self._statuses.items():
                details.append({
                    'name': name,
                    'healthy': healthy,
                    'last_check': self._last_check_times.get(name)
                })
            
            return {
                'healthy': all_healthy,
                'timestamp': time.time(),
                'details': details
            }
    
    def start(self):
        if self._thread is not None:
            return
        
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"HealthChecker '{self.name}' started")
    
    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None
        logger.info(f"HealthChecker '{self.name}' stopped")
    
    def _run_loop(self):
        while not self._stop_event.is_set():
            try:
                self.run_checks()
            except Exception as e:
                logger.error(f"HealthChecker loop error: {e}")
            
            self._stop_event.wait(self.check_interval)


def timed(monitor: PerformanceMonitor, metric_name: str):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                elapsed = time.time() - start_time
                monitor.record(metric_name, elapsed)
        return wrapper
    return decorator


def with_circuit_breaker(breaker: CircuitBreaker, fallback: Optional[Callable] = None):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not breaker.can_execute():
                logger.warning(f"CircuitBreaker '{breaker.name}' is OPEN, rejecting request")
                if fallback:
                    return fallback(*args, **kwargs)
                raise Exception(f"Service unavailable: CircuitBreaker '{breaker.name}' is OPEN")
            
            try:
                result = func(*args, **kwargs)
                breaker.record_success()
                return result
            except Exception as e:
                breaker.record_failure(e)
                raise
        return wrapper
    return decorator


def rate_limited(limiter: RateLimiter, tokens: int = 1, fallback: Optional[Callable] = None):
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not limiter.try_acquire(tokens):
                logger.warning(f"RateLimiter '{limiter.name}' rate limit exceeded")
                if fallback:
                    return fallback(*args, **kwargs)
                raise Exception("Rate limit exceeded")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator
