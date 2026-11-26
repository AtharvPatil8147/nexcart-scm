"""Password hashing, signed access tokens, and NexCart RBAC rules."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import HTTPException, status
from backend.core.settings import settings

TOKEN_TTL_MINUTES = settings.access_token_expire_minutes
PBKDF2_ITERATIONS = 600_000

ROLE_LABELS = {
    "platform_admin": "Platform administrator",
    "operations_manager": "Operations manager",
    "supply_analyst": "Supply analyst",
    "campaign_manager": "Campaign manager",
    "viewer": "Read-only viewer",
}


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    )


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        expected = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations)
        )
        return hmac.compare_digest(expected, base64.urlsafe_b64decode(digest))
    except (ValueError, TypeError):
        return False


def _b64encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode()


def _b64decode(value: str) -> bytes:
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


def create_access_token(user: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": user["email"],
        "name": user["name"],
        "role": user["role"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=TOKEN_TTL_MINUTES)).timestamp()),
    }
    header = {"alg": "HS256", "typ": "JWT"}
    signing_input = f"{_b64encode(json.dumps(header, separators=(',', ':')).encode())}.{_b64encode(json.dumps(payload, separators=(',', ':')).encode())}"
    signature = hmac.new(settings.app_secret_key.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        header, payload, signature = token.split(".")
        signing_input = f"{header}.{payload}".encode()
        expected = hmac.new(settings.app_secret_key.encode(), signing_input, hashlib.sha256).digest()
        if not hmac.compare_digest(expected, _b64decode(signature)):
            raise ValueError("invalid signature")
        data = json.loads(_b64decode(payload))
        if data.get("exp", 0) <= datetime.now(timezone.utc).timestamp() or data.get("role") not in ROLE_LABELS:
            raise ValueError("expired or invalid token")
        return data
    except (ValueError, KeyError, json.JSONDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired access token")


def allows(role: str, method: str, path: str) -> bool:
    """Map API operations to the least-privileged NexCart role."""
    if role == "platform_admin":
        return True
    if method == "GET":
        if path.startswith("/api/nudges"):
            return role == "campaign_manager"
        if path.startswith("/api/analytics"):
            return role in {"operations_manager", "supply_analyst", "campaign_manager"}
        return role in {"operations_manager", "supply_analyst", "campaign_manager", "viewer"}
    if path.startswith("/api/signals"):
        return role in {"operations_manager", "supply_analyst"}
    if path.startswith("/api/skus") or path.startswith("/api/disruptions"):
        return role == "operations_manager"
    if path.startswith("/api/nudges") or path.startswith("/api/agents/run-nudge"):
        return role == "campaign_manager"
    if path.startswith("/api/agents/run-disruption"):
        return role == "operations_manager"
    return False
