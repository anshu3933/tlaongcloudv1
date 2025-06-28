import time
import asyncio
import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import json

logger = logging.getLogger(__name__)


@dataclass
class ConflictEvent:
    """Represents a version conflict event"""
    timestamp: datetime
    student_id: str
    academic_year: str
    attempted_version: int
    conflict_type: str  # 'version_conflict', 'retry_exhausted', 'database_error'
    retry_count: int
    resolution_time_ms: float
    error_message: Optional[str] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for operations"""
    operation_name: str
    timestamp: datetime
    duration_ms: float
    success: bool
    retry_count: int = 0
    error_type: Optional[str] = None


@dataclass
class SystemHealthMetrics:
    """System health snapshot"""
    timestamp: datetime
    active_sessions: int
    pending_operations: int
    average_response_time_ms: float
    error_rate_percent: float
    memory_usage_mb: float
    database_pool_size: int
    database_pool_used: int


class MetricsCollector:
    """Collects and aggregates metrics for version conflicts and system health"""
    
    def __init__(self, max_events: int = 1000, retention_hours: int = 24):
        self.max_events = max_events
        self.retention_hours = retention_hours
        self._lock = threading.RLock()
        
        # Event storage
        self.conflict_events: deque = deque(maxlen=max_events)
        self.performance_metrics: deque = deque(maxlen=max_events * 2)
        self.health_snapshots: deque = deque(maxlen=max_events // 10)
        
        # Real-time counters
        self.active_operations = 0
        self.total_operations = 0
        self.total_conflicts = 0
        self.total_retries = 0
        
        # Aggregated metrics
        self.hourly_stats: Dict[str, Dict] = defaultdict(lambda: {
            "operations": 0,
            "conflicts": 0,
            "retries": 0,
            "avg_duration_ms": 0.0,
            "error_rate": 0.0
        })
        
        logger.info("MetricsCollector initialized")
    
    def record_conflict_event(
        self,
        student_id: str,
        academic_year: str,
        attempted_version: int,
        conflict_type: str,
        retry_count: int,
        resolution_time_ms: float,
        error_message: Optional[str] = None
    ):
        """Record a version conflict event"""
        with self._lock:
            event = ConflictEvent(
                timestamp=datetime.now(),
                student_id=student_id,
                academic_year=academic_year,
                attempted_version=attempted_version,
                conflict_type=conflict_type,
                retry_count=retry_count,
                resolution_time_ms=resolution_time_ms,
                error_message=error_message
            )
            
            self.conflict_events.append(event)
            self.total_conflicts += 1
            self.total_retries += retry_count
            
            # Update hourly stats
            hour_key = event.timestamp.strftime("%Y-%m-%d-%H")
            self.hourly_stats[hour_key]["conflicts"] += 1
            self.hourly_stats[hour_key]["retries"] += retry_count
            
            logger.warning(
                f"Version conflict recorded: student={student_id}, "
                f"year={academic_year}, version={attempted_version}, "
                f"type={conflict_type}, retries={retry_count}, "
                f"resolution_time={resolution_time_ms:.2f}ms"
            )
    
    def record_performance_metric(
        self,
        operation_name: str,
        duration_ms: float,
        success: bool,
        retry_count: int = 0,
        error_type: Optional[str] = None
    ):
        """Record a performance metric"""
        with self._lock:
            metric = PerformanceMetrics(
                operation_name=operation_name,
                timestamp=datetime.now(),
                duration_ms=duration_ms,
                success=success,
                retry_count=retry_count,
                error_type=error_type
            )
            
            self.performance_metrics.append(metric)
            self.total_operations += 1
            
            # Update hourly stats
            hour_key = metric.timestamp.strftime("%Y-%m-%d-%H")
            stats = self.hourly_stats[hour_key]
            stats["operations"] += 1
            
            # Update average duration (running average)
            if stats["avg_duration_ms"] == 0:
                stats["avg_duration_ms"] = duration_ms
            else:
                stats["avg_duration_ms"] = (stats["avg_duration_ms"] + duration_ms) / 2
            
            # Update error rate
            if not success:
                current_errors = stats.get("errors", 0) + 1
                stats["errors"] = current_errors
                stats["error_rate"] = (current_errors / stats["operations"]) * 100
    
    def record_health_snapshot(
        self,
        active_sessions: int,
        pending_operations: int,
        average_response_time_ms: float,
        error_rate_percent: float,
        memory_usage_mb: float,
        database_pool_size: int,
        database_pool_used: int
    ):
        """Record a system health snapshot"""
        with self._lock:
            snapshot = SystemHealthMetrics(
                timestamp=datetime.now(),
                active_sessions=active_sessions,
                pending_operations=pending_operations,
                average_response_time_ms=average_response_time_ms,
                error_rate_percent=error_rate_percent,
                memory_usage_mb=memory_usage_mb,
                database_pool_size=database_pool_size,
                database_pool_used=database_pool_used
            )
            
            self.health_snapshots.append(snapshot)
    
    def start_operation(self) -> str:
        """Mark the start of an operation and return operation ID"""
        with self._lock:
            self.active_operations += 1
            operation_id = f"op_{int(time.time() * 1000)}_{self.active_operations}"
            return operation_id
    
    def end_operation(self):
        """Mark the end of an operation"""
        with self._lock:
            if self.active_operations > 0:
                self.active_operations -= 1
    
    def get_conflict_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get conflict summary for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_conflicts = [
                event for event in self.conflict_events 
                if event.timestamp >= cutoff_time
            ]
            
            if not recent_conflicts:
                return {
                    "total_conflicts": 0,
                    "conflict_rate_per_hour": 0.0,
                    "avg_retry_count": 0.0,
                    "avg_resolution_time_ms": 0.0,
                    "conflict_types": {},
                    "most_affected_students": []
                }
            
            # Aggregate statistics
            conflict_types = defaultdict(int)
            student_conflicts = defaultdict(int)
            total_retries = sum(event.retry_count for event in recent_conflicts)
            total_resolution_time = sum(event.resolution_time_ms for event in recent_conflicts)
            
            for event in recent_conflicts:
                conflict_types[event.conflict_type] += 1
                student_conflicts[event.student_id] += 1
            
            return {
                "total_conflicts": len(recent_conflicts),
                "conflict_rate_per_hour": len(recent_conflicts) / hours,
                "avg_retry_count": total_retries / len(recent_conflicts),
                "avg_resolution_time_ms": total_resolution_time / len(recent_conflicts),
                "conflict_types": dict(conflict_types),
                "most_affected_students": sorted(
                    student_conflicts.items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )[:5]
            }
    
    def get_performance_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get performance summary for the specified time period"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            recent_metrics = [
                metric for metric in self.performance_metrics 
                if metric.timestamp >= cutoff_time
            ]
            
            if not recent_metrics:
                return {
                    "total_operations": 0,
                    "success_rate": 100.0,
                    "avg_duration_ms": 0.0,
                    "p95_duration_ms": 0.0,
                    "operations_per_minute": 0.0,
                    "slowest_operations": []
                }
            
            # Calculate statistics
            successful_ops = [m for m in recent_metrics if m.success]
            success_rate = (len(successful_ops) / len(recent_metrics)) * 100
            
            durations = [m.duration_ms for m in recent_metrics]
            durations.sort()
            avg_duration = sum(durations) / len(durations)
            p95_index = int(len(durations) * 0.95)
            p95_duration = durations[p95_index] if p95_index < len(durations) else durations[-1]
            
            operations_per_minute = len(recent_metrics) / (hours * 60)
            
            # Find slowest operations
            slowest_ops = sorted(recent_metrics, key=lambda x: x.duration_ms, reverse=True)[:5]
            
            return {
                "total_operations": len(recent_metrics),
                "success_rate": success_rate,
                "avg_duration_ms": avg_duration,
                "p95_duration_ms": p95_duration,
                "operations_per_minute": operations_per_minute,
                "slowest_operations": [
                    {
                        "operation": op.operation_name,
                        "duration_ms": op.duration_ms,
                        "timestamp": op.timestamp.isoformat(),
                        "success": op.success
                    }
                    for op in slowest_ops
                ]
            }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current system health status"""
        with self._lock:
            if not self.health_snapshots:
                return {
                    "status": "unknown",
                    "message": "No health data available",
                    "last_update": None
                }
            
            latest_snapshot = self.health_snapshots[-1]
            
            # Determine health status based on metrics
            status = "healthy"
            issues = []
            
            if latest_snapshot.error_rate_percent > 5.0:
                status = "degraded"
                issues.append(f"High error rate: {latest_snapshot.error_rate_percent:.1f}%")
            
            if latest_snapshot.average_response_time_ms > 1000:
                status = "degraded"
                issues.append(f"Slow response time: {latest_snapshot.average_response_time_ms:.0f}ms")
            
            if latest_snapshot.database_pool_used / latest_snapshot.database_pool_size > 0.9:
                status = "degraded"
                issues.append("Database pool near capacity")
            
            if latest_snapshot.memory_usage_mb > 1024:  # 1GB
                issues.append(f"High memory usage: {latest_snapshot.memory_usage_mb:.0f}MB")
            
            if len(issues) > 2:
                status = "unhealthy"
            
            return {
                "status": status,
                "message": "; ".join(issues) if issues else "All systems operational",
                "last_update": latest_snapshot.timestamp.isoformat(),
                "metrics": {
                    "active_sessions": latest_snapshot.active_sessions,
                    "pending_operations": latest_snapshot.pending_operations,
                    "avg_response_time_ms": latest_snapshot.average_response_time_ms,
                    "error_rate_percent": latest_snapshot.error_rate_percent,
                    "memory_usage_mb": latest_snapshot.memory_usage_mb,
                    "db_pool_utilization": latest_snapshot.database_pool_used / latest_snapshot.database_pool_size * 100
                }
            }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data"""
        return {
            "conflicts": self.get_conflict_summary(hours=24),
            "performance": self.get_performance_summary(hours=24),
            "health": self.get_health_status(),
            "summary": {
                "total_operations": self.total_operations,
                "total_conflicts": self.total_conflicts,
                "total_retries": self.total_retries,
                "active_operations": self.active_operations,
                "conflict_rate": (self.total_conflicts / max(self.total_operations, 1)) * 100
            }
        }
    
    def cleanup_old_data(self):
        """Remove old data beyond retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)
        
        with self._lock:
            # Clean conflict events
            self.conflict_events = deque(
                [event for event in self.conflict_events if event.timestamp >= cutoff_time],
                maxlen=self.max_events
            )
            
            # Clean performance metrics
            self.performance_metrics = deque(
                [metric for metric in self.performance_metrics if metric.timestamp >= cutoff_time],
                maxlen=self.max_events * 2
            )
            
            # Clean health snapshots
            self.health_snapshots = deque(
                [snapshot for snapshot in self.health_snapshots if snapshot.timestamp >= cutoff_time],
                maxlen=self.max_events // 10
            )
            
            # Clean hourly stats
            cutoff_hour = cutoff_time.strftime("%Y-%m-%d-%H")
            self.hourly_stats = {
                k: v for k, v in self.hourly_stats.items() 
                if k >= cutoff_hour
            }


# Global metrics collector instance
metrics_collector = MetricsCollector()