# Spendlot Receipt Tracker Backend Makefile

.PHONY: help install dev test lint format clean docker-build docker-up docker-down init-db migrate

# Default target
help:
	@echo "Available commands:"
	@echo "  install     Install dependencies"
	@echo "  dev         Start development server"
	@echo "  test        Run tests"
	@echo "  lint        Run linting"
	@echo "  format      Format code"
	@echo "  clean       Clean up temporary files"
	@echo "  docker-build Build Docker images"
	@echo "  docker-up   Start Docker services"
	@echo "  docker-down Stop Docker services"
	@echo "  init-db     Initialize database"
	@echo "  migrate     Run database migrations"

# Install dependencies
install:
	pip install -r requirements.txt

# Start development server
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	python scripts/run_tests.py

# Run linting
lint:
	flake8 app/ tests/
	mypy app/

# Format code
format:
	black app/ tests/
	isort app/ tests/

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# Docker commands
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Database commands
init-db:
	python scripts/init_db.py

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate -m "$(name)"

# Development setup
setup-dev: install init-db migrate
	@echo "Development environment setup complete!"

# Production commands
prod-up:
	docker-compose -f docker-compose.prod.yml up -d

prod-down:
	docker-compose -f docker-compose.prod.yml down

# Celery commands
celery-worker:
	celery -A app.tasks.celery_app worker --loglevel=info

celery-beat:
	celery -A app.tasks.celery_app beat --loglevel=info

celery-flower:
	celery -A app.tasks.celery_app flower --port=5555

# Status and deployment
status:
	python scripts/status_check.py

quick-deploy:
	python scripts/quick_deploy.py

# Complete setup for new developers
setup-dev-complete: install init-db migrate
	@echo "🎉 Development environment setup complete!"
	@echo "Run 'make dev' to start the development server"

# Production deployment
deploy-prod: docker-build
	docker-compose -f docker-compose.prod.yml up -d
