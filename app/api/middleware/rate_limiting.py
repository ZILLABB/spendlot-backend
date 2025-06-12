"""
Rate limiting middleware for API endpoints.
"""
import time
from typing import Dict
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import redis

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Redis client for rate limiting
try:
    redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
    redis_client = None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Rate limiting middleware using Redis."""
    
    def __init__(self, app, calls_per_minute: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or settings.RATE_LIMIT_PER_MINUTE
        self.window_size = 60  # 1 minute window
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting."""
        
        # Skip rate limiting for health checks and docs
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Get client identifier
        client_id = self.get_client_id(request)
        
        # Check rate limit
        if not await self.is_allowed(client_id):
            logger.warning(f"Rate limit exceeded for client: {client_id}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": "60"}
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = await self.get_remaining_calls(client_id)
        response.headers["X-RateLimit-Limit"] = str(self.calls_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.window_size)
        
        return response
    
    def get_client_id(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Try to get user ID from JWT token
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            # In a real implementation, you'd decode the JWT here
            # For now, use the token as identifier
            return f"user:{auth_header[7:20]}"  # First 13 chars of token
        
        # Fall back to IP address
        client_ip = request.client.host
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()
        
        return f"ip:{client_ip}"
    
    async def is_allowed(self, client_id: str) -> bool:
        """Check if client is allowed to make request."""
        if not redis_client:
            return True  # Allow if Redis is not available
        
        try:
            key = f"rate_limit:{client_id}"
            current_time = int(time.time())
            window_start = current_time - self.window_size
            
            # Remove old entries
            redis_client.zremrangebyscore(key, 0, window_start)
            
            # Count current requests
            current_requests = redis_client.zcard(key)
            
            if current_requests >= self.calls_per_minute:
                return False
            
            # Add current request
            redis_client.zadd(key, {str(current_time): current_time})
            redis_client.expire(key, self.window_size)
            
            return True
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow on error
    
    async def get_remaining_calls(self, client_id: str) -> int:
        """Get remaining calls for client."""
        if not redis_client:
            return self.calls_per_minute
        
        try:
            key = f"rate_limit:{client_id}"
            current_requests = redis_client.zcard(key)
            return max(0, self.calls_per_minute - current_requests)
        except Exception:
            return self.calls_per_minute
