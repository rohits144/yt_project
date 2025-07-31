#!/bin/sh

# Exit if any command fails
set -e

echo "Running database migrations..."
uv run manage.py migrate

echo "Starting Django server..."
exec uv run manage.py runserver 0.0.0.0:8000
