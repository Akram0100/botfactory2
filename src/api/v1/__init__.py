# API v1 module
from fastapi import APIRouter

from src.api.v1.auth import router as auth_router
from src.api.v1.bots import router as bots_router
from src.api.v1.knowledge import router as knowledge_router
from src.api.v1.payments import router as payments_router
from src.api.v1.webhooks import router as webhooks_router
from src.api.v1.admin import router as admin_router

# Create main v1 router
router = APIRouter()

# Include all sub-routers
router.include_router(auth_router)
router.include_router(bots_router)
router.include_router(knowledge_router)
router.include_router(payments_router)
router.include_router(webhooks_router)
router.include_router(admin_router)

__all__ = ["router"]
