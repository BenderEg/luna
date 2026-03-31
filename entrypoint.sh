#!/bin/bash
set -e

export PYTHONPATH=.:./src

poetry run alembic upgrade head

exec poetry run uvicorn src.app.main:app \
  --host 0.0.0.0 \
  --workers 1 \
  --ws-ping-interval 30 \
  --ws-ping-timeout 30
