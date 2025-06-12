"""
Enhanced error handling middleware.
"""
import traceback
from typing import Dict, Any
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from pydantic import ValidationError
import redis.exceptions
from plaid.exceptions import PlaidError
from google.api_core.exceptions import GoogleAPIError

from app.core.logging import get_logger

logger = get_logger(__name__)


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for comprehensive error handling."""
    
    async def dispatch(self, request: Request, call_next):
        """Process request with enhanced error handling."""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException:
            # Re-raise HTTP exceptions (they're handled by FastAPI)
            raise
            
        except ValidationError as e:
            # Pydantic validation errors
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=422,
                content={
                    "error": "Validation Error",
                    "message": "Invalid input data",
                    "details": e.errors()
                }
            )
            
        except IntegrityError as e:
            # Database integrity constraint violations
            logger.error(f"Database integrity error: {str(e)}")
            
            error_message = "Database constraint violation"
            if "unique constraint" in str(e).lower():
                error_message = "A record with this information already exists"
            elif "foreign key constraint" in str(e).lower():
                error_message = "Referenced record does not exist"
            elif "not null constraint" in str(e).lower():
                error_message = "Required field is missing"
            
            return JSONResponse(
                status_code=409,
                content={
                    "error": "Conflict",
                    "message": error_message,
                    "type": "integrity_error"
                }
            )
            
        except SQLAlchemyError as e:
            # Other database errors
            logger.error(f"Database error: {str(e)}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Database Error",
                    "message": "A database error occurred",
                    "type": "database_error"
                }
            )
            
        except redis.exceptions.RedisError as e:
            # Redis connection/operation errors
            logger.error(f"Redis error: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service Unavailable",
                    "message": "Cache service temporarily unavailable",
                    "type": "redis_error"
                }
            )
            
        except PlaidError as e:
            # Plaid API errors
            logger.error(f"Plaid API error: {str(e)}")
            
            error_message = "Banking service error"
            status_code = 502
            
            if hasattr(e, 'error_code'):
                if e.error_code == 'ITEM_LOGIN_REQUIRED':
                    error_message = "Please re-authenticate your bank account"
                    status_code = 401
                elif e.error_code == 'INSUFFICIENT_CREDENTIALS':
                    error_message = "Invalid banking credentials"
                    status_code = 401
                elif e.error_code == 'ITEM_LOCKED':
                    error_message = "Bank account is temporarily locked"
                    status_code = 423
                elif e.error_code == 'RATE_LIMIT_EXCEEDED':
                    error_message = "Too many requests to banking service"
                    status_code = 429
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": "Banking Service Error",
                    "message": error_message,
                    "type": "plaid_error",
                    "error_code": getattr(e, 'error_code', None)
                }
            )
            
        except GoogleAPIError as e:
            # Google API errors (Vision, Gmail, etc.)
            logger.error(f"Google API error: {str(e)}")
            
            error_message = "External service error"
            status_code = 502
            
            if hasattr(e, 'code'):
                if e.code == 401:
                    error_message = "Authentication required for Google services"
                    status_code = 401
                elif e.code == 403:
                    error_message = "Access denied to Google services"
                    status_code = 403
                elif e.code == 429:
                    error_message = "Rate limit exceeded for Google services"
                    status_code = 429
            
            return JSONResponse(
                status_code=status_code,
                content={
                    "error": "External Service Error",
                    "message": error_message,
                    "type": "google_api_error"
                }
            )
            
        except FileNotFoundError as e:
            # File operation errors
            logger.error(f"File not found: {str(e)}")
            return JSONResponse(
                status_code=404,
                content={
                    "error": "File Not Found",
                    "message": "Requested file could not be found",
                    "type": "file_error"
                }
            )
            
        except PermissionError as e:
            # File permission errors
            logger.error(f"Permission error: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Permission Denied",
                    "message": "Insufficient permissions to access resource",
                    "type": "permission_error"
                }
            )
            
        except ConnectionError as e:
            # Network/connection errors
            logger.error(f"Connection error: {str(e)}")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service Unavailable",
                    "message": "Unable to connect to external service",
                    "type": "connection_error"
                }
            )
            
        except TimeoutError as e:
            # Timeout errors
            logger.error(f"Timeout error: {str(e)}")
            return JSONResponse(
                status_code=504,
                content={
                    "error": "Gateway Timeout",
                    "message": "Request timed out",
                    "type": "timeout_error"
                }
            )
            
        except ValueError as e:
            # Value/parsing errors
            logger.warning(f"Value error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad Request",
                    "message": "Invalid data format or value",
                    "type": "value_error"
                }
            )
            
        except Exception as e:
            # Catch-all for unexpected errors
            logger.error(
                f"Unhandled exception: {str(e)}",
                exc_info=True,
                extra={
                    "request_url": str(request.url),
                    "request_method": request.method,
                    "traceback": traceback.format_exc()
                }
            )
            
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal Server Error",
                    "message": "An unexpected error occurred",
                    "type": "unknown_error",
                    "request_id": getattr(request.state, 'request_id', None)
                }
            )


def create_error_response(
    status_code: int,
    error_type: str,
    message: str,
    details: Dict[str, Any] = None
) -> JSONResponse:
    """Create standardized error response."""
    content = {
        "error": error_type,
        "message": message,
        "status_code": status_code
    }
    
    if details:
        content["details"] = details
    
    return JSONResponse(status_code=status_code, content=content)


class RetryableError(Exception):
    """Exception for operations that can be retried."""
    
    def __init__(self, message: str, retry_after: int = 60):
        self.message = message
        self.retry_after = retry_after
        super().__init__(self.message)


class BusinessLogicError(Exception):
    """Exception for business logic violations."""
    
    def __init__(self, message: str, error_code: str = None):
        self.message = message
        self.error_code = error_code
        super().__init__(self.message)
