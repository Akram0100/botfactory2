# ============================================
# BotFactory AI - Main FastAPI Application
# ============================================

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.core.config import settings
from src.core.logging import setup_logging, get_logger
from src.core.exceptions import BotFactoryException
from src.db.session import init_db, close_db
from src.api.v1 import router as v1_router

# Setup logging
setup_logging()
logger = get_logger("botfactory.main")

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Templates
templates = Jinja2Templates(directory=str(BASE_DIR / "frontend" / "templates"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifespan handler."""
    # Startup
    logger.info("Starting BotFactory AI...")
    # await init_db()  # Uncomment when using Alembic migrations
    logger.info("BotFactory AI started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BotFactory AI...")
    await close_db()
    logger.info("BotFactory AI shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="O'zbek tilidagi AI chatbot yaratish platformasi",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)


# ===========================================
# Middleware
# ===========================================

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.DEBUG else ["https://botfactory.uz"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    if not settings.DEBUG:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.debug(f"{request.method} {request.url.path}")
    response = await call_next(request)
    return response


# ===========================================
# Exception handlers
# ===========================================

@app.exception_handler(BotFactoryException)
async def botfactory_exception_handler(request: Request, exc: BotFactoryException):
    """Handle custom BotFactory exceptions."""
    status_map = {
        "AUTH_ERROR": status.HTTP_401_UNAUTHORIZED,
        "FORBIDDEN": status.HTTP_403_FORBIDDEN,
        "NOT_FOUND": status.HTTP_404_NOT_FOUND,
        "ALREADY_EXISTS": status.HTTP_409_CONFLICT,
        "VALIDATION_ERROR": status.HTTP_422_UNPROCESSABLE_ENTITY,
        "RATE_LIMIT_EXCEEDED": status.HTTP_429_TOO_MANY_REQUESTS,
        "EXTERNAL_SERVICE_ERROR": status.HTTP_502_BAD_GATEWAY,
    }
    
    return JSONResponse(
        status_code=status_map.get(exc.code, status.HTTP_500_INTERNAL_SERVER_ERROR),
        content={
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "details": exc.details,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "code": "INTERNAL_ERROR",
            "message": "Ichki server xatosi. Iltimos, keyinroq qayta urinib ko'ring.",
        },
    )


# ===========================================
# Static Files
# ===========================================

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "frontend" / "static")), name="static")


# ===========================================
# API Routes
# ===========================================

# Include API v1 router
app.include_router(v1_router, prefix="/api/v1")


# ===========================================
# Frontend Page Routes
# ===========================================

@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home_page(request: Request):
    """Landing page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/login", response_class=HTMLResponse, tags=["Pages"])
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request, "user": None})


@app.get("/register", response_class=HTMLResponse, tags=["Pages"])
async def register_page(request: Request):
    """Registration page."""
    return templates.TemplateResponse("register.html", {"request": request, "user": None})


@app.get("/dashboard", response_class=HTMLResponse, tags=["Pages"])
async def dashboard_page(request: Request):
    """Dashboard page (demo with mock data)."""
    # Mock user data for demo
    mock_user = {
        "username": "demo_user",
        "full_name": "Demo Foydalanuvchi",
        "subscription_type": type("obj", (object,), {"value": "free"})(),
        "is_subscription_active": True,
        "bot_limit": 1,
        "message_limit": 100,
        "messages_this_month": 42,
        "subscription_expires_at": None,
    }
    
    mock_stats = {
        "total_bots": 1,
        "active_bots": 1,
        "total_messages": 142,
        "total_users": 28,
    }
    
    mock_bots = [
        {
            "id": 1,
            "name": "Demo Bot",
            "platform": type("obj", (object,), {"value": "telegram"})(),
            "is_active": True,
            "total_messages": 142,
            "total_users": 28,
        }
    ]
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": mock_user,
        "stats": mock_stats,
        "bots": mock_bots,
        "active_page": "dashboard",
    })


@app.get("/bots", response_class=HTMLResponse, tags=["Pages"])
async def bots_page(request: Request):
    """Bots management page (demo with mock data)."""
    mock_user = {
        "username": "demo_user",
        "full_name": "Demo Foydalanuvchi",
        "subscription_type": type("obj", (object,), {"value": "starter"})(),
        "is_subscription_active": True,
    }
    
    mock_bots = [
        {
            "id": 1,
            "name": "Savdo yordamchisi",
            "description": "Mijozlarga mahsulotlar haqida ma'lumot beradi",
            "platform": type("obj", (object,), {"value": "telegram"})(),
            "is_active": True,
            "total_messages": 1542,
            "total_users": 128,
            "knowledge_count": 45,
        },
        {
            "id": 2,
            "name": "FAQ Bot",
            "description": "Ko'p so'raladigan savollarga javob beradi",
            "platform": type("obj", (object,), {"value": "telegram"})(),
            "is_active": False,
            "total_messages": 856,
            "total_users": 67,
            "knowledge_count": 23,
        },
    ]
    
    return templates.TemplateResponse("bots.html", {
        "request": request,
        "user": mock_user,
        "bots": mock_bots,
        "active_page": "bots",
    })


