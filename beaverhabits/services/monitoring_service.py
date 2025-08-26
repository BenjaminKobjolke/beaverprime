"""
Performance monitoring service for BeaverHabits application.

Provides metrics collection and performance monitoring capabilities
to track application performance and identify bottlenecks.
"""

import asyncio
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from uuid import UUID

from beaverhabits.logging import logger


@dataclass
class QueryMetric:
    """Represents a database query performance metric."""
    query_type: str
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[UUID] = None
    record_count: Optional[int] = None
    cache_hit: bool = False


@dataclass
class EndpointMetric:
    """Represents an API endpoint performance metric."""
    endpoint: str
    method: str
    duration_ms: float
    status_code: int
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[UUID] = None
    query_count: int = 0
    cache_hits: int = 0


class PerformanceMonitor:
    """Performance monitoring and metrics collection service."""
    
    def __init__(self, max_metrics_retention: int = 1000):
        self._query_metrics: List[QueryMetric] = []
        self._endpoint_metrics: List[EndpointMetric] = []
        self._max_retention = max_metrics_retention
        self._lock = asyncio.Lock()
        
        # Performance counters
        self._total_queries = 0
        self._total_cache_hits = 0
        self._slow_query_threshold_ms = 100
        self._slow_endpoint_threshold_ms = 1000
    
    @asynccontextmanager
    async def track_query(self, query_type: str, user_id: Optional[UUID] = None):
        """Context manager to track database query performance."""
        start_time = time.perf_counter()
        query_info = {
            'record_count': 0,
            'cache_hit': False
        }
        
        try:
            yield query_info
        finally:
            duration = (time.perf_counter() - start_time) * 1000  # Convert to milliseconds
            
            metric = QueryMetric(
                query_type=query_type,
                duration_ms=duration,
                user_id=user_id,
                record_count=query_info.get('record_count'),
                cache_hit=query_info.get('cache_hit', False)
            )
            
            await self._record_query_metric(metric)
            
            if duration > self._slow_query_threshold_ms:
                logger.warning(f"[Monitor] Slow query detected: {query_type} took {duration:.1f}ms")
    
    @asynccontextmanager
    async def track_endpoint(self, endpoint: str, method: str = "GET", user_id: Optional[UUID] = None):
        """Context manager to track API endpoint performance."""
        start_time = time.perf_counter()
        endpoint_info = {
            'status_code': 200,
            'query_count': 0,
            'cache_hits': 0
        }
        
        try:
            yield endpoint_info
        finally:
            duration = (time.perf_counter() - start_time) * 1000
            
            metric = EndpointMetric(
                endpoint=endpoint,
                method=method,
                duration_ms=duration,
                status_code=endpoint_info.get('status_code', 200),
                user_id=user_id,
                query_count=endpoint_info.get('query_count', 0),
                cache_hits=endpoint_info.get('cache_hits', 0)
            )
            
            await self._record_endpoint_metric(metric)
            
            if duration > self._slow_endpoint_threshold_ms:
                logger.warning(f"[Monitor] Slow endpoint detected: {method} {endpoint} took {duration:.1f}ms")
    
    async def _record_query_metric(self, metric: QueryMetric):
        """Record a query performance metric."""
        async with self._lock:
            self._query_metrics.append(metric)
            self._total_queries += 1
            
            if metric.cache_hit:
                self._total_cache_hits += 1
            
            # Trim old metrics if we exceed retention limit
            if len(self._query_metrics) > self._max_retention:
                self._query_metrics = self._query_metrics[-self._max_retention:]
    
    async def _record_endpoint_metric(self, metric: EndpointMetric):
        """Record an endpoint performance metric."""
        async with self._lock:
            self._endpoint_metrics.append(metric)
            
            # Trim old metrics if we exceed retention limit
            if len(self._endpoint_metrics) > self._max_retention:
                self._endpoint_metrics = self._endpoint_metrics[-self._max_retention:]
    
    async def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        async with self._lock:
            # Filter metrics within the time period
            recent_queries = [m for m in self._query_metrics if m.timestamp >= cutoff_time]
            recent_endpoints = [m for m in self._endpoint_metrics if m.timestamp >= cutoff_time]
            
            # Calculate query statistics
            if recent_queries:
                avg_query_time = sum(m.duration_ms for m in recent_queries) / len(recent_queries)
                slow_queries = len([m for m in recent_queries if m.duration_ms > self._slow_query_threshold_ms])
                cache_hit_rate = len([m for m in recent_queries if m.cache_hit]) / len(recent_queries) * 100
            else:
                avg_query_time = 0
                slow_queries = 0
                cache_hit_rate = 0
            
            # Calculate endpoint statistics
            if recent_endpoints:
                avg_endpoint_time = sum(m.duration_ms for m in recent_endpoints) / len(recent_endpoints)
                slow_endpoints = len([m for m in recent_endpoints if m.duration_ms > self._slow_endpoint_threshold_ms])
                error_rate = len([m for m in recent_endpoints if m.status_code >= 400]) / len(recent_endpoints) * 100
            else:
                avg_endpoint_time = 0
                slow_endpoints = 0
                error_rate = 0
            
            # Find top slow queries
            slow_query_types = {}
            for metric in recent_queries:
                if metric.duration_ms > self._slow_query_threshold_ms:
                    if metric.query_type not in slow_query_types:
                        slow_query_types[metric.query_type] = []
                    slow_query_types[metric.query_type].append(metric.duration_ms)
            
            top_slow_queries = sorted(
                [(qtype, max(times), len(times)) for qtype, times in slow_query_types.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
            
            return {
                'time_period_hours': hours,
                'query_stats': {
                    'total_queries': len(recent_queries),
                    'avg_duration_ms': round(avg_query_time, 2),
                    'slow_queries': slow_queries,
                    'cache_hit_rate_percent': round(cache_hit_rate, 1),
                    'top_slow_queries': [
                        {'query_type': qtype, 'max_duration_ms': round(max_dur, 2), 'count': count}
                        for qtype, max_dur, count in top_slow_queries
                    ]
                },
                'endpoint_stats': {
                    'total_requests': len(recent_endpoints),
                    'avg_duration_ms': round(avg_endpoint_time, 2),
                    'slow_endpoints': slow_endpoints,
                    'error_rate_percent': round(error_rate, 1)
                },
                'overall_stats': {
                    'total_lifetime_queries': self._total_queries,
                    'total_lifetime_cache_hits': self._total_cache_hits,
                    'lifetime_cache_hit_rate': round(
                        (self._total_cache_hits / self._total_queries * 100) if self._total_queries > 0 else 0, 1
                    )
                }
            }
    
    async def get_user_performance(self, user_id: UUID, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics for a specific user."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        async with self._lock:
            user_queries = [
                m for m in self._query_metrics 
                if m.user_id == user_id and m.timestamp >= cutoff_time
            ]
            user_endpoints = [
                m for m in self._endpoint_metrics
                if m.user_id == user_id and m.timestamp >= cutoff_time
            ]
            
            if not user_queries and not user_endpoints:
                return {'message': f'No activity found for user {user_id} in the last {hours} hours'}
            
            query_count = len(user_queries)
            avg_query_time = sum(m.duration_ms for m in user_queries) / query_count if query_count > 0 else 0
            
            endpoint_count = len(user_endpoints)
            avg_endpoint_time = sum(m.duration_ms for m in user_endpoints) / endpoint_count if endpoint_count > 0 else 0
            
            return {
                'user_id': str(user_id),
                'time_period_hours': hours,
                'query_count': query_count,
                'avg_query_time_ms': round(avg_query_time, 2),
                'endpoint_count': endpoint_count,
                'avg_endpoint_time_ms': round(avg_endpoint_time, 2),
                'cache_hits': len([m for m in user_queries if m.cache_hit]),
                'total_records_processed': sum(m.record_count or 0 for m in user_queries)
            }
    
    async def clear_old_metrics(self, hours: int = 24):
        """Clear metrics older than the specified hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        async with self._lock:
            old_query_count = len(self._query_metrics)
            old_endpoint_count = len(self._endpoint_metrics)
            
            self._query_metrics = [m for m in self._query_metrics if m.timestamp >= cutoff_time]
            self._endpoint_metrics = [m for m in self._endpoint_metrics if m.timestamp >= cutoff_time]
            
            removed_queries = old_query_count - len(self._query_metrics)
            removed_endpoints = old_endpoint_count - len(self._endpoint_metrics)
            
            if removed_queries > 0 or removed_endpoints > 0:
                logger.info(f"[Monitor] Cleared {removed_queries} old query metrics and {removed_endpoints} old endpoint metrics")
    
    async def set_thresholds(self, slow_query_ms: int = None, slow_endpoint_ms: int = None):
        """Update performance thresholds for slow query/endpoint detection."""
        if slow_query_ms is not None:
            self._slow_query_threshold_ms = slow_query_ms
            logger.info(f"[Monitor] Updated slow query threshold to {slow_query_ms}ms")
        
        if slow_endpoint_ms is not None:
            self._slow_endpoint_threshold_ms = slow_endpoint_ms
            logger.info(f"[Monitor] Updated slow endpoint threshold to {slow_endpoint_ms}ms")


# Global performance monitor instance
performance_monitor = PerformanceMonitor()


async def performance_cleanup_task():
    """Background task to clean up old performance metrics."""
    while True:
        try:
            await asyncio.sleep(3600)  # Run every hour
            await performance_monitor.clear_old_metrics(hours=24)
        except Exception as e:
            logger.error(f"[Monitor] Cleanup task error: {e}")


# Background cleanup task management
_cleanup_task = None

def start_performance_monitoring():
    """Start the performance monitoring background task."""
    global _cleanup_task
    if _cleanup_task is None:
        _cleanup_task = asyncio.create_task(performance_cleanup_task())
        logger.info("[Monitor] Started performance monitoring")

def stop_performance_monitoring():
    """Stop the performance monitoring background task."""
    global _cleanup_task
    if _cleanup_task:
        _cleanup_task.cancel()
        _cleanup_task = None
        logger.info("[Monitor] Stopped performance monitoring")