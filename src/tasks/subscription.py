# ============================================
# BotFactory AI - Subscription Tasks
# ============================================

from datetime import datetime, timedelta

from src.tasks.celery_app import celery_app
from src.core.logging import task_logger


@celery_app.task(name="src.tasks.subscription.check_expiring_subscriptions")
def check_expiring_subscriptions():
    """
    Check for subscriptions expiring in the next 3 days
    and send reminder notifications.
    """
    task_logger.info("Checking expiring subscriptions...")
    
    # TODO: Implement actual logic
    # 1. Query users with subscription expiring in 3 days
    # 2. Send Telegram/email notification
    # 3. Log results
    
    task_logger.info("Expiring subscriptions check complete")
    return {"checked": True}


@celery_app.task(name="src.tasks.subscription.reset_monthly_message_counts")
def reset_monthly_message_counts():
    """
    Reset monthly message counts for all users.
    Runs on the 1st of each month.
    """
    task_logger.info("Resetting monthly message counts...")
    
    # TODO: Implement actual logic
    # UPDATE users SET messages_this_month = 0, messages_reset_at = NOW()
    
    task_logger.info("Monthly message counts reset complete")
    return {"reset": True}


@celery_app.task(name="src.tasks.subscription.process_subscription_activation")
def process_subscription_activation(user_id: int, subscription_type: str, months: int):
    """
    Process subscription activation after successful payment.
    """
    task_logger.info(f"Activating subscription for user {user_id}: {subscription_type} for {months} months")
    
    # TODO: Implement actual logic
    # 1. Update user subscription type and expiry
    # 2. Send confirmation notification
    # 3. Log the activation
    
    return {"activated": True, "user_id": user_id}


@celery_app.task(name="src.tasks.subscription.send_expiry_reminder")
def send_expiry_reminder(user_id: int, days_remaining: int):
    """
    Send subscription expiry reminder to user.
    """
    task_logger.info(f"Sending expiry reminder to user {user_id}: {days_remaining} days remaining")
    
    # TODO: Implement actual notification sending
    
    return {"sent": True}
