# BizPilot AI — Backend

FastAPI backend for BizPilot AI. Layered architecture (API → services →
repositories → models) with async SQLAlchemy 2.0, JWT auth, and Alembic
migrations.

## Quick start (local)

```bash
cd backend
python -m venv .venv
source .venv/Scripts/activate     # Windows (Git Bash);  use .venv/bin/activate on macOS/Linux
pip install -e ".[dev]"

cp .env.example .env              # then edit SECRET_KEY etc.
alembic upgrade head              # create the schema
python -m app.scripts.seed        # create the first admin (optional)

uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

## Testing

```bash
pytest                 # run the suite
pytest --cov           # with coverage
ruff check .           # lint
mypy app               # type-check
```

## Layout

```
app/
├── core/          config, security, logging, exceptions, middleware
├── db/            engine, session, declarative base
├── models/        SQLAlchemy ORM models
├── schemas/       Pydantic request/response contracts
├── repositories/  data access (Repository pattern)
├── services/      business logic + transactions
├── api/           routers + DI dependencies (versioned under /api/v1)
└── main.py        application factory
```
