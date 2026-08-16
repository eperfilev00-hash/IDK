#!/bin/sh
set -e

echo "Running migrations..."
cd /app
# Указываем путь к alembic.ini, так как он лежит в подпапке app
alembic -c app/alembic.ini upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000