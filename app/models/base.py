"""
Base model with common fields and functionality.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.ext.declarative import as_declarative, declared_attr


@as_declarative()
class Base:
    """Base class for all database models."""
    
    id: Any
    __name__: str
    
    # Generate __tablename__ automatically
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()


class TimestampMixin:
    """Mixin to add timestamp fields to models."""
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class BaseModel(Base, TimestampMixin):
    """Base model with ID and timestamps."""
    
    __abstract__ = True
    
    id = Column(Integer, primary_key=True, index=True)
    
    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
