# ============================================
# BotFactory AI - Makefile
# ============================================

.PHONY: help install dev test lint format migrate docker-up docker-down clean

# Default target
help:
	@echo "BotFactory AI - Available Commands"
	@echo "==================================="
	@echo "make install    - Install dependencies"
	@echo "make dev        - Run development server"
	@echo "make test       - Run tests with coverage"
	@echo "make lint       - Run linters"
	@echo "make format     - Format code"
	@echo "make migrate    - Run database migrations"
	@echo "make docker-up  - Start Docker containers"
	@echo "make docker-down - Stop Docker containers"
	@echo "make clean      - Clean cache files"

# Install dependencies
install:
	poetry install

# Run development server
dev:
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	pytest tests/ -v --cov=src --cov-report=html --cov-fail-under=80

# Run linters
lint:
	flake8 src tests
	mypy src
	isort --check-only src tests
	black --check src tests

# Format code
format:
	isort src tests
	black src tests

# Database migrations
migrate:
	alembic upgrade head

# Create new migration
migration:
	@read -p "Migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

# Docker commands
docker-up:
	docker-compose up -d --build

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Start Celery worker (local)
celery-worker:
	celery -A src.tasks.celery_app worker -l info

# Start Celery beat (local)
celery-beat:
	celery -A src.tasks.celery_app beat -l info

# Clean cache files
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	find . -type d -name ".mypy_cache" -delete
	rm -rf .coverage htmlcov/

# Create admin user
create-admin:
	python scripts/create_admin.py

# Seed database
seed:
	python scripts/seed_data.py
