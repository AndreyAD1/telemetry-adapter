#!/bin/bash
set -xue

poetry run alembic upgrade head
poetry run uvicorn --host 0.0.0.0 --port ${API_LISTEN_PORT:-"7777"} --reload --log-level debug app.asgi:app
