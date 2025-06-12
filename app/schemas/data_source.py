"""
Data source-related Pydantic schemas.
"""
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class DataSourceBase(BaseModel):
    """Base data source schema with common fields."""
    
    name: str = Field(..., description="Data source name")
    display_name: str = Field(..., description="Display name")
    description: Optional[str] = Field(None, description="Data source description")
    source_type: str = Field(..., description="Source type")


class DataSourceCreate(DataSourceBase):
    """Schema for creating a new data source."""
    
    is_active: bool = Field(default=True, description="Active status")
    auto_process: bool = Field(default=True, description="Auto-process enabled")
    requires_verification: bool = Field(default=False, description="Requires verification")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration settings")


class DataSourceUpdate(BaseModel):
    """Schema for updating data source information."""
    
    display_name: Optional[str] = Field(None, description="Display name")
    description: Optional[str] = Field(None, description="Data source description")
    is_active: Optional[bool] = Field(None, description="Active status")
    auto_process: Optional[bool] = Field(None, description="Auto-process enabled")
    requires_verification: Optional[bool] = Field(None, description="Requires verification")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration settings")


class DataSourceInDB(DataSourceBase):
    """Schema for data source data stored in database."""
    
    id: int = Field(..., description="Data source ID")
    is_active: bool = Field(..., description="Active status")
    is_system: bool = Field(..., description="System data source")
    auto_process: bool = Field(..., description="Auto-process enabled")
    requires_verification: bool = Field(..., description="Requires verification")
    config: Optional[Dict[str, Any]] = Field(None, description="Configuration settings")
    api_endpoint: Optional[str] = Field(None, description="API endpoint")
    webhook_url: Optional[str] = Field(None, description="Webhook URL")
    
    class Config:
        from_attributes = True


class DataSource(DataSourceInDB):
    """Public data source schema."""
    
    pass
