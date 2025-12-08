# ============================================
# BotFactory AI - Gemini AI Service
# ============================================

from typing import Optional, List, Dict, Any
import asyncio

import google.generativeai as genai

from src.core.config import settings
from src.core.logging import ai_logger
from src.core.exceptions import AIServiceError


class GeminiService:
    """Google Gemini AI service for chat generation."""

    def __init__(self):
        self._configured = False
        self._model = None

    def _configure(self):
        """Configure Gemini API."""
        if self._configured:
            return
        
        if not settings.GOOGLE_API_KEY:
            raise AIServiceError("GOOGLE_API_KEY sozlanmagan")
        
        genai.configure(api_key=settings.GOOGLE_API_KEY)
        self._model = genai.GenerativeModel(settings.AI_MODEL)
        self._configured = True
        ai_logger.info(f"Gemini configured with model: {settings.AI_MODEL}")

    async def generate_response(
        self,
        message: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        language: str = "uz",
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate AI response for user message.
        
        Args:
            message: User's message
            context: Relevant context from knowledge base
            history: Chat history [(role, content), ...]
            system_prompt: Custom system prompt
            language: Response language (uz/ru/en)
            temperature: Creativity level (0-2)
            max_tokens: Maximum response length
            
        Returns:
            Generated response text
        """
        try:
            self._configure()

            # Build the full prompt
            full_prompt = self._build_prompt(
                message=message,
                context=context,
                history=history,
                system_prompt=system_prompt,
                language=language,
            )

            # Generate response
            generation_config = genai.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens,
            )

            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._model.generate_content(
                    full_prompt,
                    generation_config=generation_config,
                )
            )

            if not response.text:
                ai_logger.warning("Empty response from Gemini")
                return self._get_fallback_response(language)

            ai_logger.debug(f"Generated response: {response.text[:100]}...")
            return response.text

        except Exception as e:
            ai_logger.error(f"Gemini error: {e}")
            raise AIServiceError(f"AI xatosi: {str(e)}")

    def _build_prompt(
        self,
        message: str,
        context: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None,
        language: str = "uz",
    ) -> str:
        """Build the full prompt for Gemini."""
        
        # Default system prompts by language
        default_prompts = {
            "uz": """Sen BotFactory AI yordamchisissan. Foydalanuvchilarga professional va samimiy tarzda yordam berasan.

Qoidalar:
- O'zbek tilida javob ber
- Qisqa va aniq javoblar ber
- Foydalanuvchiga yordam berishga harakat qil
- Noaniq savollar uchun aniqlik so'ra""",
            
            "ru": """Ты AI-помощник BotFactory. Помогай пользователям профессионально и дружелюбно.

Правила:
- Отвечай на русском языке
- Давай краткие и точные ответы
- Старайся помочь пользователю
- При неясных вопросах проси уточнения""",
            
            "en": """You are BotFactory AI assistant. Help users professionally and friendly.

Rules:
- Respond in English
- Give concise and accurate answers
- Try to help the user
- Ask for clarification on unclear questions""",
        }

        parts = []

        # System prompt
        prompt = system_prompt or default_prompts.get(language, default_prompts["uz"])
        parts.append(f"SYSTEM: {prompt}")

        # Context from knowledge base
        if context:
            parts.append(f"\nKONTEKST (bilimlar bazasidan):\n{context}")

        # Chat history
        if history:
            parts.append("\nOLDINGI SUHBAT:")
            for msg in history[-10:]:  # Last 10 messages
                role = "Foydalanuvchi" if msg.get("role") == "user" else "Yordamchi"
                parts.append(f"{role}: {msg.get('content', '')}")

        # Current message
        parts.append(f"\nFoydalanuvchi: {message}")
        parts.append("\nYordamchi:")

        return "\n".join(parts)

    def _get_fallback_response(self, language: str) -> str:
        """Get fallback response when AI fails."""
        fallbacks = {
            "uz": "Kechirasiz, hozir javob bera olmayapman. Iltimos, keyinroq qayta urinib ko'ring.",
            "ru": "Извините, не могу ответить сейчас. Пожалуйста, попробуйте позже.",
            "en": "Sorry, I can't respond right now. Please try again later.",
        }
        return fallbacks.get(language, fallbacks["uz"])

    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate text embedding for semantic search.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        try:
            self._configure()
            
            # Use embedding model
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: genai.embed_content(
                    model="models/embedding-001",
                    content=text,
                    task_type="retrieval_document",
                )
            )
            
            return result["embedding"]
            
        except Exception as e:
            ai_logger.error(f"Embedding error: {e}")
            raise AIServiceError(f"Embedding xatosi: {str(e)}")


# Global instance
gemini_service = GeminiService()
