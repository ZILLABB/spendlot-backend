"""
Application metrics collection and monitoring.
"""
import time
import psutil
from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict, deque
from contextlib import contextmanager

from app.core.logging import get_logger
from app.core.caching import cache

logger = get_logger(__name__)


class MetricsCollector:
    """Collect and store application metrics."""
    
    def __init__(self):
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        self.histograms = defaultdict(list)
        self.timers = defaultdict(deque)
        self.start_time = time.time()
    
    def increment_counter(self, name: str, value: int = 1, tags: Dict[str, str] = None):
        """Increment a counter metric."""
        key = self._build_key(name, tags)
        self.counters[key] += value
    
    def set_gauge(self, name: str, value: float, tags: Dict[str, str] = None):
        """Set a gauge metric."""
        key = self._build_key(name, tags)
        self.gauges[key] = value
    
    def record_histogram(self, name: str, value: float, tags: Dict[str, str] = None):
        """Record a value in a histogram."""
        key = self._build_key(name, tags)
        self.histograms[key].append(value)
        
        # Keep only last 1000 values
        if len(self.histograms[key]) > 1000:
            self.histograms[key] = self.histograms[key][-1000:]
    
    def record_timer(self, name: str, duration: float, tags: Dict[str, str] = None):
        """Record a timer metric."""
        key = self._build_key(name, tags)
        self.timers[key].append((time.time(), duration))
        
        # Keep only last hour of data
        cutoff = time.time() - 3600
        while self.timers[key] and self.timers[key][0][0] < cutoff:
            self.timers[key].popleft()
    
    def _build_key(self, name: str, tags: Dict[str, str] = None) -> str:
        """Build metric key with tags."""
        if not tags:
            return name
        
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}[{tag_str}]"
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics."""
        return {
            "counters": dict(self.counters),
            "gauges": dict(self.gauges),
            "histograms": {
                name: {
                    "count": len(values),
                    "min": min(values) if values else 0,
                    "max": max(values) if values else 0,
                    "avg": sum(values) / len(values) if values else 0
                }
                for name, values in self.histograms.items()
            },
            "timers": {
                name: {
                    "count": len(values),
                    "avg_duration": sum(v[1] for v in values) / len(values) if values else 0,
                    "total_duration": sum(v[1] for v in values)
                }
                for name, values in self.timers.items()
            },
            "uptime": time.time() - self.start_time
        }


# Global metrics collector
metrics = MetricsCollector()


@contextmanager
def timer_context(name: str, tags: Dict[str, str] = None):
    """Context manager for timing operations."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        metrics.record_timer(name, duration, tags)


def timed(metric_name: str, tags: Dict[str, str] = None):
    """Decorator for timing function execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with timer_context(metric_name, tags):
                return func(*args, **kwargs)
        return wrapper
    return decorator


class SystemMetrics:
    """Collect system-level metrics."""
    
    @staticmethod
    def get_cpu_usage() -> float:
        """Get CPU usage percentage."""
        return psutil.cpu_percent(interval=1)
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """Get memory usage information."""
        memory = psutil.virtual_memory()
        return {
            "total": memory.total,
            "available": memory.available,
            "used": memory.used,
            "percentage": memory.percent
        }
    
    @staticmethod
    def get_disk_usage() -> Dict[str, float]:
        """Get disk usage information."""
        disk = psutil.disk_usage('/')
        return {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percentage": (disk.used / disk.total) * 100
        }
    
    @staticmethod
    def get_network_stats() -> Dict[str, int]:
        """Get network statistics."""
        net_io = psutil.net_io_counters()
        return {
            "bytes_sent": net_io.bytes_sent,
            "bytes_recv": net_io.bytes_recv,
            "packets_sent": net_io.packets_sent,
            "packets_recv": net_io.packets_recv
        }


class DatabaseMetrics:
    """Collect database-related metrics."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_connection_pool_stats(self) -> Dict[str, int]:
        """Get database connection pool statistics."""
        try:
            engine = self.db.bind
            pool = engine.pool
            
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "invalid": pool.invalid()
            }
        except Exception as e:
            logger.error(f"Error getting connection pool stats: {str(e)}")
            return {}
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """Get slow query statistics."""
        from app.core.database_optimization import query_monitor
        return query_monitor.get_stats()


