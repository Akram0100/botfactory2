# ============================================
# BotFactory AI - Chat Service
# ============================================

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.logging import bot_logger
from src.models.bot import Bot
from src.models.chat import ChatHistory, MessageType, MessageRole
from src.models.knowledge import KnowledgeBase, KnowledgeSourceType
from src.services.ai.gemini import gemini_service


class ChatService:
    """
    Service for processing chat messages and generating AI responses.
    Handles context management, knowledge base search, and history.
    """

    def __init__(self, db: AsyncSession, bot: Bot):
        self.db = db
        self.bot = bot
        self.settings = bot.settings or {}

    async def process_message(
        self,
        platform_user_id: str,
        message_text: str,
        message_type: MessageType = MessageType.TEXT,
        media_url: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        Process incoming message and generate AI response.
        
        Args:
            platform_user_id: User ID on the platform
            message_text: Message content
            message_type: Type of message (text, voice, etc.)
            media_url: URL to media if applicable
            session_id: Session ID for context grouping
            
        Returns:
            AI-generated response text
        """
        try:
            # Get or create session
            if not session_id:
                session_id = await self._get_or_create_session(platform_user_id)

            # Save incoming message
            await self._save_message(
                platform_user_id=platform_user_id,
                role=MessageRole.USER,
                content=message_text,
                message_type=message_type,
                media_url=media_url,
                session_id=session_id,
            )

            # Get chat history for context
            history = await self._get_chat_history(platform_user_id, limit=10)

            # Search knowledge base for relevant context
            context = await self._search_knowledge_base(message_text)

            # Get bot configuration
            system_prompt = self.settings.get("system_prompt") or self.bot.system_prompt
            language = self.bot.language.value if self.bot.language else "uz"
            temperature = self.settings.get("temperature", 0.7)
            max_tokens = self.settings.get("max_tokens", 1000)

            # Generate AI response
            response = await gemini_service.generate_response(
                message=message_text,
                context=context,
                history=history,
                system_prompt=system_prompt,
                language=language,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Save bot response
            await self._save_message(
                platform_user_id=platform_user_id,
                role=MessageRole.ASSISTANT,
                content=response,
                message_type=MessageType.TEXT,
                session_id=session_id,
                context_ids=await self._get_context_ids(message_text),
            )

            # Update bot statistics
            await self._update_bot_stats()

            bot_logger.info(
                f"Chat processed for bot {self.bot.id}: "
                f"user={platform_user_id}, response_len={len(response)}"
            )

            return response

        except Exception as e:
            bot_logger.error(f"Chat processing error: {e}")
            return self._get_fallback_response()

    async def _get_or_create_session(self, platform_user_id: str) -> str:
        """Get existing session or create new one."""
        # Look for recent session (within 30 minutes)
        thirty_min_ago = datetime.utcnow() - timedelta(minutes=30)
        
        result = await self.db.execute(
            select(ChatHistory.session_id)
            .where(
                and_(
                    ChatHistory.bot_id == self.bot.id,
                    ChatHistory.platform_user_id == platform_user_id,
                    ChatHistory.created_at > thirty_min_ago,
                )
            )
            .order_by(ChatHistory.created_at.desc())
            .limit(1)
        )
        
        existing = result.scalar_one_or_none()
        if existing:
            return existing
        
        # Create new session ID
        import uuid
        return str(uuid.uuid4())

    async def _save_message(
        self,
        platform_user_id: str,
        role: MessageRole,
        content: str,
        message_type: MessageType,
        media_url: Optional[str] = None,
        session_id: Optional[str] = None,
        context_ids: Optional[List[int]] = None,
    ) -> ChatHistory:
        """Save message to chat history."""
        message = ChatHistory(
            bot_id=self.bot.id,
            platform_user_id=platform_user_id,
            session_id=session_id,
            message_type=message_type,
            role=role,
            content=content,
            media_url=media_url,
            context_ids=context_ids or [],
        )
        
        self.db.add(message)
        await self.db.commit()
        await self.db.refresh(message)
        
        return message

    async def _get_chat_history(
        self,
        platform_user_id: str,
        limit: int = 10,
    ) -> List[Dict[str, str]]:
        """Get recent chat history for context."""
        result = await self.db.execute(
            select(ChatHistory)
            .where(
                and_(
                    ChatHistory.bot_id == self.bot.id,
                    ChatHistory.platform_user_id == platform_user_id,
                )
            )
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        
        messages = result.scalars().all()
        
        # Convert to format expected by AI
        history = []
        for msg in reversed(messages):
            history.append({
                "role": "user" if msg.role == MessageRole.USER else "assistant",
                "content": msg.content,
            })
        
        return history

    async def _search_knowledge_base(
        self,
        query: str,
        limit: int = 3,
    ) -> Optional[str]:
        """Search knowledge base for relevant context."""
        # Simple text search (TODO: implement semantic search with embeddings)
        result = await self.db.execute(
            select(KnowledgeBase)
            .where(
                and_(
                    KnowledgeBase.bot_id == self.bot.id,
                    KnowledgeBase.is_active == True,
                    KnowledgeBase.content.ilike(f"%{query[:50]}%"),
                )
            )
            .limit(limit)
        )
        
        items = result.scalars().all()
        
        if not items:
            return None
        
        # Build context string
        context_parts = []
        for item in items:
            if item.source_type == KnowledgeSourceType.FAQ:
                context_parts.append(f"Savol: {item.question}\nJavob: {item.answer}")
            elif item.source_type == KnowledgeSourceType.PRODUCT:
                data = item.extra_data or {}
                context_parts.append(
                    f"Mahsulot: {item.title}\n"
                    f"Tavsif: {item.content}\n"
                    f"Narx: {data.get('price', 'N/A')} so'm"
                )
            else:
                context_parts.append(f"{item.title}: {item.content[:500]}")
        
        return "\n\n---\n\n".join(context_parts)

    async def _get_context_ids(self, query: str) -> List[int]:
        """Get IDs of knowledge base items used for context."""
        result = await self.db.execute(
            select(KnowledgeBase.id)
            .where(
                and_(
                    KnowledgeBase.bot_id == self.bot.id,
                    KnowledgeBase.is_active == True,
                    KnowledgeBase.content.ilike(f"%{query[:50]}%"),
                )
            )
            .limit(3)
        )
        return list(result.scalars().all())

    async def _update_bot_stats(self) -> None:
        """Update bot message statistics."""
        self.bot.total_messages = (self.bot.total_messages or 0) + 1
        self.bot.last_message_at = datetime.utcnow()
        await self.db.commit()

    def _get_fallback_response(self) -> str:
        """Get fallback response when AI fails."""
        fallback = self.settings.get("fallback_message")
        if fallback:
            return fallback
        
        language = self.bot.language.value if self.bot.language else "uz"
        fallbacks = {
            "uz": "Kechirasiz, hozir javob bera olmayapman. Iltimos, keyinroq qayta urinib ko'ring.",
            "ru": "Извините, не могу ответить сейчас. Попробуйте позже.",
            "en": "Sorry, I can't respond right now. Please try again later.",
        }
        return fallbacks.get(language, fallbacks["uz"])


# Convenience function
async def get_chat_service(db: AsyncSession, bot: Bot) -> ChatService:
    """Get chat service instance for a bot."""
    return ChatService(db, bot)
