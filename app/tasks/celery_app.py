"""
Celery application configuration.
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "spendlot",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.ocr_tasks",
        "app.tasks.gmail_tasks",
        "app.tasks.plaid_tasks",
        "app.tasks.sms_tasks",
        "app.tasks.categorization_tasks",
        "app.tasks.duplicate_detection_tasks"
    ]
)

# Configure Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Periodic tasks
celery_app.conf.beat_schedule = {
    # Gmail polling every hour
    "poll-gmail-receipts": {
        "task": "app.tasks.gmail_tasks.poll_gmail_receipts",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Plaid transaction sync every 4 hours
    "sync-plaid-transactions": {
        "task": "app.tasks.plaid_tasks.sync_all_plaid_transactions",
        "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
    },
    
    # Process pending receipts every 5 minutes
    "process-pending-receipts": {
        "task": "app.tasks.ocr_tasks.process_pending_receipts",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
    
    # Categorize uncategorized transactions daily
    "categorize-transactions": {
        "task": "app.tasks.categorization_tasks.categorize_uncategorized_transactions",
        "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
    },
    
    # Detect duplicates daily
    "detect-duplicates": {
        "task": "app.tasks.duplicate_detection_tasks.detect_all_duplicates",
        "schedule": crontab(hour=3, minute=0),  # Daily at 3 AM
    },

    # Process pending SMS receipts every 10 minutes
    "process-pending-sms": {
        "task": "app.tasks.sms_tasks.process_pending_sms_receipts",
        "schedule": crontab(minute="*/10"),  # Every 10 minutes
    },
}

if __name__ == "__main__":
    celery_app.start()