@app.get("/bots/new", response_class=HTMLResponse, tags=["Pages"])
async def new_bot_page(request: Request):
    """New bot creation page."""
    mock_user = {
        "username": "demo_user",
        "subscription_type": type("obj", (object,), {"value": "starter"})(),
    }
    
    return templates.TemplateResponse("bot_new.html", {
        "request": request,
        "user": mock_user,
        "active_page": "bots",
    })


@app.get("/bots/{bot_id}", response_class=HTMLResponse, tags=["Pages"])
async def bot_detail_page(request: Request, bot_id: int):
    """Bot detail/settings page."""
    mock_user = {
        "username": "demo_user",
        "subscription_type": type("obj", (object,), {"value": "starter"})(),
    }
    
    mock_bot = {
        "id": bot_id,
        "name": "Savdo yordamchisi",
        "description": "Mijozlarga mahsulotlar haqida ma'lumot beradi",
        "platform": type("obj", (object,), {"value": "telegram"})(),
        "is_active": True,
        "token": "123456:ABC...",
        "welcome_message": "Salom! Men sizga qanday yordam bera olaman?",
        "ai_prompt": "Siz do'kon yordamchisisiz...",
    }
    
    return templates.TemplateResponse("bot_detail.html", {
        "request": request,
        "user": mock_user,
        "bot": mock_bot,
        "active_page": "bots",
    })


@app.get("/bots/{bot_id}/knowledge", response_class=HTMLResponse, tags=["Pages"])
async def bot_knowledge_page(request: Request, bot_id: int):
    """Bot knowledge base page."""
    mock_user = {
        "username": "demo_user",
        "subscription_type": type("obj", (object,), {"value": "starter"})(),
    }
    
    mock_bot = {"id": bot_id, "name": "Savdo yordamchisi"}
    
    return templates.TemplateResponse("knowledge.html", {
        "request": request,
        "user": mock_user,
        "bots": [mock_bot],
        "stats": {"total": 45, "faq": 20, "products": 15, "texts": 10},
        "knowledge_items": [],
        "active_page": "knowledge",
    })



@app.get("/knowledge", response_class=HTMLResponse, tags=["Pages"])
async def knowledge_page(request: Request):
    """Knowledge base management page."""
    mock_user = {
        "username": "demo_user",
        "subscription_type": type("obj", (object,), {"value": "starter"})(),
    }
    
    mock_bots = [
        {"id": 1, "name": "Savdo yordamchisi"},
        {"id": 2, "name": "FAQ Bot"},
    ]
    
    mock_stats = {"total": 68, "faq": 23, "products": 30, "texts": 15}
    
    mock_items = [
        {"id": 1, "source_type": "faq", "title": "Yetkazib berish", "question": "Yetkazib berish bormi?", "is_active": True, "created_at": "15.01.2024"},
        {"id": 2, "source_type": "product", "title": "iPhone 15 Pro", "question": None, "is_active": True, "created_at": "14.01.2024"},
        {"id": 3, "source_type": "text", "title": "Kompaniya haqida", "question": None, "is_active": True, "created_at": "10.01.2024"},
    ]
    
    return templates.TemplateResponse("knowledge.html", {
        "request": request,
        "user": mock_user,
        "bots": mock_bots,
        "stats": mock_stats,
        "knowledge_items": mock_items,
        "active_page": "knowledge",
    })


@app.get("/analytics", response_class=HTMLResponse, tags=["Pages"])
async def analytics_page(request: Request):
    """Analytics dashboard page."""
    mock_user = {
        "username": "demo_user",
        "subscription_type": type("obj", (object,), {"value": "basic"})(),
    }
    
    mock_bots = [
        {"id": 1, "name": "Savdo yordamchisi"},
        {"id": 2, "name": "FAQ Bot"},
    ]
    
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "user": mock_user,
        "bots": mock_bots,
        "stats": {},
        "active_page": "analytics",
    })


@app.get("/settings", response_class=HTMLResponse, tags=["Pages"])
async def settings_page(request: Request):
    """User settings page."""
    mock_user = {
        "username": "demo_user",
        "email": "demo@example.com",
        "full_name": "Demo Foydalanuvchi",
        "phone": "+998 90 123 45 67",
        "subscription_type": type("obj", (object,), {"value": "starter"})(),
        "subscription_expires_at": "15.02.2024",
    }
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "user": mock_user,
        "active_page": "settings",
    })


@app.get("/pricing", response_class=HTMLResponse, tags=["Pages"])
async def pricing_page(request: Request):
    """Pricing page."""
    return templates.TemplateResponse("pricing.html", {
        "request": request,
        "user": None,
    })


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "app_name": settings.APP_NAME,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

