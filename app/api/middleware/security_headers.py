"""
Security headers middleware.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.config import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response."""
        response = await call_next(request)
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src 'self' 'unsafe-inline'",
            "img-src 'self' data: https:",
            "font-src 'self'",
            "connect-src 'self' https://api.plaid.com https://production.plaid.com https://sandbox.plaid.com",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        
        if settings.ENVIRONMENT == "development":
            # More permissive CSP for development
            csp_directives = [
                "default-src 'self' 'unsafe-inline' 'unsafe-eval'",
                "connect-src 'self' http://localhost:* ws://localhost:* https://api.plaid.com https://sandbox.plaid.com"
            ]
        
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)
        
        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # XSS Protection
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy (formerly Feature Policy)
        permissions_policy = [
            "camera=()",
            "microphone=()",
            "geolocation=(self)",
            "payment=(self)",
            "usb=()",
            "magnetometer=()",
            "accelerometer=()",
            "gyroscope=()"
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)
        
        # HSTS (only in production with HTTPS)
        if settings.ENVIRONMENT == "production":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
        
        # Remove server information
        response.headers.pop("Server", None)
        
        # API-specific headers
        if request.url.path.startswith("/api/"):
            # Prevent caching of API responses
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            
            # API versioning header
            response.headers["API-Version"] = "v1"
            
            # Rate limiting headers (if rate limiting is active)
            if hasattr(request.state, "rate_limit_remaining"):
                response.headers["X-RateLimit-Remaining"] = str(request.state.rate_limit_remaining)
                response.headers["X-RateLimit-Reset"] = str(request.state.rate_limit_reset)
        
        return response


class CORSSecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced CORS middleware with security considerations."""
    
    def __init__(self, app, allowed_origins: list = None):
        super().__init__(app)
        self.allowed_origins = allowed_origins or []
        
        # Add default allowed origins based on environment
        if settings.ENVIRONMENT == "development":
            self.allowed_origins.extend([
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000"
            ])
        elif settings.ENVIRONMENT == "production":
            # Add production frontend URLs
            if settings.FRONTEND_URL:
                self.allowed_origins.append(settings.FRONTEND_URL)
    
    async def dispatch(self, request: Request, call_next):
        """Handle CORS with security checks."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            
            if self._is_origin_allowed(origin):
                response.headers["Access-Control-Allow-Origin"] = origin
                response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
                response.headers["Access-Control-Allow-Headers"] = (
                    "Authorization, Content-Type, X-Requested-With, X-Request-ID"
                )
                response.headers["Access-Control-Max-Age"] = "86400"  # 24 hours
            
            return response
        
        # Process actual request
        response = await call_next(request)
        
        # Add CORS headers to response
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Expose-Headers"] = (
                "X-Request-ID, X-RateLimit-Remaining, X-RateLimit-Reset"
            )
        
        return response
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return False
        
        # Check exact matches
        if origin in self.allowed_origins:
            return True
        
        # Check wildcard patterns (be careful with this in production)
        for allowed_origin in self.allowed_origins:
            if allowed_origin == "*":
                return True
            if allowed_origin.endswith("*"):
                prefix = allowed_origin[:-1]
                if origin.startswith(prefix):
                    return True
        
        return False


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add unique request ID to each request."""
    
    async def dispatch(self, request: Request, call_next):
        """Add request ID to request and response."""
        import uuid
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Add to request state
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
