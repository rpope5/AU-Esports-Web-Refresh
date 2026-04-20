#!/usr/bin/env bash
set -euo pipefail

if [[ "${RUN_DB_MIGRATIONS_ON_STARTUP:-false}" =~ ^(1|true|yes|on)$ ]]; then
  alembic upgrade head
fi

exec gunicorn \
  -k uvicorn.workers.UvicornWorker \
  app.main:app \
  --bind "0.0.0.0:${PORT:-8000}" \
  --timeout 120 \
  --access-logfile - \
  --error-logfile -
