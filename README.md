# 🏭 BotFactory AI

O'zbek tilidagi SaaS platformasi - foydalanuvchilarga kod yozmasdan AI chatbotlarni yaratish, boshqarish va monetizatsiya qilish imkonini beradi.

## 🚀 Xususiyatlar

- ✅ **Multi-platform**: Telegram, WhatsApp, Instagram
- ✅ **AI-powered**: Google Gemini 2.0 bilan
- ✅ **Bilimlar bazasi**: FAQ, matnlar, hujjatlar
- ✅ **To'lov tizimlari**: PayMe, Click, Uzum
- ✅ **O'zbek tilida**: To'liq O'zbekcha interfeys

## 📋 Talablar

- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Docker & Docker Compose (ixtiyoriy)

## 🛠️ O'rnatish

### 1. Loyihani klonlash

```bash
git clone https://github.com/your-username/botfactory.git
cd botfactory
```

### 2. Virtual muhit yaratish

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

### 3. Bog'liqliklarni o'rnatish

```bash
pip install poetry
poetry install
```

### 4. Muhit o'zgaruvchilarini sozlash

```bash
copy .env.example .env
# .env faylini tahrirlang
```

### 5. Ma'lumotlar bazasini ishga tushirish

```bash
# Docker bilan
docker-compose up -d db redis

# Migratsiyalarni bajarish
alembic upgrade head
```

### 6. Serverni ishga tushirish

```bash
# Development
make dev
# yoki
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 🐳 Docker bilan ishga tushirish

```bash
# Barcha xizmatlarni ishga tushirish
docker-compose up -d

# Loglarni ko'rish
docker-compose logs -f web
```

## 📁 Loyiha strukturasi

```
botfactory/
├── src/
│   ├── api/           # FastAPI endpointlar
│   ├── core/          # Konfiguratsiya, xavfsizlik
│   ├── db/            # Ma'lumotlar bazasi
│   ├── models/        # SQLAlchemy modellari
│   ├── schemas/       # Pydantic schemalar
│   ├── services/      # Biznes mantiq
│   └── tasks/         # Celery vazifalar
├── tests/             # Testlar
├── frontend/          # HTML shablonlar
└── docs/              # Hujjatlar
```

## 🧪 Testlarni ishga tushirish

```bash
# Barcha testlar
pytest

# Coverage bilan
pytest --cov=src --cov-report=html
```

## 📖 API Dokumentatsiyasi

Server ishga tushgandan so'ng:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🔑 Muhit O'zgaruvchilari

| O'zgaruvchi | Tavsif | Misol |
|-------------|--------|-------|
| SECRET_KEY | JWT maxfiy kalit | `your-secret-key` |
| DATABASE_URL | PostgreSQL URL | `postgresql+asyncpg://...` |
| GOOGLE_API_KEY | Gemini API kalit | `AIza...` |
| TELEGRAM_BOT_TOKEN | Telegram bot token | `123:ABC...` |

## 📞 Aloqa

- Telegram: @botfactory_support
- Email: support@botfactory.uz

## 📄 Litsenziya

MIT License
