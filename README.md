<div align="center">

# 🚀 BizPilot AI

### Run Your Business Smarter with AI

An AI-powered **Business Operating System** for small and medium businesses —
Business Intelligence, AI Copilot, Inventory, CRM, Accounting, Reports,
Forecasting, and Document Intelligence in one premium platform.

</div>

---

> **Phase 1 (this release):** project architecture, monorepo scaffolding,
> production-grade authentication (JWT access + rotating refresh tokens, RBAC),
> configuration, database + migrations, Docker, and CI. Subsequent phases add the
> business modules (Dashboard metrics, AI Copilot, Inventory, Sales, CRM, …).

## 🧱 Tech stack

| Layer        | Technology                                                                 |
| ------------ | -------------------------------------------------------------------------- |
| **Frontend** | React 19, TypeScript, Vite, TailwindCSS, shadcn/ui, React Router, TanStack Query, Axios, React Hook Form, Zod, Framer Motion, Recharts |
| **Backend**  | Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, Pydantic v2, JWT, Argon2 |
| **Database** | PostgreSQL (prod), SQLite (dev) — async drivers                            |
| **Infra**    | Docker, Docker Compose, Redis, Nginx, GitHub Actions                       |

## 🏛️ Architecture

```
┌─────────────────────────────┐        ┌──────────────────────────────────────┐
│        Frontend (SPA)       │        │            Backend (FastAPI)          │
│  React 19 · Vite · Tailwind │ HTTPS  │  api → services → repositories → ORM  │
│  TanStack Query · Axios     │ ─────► │  core: config·security·logging·errors │
│  Auth context · refresh     │  JSON  │  JWT auth · RBAC · Alembic            │
└─────────────────────────────┘        └───────────────────┬──────────────────┘
                                                            │
                                              ┌─────────────┴─────────────┐
                                              │   PostgreSQL   ·   Redis   │
                                              └───────────────────────────┘
```

The backend follows a strict layered architecture (Repository + Service patterns,
Dependency Injection) so business logic is reusable across the API, background
jobs, and AI agents added in later phases. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## ⚡ Quick start

### Option A — Docker (everything, one command)

```bash
cp .env.example .env          # then set SECRET_KEY
docker compose up --build
```

- Frontend → http://localhost:5173
- Backend API docs → http://localhost:8000/docs
- A first admin is auto-seeded (`FIRST_SUPERUSER_EMAIL` / `FIRST_SUPERUSER_PASSWORD`).

### Option B — Run locally (two terminals)

**Backend**
```bash
cd backend
python -m venv .venv && source .venv/Scripts/activate   # macOS/Linux: source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
alembic upgrade head
python -m app.scripts.seed        # optional: create the admin
uvicorn app.main:app --reload
```

**Frontend**
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

## 🔐 Authentication flow

1. **Register / Login** → backend returns a short-lived **access token** (15 min)
   and a long-lived **refresh token** (7 days).
2. Access token is held in memory; refresh token is persisted to `localStorage`.
3. On a `401`, the Axios client transparently calls `/auth/refresh`, **rotates**
   the refresh token, and retries the original request (single-flight).
4. **Logout** revokes the refresh token server-side (stored hashed, so a DB leak
   never exposes usable tokens).

## ✅ Testing

```bash
# Backend
cd backend && pytest --cov

# Frontend
cd frontend && npm run typecheck && npm run lint && npm run build
```

## 📂 Repository layout

```
BizPilotAI/
├── backend/            FastAPI app (app/), Alembic, tests, Dockerfile
├── frontend/           React app (src/), Vite, Tailwind, Dockerfile + nginx
├── docs/               Architecture & deployment docs
├── .github/workflows/  CI pipeline
├── docker-compose.yml  Full local stack
└── README.md
```

## 🗺️ Roadmap (phases)

- **Phase 1 ✅** — Foundation & Auth
- **Phase 2 ✅** — Multi-tenancy (Company model), Settings, API Keys
- **Phase 4 ✅** — Inventory (Products, Suppliers, stock) + Sales (Customers, Invoices)
- **Phase 3 ✅** — Live Dashboard metrics (revenue/profit, health score, top products)
- **Phase 7** — AI Copilot (Gemini + RAG over business data)
- **Billing** — Stripe subscriptions
- Later: CRM depth, Document Intelligence/OCR, Forecasting, Reports, Tasks/Calendar, Global Search

## 📄 License

Proprietary — see [LICENSE](LICENSE).
