"""
Data source service for managing data sources.
"""
from typing import Optional
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.schemas.data_source import DataSourceCreate, DataSourceUpdate
from app.services.base_service import BaseService


class DataSourceService(BaseService[DataSource, DataSourceCreate, DataSourceUpdate]):
    """Service for data source management operations."""
    
    def __init__(self, db: Session):
        super().__init__(DataSource, db)
    
    def get_by_name(self, name: str) -> Optional[DataSource]:
        """Get data source by name."""
        return self.db.query(DataSource).filter(DataSource.name == name).first()
    
    def get_by_type(self, source_type: str) -> list[DataSource]:
        """Get data sources by type."""
        return self.db.query(DataSource).filter(DataSource.source_type == source_type).all()
    
    def create_manual_upload_source(self) -> DataSource:
        """Create manual upload data source."""
        source = DataSource(
            name="manual_upload",
            display_name="Manual Upload",
            description="Receipts uploaded manually by users",
            source_type="manual",
            is_active=True,
            is_system=True,
            auto_process=True,
            requires_verification=False
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source
    
    def create_gmail_source(self) -> DataSource:
        """Create Gmail data source."""
        source = DataSource(
            name="gmail_receipts",
            display_name="Gmail Receipts",
            description="Receipts extracted from Gmail emails",
            source_type="gmail",
            is_active=True,
            is_system=True,
            auto_process=True,
            requires_verification=True,
            config={
                "search_query": "receipt OR invoice",
                "max_results": 50,
                "check_interval": 3600  # 1 hour
            }
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source
    
    def create_plaid_source(self) -> DataSource:
        """Create Plaid data source."""
        source = DataSource(
            name="plaid_transactions",
            display_name="Bank Transactions",
            description="Transactions synced from bank accounts via Plaid",
            source_type="plaid",
            is_active=True,
            is_system=True,
            auto_process=True,
            requires_verification=False,
            config={
                "sync_interval": 3600,  # 1 hour
                "transaction_days": 30
            }
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source
    
    def create_sms_source(self) -> DataSource:
        """Create SMS data source."""
        source = DataSource(
            name="sms_receipts",
            display_name="SMS Receipts",
            description="Receipts received via SMS",
            source_type="sms",
            is_active=True,
            is_system=True,
            auto_process=True,
            requires_verification=True,
            webhook_url="/webhooks/twilio/sms",
            config={
                "keywords": ["receipt", "purchase", "transaction", "payment"]
            }
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source
    
    def initialize_default_sources(self) -> None:
        """Initialize default data sources if they don't exist."""
        sources = [
            ("manual_upload", self.create_manual_upload_source),
            ("gmail_receipts", self.create_gmail_source),
            ("plaid_transactions", self.create_plaid_source),
            ("sms_receipts", self.create_sms_source)
        ]
        
        for name, create_func in sources:
            if not self.get_by_name(name):
                create_func()
