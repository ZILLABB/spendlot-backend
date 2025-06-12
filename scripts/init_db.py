"""
Initialize database with default data.
"""
import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal, engine
from app.models.base import Base
from app.services.categorization_service import CategorizationService
from app.services.data_source_service import DataSourceService
from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

# Configure logging
configure_logging()
logger = get_logger(__name__)


def create_tables():
    """Create all database tables."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")


def initialize_data():
    """Initialize default data."""
    db = SessionLocal()
    try:
        logger.info("Initializing default data...")
        
        # Initialize data sources
        data_source_service = DataSourceService(db)
        data_source_service.initialize_default_sources()
        logger.info("Default data sources initialized")
        
        # Initialize categories
        categorization_service = CategorizationService(db)
        categories = categorization_service.initialize_default_categories()
        logger.info(f"Initialized {len(categories)} default categories")
        
        # Create superuser if it doesn't exist
        user_service = UserService(db)
        superuser = user_service.get_by_email(settings.FIRST_SUPERUSER)
        
        if not superuser:
            superuser_data = UserCreate(
                email=settings.FIRST_SUPERUSER,
                password=settings.FIRST_SUPERUSER_PASSWORD,
                full_name="System Administrator"
            )
            superuser = user_service.create(superuser_data)
            superuser.is_superuser = True
            superuser.is_verified = True
            db.commit()
            logger.info(f"Created superuser: {settings.FIRST_SUPERUSER}")
        else:
            logger.info("Superuser already exists")
        
        logger.info("Default data initialization completed")
        
    except Exception as e:
        logger.error(f"Error initializing data: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()


def main():
    """Main initialization function."""
    try:
        logger.info("Starting database initialization...")
        
        # Create tables
        create_tables()
        
        # Initialize default data
        initialize_data()
        
        logger.info("Database initialization completed successfully!")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
