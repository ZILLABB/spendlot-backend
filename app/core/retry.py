"""
Retry mechanisms for external API calls and operations.
"""
import asyncio
import time
from typing import Callable, Any, List, Type, Optional
from functools import wraps
import random

from app.core.logging import get_logger

logger = get_logger(__name__)


class RetryConfig:
    """Configuration for retry behavior."""
    
    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: List[Type[Exception]] = None
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [
            ConnectionError,
            TimeoutError,
            OSError
        ]


def retry_with_backoff(config: RetryConfig = None):
    """Decorator for retrying functions with exponential backoff."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.warning(f"Non-retryable exception in {func.__name__}: {str(e)}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts - 1:
                        break
                    
                    # Calculate delay
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    time.sleep(delay)
            
            # All attempts failed
            logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


def async_retry_with_backoff(config: RetryConfig = None):
    """Decorator for retrying async functions with exponential backoff."""
    if config is None:
        config = RetryConfig()
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                    
                except Exception as e:
                    last_exception = e
                    
                    # Check if exception is retryable
                    if not any(isinstance(e, exc_type) for exc_type in config.retryable_exceptions):
                        logger.warning(f"Non-retryable exception in {func.__name__}: {str(e)}")
                        raise
                    
                    # Don't retry on last attempt
                    if attempt == config.max_attempts - 1:
                        break
                    
                    # Calculate delay
                    delay = min(
                        config.base_delay * (config.exponential_base ** attempt),
                        config.max_delay
                    )
                    
                    # Add jitter to prevent thundering herd
                    if config.jitter:
                        delay *= (0.5 + random.random() * 0.5)
                    
                    logger.warning(
                        f"Attempt {attempt + 1}/{config.max_attempts} failed for {func.__name__}: {str(e)}. "
                        f"Retrying in {delay:.2f} seconds..."
                    )
                    
                    await asyncio.sleep(delay)
            
            # All attempts failed
            logger.error(f"All {config.max_attempts} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


class CircuitBreaker:
    """Circuit breaker pattern implementation."""
    
    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        expected_exception: Type[Exception] = Exception
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception
        
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    def __call__(self, func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            if self.state == "OPEN":
                if self._should_attempt_reset():
                    self.state = "HALF_OPEN"
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
                
            except self.expected_exception as e:
                self._on_failure()
                raise
        
        return wrapper
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        return (
            self.last_failure_time and
            time.time() - self.last_failure_time >= self.recovery_timeout
        )
    
    def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0
        self.state = "CLOSED"
    
    def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")


# Predefined retry configurations for different services
PLAID_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=2.0,
    max_delay=30.0,
    retryable_exceptions=[ConnectionError, TimeoutError]
)

GMAIL_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=1.0,
    max_delay=15.0,
    retryable_exceptions=[ConnectionError, TimeoutError]
)

OCR_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay=3.0,
    max_delay=10.0,
    retryable_exceptions=[ConnectionError, TimeoutError]
)

DATABASE_RETRY_CONFIG = RetryConfig(
    max_attempts=3,
    base_delay=0.5,
    max_delay=5.0,
    retryable_exceptions=[ConnectionError, OSError]
)
