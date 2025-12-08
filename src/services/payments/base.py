# ============================================
# BotFactory AI - Base Payment Service
# ============================================

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class PaymentResult(BaseModel):
    """Result of payment operation."""
    success: bool
    transaction_id: Optional[str] = None
    payment_url: Optional[str] = None
    error_message: Optional[str] = None
    provider_data: Dict[str, Any] = {}


class BasePaymentProvider(ABC):
    """
    Abstract base class for payment providers.
    Implements common interface for PayMe, Click, Uzum.
    """

    def __init__(self, merchant_id: str, secret_key: str):
        self.merchant_id = merchant_id
        self.secret_key = secret_key

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Return provider name."""
        pass

    @abstractmethod
    async def create_payment(
        self,
        amount: int,
        order_id: str,
        description: str,
        return_url: Optional[str] = None,
    ) -> PaymentResult:
        """
        Create a new payment.
        
        Args:
            amount: Amount in tiyin (1 UZS = 100 tiyin)
            order_id: Internal order/payment ID
            description: Payment description
            return_url: URL to redirect after payment
            
        Returns:
            PaymentResult with payment URL
        """
        pass

    @abstractmethod
    async def check_payment(self, transaction_id: str) -> PaymentResult:
        """
        Check payment status.
        
        Args:
            transaction_id: Provider transaction ID
            
        Returns:
            PaymentResult with status
        """
        pass

    @abstractmethod
    async def cancel_payment(self, transaction_id: str, reason: str) -> PaymentResult:
        """
        Cancel/refund a payment.
        
        Args:
            transaction_id: Provider transaction ID
            reason: Cancellation reason
            
        Returns:
            PaymentResult with status
        """
        pass

    @abstractmethod
    def verify_webhook(self, payload: Dict[str, Any], signature: str) -> bool:
        """
        Verify webhook signature.
        
        Args:
            payload: Webhook payload
            signature: Signature from headers
            
        Returns:
            True if signature is valid
        """
        pass

    @abstractmethod
    async def handle_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhook from provider.
        
        Args:
            payload: Webhook payload
            
        Returns:
            Response to send back to provider
        """
        pass