class ApplicationMetrics:
    """Collect application-specific metrics."""
    
    def __init__(self, db_session):
        self.db = db_session
    
    def get_user_stats(self) -> Dict[str, int]:
        """Get user statistics."""
        try:
            from app.models.user import User
            
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            verified_users = self.db.query(User).filter(User.is_verified == True).count()
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "verified_users": verified_users
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {str(e)}")
            return {}
    
    def get_receipt_stats(self) -> Dict[str, int]:
        """Get receipt processing statistics."""
        try:
            from app.models.receipt import Receipt
            
            total_receipts = self.db.query(Receipt).count()
            processed_receipts = self.db.query(Receipt).filter(
                Receipt.processing_status == "completed"
            ).count()
            pending_receipts = self.db.query(Receipt).filter(
                Receipt.processing_status == "pending"
            ).count()
            failed_receipts = self.db.query(Receipt).filter(
                Receipt.processing_status == "failed"
            ).count()
            
            return {
                "total_receipts": total_receipts,
                "processed_receipts": processed_receipts,
                "pending_receipts": pending_receipts,
                "failed_receipts": failed_receipts,
                "processing_rate": (processed_receipts / total_receipts * 100) if total_receipts > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting receipt stats: {str(e)}")
            return {}
    
    def get_transaction_stats(self) -> Dict[str, int]:
        """Get transaction statistics."""
        try:
            from app.models.transaction import Transaction
            
            total_transactions = self.db.query(Transaction).count()
            
            # Get transactions from last 24 hours
            yesterday = datetime.now() - timedelta(days=1)
            recent_transactions = self.db.query(Transaction).filter(
                Transaction.created_at >= yesterday
            ).count()
            
            return {
                "total_transactions": total_transactions,
                "recent_transactions": recent_transactions
            }
        except Exception as e:
            logger.error(f"Error getting transaction stats: {str(e)}")
            return {}


def collect_all_metrics(db_session) -> Dict[str, Any]:
    """Collect all application metrics."""
    system_metrics = SystemMetrics()
    db_metrics = DatabaseMetrics(db_session)
    app_metrics = ApplicationMetrics(db_session)
    
    all_metrics = {
        "timestamp": datetime.now().isoformat(),
        "system": {
            "cpu_usage": system_metrics.get_cpu_usage(),
            "memory": system_metrics.get_memory_usage(),
            "disk": system_metrics.get_disk_usage(),
            "network": system_metrics.get_network_stats()
        },
        "database": {
            "connection_pool": db_metrics.get_connection_pool_stats(),
            "slow_queries": db_metrics.get_slow_queries()[:10]  # Top 10 slow queries
        },
        "application": {
            "users": app_metrics.get_user_stats(),
            "receipts": app_metrics.get_receipt_stats(),
            "transactions": app_metrics.get_transaction_stats(),
            "custom_metrics": metrics.get_metrics()
        }
    }
    
    # Cache metrics for 1 minute
    cache.set("system_metrics", all_metrics, ttl=60)
    
    return all_metrics


def get_health_status(db_session) -> Dict[str, Any]:
    """Get overall system health status."""
    try:
        # Check database connectivity
        db_session.execute("SELECT 1")
        db_healthy = True
    except Exception:
        db_healthy = False
    
    # Check Redis connectivity
    try:
        cache.set("health_check", "ok", ttl=10)
        redis_healthy = cache.get("health_check") == "ok"
    except Exception:
        redis_healthy = False
    
    # Check system resources
    memory = SystemMetrics.get_memory_usage()
    disk = SystemMetrics.get_disk_usage()
    
    system_healthy = (
        memory["percentage"] < 90 and
        disk["percentage"] < 90
    )
    
    overall_healthy = db_healthy and redis_healthy and system_healthy
    
    return {
        "status": "healthy" if overall_healthy else "unhealthy",
        "checks": {
            "database": "healthy" if db_healthy else "unhealthy",
            "redis": "healthy" if redis_healthy else "unhealthy",
            "system": "healthy" if system_healthy else "unhealthy"
        },
        "details": {
            "memory_usage": memory["percentage"],
            "disk_usage": disk["percentage"]
        }
    }
