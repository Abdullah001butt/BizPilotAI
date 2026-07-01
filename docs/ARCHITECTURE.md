# BizPilot AI — Architecture

This document explains the structural decisions behind BizPilot AI and the
reasoning that will keep the codebase maintainable as all 20 modules land.

## Guiding principles

- **SOLID + DRY** — small, single-responsibility units; shared behaviour lives in
  mixins, base classes, and reusable hooks/components.
- **Separation of concerns** — the web framework, business logic, and data access
  are distinct layers that depend inward only.
- **Type safety end-to-end** — Pydantic v2 + SQLAlchemy `Mapped[...]` on the
  backend; strict TypeScript + Zod on the frontend.
- **Production parity** — the same async drivers and migrations run locally and
  in production; Docker reproduces the full stack.

## Backend layers

```
            HTTP request
                 │
   ┌─────────────▼─────────────┐
   │ api/  (routers + deps)     │  Parse/validate I/O (Pydantic), wire DI,
   │                            │  enforce authn/authz. No business logic.
   ├─────────────▼─────────────┤
   │ services/                  │  Business rules + transaction boundaries.
   │                            │  Framework-agnostic; reusable by jobs/agents.
   ├─────────────▼─────────────┤
   │ repositories/              │  The ONLY layer that talks to SQLAlchemy.
   │                            │  Encapsulates queries; trivially mockable.
   ├─────────────▼─────────────┤
   │ models/  (ORM)             │  Tables, relationships, audit mixins.
   └────────────────────────────┘

   core/   cross-cutting: config, security, logging, exceptions, middleware
   schemas/ Pydantic request/response contracts shared by api + services
```

**Why these patterns**

- **Repository pattern** isolates persistence, so swapping a query, adding caching,
  or unit-testing a service requires no database.
- **Service layer** centralises business rules and owns commits, so the same
  operation behaves identically whether triggered by an endpoint, a Celery task,
  or an AI tool call.
- **Dependency Injection** (`Depends`) makes every collaborator explicit and
  overridable in tests (see `tests/conftest.py` swapping `get_db`).

## Error contract

Domain code raises `AppError` subclasses (`NotFoundError`, `ConflictError`,
`AuthenticationError`, …). A single set of handlers in `main.py` maps them to a
uniform JSON envelope:

```json
{ "error": { "code": "conflict", "message": "...", "details": [] } }
```

The frontend reads this envelope via `getApiErrorMessage`, so every screen shows
consistent, human-readable errors.

## Authentication & RBAC

- **Argon2id** password hashing (OWASP-recommended).
- **JWT access token** (stateless, 15 min) carries `sub` + `role`.
- **Refresh token** (7 days) carries a random `jti`; only a SHA-256 hash of the
  `jti` is stored. Refresh **rotates** the token and revokes the old one;
  logout revokes it. This enables real session invalidation.
- **Roles**: `admin`, `manager`, `employee` + a `is_superuser` override, enforced
  by the `require_roles(...)` dependency factory.

## Frontend structure

```
src/
├── components/ui/     shadcn-style primitives (button, input, card, …)
├── components/layout/ AppShell (sidebar + topbar)
├── context/           AuthProvider + context (session state)
├── features/          feature-first modules (auth, dashboard, …)
├── hooks/             useAuth, useTheme
├── lib/api/           axios client (+ transparent refresh), endpoints, tokens
├── routes/            ProtectedRoute / PublicOnlyRoute guards
└── types/             shared TS types
```

State strategy: **server state** via TanStack Query; **session state** via a
lightweight Auth context; **form state** via React Hook Form + Zod.

## Database & migrations

- Async SQLAlchemy 2.0 (`asyncpg` prod, `aiosqlite` dev).
- A consistent constraint **naming convention** keeps Alembic autogenerate
  diffs stable across SQLite and Postgres.
- Migrations run via an async Alembic env; the container entrypoint applies
  `alembic upgrade head` on start.

## Deployment targets

- **Frontend** → Vercel (static SPA) or the nginx container.
- **Backend** → Render / any container host.
- **Database** → Supabase Postgres (or managed Postgres).
