# ============================================
# BotFactory AI - Bot Manager Service
# ============================================

from typing import Optional, Dict, Type
from enum import Enum

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import settings
from src.core.logging import bot_logger
from src.models.bot import Bot, BotPlatform, BotStatus
from src.services.bots.base import BaseBot
from src.services.bots.telegram import TelegramBot


class BotManager:
    """
    Factory and manager for bot instances.
    Handles bot creation, lifecycle, and webhook management.
    """

    # Platform to bot class mapping
    BOT_CLASSES: Dict[BotPlatform, Type[BaseBot]] = {
        BotPlatform.TELEGRAM: TelegramBot,
        # BotPlatform.WHATSAPP: WhatsAppBot,  # TODO: Implement
        # BotPlatform.INSTAGRAM: InstagramBot,  # TODO: Implement
    }

    def __init__(self, db: AsyncSession):
        self.db = db
        self._bot_cache: Dict[int, BaseBot] = {}

    def get_bot_instance(self, bot: Bot) -> Optional[BaseBot]:
        """
        Get or create bot instance for the given bot model.
        
        Args:
            bot: Bot model instance
            
        Returns:
            Platform-specific bot instance
        """
        # Check cache
        if bot.id in self._bot_cache:
            return self._bot_cache[bot.id]

        # Get bot class for platform
        bot_class = self.BOT_CLASSES.get(bot.platform)
        if not bot_class:
            bot_logger.warning(f"No bot class for platform: {bot.platform}")
            return None

        # Create instance
        instance = bot_class(
            bot_id=bot.id,
            token=bot.token,
            config=bot.settings or {},
        )

        # Cache it
        self._bot_cache[bot.id] = instance

        return instance

    async def get_bot_by_token(self, token: str, platform: BotPlatform) -> Optional[Bot]:
        """
        Get bot by token and platform.
        
        Args:
            token: Bot token
            platform: Bot platform
            
        Returns:
            Bot model if found
        """
        result = await self.db.execute(
            select(Bot).where(
                Bot.token == token,
                Bot.platform == platform,
                Bot.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def validate_and_activate_bot(self, bot: Bot) -> bool:
        """
        Validate bot token and activate the bot.
        
        Args:
            bot: Bot model
            
        Returns:
            True if validation successful
        """
        instance = self.get_bot_instance(bot)
        if not instance:
            return False

        try:
            # Validate token with platform
            is_valid = await instance.validate_token()
            if not is_valid:
                bot.status = BotStatus.ERROR
                bot.error_message = "Token yaroqsiz"
                await self.db.commit()
                return False

            # Get bot info and update
            if hasattr(instance, 'get_bot_info'):
                info = await instance.get_bot_info()
                if info:
                    bot.platform_bot_id = str(info.get('id', ''))
                    # Could also update username, etc.

            # Setup webhook
            webhook_url = self.get_webhook_url(bot)
            await instance.setup_webhook(webhook_url)

            # Activate bot
            bot.status = BotStatus.ACTIVE
            bot.is_active = True
            bot.webhook_url = webhook_url
            bot.error_message = None
            await self.db.commit()

            bot_logger.info(f"Bot activated: {bot.id} ({bot.name})")
            return True

        except Exception as e:
            bot_logger.error(f"Bot activation failed: {e}")
            bot.status = BotStatus.ERROR
            bot.error_message = str(e)
            await self.db.commit()
            return False

    async def deactivate_bot(self, bot: Bot) -> bool:
        """
        Deactivate a bot.
        
        Args:
            bot: Bot model
            
        Returns:
            True if deactivation successful
        """
        try:
            instance = self.get_bot_instance(bot)
            
            # Remove webhook if possible
            if instance and hasattr(instance, 'remove_webhook'):
                await instance.remove_webhook()

            # Update bot status
            bot.status = BotStatus.INACTIVE
            bot.is_active = False
            await self.db.commit()

            # Remove from cache
            if bot.id in self._bot_cache:
                del self._bot_cache[bot.id]

            bot_logger.info(f"Bot deactivated: {bot.id} ({bot.name})")
            return True

        except Exception as e:
            bot_logger.error(f"Bot deactivation failed: {e}")
            return False

    def get_webhook_url(self, bot: Bot) -> str:
        """
        Generate webhook URL for a bot.
        
        Args:
            bot: Bot model
            
        Returns:
            Webhook URL
        """
        base_url = settings.APP_URL or "https://api.botfactory.uz"
        
        if bot.platform == BotPlatform.TELEGRAM:
            return f"{base_url}/api/v1/webhooks/telegram/{bot.token}"
        elif bot.platform == BotPlatform.WHATSAPP:
            return f"{base_url}/api/v1/webhooks/whatsapp"
        elif bot.platform == BotPlatform.INSTAGRAM:
            return f"{base_url}/api/v1/webhooks/instagram"
        
        return f"{base_url}/api/v1/webhooks/{bot.platform.value}/{bot.id}"

    async def process_webhook(
        self,
        bot: Bot,
        payload: Dict,
    ) -> bool:
        """
        Process incoming webhook for a bot.
        
        Args:
            bot: Bot model
            payload: Webhook payload
            
        Returns:
            True if processed successfully
        """
        try:
            instance = self.get_bot_instance(bot)
            if not instance:
                return False

            # Let the bot handle the webhook
            await instance.handle_webhook(payload)
            return True

        except Exception as e:
            bot_logger.error(f"Webhook processing error for bot {bot.id}: {e}")
            return False

    def clear_cache(self, bot_id: Optional[int] = None) -> None:
        """Clear bot instance cache."""
        if bot_id:
            self._bot_cache.pop(bot_id, None)
        else:
            self._bot_cache.clear()


# Convenience function
async def get_bot_manager(db: AsyncSession) -> BotManager:
    """Get bot manager instance."""
    return BotManager(db)
