"""
NexCart — FastAPI Application Entry Point
============================================
Main app: mounts routers, CORS, lifespan events,
request logging middleware, and global error handler.
"""

import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse

from backend.core.settings import settings, startup_health_check
from backend.database.connection import close_mongo_connection, connect_to_mongo
from backend.utils.logger import get_logger

logger = get_logger("main")


# ══════════════════════════════════════════════════════════════════
# LIFESPAN (startup + shutdown)
# ══════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown hooks."""
    # ── Startup ───────────────────────────────────────────────────
    logger.info("Starting NexCart API...")

    # 1. Connect to MongoDB
    try:
        await connect_to_mongo()
        from backend.routers.auth import bootstrap_admin
        await bootstrap_admin()
    except Exception as exc:
        logger.error(f"MongoDB connection failed: {exc}")

    # 2. Run health checks
    try:
        await startup_health_check()
    except Exception as exc:
        logger.error(f"Health check error: {exc}")

    # 3. Start APScheduler for disruption agent
    try:
        from backend.agents.disruption_agent import start_disruption_scheduler
        start_disruption_scheduler()
    except Exception as exc:
        logger.warning(f"Scheduler start failed: {exc}")

    yield

    # ── Shutdown ──────────────────────────────────────────────────
    logger.info("Shutting down NexCart API...")

    try:
        from backend.agents.disruption_agent import stop_disruption_scheduler
        stop_disruption_scheduler()
    except Exception as exc:
        logger.warning(f"Scheduler stop error: {exc}")

    await close_mongo_connection()
    logger.info("NexCart API shutdown complete")


# ══════════════════════════════════════════════════════════════════
# APP INSTANCE
# ══════════════════════════════════════════════════════════════════

app = FastAPI(
    title="NexCart API",
    version="1.0.0",
    description=(
        "AI Supply-Chain Disruption Radar + "
        "Hyper-Personalised Restock Nudging Platform"
    ),
    lifespan=lifespan,
)


# ══════════════════════════════════════════════════════════════════
# CORS MIDDLEWARE
# ══════════════════════════════════════════════════════════════════

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def authentication_middleware(request: Request, call_next):
    """Require a valid role-bearing token for all business API operations."""
    public_paths = {"/api/health", "/api/health/db", "/api/auth/login", "/api/auth/roles", "/docs", "/openapi.json", "/redoc"}
    if not request.url.path.startswith("/api/") or request.url.path in public_paths:
        return await call_next(request)
    from backend.security import allows, decode_access_token
    token = request.headers.get("Authorization", "").removeprefix("Bearer ").strip() or request.query_params.get("access_token", "")
    if not token:
        return JSONResponse(status_code=401, content={"detail": "Authentication required"})
    try:
        user = decode_access_token(token)
    except HTTPException as exc:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    if not allows(user["role"], request.method, request.url.path):
        return JSONResponse(status_code=403, content={"detail": "Your role is not allowed to perform this action"})
    request.state.user = user
    return await call_next(request)


# ══════════════════════════════════════════════════════════════════
# REQUEST LOGGING MIDDLEWARE
# ══════════════════════════════════════════════════════════════════

@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log method, path, status_code, and duration_ms for every request."""
    start_time = time.perf_counter()

    response = await call_next(request)

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    logger.info(
        f"{request.method} {request.url.path} -> {response.status_code} "
        f"({duration_ms}ms)",
        extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        },
    )

    return response


# ══════════════════════════════════════════════════════════════════
# GLOBAL EXCEPTION HANDLER
# ══════════════════════════════════════════════════════════════════

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Catch all unhandled exceptions and return a structured JSON error."""
    logger.error(f"Unhandled exception: {exc}", extra={"path": request.url.path})
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "path": request.url.path,
        },
    )


# ══════════════════════════════════════════════════════════════════
# MOUNT ROUTERS
# ══════════════════════════════════════════════════════════════════

from backend.routers.dashboard import router as dashboard_router
from backend.routers.auth import router as auth_router
from backend.routers.disruptions import router as disruptions_router
from backend.routers.nudges import router as nudges_router
from backend.routers.signals import router as signals_router
from backend.routers.skus import router as skus_router

app.include_router(dashboard_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
app.include_router(skus_router, prefix="/api")
app.include_router(disruptions_router, prefix="/api")
app.include_router(signals_router, prefix="/api")
app.include_router(nudges_router, prefix="/api")

# ══════════════════════════════════════════════════════════════════
# ROOT REDIRECT
# ══════════════════════════════════════════════════════════════════

@app.get("/", include_in_schema=False)
async def root_redirect():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs")

# End of application configuration.
