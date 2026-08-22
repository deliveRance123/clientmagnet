#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -e

echo "==> Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "==> Running PostgreSQL database migrations..."
alembic upgrade head

echo "==> Build process completed successfully!"
