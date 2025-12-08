# ============================================
# BotFactory AI - Webhooks API (Updated)
# ============================================

import base64
from typing import Any

from fastapi import APIRouter, Request, HTTPException, status, Header
from sqlalchemy import select

from src.db.session import async_session_factory
from src.core.config import settings
from src.core.logging import bot_logger, payment_logger
from src.models.bot import Bot, BotPlatform, BotStatus
from src.models.chat import MessageType
from src.services.chat import ChatService
from src.services.bots.telegram import TelegramBot
from src.services.bots.base import BotResponse
from src.services.payments import payme_provider, click_provider

router = APIRouter(prefix="/webhooks", tags=["Webhooks"])


# ===========================================
# Telegram Webhooks
# ===========================================

@router.get("/telegram/{bot_token}")
async def telegram_webhook_verify(bot_token: str):
    """Telegram webhook verification."""
    return {"ok": True}


@router.post("/telegram/{bot_token}")
async def telegram_webhook(
    bot_token: str,
    request: Request,
):
    """
    Telegram webhook handler.
    Receives updates from Telegram Bot API and processes with AI.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    async with async_session_factory() as db:
        # Find bot by token
        result = await db.execute(
            select(Bot).where(
                Bot.token == bot_token,
                Bot.platform == BotPlatform.TELEGRAM,
                Bot.is_active == True,
            )
        )
        bot = result.scalar_one_or_none()

        if not bot:
            bot_logger.warning(f"Telegram webhook: Bot not found for token")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Bot not found",
            )

        # Extract message
        message_data = payload.get("message") or payload.get("edited_message")
        callback_query = payload.get("callback_query")

        if message_data:
            await _process_telegram_message(db, bot, message_data)
        elif callback_query:
            await _process_telegram_callback(db, bot, callback_query)

    return {"ok": True}


async def _process_telegram_message(db, bot: Bot, message_data: dict):
    """Process incoming Telegram message with AI."""
    chat = message_data.get("chat", {})
    chat_id = str(chat.get("id"))
    text = message_data.get("text", "")

    if not text:
        # Skip non-text messages for now
        return

    bot_logger.info(f"Telegram message for bot {bot.id}: {text[:50]}...")

    # Create chat service
    chat_service = ChatService(db, bot)

    # Process message and get AI response
    response_text = await chat_service.process_message(
        platform_user_id=chat_id,
        message_text=text,
        message_type=MessageType.TEXT,
    )

    # Send response via Telegram
    telegram_bot = TelegramBot(
        bot_id=bot.id,
        token=bot.token,
        config=bot.settings or {},
    )

    await telegram_bot.send_message(
        recipient_id=chat_id,
        response=BotResponse(text=response_text),
    )


async def _process_telegram_callback(db, bot: Bot, callback_query: dict):
    """Process Telegram callback query."""
    user = callback_query.get("from", {})
    data = callback_query.get("data", "")
    
    bot_logger.info(f"Telegram callback for bot {bot.id}: {data}")

    telegram_bot = TelegramBot(
        bot_id=bot.id,
        token=bot.token,
        config=bot.settings or {},
    )

    # Answer callback
    await telegram_bot._make_request("answerCallbackQuery", {
        "callback_query_id": callback_query.get("id"),
    })


# ===========================================
# WhatsApp Webhooks
# ===========================================

@router.get("/whatsapp")
async def whatsapp_webhook_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """WhatsApp webhook verification."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        bot_logger.info("WhatsApp webhook verified")
        return int(hub_challenge) if hub_challenge else ""
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed",
    )


@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """WhatsApp webhook handler."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    bot_logger.info(f"WhatsApp webhook received")

    # TODO: Implement WhatsApp message processing
    # Similar to Telegram but with Meta's API

    return {"status": "received"}


# ===========================================
# Instagram Webhooks
# ===========================================

@router.get("/instagram")
async def instagram_webhook_verify(
    hub_mode: str = None,
    hub_verify_token: str = None,
    hub_challenge: str = None,
):
    """Instagram webhook verification."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_VERIFY_TOKEN:
        bot_logger.info("Instagram webhook verified")
        return int(hub_challenge) if hub_challenge else ""
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Verification failed",
    )


@router.post("/instagram")
async def instagram_webhook(request: Request):
    """Instagram webhook handler."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    bot_logger.info(f"Instagram webhook received")

    # TODO: Implement Instagram message processing

    return {"status": "received"}


# ===========================================
# Payment Webhooks
# ===========================================

@router.post("/payme")
async def payme_webhook(
    request: Request,
    authorization: str = Header(None),
):
    """
    PayMe Merchant API webhook.
    Handles CheckPerformTransaction, CreateTransaction, etc.
    """
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload",
        )

    # Verify authorization
    if not payme_provider.verify_webhook(payload, authorization or ""):
        payment_logger.warning("PayMe webhook: Invalid authorization")
        return {
            "jsonrpc": "2.0",
            "id": payload.get("id"),
            "error": {
                "code": -32504,
                "message": {"uz": "Avtorizatsiya xatosi"},
            },
        }

    # Handle the webhook
    response = await payme_provider.handle_webhook(payload)
    return response


@router.post("/click/prepare")
async def click_prepare_webhook(request: Request):
    """Click prepare webhook (action=0)."""
    try:
        payload = await request.form()
        payload_dict = dict(payload)
    except Exception:
        return {"error": -8, "error_note": "Invalid request"}

    sign_string = payload_dict.get("sign_string", "")
    
    if not click_provider.verify_webhook(payload_dict, sign_string):
        payment_logger.warning("Click prepare webhook: Invalid signature")
        return {"error": -1, "error_note": "Sign check failed"}

    response = await click_provider.handle_webhook({**payload_dict, "action": 0})
    return response


@router.post("/click/complete")
async def click_complete_webhook(request: Request):
    """Click complete webhook (action=1)."""
    try:
        payload = await request.form()
        payload_dict = dict(payload)
    except Exception:
        return {"error": -8, "error_note": "Invalid request"}

    sign_string = payload_dict.get("sign_string", "")
    
    if not click_provider.verify_webhook(payload_dict, sign_string):
        payment_logger.warning("Click complete webhook: Invalid signature")
        return {"error": -1, "error_note": "Sign check failed"}

    response = await click_provider.handle_webhook({**payload_dict, "action": 1})
    return response
