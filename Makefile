# PiPool Makefile
# Database migration and development tasks

.PHONY: help dev migrate migrate-new migrate-status migrate-stamp migrate-history migrate-downgrade

help:
	@echo "PiPool Makefile Commands:"
	@echo "  make dev               - Run development server"
	@echo "  make migrate           - Run all pending migrations"
	@echo "  make migrate-new MSG='description' - Create new migration"
	@echo "  make migrate-status    - Show current migration status"
	@echo "  make migrate-stamp     - Mark database as current without running migrations"
	@echo "  make migrate-history   - Show migration history"
	@echo "  make migrate-downgrade - Downgrade one migration (careful!)"

dev:
	uv run python -m pipool

test:
	uv run pytest

migrate:
	uv run alembic upgrade head

migrate-new:
	@if [ -z "$(MSG)" ]; then \
		echo "Error: MSG parameter required. Usage: make migrate-new MSG='description'"; \
		exit 1; \
	fi
	uv run alembic revision --autogenerate -m "$(MSG)"

migrate-status:
	uv run alembic current

migrate-stamp:
	uv run alembic stamp head

migrate-history:
	uv run alembic history --verbose

migrate-downgrade:
	uv run alembic downgrade -1
