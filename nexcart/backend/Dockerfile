# ══════════════════════════════════════════════════════════════════
# NexCart — Backend Dockerfile
# Build context: ./backend  (the backend/ folder is the root)
# The volume mount in docker-compose maps ./backend → /app
# so all backend files sit at /app/* (not /app/backend/*)
# We set PYTHONPATH=/app/.. so `from backend.xxx` resolves to /app/xxx
# ══════════════════════════════════════════════════════════════════

FROM python:3.11-slim

# Prevent .pyc files and enable unbuffered logs
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# The volume in docker-compose mounts ./backend → /app
# So /app contains main.py, agents/, routers/, etc.
# To allow `from backend.xxx import yyy`, parent of /app must be on PYTHONPATH
# We'll put everything under /nexcart/backend/ instead.
WORKDIR /nexcart

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy backend source into /nexcart/backend/
COPY . /nexcart/backend/

# PYTHONPATH = /nexcart so `from backend.main import app` works
ENV PYTHONPATH=/nexcart

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Start uvicorn using the backend package path
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "/nexcart/backend"]
