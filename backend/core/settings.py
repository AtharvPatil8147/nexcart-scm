"""Single source of truth for NexCart runtime configuration."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    mongodb_uri: str = os.getenv("MONGODB_URI", "")
    mongodb_db_name: str = os.getenv("MONGODB_DB_NAME", "nexcart")
    aws_access_key_id: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret_access_key: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    bedrock_model_id: str = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-4-5")
    eventbridge_bus_name: str = os.getenv("EVENTBRIDGE_BUS_NAME", "nexcart-events")
    eventbridge_source: str = os.getenv("EVENTBRIDGE_SOURCE", "com.nexcart.signals")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    openweather_api_key: str = os.getenv("OPENWEATHER_API_KEY", "")
    marine_traffic_api_key: str = os.getenv("MARINE_TRAFFIC_API_KEY", "")
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    firebase_server_key: str = os.getenv("FIREBASE_SERVER_KEY", "")
    frontend_url: str = os.getenv("FRONTEND_URL", "http://localhost:5173")
    app_env: str = os.getenv("APP_ENV", "development")
    app_secret_key: str = os.getenv("APP_SECRET_KEY", "")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    signal_poll_interval_seconds: int = int(os.getenv("SIGNAL_POLL_INTERVAL_SECONDS", "300"))
    access_token_expire_minutes: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    bootstrap_admin_email: str = os.getenv("BOOTSTRAP_ADMIN_EMAIL", "").strip().lower()
    bootstrap_admin_password: str = os.getenv("BOOTSTRAP_ADMIN_PASSWORD", "")
    bootstrap_admin_name: str = os.getenv("BOOTSTRAP_ADMIN_NAME", "NexCart Administrator")
    app_name: str = "NexCart"
    app_version: str = "1.0.0"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_runtime(self) -> None:
        if self.app_env not in {"development", "staging", "production"}:
            raise RuntimeError("APP_ENV must be development, staging, or production")
        if not 1 <= self.backend_port <= 65535:
            raise RuntimeError("BACKEND_PORT must be between 1 and 65535")
        if self.signal_poll_interval_seconds <= 0:
            raise RuntimeError("SIGNAL_POLL_INTERVAL_SECONDS must be positive")
        if self.is_production and (len(self.app_secret_key) < 32 or self.app_secret_key.startswith("change_this")):
            raise RuntimeError("Production requires a unique APP_SECRET_KEY of at least 32 characters")


settings = Settings()


async def startup_health_check() -> None:
    """Log non-secret dependency health after configuration validation."""
    from backend.database.connection import ping_database
    from backend.utils.logger import get_logger

    settings.validate_runtime()
    logger = get_logger("startup")
    logger.info("Starting %s v%s in %s", settings.app_name, settings.app_version, settings.app_env)
    db_status = await ping_database()
    if db_status["status"] == "ok":
        logger.info("MongoDB ping OK — latency %sms", db_status["latency_ms"])
    else:
        logger.error("MongoDB ping failed — %s", db_status.get("detail", "unknown error"))
    if not (settings.aws_access_key_id and settings.aws_secret_access_key):
        logger.warning("AWS credentials not configured; Bedrock and EventBridge are disabled")
    if not settings.news_api_key:
        logger.warning("NEWS_API_KEY not configured; Google News RSS remains available")
