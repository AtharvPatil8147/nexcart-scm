"""
NexCart — Central Configuration Loader
========================================
Loads all environment variables into a typed Settings class
and provides a startup health-check function.
"""

import os
from typing import Optional

from dotenv import load_dotenv

# Load .env file before anything else
load_dotenv()


class Settings:
    """Typed configuration loaded from environment variables."""

    # ── MongoDB ───────────────────────────────────────────────────
    MONGODB_URI: str = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "nexcart")

    # ── AWS Bedrock ───────────────────────────────────────────────
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    BEDROCK_MODEL_ID: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-4-5")

    # ── AWS EventBridge ───────────────────────────────────────────
    EVENTBRIDGE_BUS_NAME: str = os.getenv("EVENTBRIDGE_BUS_NAME", "nexcart-events")
    EVENTBRIDGE_SOURCE: str = os.getenv("EVENTBRIDGE_SOURCE", "com.nexcart.signals")

    # ── External Signal APIs ──────────────────────────────────────
    NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    MARINE_TRAFFIC_API_KEY: str = os.getenv("MARINE_TRAFFIC_API_KEY", "")

    # ── Notifications ─────────────────────────────────────────────
    SMTP_HOST: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER: str = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")
    FIREBASE_SERVER_KEY: str = os.getenv("FIREBASE_SERVER_KEY", "")

    # ── App ───────────────────────────────────────────────────────
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change_this_to_a_random_string")
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    BACKEND_PORT: int = int(os.getenv("BACKEND_PORT", "8000"))
    SIGNAL_POLL_INTERVAL_SECONDS: int = int(os.getenv("SIGNAL_POLL_INTERVAL_SECONDS", "300"))

    # ── Derived ───────────────────────────────────────────────────
    APP_NAME: str = "NexCart"
    APP_VERSION: str = "1.0.0"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"


# Singleton instance used across the app
settings = Settings()


async def startup_health_check() -> None:
    """
    Run on application startup to verify all critical services.
    - Pings MongoDB and logs the result
    - Checks AWS credentials are present
    - Prints a startup banner
    """
    from backend.database.connection import ping_database
    from backend.utils.logger import get_logger

    logger = get_logger("startup")

    # ── Startup Banner ────────────────────────────────────────────
    banner = (
        "\n"
        "══════════════════════════════════════════════════════════\n"
        f"  🚀  {settings.APP_NAME} v{settings.APP_VERSION}\n"
        f"  📦  Environment : {settings.APP_ENV}\n"
        f"  🌐  Backend     : http://localhost:{settings.BACKEND_PORT}\n"
        f"  🖥️   Frontend    : {settings.FRONTEND_URL}\n"
        "══════════════════════════════════════════════════════════"
    )
    print(banner)
    logger.info("Starting NexCart health checks...")

    # ── MongoDB Ping ──────────────────────────────────────────────
    db_status = await ping_database()
    if db_status["status"] == "ok":
        logger.info(f"MongoDB ping OK — latency {db_status['latency_ms']}ms")
    else:
        logger.error(f"MongoDB ping FAILED — {db_status.get('detail', 'unknown error')}")

    # ── AWS Credentials Check ─────────────────────────────────────
    aws_ok = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY)
    if aws_ok:
        logger.info("AWS credentials present ✓")
    else:
        logger.warning("AWS credentials NOT set — Bedrock/EventBridge will not work")

    # ── API Keys Check ────────────────────────────────────────────
    missing_keys = []
    if not settings.NEWS_API_KEY:
        missing_keys.append("NEWS_API_KEY")
    if not settings.OPENWEATHER_API_KEY:
        missing_keys.append("OPENWEATHER_API_KEY")
    if missing_keys:
        logger.warning(f"Missing API keys: {', '.join(missing_keys)}")
    else:
        logger.info("External API keys present ✓")

    logger.info("Startup health checks complete")


print("✓ config.py complete")
