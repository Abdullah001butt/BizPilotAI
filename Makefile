# Convenience commands. Usage: `make <target>`
.PHONY: help up down logs backend frontend test lint migrate seed

help:
	@echo "BizPilot AI — common tasks"
	@echo "  make up        Start the full stack (docker compose up --build)"
	@echo "  make down      Stop the stack"
	@echo "  make logs      Tail backend logs"
	@echo "  make backend   Run the backend locally (uvicorn --reload)"
	@echo "  make frontend  Run the frontend dev server"
	@echo "  make test      Run backend tests"
	@echo "  make lint      Lint backend + frontend"
	@echo "  make migrate   Apply database migrations"
	@echo "  make seed      Seed the first admin user"

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f backend

backend:
	cd backend && uvicorn app.main:app --reload

frontend:
	cd frontend && npm run dev

test:
	cd backend && pytest

lint:
	cd backend && ruff check .
	cd frontend && npm run lint

migrate:
	cd backend && alembic upgrade head

seed:
	cd backend && python -m app.scripts.seed
