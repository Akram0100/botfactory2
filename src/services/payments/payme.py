# ============================================
# BotFactory AI - PayMe Payment Service
# ============================================

import hashlib
import base64
import json
from typing import Optional, Dict, Any
from datetime import datetime

import aiohttp

from src.core.config import settings
from src.core.logging import payment_logger
from src.services.payments.base import BasePaymentProvider, PaymentResult


class PayMeProvider(BasePaymentProvider):
    """
    PayMe payment provider implementation.
    Supports Merchant API for creating and managing payments.
    """

    PAYME_CHECKOUT_URL = "https://checkout.paycom.uz"
    PAYME_MERCHANT_URL = "https://checkout.paycom.uz/api"

    def __init__(
        self,
        merchant_id: str = None,
        secret_key: str = None,
    ):
        self.merchant_id = merchant_id or settings.PAYME_MERCHANT_ID
        self.secret_key = secret_key or settings.PAYME_SECRET_KEY
        
    @property
    def provider_name(self) -> str:
        return "payme"

    async def create_payment(
        self,
        amount: int,
        order_id: str,
        description: str,
        return_url: Optional[str] = None,
    ) -> PaymentResult:
        """
        Create PayMe checkout URL.
        
        PayMe uses base64-encoded URL parameters for checkout.
        """
        try:
            # PayMe expects amount in tiyin
            params = {
                "m": self.merchant_id,
                "ac.order_id": order_id,
                "a": amount,
                "c": return_url or settings.APP_URL,
            }

            # Build checkout URL
            encoded_params = base64.b64encode(
                json.dumps(params).encode()
            ).decode()

            payment_url = f"{self.PAYME_CHECKOUT_URL}/{encoded_params}"

            payment_logger.info(f"PayMe payment created: {order_id}, amount: {amount}")

            return PaymentResult(
                success=True,
                transaction_id=order_id,
                payment_url=payment_url,
            )

        except Exception as e:
            payment_logger.error(f"PayMe create error: {e}")
            return PaymentResult(
                success=False,
                error_message=str(e),
            )

    async def check_payment(self, transaction_id: str) -> PaymentResult:
        """Check transaction status via Merchant API."""
        try:
            async with aiohttp.ClientSession() as session:
                auth = base64.b64encode(
                    f"Paycom:{self.secret_key}".encode()
                ).decode()

                async with session.post(
                    self.PAYME_MERCHANT_URL,
                    json={
                        "method": "CheckTransaction",
                        "params": {"id": transaction_id},
                    },
                    headers={
                        "Authorization": f"Basic {auth}",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    data = await response.json()

                    if "error" in data:
                        return PaymentResult(
                            success=False,
                            error_message=data["error"].get("message"),
                        )

                    result = data.get("result", {})
                    return PaymentResult(
                        success=True,
                        transaction_id=transaction_id,
                        provider_data=result,
                    )

        except Exception as e:
            payment_logger.error(f"PayMe check error: {e}")
            return PaymentResult(success=False, error_message=str(e))

    async def cancel_payment(self, transaction_id: str, reason: str) -> PaymentResult:
        """Cancel transaction via Merchant API."""
        try:
            async with aiohttp.ClientSession() as session:
                auth = base64.b64encode(
                    f"Paycom:{self.secret_key}".encode()
                ).decode()

                async with session.post(
                    self.PAYME_MERCHANT_URL,
                    json={
                        "method": "CancelTransaction",
                        "params": {
                            "id": transaction_id,
                            "reason": 1,  # 1 = one-sided cancel
                        },
                    },
                    headers={
                        "Authorization": f"Basic {auth}",
                        "Content-Type": "application/json",
                    },
                ) as response:
                    data = await response.json()

                    if "error" in data:
                        return PaymentResult(
                            success=False,
                            error_message=data["error"].get("message"),
                        )

                    payment_logger.info(f"PayMe payment cancelled: {transaction_id}")
                    return PaymentResult(
                        success=True,
                        transaction_id=transaction_id,
                    )

        except Exception as e:
            payment_logger.error(f"PayMe cancel error: {e}")
            return PaymentResult(success=False, error_message=str(e))

    def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify PayMe webhook authorization.
        PayMe uses Basic Auth with merchant credentials.
        """
        try:
            # Expected format: "Basic base64(merchant_id:secret_key)"
            if not signature.startswith("Basic "):
                return False

            encoded = signature[6:]  # Remove "Basic "
            decoded = base64.b64decode(encoded).decode()
            
            expected = f"Paycom:{self.secret_key}"
            return decoded == expected

        except Exception as e:
            payment_logger.error(f"PayMe verify error: {e}")
            return False

    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle PayMe Merchant API webhook.
        
        PayMe sends JSON-RPC 2.0 requests for:
        - CheckPerformTransaction
        - CreateTransaction
        - PerformTransaction
        - CancelTransaction
        - CheckTransaction
        """
        method = payload.get("method")
        params = payload.get("params", {})
        request_id = payload.get("id")

        payment_logger.info(f"PayMe webhook: {method}")

        try:
            if method == "CheckPerformTransaction":
                return await self._check_perform_transaction(params, request_id)
            elif method == "CreateTransaction":
                return await self._create_transaction(params, request_id)
            elif method == "PerformTransaction":
                return await self._perform_transaction(params, request_id)
            elif method == "CancelTransaction":
                return await self._cancel_transaction(params, request_id)
            elif method == "CheckTransaction":
                return await self._check_transaction(params, request_id)
            else:
                return self._error_response(-32601, "Method not found", request_id)

        except Exception as e:
            payment_logger.error(f"PayMe webhook error: {e}")
            return self._error_response(-31001, str(e), request_id)

    async def _check_perform_transaction(
        self, params: Dict, request_id: Any
    ) -> Dict[str, Any]:
        """Check if transaction can be performed."""
        account = params.get("account", {})
        order_id = account.get("order_id")
        amount = params.get("amount")

        # Validate order exists and amount matches
        # TODO: Implement actual validation with database

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"allow": True},
        }

    async def _create_transaction(
        self, params: Dict, request_id: Any
    ) -> Dict[str, Any]:
        """Create transaction."""
        transaction_id = params.get("id")
        time = params.get("time")
        amount = params.get("amount")
        account = params.get("account", {})
        order_id = account.get("order_id")

        # TODO: Create transaction in database

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "create_time": time,
                "transaction": transaction_id,
                "state": 1,  # Created
            },
        }

    async def _perform_transaction(
        self, params: Dict, request_id: Any
    ) -> Dict[str, Any]:
        """Perform (complete) transaction."""
        transaction_id = params.get("id")

        # TODO: Update transaction status in database
        # TODO: Activate user subscription

        perform_time = int(datetime.utcnow().timestamp() * 1000)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "transaction": transaction_id,
                "perform_time": perform_time,
                "state": 2,  # Completed
            },
        }

    async def _cancel_transaction(
        self, params: Dict, request_id: Any
    ) -> Dict[str, Any]:
        """Cancel transaction."""
        transaction_id = params.get("id")
        reason = params.get("reason")

        # TODO: Update transaction status in database

        cancel_time = int(datetime.utcnow().timestamp() * 1000)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "transaction": transaction_id,
                "cancel_time": cancel_time,
                "state": -1,  # Cancelled
            },
        }

    async def _check_transaction(
        self, params: Dict, request_id: Any
    ) -> Dict[str, Any]:
        """Check transaction status."""
        transaction_id = params.get("id")

        # TODO: Get transaction from database

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "create_time": 0,
                "perform_time": 0,
                "cancel_time": 0,
                "transaction": transaction_id,
                "state": 1,
                "reason": None,
            },
        }

    def _error_response(
        self, code: int, message: str, request_id: Any
    ) -> Dict[str, Any]:
        """Build error response."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": code,
                "message": {"uz": message, "ru": message, "en": message},
            },
        }


# Singleton instance
payme_provider = PayMeProvider()
