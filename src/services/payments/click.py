# ============================================
# BotFactory AI - Click Payment Service
# ============================================

import hashlib
import json
from typing import Optional, Dict, Any
from datetime import datetime

import aiohttp

from src.core.config import settings
from src.core.logging import payment_logger
from src.services.payments.base import BasePaymentProvider, PaymentResult


class ClickProvider(BasePaymentProvider):
    """
    Click payment provider implementation.
    """

    CLICK_API_URL = "https://api.click.uz/v2/merchant"
    CLICK_CHECKOUT_URL = "https://my.click.uz/services/pay"

    def __init__(
        self,
        merchant_id: str = None,
        secret_key: str = None,
        service_id: str = None,
    ):
        self.merchant_id = merchant_id or settings.CLICK_MERCHANT_ID
        self.secret_key = secret_key or settings.CLICK_SECRET_KEY
        self.service_id = service_id or settings.CLICK_SERVICE_ID

    @property
    def provider_name(self) -> str:
        return "click"

    async def create_payment(
        self,
        amount: int,
        order_id: str,
        description: str,
        return_url: Optional[str] = None,
    ) -> PaymentResult:
        """
        Create Click checkout URL.
        
        Click expects amount in sum (not tiyin).
        """
        try:
            # Click expects amount in sum
            amount_sum = amount // 100

            # Build checkout URL
            params = (
                f"?service_id={self.service_id}"
                f"&merchant_id={self.merchant_id}"
                f"&amount={amount_sum}"
                f"&transaction_param={order_id}"
                f"&return_url={return_url or settings.APP_URL}"
            )

            payment_url = f"{self.CLICK_CHECKOUT_URL}{params}"

            payment_logger.info(f"Click payment created: {order_id}, amount: {amount_sum}")

            return PaymentResult(
                success=True,
                transaction_id=order_id,
                payment_url=payment_url,
            )

        except Exception as e:
            payment_logger.error(f"Click create error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e),
            )

    async def check_payment(self, transaction_id: str) -> PaymentResult:
        """Check transaction status."""
        # Click doesn't have a simple status check API
        # Status is tracked via webhooks
        return PaymentResult(
            success=True,
            transaction_id=transaction_id,
        )

    async def cancel_payment(self, transaction_id: str, reason: str) -> PaymentResult:
        """Cancel is not directly supported by Click merchant API."""
        return PaymentResult(
            success=False,
            error_message="Click to'lovini bekor qilish imkonsiz",
        )

    def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify Click webhook signature.
        
        sign_string = click_trans_id + service_id + SECRET_KEY + 
                      merchant_trans_id + amount + action + sign_time
        """
        try:
            click_trans_id = str(payload.get("click_trans_id", ""))
            service_id = str(payload.get("service_id", ""))
            merchant_trans_id = str(payload.get("merchant_trans_id", ""))
            amount = str(payload.get("amount", ""))
            action = str(payload.get("action", ""))
            sign_time = str(payload.get("sign_time", ""))

            sign_string = (
                click_trans_id +
                service_id +
                self.secret_key +
                merchant_trans_id +
                amount +
                action +
                sign_time
            )

            expected_signature = hashlib.md5(sign_string.encode()).hexdigest()

            return signature == expected_signature

        except Exception as e:
            payment_logger.error(f"Click verify error: {e}")
            return False

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle Click webhook.
        
        Click sends two types of requests:
        - action=0: Prepare (validate)
        - action=1: Complete
        """
        action = payload.get("action")
        click_trans_id = payload.get("click_trans_id")
        merchant_trans_id = payload.get("merchant_trans_id")
        amount = payload.get("amount")

        payment_logger.info(f"Click webhook: action={action}, trans={click_trans_id}")

        try:
            if action == 0:
                # Prepare - validate transaction
                return await self._prepare_transaction(payload)
            elif action == 1:
                # Complete - confirm payment
                return await self._complete_transaction(payload)
            else:
                return {"error": -3, "error_note": "Invalid action"}

        except Exception as e:
            payment_logger.error(f"Click webhook error: {e}")
            return {"error": -9, "error_note": str(e)}

    async def _prepare_transaction(self, payload: Dict) -> Dict[str, Any]:
        """Prepare (validate) transaction."""
        merchant_trans_id = payload.get("merchant_trans_id")
        amount = payload.get("amount")

        # TODO: Validate order exists and amount matches

        return {
            "click_trans_id": payload.get("click_trans_id"),
            "merchant_trans_id": merchant_trans_id,
            "merchant_prepare_id": merchant_trans_id,
            "error": 0,
            "error_note": "Success",
        }

    async def _complete_transaction(self, payload: Dict) -> Dict[str, Any]:
        """Complete transaction."""
        merchant_trans_id = payload.get("merchant_trans_id")
        
        # TODO: Update payment status in database
        # TODO: Activate user subscription

        return {
            "click_trans_id": payload.get("click_trans_id"),
            "merchant_trans_id": merchant_trans_id,
            "merchant_confirm_id": merchant_trans_id,
            "error": 0,
            "error_note": "Success",
        }


# Singleton instance
click_provider = ClickProvider()
