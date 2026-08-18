.PHONY: up down build api worker test logs db-migrate db-seed

# Docker
up:
	docker compose up --build -d

down:
	docker compose down

build:
	docker compose build

logs:
	docker compose logs -f

logs-api:
	docker compose logs -f api

logs-worker:
	docker compose logs -f worker

# Infrastructure only (postgres, redis, minio)
infra:
	docker compose up postgres redis minio minio-init -d

# Local development (requires infra running)
api:
	cd apps/api && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker:
	celery -A workers.celery_app worker --loglevel=INFO --concurrency=2

frontend:
	cd apps/frontend && npm run dev

# Database
db-migrate:
	cd apps/api && alembic upgrade head

db-downgrade:
	cd apps/api && alembic downgrade -1

db-revision:
	cd apps/api && alembic revision --autogenerate -m "$(msg)"

db-seed:
	python scripts/seed_demo.py

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Utilities
shell-db:
	docker compose exec postgres psql -U pench -d pench

shell-redis:
	docker compose exec redis redis-cli

clean:
	docker compose down -v --remove-orphans
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
