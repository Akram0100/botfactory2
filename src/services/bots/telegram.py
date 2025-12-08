# ============================================
# BotFactory AI - Telegram Bot Service
# ============================================

from typing import Dict, Any, Optional
import aiohttp

from src.services.bots.base import BaseBot, BotMessage, BotResponse
from src.core.logging import bot_logger
from src.core.exceptions import BotPlatformError


class TelegramBot(BaseBot):
    """Telegram bot implementation."""

    TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/{method}"

    @property
    def platform(self) -> str:
        return "telegram"

    def _get_api_url(self, method: str) -> str:
        """Get Telegram API URL for method."""
        return self.TELEGRAM_API_URL.format(token=self.token, method=method)

    async def _make_request(
        self,
        method: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make request to Telegram API."""
        url = self._get_api_url(method)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                
                if not result.get("ok"):
                    error_desc = result.get("description", "Unknown error")
                    bot_logger.error(f"Telegram API error: {error_desc}")
                    raise BotPlatformError("Telegram", error_desc)
                
                return result.get("result", {})

    async def send_message(
        self,
        recipient_id: str,
        response: BotResponse,
    ) -> bool:
        """Send message to Telegram user."""
        try:
            # Send text message
            data = {
                "chat_id": recipient_id,
                "text": response.text,
                "parse_mode": "HTML",
            }

            # Add keyboard if buttons provided
            if response.buttons:
                keyboard = {
                    "inline_keyboard": [
                        [
                            {
                                "text": btn.get("text", ""),
                                "callback_data": btn.get("callback_data", ""),
                            }
                            for btn in row
                        ]
                        for row in self._chunk_buttons(response.buttons)
                    ]
                }
                data["reply_markup"] = keyboard

            await self._make_request("sendMessage", data)

            # Send image if provided
            if response.image_url:
                await self._make_request("sendPhoto", {
                    "chat_id": recipient_id,
                    "photo": response.image_url,
                })

            # Send audio if provided
            if response.audio_url:
                await self._make_request("sendVoice", {
                    "chat_id": recipient_id,
                    "voice": response.audio_url,
                })

            return True

        except Exception as e:
            bot_logger.error(f"Failed to send Telegram message: {e}")
            return False

    def _chunk_buttons(self, buttons: list, size: int = 2) -> list:
        """Chunk buttons into rows."""
        return [buttons[i:i + size] for i in range(0, len(buttons), size)]

    async def send_typing_indicator(self, recipient_id: str) -> None:
        """Send typing indicator to user."""
        try:
            await self._make_request("sendChatAction", {
                "chat_id": recipient_id,
                "action": "typing",
            })
        except Exception as e:
            bot_logger.warning(f"Failed to send typing indicator: {e}")

    async def handle_webhook(self, payload: Dict[str, Any]) -> None:
        """Handle incoming Telegram webhook."""
        # Extract message
        message_data = payload.get("message") or payload.get("edited_message")
        callback_query = payload.get("callback_query")

        if callback_query:
            # Handle button callback
            await self._handle_callback(callback_query)
        elif message_data:
            # Handle message
            await self._handle_message(message_data)

    async def _handle_message(self, message_data: Dict[str, Any]) -> None:
        """Handle incoming message."""
        chat = message_data.get("chat", {})
        user = message_data.get("from", {})
        
        # Build BotMessage
        message = BotMessage(
            sender_id=str(chat.get("id")),
            text=message_data.get("text"),
            metadata={
                "message_id": message_data.get("message_id"),
                "username": user.get("username"),
                "first_name": user.get("first_name"),
                "last_name": user.get("last_name"),
                "chat_type": chat.get("type"),
            },
        )

        # Handle voice message
        voice = message_data.get("voice")
        if voice:
            file_id = voice.get("file_id")
            # TODO: Download and transcribe voice
            message.audio_url = f"file:{file_id}"

        # Handle photo
        photos = message_data.get("photo", [])
        if photos:
            # Get highest resolution photo
            photo = max(photos, key=lambda x: x.get("file_size", 0))
            message.image_url = f"file:{photo.get('file_id')}"

        # Show typing indicator
        if self.get_setting("enable_typing_indicator", True):
            await self.send_typing_indicator(message.sender_id)

        # Process message
        response = await self.process_message(message)

        # Send response
        await self.send_message(message.sender_id, response)

    async def _handle_callback(self, callback_query: Dict[str, Any]) -> None:
        """Handle callback query from inline keyboard."""
        user = callback_query.get("from", {})
        data = callback_query.get("data", "")
        message = callback_query.get("message", {})
        
        bot_logger.info(f"Callback from {user.get('id')}: {data}")
        
        # Answer callback query
        await self._make_request("answerCallbackQuery", {
            "callback_query_id": callback_query.get("id"),
        })

        # TODO: Handle specific callbacks

    async def validate_token(self) -> bool:
        """Validate bot token with Telegram."""
        try:
            result = await self._make_request("getMe")
            bot_logger.info(f"Telegram bot validated: @{result.get('username')}")
            return True
        except Exception as e:
            bot_logger.error(f"Token validation failed: {e}")
            return False

    async def setup_webhook(self, webhook_url: str) -> bool:
        """Setup webhook with Telegram."""
        try:
            await self._make_request("setWebhook", {
                "url": webhook_url,
                "allowed_updates": ["message", "edited_message", "callback_query"],
            })
            bot_logger.info(f"Telegram webhook set: {webhook_url}")
            return True
        except Exception as e:
            bot_logger.error(f"Failed to set webhook: {e}")
            return False

    async def get_bot_info(self) -> Dict[str, Any]:
        """Get bot information from Telegram."""
        return await self._make_request("getMe")
