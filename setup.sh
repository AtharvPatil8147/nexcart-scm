#!/usr/bin/env sh
set -eu

cd "$(dirname "$0")"

if command -v python3 >/dev/null 2>&1; then
    PYTHON=python3
elif command -v python >/dev/null 2>&1; then
    PYTHON=python
else
    echo "Python 3.11 or newer is required. Install it from https://www.python.org/downloads/" >&2
    exit 1
fi

if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)'; then
    echo "Python 3.11 or newer is required." >&2
    exit 1
fi

if ! command -v node >/dev/null 2>&1; then
    echo "Node.js 18 or newer is required. Install it from https://nodejs.org/" >&2
    exit 1
fi
if ! node -e 'process.exit(Number(process.versions.node.split(".")[0]) >= 18 ? 0 : 1)'; then
    echo "Node.js 18 or newer is required." >&2
    exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
    echo "npm is required. Reinstall Node.js from https://nodejs.org/ with npm included." >&2
    exit 1
fi

if [ ! -x .venv/bin/python ]; then
    echo "Creating Python virtual environment..."
    "$PYTHON" -m venv .venv
fi

echo "Installing backend dependencies..."
.venv/bin/python -m pip install -r backend/requirements.txt

echo "Installing frontend dependencies..."
npm --prefix frontend ci

if [ ! -f .env ] && [ -f .env.example ]; then
    cp .env.example .env
    echo "Created .env from .env.example; add your credentials before starting the app."
fi

echo
echo "Setup Complete!"
echo "Start the full stack with: docker compose up --build"
echo "For local development, start the backend with:"
echo "  .venv/bin/python -m uvicorn backend.main:app --reload"
echo "Then start the frontend in another terminal with:"
echo "  cd frontend && npm run dev"
