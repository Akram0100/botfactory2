# BotFactory AI

An Uzbek-language SaaS platform for creating AI chatbots for Telegram, WhatsApp, and Instagram.

## Overview

BotFactory AI allows users to create professional AI-powered chatbots without coding. The platform supports multiple messaging platforms and integrates with local payment systems (PayMe, Click, Uzum).

## Architecture

- **Backend**: Python FastAPI with async support
- **Frontend**: Jinja2 templates with static CSS/JS
- **Database**: PostgreSQL with SQLAlchemy ORM and Alembic migrations
- **AI Integration**: Google Gemini AI

## Project Structure

```
├── frontend/           # Frontend templates and static files
│   ├── static/         # CSS and JavaScript
│   └── templates/      # Jinja2 HTML templates
├── src/                # Backend source code
│   ├── api/v1/         # API routes
│   ├── core/           # Configuration, logging, security
│   ├── db/             # Database session and migrations
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic services
│   └── tasks/          # Celery background tasks
└── tests/              # Test files
```

## Running the Application

The application runs on port 5000 using uvicorn:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

## Database

Uses PostgreSQL with async support (asyncpg). Migrations are managed with Alembic:
```bash
alembic upgrade head
```

## Environment Variables

- `DATABASE_URL`: PostgreSQL connection string
- `DEBUG`: Enable debug mode (default: false)
- `SECRET_KEY`: JWT secret key
- `GOOGLE_API_KEY`: Google Gemini AI API key (optional)

## Key Features

- User authentication (JWT-based)
- Multi-platform bot management (Telegram, WhatsApp, Instagram)
- Knowledge base management for bots
- Subscription-based pricing with local payment integration
- Analytics dashboard
