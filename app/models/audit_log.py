"""
Audit log model for tracking data changes and user actions.
"""
from sqlalchemy import Column, String, Text, Integer, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class AuditLog(BaseModel):
    """Audit log model for tracking user actions and data changes."""
    
    __tablename__ = "audit_logs"
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    
    # Action information
    action = Column(String(100), nullable=False, index=True)  # create, update, delete, login, etc.
    entity_type = Column(String(100), nullable=False, index=True)  # user, receipt, transaction, etc.
    entity_id = Column(Integer, nullable=True, index=True)
    
    # Request information
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(Text, nullable=True)
    request_id = Column(String(100), nullable=True, index=True)
    
    # Change details
    old_values = Column(JSON, nullable=True)  # Previous values
    new_values = Column(JSON, nullable=True)  # New values
    changes = Column(JSON, nullable=True)     # Summary of changes
    
    # Additional context
    description = Column(Text, nullable=True)
    extra_metadata = Column(JSON, nullable=True)
    
    # Status
    status = Column(String(50), default="success", nullable=False)  # success, failed, pending
    error_message = Column(Text, nullable=True)
    
    # Timestamp (override to use specific field name)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', entity='{self.entity_type}')>"
