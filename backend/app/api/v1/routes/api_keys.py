"""API key management endpoints (company-scoped, admin-only)."""

from __future__ import annotations

from fastapi import APIRouter, Response, status

from app.api.deps import AdminUser, ApiKeyServiceDep
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyPublic

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyPublic], summary="List API keys")
async def list_api_keys(service: ApiKeyServiceDep, _: AdminUser) -> list[ApiKeyPublic]:
    """List the current company's API keys (secrets are never returned)."""
    keys = await service.list()
    return [ApiKeyPublic.model_validate(key) for key in keys]


@router.post(
    "",
    response_model=ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
    summary="Create an API key",
)
async def create_api_key(
    data: ApiKeyCreate, service: ApiKeyServiceDep, _: AdminUser
) -> ApiKeyCreated:
    """Create a new API key. The plaintext key is returned **once**, here only."""
    api_key, plaintext = await service.create(data.name)
    return ApiKeyCreated(
        **ApiKeyPublic.model_validate(api_key).model_dump(), key=plaintext
    )


@router.delete(
    "/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
)
async def revoke_api_key(
    api_key_id: int, service: ApiKeyServiceDep, _: AdminUser
) -> Response:
    """Revoke (permanently disable) an API key owned by the current company."""
    await service.revoke(api_key_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
