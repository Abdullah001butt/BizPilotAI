#!/usr/bin/env bash
# Container entrypoint: apply database migrations (and optionally seed the first
# admin) before handing off to the main process (uvicorn, passed as CMD).
set -euo pipefail

echo "→ Applying database migrations..."
alembic upgrade head

if [[ "${SEED_ON_START:-false}" == "true" ]]; then
  echo "→ Seeding initial admin user..."
  python -m app.scripts.seed
fi

echo "→ Starting: $*"
exec "$@"
