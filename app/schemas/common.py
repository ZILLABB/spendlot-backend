"""
Common Pydantic schemas used across the application.
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class PaginatedResponse(BaseModel, Generic[DataT]):
    """Generic paginated response schema."""
    
    items: List[DataT]
    total: int = Field(..., description="Total number of items")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Number of items per page")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")


class HealthCheck(BaseModel):
    """Health check response schema."""
    
    status: str = Field(..., description="Service status")
    timestamp: str = Field(..., description="Current timestamp")
    version: str = Field(..., description="Application version")
    database: str = Field(..., description="Database connection status")
    redis: str = Field(..., description="Redis connection status")


class ErrorResponse(BaseModel):
    """Error response schema."""
    
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Any] = Field(None, description="Additional error details")


class SuccessResponse(BaseModel):
    """Success response schema."""
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    data: Optional[Any] = Field(None, description="Response data")


class FileUploadResponse(BaseModel):
    """File upload response schema."""
    
    filename: str = Field(..., description="Uploaded filename")
    file_path: str = Field(..., description="File storage path")
    file_size: int = Field(..., description="File size in bytes")
    mime_type: str = Field(..., description="File MIME type")
    upload_id: str = Field(..., description="Unique upload identifier")
