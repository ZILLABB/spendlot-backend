"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.api.v1.api import api_router
from app.api.middleware.rate_limiting import RateLimitMiddleware
from app.api.middleware.request_logging import RequestLoggingMiddleware
from app.api.middleware.error_handling import ErrorHandlingMiddleware
from app.api.middleware.security_headers import SecurityHeadersMiddleware, RequestIDMiddleware

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.ENVIRONMENT == "development" else ["localhost", "127.0.0.1"]
)

# Add middleware in order (last added = first executed)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIDMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(
        "Unhandled exception",
        exc_info=exc,
        request_url=str(request.url),
        request_method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred"
        }
    )


# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs_url": f"{settings.API_V1_STR}/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from app.core.database import SessionLocal
    from app.utils.metrics import get_health_status

    db = SessionLocal()
    try:
        health_status = get_health_status(db)
        return {
            **health_status,
            "timestamp": time.time(),
            "version": settings.VERSION,
            "environment": settings.ENVIRONMENT
        }
    finally:
        db.close()


@app.get("/metrics")
async def get_metrics():
    """Get application metrics (admin only in production)."""
    from app.core.database import SessionLocal
    from app.utils.metrics import collect_all_metrics

    # In production, this should be protected by authentication
    if settings.ENVIRONMENT == "production":
        # Add authentication check here
        pass

    db = SessionLocal()
    try:
        return collect_all_metrics(db)
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.ENVIRONMENT == "development"
    )
