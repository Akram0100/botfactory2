# ============================================
# BotFactory AI - Celery Configuration
# ============================================

from celery import Celery
from celery.schedules import crontab

from src.core.config import settings

# Create Celery app
celery_app = Celery(
    "botfactory",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "src.tasks.subscription",
        "src.tasks.cleanup",
        "src.tasks.analytics",
    ],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=270,  # 4.5 minutes
    worker_prefetch_multiplier=1,
    worker_concurrency=2,
)

# Periodic tasks (Celery Beat)
celery_app.conf.beat_schedule = {
    # Check subscription expiry every hour
    "check-subscription-expiry": {
        "task": "src.tasks.subscription.check_expiring_subscriptions",
        "schedule": crontab(minute=0),  # Every hour
    },
    
    # Cleanup old chat history daily at 3 AM
    "cleanup-old-chats": {
        "task": "src.tasks.cleanup.cleanup_old_chat_history",
        "schedule": crontab(hour=3, minute=0),
    },
    
    # Reset monthly message counts on 1st of each month
    "reset-message-counts": {
        "task": "src.tasks.subscription.reset_monthly_message_counts",
        "schedule": crontab(day_of_month=1, hour=0, minute=0),
    },
    
    # Aggregate analytics daily at 2 AM
    "aggregate-daily-analytics": {
        "task": "src.tasks.analytics.aggregate_daily_stats",
        "schedule": crontab(hour=2, minute=0),
    },
}
