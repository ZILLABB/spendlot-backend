"""
Database optimization utilities and query performance monitoring.
"""
import time
from typing import Dict, Any, List, Optional
from contextlib import contextmanager
from sqlalchemy import event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, Query
from sqlalchemy.pool import QueuePool

from app.core.logging import get_logger

logger = get_logger(__name__)


class QueryPerformanceMonitor:
    """Monitor and log slow database queries."""
    
    def __init__(self, slow_query_threshold: float = 1.0):
        self.slow_query_threshold = slow_query_threshold
        self.query_stats = {}
    
    def log_query(self, query: str, duration: float, params: Dict[str, Any] = None):
        """Log query performance."""
        if duration > self.slow_query_threshold:
            logger.warning(
                f"Slow query detected: {duration:.3f}s",
                extra={
                    "query": query[:500],  # Truncate long queries
                    "duration": duration,
                    "params": params,
                    "type": "slow_query"
                }
            )
        
        # Update statistics
        query_hash = hash(query)
        if query_hash not in self.query_stats:
            self.query_stats[query_hash] = {
                "query": query[:200],
                "count": 0,
                "total_time": 0.0,
                "max_time": 0.0,
                "min_time": float('inf')
            }
        
        stats = self.query_stats[query_hash]
        stats["count"] += 1
        stats["total_time"] += duration
        stats["max_time"] = max(stats["max_time"], duration)
        stats["min_time"] = min(stats["min_time"], duration)
    
    def get_stats(self) -> List[Dict[str, Any]]:
        """Get query performance statistics."""
        stats_list = []
        for query_hash, stats in self.query_stats.items():
            avg_time = stats["total_time"] / stats["count"]
            stats_list.append({
                "query": stats["query"],
                "count": stats["count"],
                "total_time": stats["total_time"],
                "avg_time": avg_time,
                "max_time": stats["max_time"],
                "min_time": stats["min_time"]
            })
        
        # Sort by total time descending
        return sorted(stats_list, key=lambda x: x["total_time"], reverse=True)


# Global query monitor
query_monitor = QueryPerformanceMonitor()


@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Record query start time."""
    context._query_start_time = time.time()


@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log query performance after execution."""
    if hasattr(context, '_query_start_time'):
        duration = time.time() - context._query_start_time
        query_monitor.log_query(statement, duration, parameters)


class DatabaseOptimizer:
    """Database optimization utilities."""
    
    @staticmethod
    def create_optimized_engine_config() -> Dict[str, Any]:
        """Create optimized database engine configuration."""
        return {
            "poolclass": QueuePool,
            "pool_size": 20,
            "max_overflow": 30,
            "pool_pre_ping": True,
            "pool_recycle": 3600,  # 1 hour
            "echo": False,  # Set to True for query logging in development
            "echo_pool": False,
            "connect_args": {
                "connect_timeout": 10,
                "application_name": "spendlot_api"
            }
        }
    
    @staticmethod
    def optimize_query_for_pagination(
        query: Query,
        page: int,
        size: int,
        order_by_column=None
    ) -> Query:
        """Optimize query for efficient pagination."""
        # Add consistent ordering for pagination
        if order_by_column is not None:
            query = query.order_by(order_by_column)
        
        # Use offset and limit
        offset = (page - 1) * size
        return query.offset(offset).limit(size)
    
    @staticmethod
    def add_query_hints(session: Session, hints: List[str]):
        """Add database-specific query hints."""
        # PostgreSQL-specific hints
        for hint in hints:
            if hint == "use_index":
                # This would be database-specific
                pass
            elif hint == "force_seq_scan":
                session.execute(text("SET enable_seqscan = on"))
            elif hint == "disable_seq_scan":
                session.execute(text("SET enable_seqscan = off"))


@contextmanager
def query_performance_context(operation_name: str):
    """Context manager for measuring query performance."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.info(
            f"Database operation '{operation_name}' completed in {duration:.3f}s",
            extra={"operation": operation_name, "duration": duration}
        )


class CacheManager:
    """Simple in-memory cache for database queries."""
    
    def __init__(self, max_size: int = 1000, ttl: int = 300):
        self.cache = {}
        self.timestamps = {}
        self.max_size = max_size
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if key not in self.cache:
            return None
        
        # Check TTL
        if time.time() - self.timestamps[key] > self.ttl:
            self.delete(key)
            return None
        
        return self.cache[key]
    
    def set(self, key: str, value: Any):
        """Set value in cache."""
        # Evict old entries if cache is full
        if len(self.cache) >= self.max_size:
            self._evict_oldest()
        
        self.cache[key] = value
        self.timestamps[key] = time.time()
    
    def delete(self, key: str):
        """Delete value from cache."""
        self.cache.pop(key, None)
        self.timestamps.pop(key, None)
    
    def clear(self):
        """Clear all cache entries."""
        self.cache.clear()
        self.timestamps.clear()
    
    def _evict_oldest(self):
        """Evict oldest cache entry."""
        if not self.timestamps:
            return
        
        oldest_key = min(self.timestamps.keys(), key=lambda k: self.timestamps[k])
        self.delete(oldest_key)


# Global cache instance
query_cache = CacheManager()


def cached_query(cache_key: str, ttl: int = 300):
    """Decorator for caching query results."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Try to get from cache
            cached_result = query_cache.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute query and cache result
            result = func(*args, **kwargs)
            query_cache.set(cache_key, result)
            return result
        
        return wrapper
    return decorator


class IndexRecommendations:
    """Analyze queries and recommend database indexes."""
    
    def __init__(self):
        self.query_patterns = []
    
    def analyze_query(self, query: str, table_name: str, where_columns: List[str]):
        """Analyze query pattern for index recommendations."""
        pattern = {
            "table": table_name,
            "where_columns": where_columns,
            "query": query,
            "frequency": 1
        }
        
        # Check if pattern already exists
        for existing_pattern in self.query_patterns:
            if (existing_pattern["table"] == table_name and 
                set(existing_pattern["where_columns"]) == set(where_columns)):
                existing_pattern["frequency"] += 1
                return
        
        self.query_patterns.append(pattern)
    
    def get_index_recommendations(self) -> List[Dict[str, Any]]:
        """Get index recommendations based on query patterns."""
        recommendations = []
        
        # Sort by frequency
        sorted_patterns = sorted(
            self.query_patterns, 
            key=lambda x: x["frequency"], 
            reverse=True
        )
        
        for pattern in sorted_patterns:
            if pattern["frequency"] >= 5:  # Only recommend for frequent queries
                recommendations.append({
                    "table": pattern["table"],
                    "columns": pattern["where_columns"],
                    "frequency": pattern["frequency"],
                    "suggested_index": f"idx_{pattern['table']}_{'_'.join(pattern['where_columns'])}"
                })
        
        return recommendations


# Global index analyzer
index_analyzer = IndexRecommendations()
