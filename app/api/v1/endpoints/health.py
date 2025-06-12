"""
Health check endpoints.
"""
import time
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import redis

from app.core.config import settings
from app.core.database import get_db
from app.schemas.common import HealthCheck

router = APIRouter()


@router.get("/", response_model=HealthCheck)
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint to verify service status.
    """
    
    # Check database connection
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        database_status = f"unhealthy: {str(e)}"
    
    # Check Redis connection
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        redis_client.ping()
        redis_status = "healthy"
    except Exception as e:
        redis_status = f"unhealthy: {str(e)}"
    
    return HealthCheck(
        status="healthy" if database_status == "healthy" and redis_status == "healthy" else "unhealthy",
        timestamp=datetime.utcnow().isoformat(),
        version=settings.VERSION,
        database=database_status,
        redis=redis_status
    )


@router.get("/database")
async def database_health(db: Session = Depends(get_db)):
    """
    Database-specific health check.
    """
    try:
        start_time = time.time()
        result = db.execute("SELECT version()").fetchone()
        response_time = time.time() - start_time
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "version": result[0] if result else "unknown"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/redis")
async def redis_health():
    """
    Redis-specific health check.
    """
    try:
        redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        start_time = time.time()
        redis_client.ping()
        response_time = time.time() - start_time
        
        info = redis_client.info()
        
        return {
            "status": "healthy",
            "response_time": response_time,
            "version": info.get("redis_version", "unknown"),
            "memory_usage": info.get("used_memory_human", "unknown")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
