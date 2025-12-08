# ============================================
# BotFactory AI - Custom Exceptions
# ============================================

from typing import Any, Optional


class BotFactoryException(Exception):
    """Base exception for BotFactory application."""

    def __init__(
        self,
        message: str = "An error occurred",
        code: str = "INTERNAL_ERROR",
        details: Optional[dict[str, Any]] = None,
    ):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)


# ===========================================
# Authentication Exceptions
# ===========================================

class AuthenticationError(BotFactoryException):
    """Authentication failed."""

    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message=message, code="AUTH_ERROR")


class InvalidCredentialsError(AuthenticationError):
    """Invalid username or password."""

    def __init__(self):
        super().__init__(message="Noto'g'ri email yoki parol")


class TokenExpiredError(AuthenticationError):
    """Token has expired."""

    def __init__(self):
        super().__init__(message="Token muddati tugagan")


class InvalidTokenError(AuthenticationError):
    """Invalid token."""

    def __init__(self):
        super().__init__(message="Noto'g'ri token")


# ===========================================
# Authorization Exceptions
# ===========================================

class AuthorizationError(BotFactoryException):
    """Authorization failed."""

    def __init__(self, message: str = "Ruxsat berilmagan"):
        super().__init__(message=message, code="FORBIDDEN")


class InsufficientPermissionsError(AuthorizationError):
    """User doesn't have required permissions."""

    def __init__(self, required_role: str = "admin"):
        super().__init__(
            message=f"Bu amal uchun {required_role} huquqi kerak"
        )


class SubscriptionRequiredError(AuthorizationError):
    """Action requires active subscription."""

    def __init__(self, required_plan: str = "starter"):
        super().__init__(
            message=f"Bu funksiya uchun {required_plan} obunasi kerak"
        )


# ===========================================
# Resource Exceptions
# ===========================================

class NotFoundError(BotFactoryException):
    """Resource not found."""

    def __init__(self, resource: str = "Resurs", resource_id: Any = None):
        message = f"{resource} topilmadi"
        if resource_id:
            message = f"{resource} (ID: {resource_id}) topilmadi"
        super().__init__(message=message, code="NOT_FOUND")


class AlreadyExistsError(BotFactoryException):
    """Resource already exists."""

    def __init__(self, resource: str = "Resurs", field: str = ""):
        message = f"{resource} allaqachon mavjud"
        if field:
            message = f"Bu {field} bilan {resource.lower()} allaqachon mavjud"
        super().__init__(message=message, code="ALREADY_EXISTS")


# ===========================================
# Validation Exceptions
# ===========================================

class ValidationError(BotFactoryException):
    """Validation failed."""

    def __init__(
        self,
        message: str = "Validation xatosi",
        details: Optional[dict] = None,
    ):
        super().__init__(message=message, code="VALIDATION_ERROR", details=details)


class RateLimitExceededError(BotFactoryException):
    """Rate limit exceeded."""

    def __init__(self):
        super().__init__(
            message="So'rovlar limiti oshib ketdi. Biroz kutib turing.",
            code="RATE_LIMIT_EXCEEDED",
        )


# ===========================================
# External Service Exceptions
# ===========================================

class ExternalServiceError(BotFactoryException):
    """External service error."""

    def __init__(self, service: str, message: str = "Xizmat bilan bog'lanishda xatolik"):
        super().__init__(
            message=f"{service}: {message}",
            code="EXTERNAL_SERVICE_ERROR",
            details={"service": service},
        )


class AIServiceError(ExternalServiceError):
    """AI service error."""

    def __init__(self, message: str = "AI xizmati bilan bog'lanishda xatolik"):
        super().__init__(service="Gemini AI", message=message)


class PaymentServiceError(ExternalServiceError):
    """Payment service error."""

    def __init__(self, provider: str, message: str = "To'lov xizmatida xatolik"):
        super().__init__(service=provider, message=message)


class BotPlatformError(ExternalServiceError):
    """Bot platform error."""

    def __init__(self, platform: str, message: str = "Bot platformasi bilan xatolik"):
        super().__init__(service=platform, message=message)


# ===========================================
# Bot Exceptions
# ===========================================

class BotLimitExceededError(BotFactoryException):
    """Bot limit exceeded for subscription."""

    def __init__(self, current_limit: int, plan: str):
        super().__init__(
            message=f"{plan} obunasida maksimum {current_limit} ta bot yaratish mumkin",
            code="BOT_LIMIT_EXCEEDED",
            details={"limit": current_limit, "plan": plan},
        )


class InvalidBotTokenError(BotFactoryException):
    """Invalid bot token."""

    def __init__(self, platform: str):
        super().__init__(
            message=f"Noto'g'ri {platform} bot tokeni",
            code="INVALID_BOT_TOKEN",
        )
