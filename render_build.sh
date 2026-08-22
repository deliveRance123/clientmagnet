#!/usr/bin/env bash
set -e

echo "==> Upgrading pip and installing requirements..."
pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
elif [ -f "backend/requirements.txt" ]; then
    pip install -r backend/requirements.txt
fi

echo "==> Running database migrations..."
if [ -d "backend" ]; then
    cd backend
    python -m alembic upgrade head
    cd ..
else
    python -m alembic upgrade head
fi

echo "==> Build complete!"
