#!/usr/bin/env bash
set -e

echo "Starting Celery worker..."
celery -A realtime_platform worker --loglevel=info --concurrency=1 &

echo "Starting Celery beat..."
celery -A realtime_platform beat --loglevel=info &

echo "Starting Daphne..."
exec daphne -b 0.0.0.0 -p "$PORT" -t 200 realtime_platform.asgi:application
