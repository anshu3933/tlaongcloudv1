import asyncio
import psutil
import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ..database import async_session_factory, engine
from .metrics_collector import metrics_collector

logger = logging.getLogger(__name__)


class HealthMonitor:
    """Monitors system health and collects metrics automatically"""
    
    def __init__(self, check_interval: int = 30):
        self.check_interval = check_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self._session_count = 0
        self._operation_times = []
        
    async def start(self):
        """Start the health monitoring background task"""
        if self.is_running:
            logger.warning("Health monitor is already running")
            return
        
        self.is_running = True
        self._task = asyncio.create_task(self._monitoring_loop())
        logger.info(f"Health monitor started with {self.check_interval}s interval")
    
    async def stop(self):
        """Stop the health monitoring background task"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Health monitor stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        try:
            while self.is_running:
                await self._collect_health_metrics()
                await asyncio.sleep(self.check_interval)
        except asyncio.CancelledError:
            logger.info("Health monitoring loop cancelled")
        except Exception as e:
            logger.error(f"Error in health monitoring loop: {e}")
    
    async def _collect_health_metrics(self):
        """Collect and record current health metrics"""
        try:
            # System metrics
            memory_info = psutil.virtual_memory()
            memory_usage_mb = memory_info.used / (1024 * 1024)
            
            # Database pool metrics (fixed to use engine directly)
            pool_size = getattr(engine.pool, 'size', lambda: 10)()
            pool_checked_out = getattr(engine.pool, 'checkedout', lambda: 0)()
            
            # Calculate error rate from recent operations
            recent_performance = metrics_collector.get_performance_summary(hours=1)
            error_rate = 100.0 - recent_performance.get("success_rate", 100.0)
            
            # Record health snapshot
            metrics_collector.record_health_snapshot(
                active_sessions=self._session_count,
                pending_operations=metrics_collector.active_operations,
                average_response_time_ms=recent_performance.get("avg_duration_ms", 0.0),
                error_rate_percent=error_rate,
                memory_usage_mb=memory_usage_mb,
                database_pool_size=pool_size,
                database_pool_used=pool_checked_out
            )
            
            # Clean up old data periodically
            metrics_collector.cleanup_old_data()
            
        except Exception as e:
            logger.error(f"Failed to collect health metrics: {e}")
    
    def track_session_start(self):
        """Track when a database session starts"""
        self._session_count += 1
    
    def track_session_end(self):
        """Track when a database session ends"""
        if self._session_count > 0:
            self._session_count -= 1
    
    async def get_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Simple database health check
            session_maker = async_session_factory
            async with session_maker() as session:
                result = await session.execute("SELECT 1")
                await result.fetchone()
            
            response_time = (time.time() - start_time) * 1000
            
            return {
                "status": "healthy",
                "response_time_ms": response_time,
                "message": "Database connection successful"
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "response_time_ms": None,
                "message": f"Database connection failed: {str(e)}"
            }
    
    async def get_comprehensive_health(self) -> Dict[str, Any]:
        """Get comprehensive system health information"""
        # System resources
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        # Database health
        db_health = await self.get_database_health()
        
        # Application metrics
        conflict_summary = metrics_collector.get_conflict_summary(hours=1)
        performance_summary = metrics_collector.get_performance_summary(hours=1)
        overall_health = metrics_collector.get_health_status()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_status": overall_health["status"],
            "system_resources": {
                "cpu_percent": cpu_percent,
                "memory": {
                    "total_mb": memory_info.total / (1024 * 1024),
                    "used_mb": memory_info.used / (1024 * 1024),
                    "percent": memory_info.percent
                },
                "disk": {
                    "total_gb": disk_info.total / (1024 * 1024 * 1024),
                    "used_gb": disk_info.used / (1024 * 1024 * 1024),
                    "percent": (disk_info.used / disk_info.total) * 100
                }
            },
            "database": db_health,
            "application": {
                "active_sessions": self._session_count,
                "active_operations": metrics_collector.active_operations,
                "total_operations": metrics_collector.total_operations,
                "total_conflicts": metrics_collector.total_conflicts,
                "recent_conflicts": conflict_summary["total_conflicts"],
                "recent_operations": performance_summary["total_operations"],
                "success_rate": performance_summary["success_rate"],
                "avg_response_time_ms": performance_summary["avg_duration_ms"]
            },
            "alerts": self._generate_alerts(overall_health, db_health, cpu_percent, memory_info.percent)
        }
    
    def _generate_alerts(self, overall_health: Dict, db_health: Dict, cpu_percent: float, memory_percent: float) -> List[Dict[str, Any]]:
        """Generate alerts based on current metrics"""
        alerts = []
        
        # Database alerts
        if db_health["status"] == "unhealthy":
            alerts.append({
                "level": "critical",
                "type": "database",
                "message": "Database connectivity issues detected",
                "timestamp": datetime.now().isoformat()
            })
        elif db_health.get("response_time_ms", 0) > 1000:
            alerts.append({
                "level": "warning",
                "type": "database",
                "message": f"Slow database response: {db_health['response_time_ms']:.0f}ms",
                "timestamp": datetime.now().isoformat()
            })
        
        # Resource alerts
        if cpu_percent > 80:
            alerts.append({
                "level": "warning",
                "type": "cpu",
                "message": f"High CPU usage: {cpu_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        if memory_percent > 85:
            alerts.append({
                "level": "warning",
                "type": "memory",
                "message": f"High memory usage: {memory_percent:.1f}%",
                "timestamp": datetime.now().isoformat()
            })
        
        # Application alerts
        if overall_health["status"] == "unhealthy":
            alerts.append({
                "level": "critical",
                "type": "application",
                "message": overall_health["message"],
                "timestamp": datetime.now().isoformat()
            })
        elif overall_health["status"] == "degraded":
            alerts.append({
                "level": "warning",
                "type": "application",
                "message": overall_health["message"],
                "timestamp": datetime.now().isoformat()
            })
        
        # Version conflict alerts
        recent_conflicts = metrics_collector.get_conflict_summary(hours=1)
        if recent_conflicts["total_conflicts"] > 10:
            alerts.append({
                "level": "warning",
                "type": "conflicts",
                "message": f"High version conflict rate: {recent_conflicts['total_conflicts']} conflicts in last hour",
                "timestamp": datetime.now().isoformat()
            })
        
        return alerts


# Global health monitor instance
health_monitor = HealthMonitor()