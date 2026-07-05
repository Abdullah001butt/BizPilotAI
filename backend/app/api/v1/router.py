"""Aggregates all v1 route modules into a single router.

Each new module (inventory, sales, crm, …) registers here in later phases, so
`main.py` only ever mounts this one router under the API prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import api_keys, auth, company, health, users

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(company.router)
api_router.include_router(api_keys.router)
