# ============================================
# BotFactory AI - Base Bot Service
# ============================================

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List

from pydantic import BaseModel

from src.core.logging import bot_logger


class BotMessage(BaseModel):
    """Incoming message from bot platform."""
    sender_id: str
    text: Optional[str] = None
    audio_url: Optional[str] = None
    image_url: Optional[str] = None
    document_url: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    contact: Optional[Dict[str, str]] = None
    metadata: Dict[str, Any] = {}


class BotResponse(BaseModel):
    """Response to send to user."""
    text: str
    buttons: List[Dict[str, Any]] = []
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    document_url: Optional[str] = None


class BaseBot(ABC):
    """
    Abstract base class for all bot implementations.
    Uses Abstract Factory pattern for platform-specific bots.
    """

    def __init__(
        self,
        bot_id: int,
        token: str,
        config: Dict[str, Any],
    ):
        self.bot_id = bot_id
        self.token = token
        self.config = config
        self._ai_service = None
        self._knowledge_service = None

    @property
    @abstractmethod
    def platform(self) -> str:
        """Return platform name."""
        pass

    @abstractmethod
    async def send_message(
        self,
        recipient_id: str,
        response: BotResponse,
    ) -> bool:
        """
        Send message to user.
        
        Args:
            recipient_id: Platform-specific user ID
            response: Response to send
            
        Returns:
            True if message sent successfully
        """
        pass

    @abstractmethod
    async def send_typing_indicator(self, recipient_id: str) -> None:
        """Show typing indicator to user."""
        pass

    @abstractmethod
    async def handle_webhook(self, payload: Dict[str, Any]) -> None:
        """
        Handle incoming webhook from platform.
        
        Args:
            payload: Raw webhook payload
        """
        pass

    @abstractmethod
    async def validate_token(self) -> bool:
        """
        Validate bot token with platform.
        
        Returns:
            True if token is valid
        """
        pass

    @abstractmethod
    async def setup_webhook(self, webhook_url: str) -> bool:
        """
        Setup webhook URL with platform.
        
        Args:
            webhook_url: URL to receive webhooks
            
        Returns:
            True if webhook set up successfully
        """
        pass

    async def process_message(self, message: BotMessage) -> BotResponse:
        """
        Process incoming message and generate response.
        This is the common logic shared by all platforms.
        
        Args:
            message: Incoming message
            
        Returns:
            Bot response
        """
        from src.services.ai.gemini import gemini_service

        try:
            # Log incoming message
            bot_logger.info(
                f"[{self.platform}] Message from {message.sender_id}: "
                f"{message.text[:50] if message.text else '[non-text]'}..."
            )

            # Get settings
            language = self.config.get("language", "uz")
            system_prompt = self.config.get("system_prompt")
            temperature = self.config.get("temperature", 0.7)
            max_tokens = self.config.get("max_tokens", 1000)

            # Get context from knowledge base
            context = await self._get_knowledge_context(message.text or "")

            # Get chat history
            history = await self._get_chat_history(message.sender_id)

            # Generate AI response
            response_text = await gemini_service.generate_response(
                message=message.text or "",
                context=context,
                history=history,
                system_prompt=system_prompt,
                language=language,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Save to chat history
            await self._save_chat_history(message, response_text)

            return BotResponse(text=response_text)

        except Exception as e:
            bot_logger.error(f"[{self.platform}] Processing error: {e}")
            fallback = self.config.get(
                "fallback_message",
                "Kechirasiz, xatolik yuz berdi. Qayta urinib ko'ring."
            )
            return BotResponse(text=fallback)

    async def _get_knowledge_context(self, query: str) -> Optional[str]:
        """Get relevant context from knowledge base."""
        # TODO: Implement semantic search in knowledge base
        return None

    async def _get_chat_history(
        self,
        user_id: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """Get recent chat history for user."""
        # TODO: Implement chat history retrieval
        return []

    async def _save_chat_history(
        self,
        message: BotMessage,
        response: str,
    ) -> None:
        """Save message and response to chat history."""
        # TODO: Implement chat history saving
        pass

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting with fallback."""
        return self.config.get(key, default)
