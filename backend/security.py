"""Password hashing, signed access tokens, and NexCart RBAC rules."""

import base64
import hashlib
import hmac
import json
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any
from typing import Optional

from fastapi import Depends, Header, HTTPException, status
from backend.core.settings import settings
from backend.database.collections import USERS
from backend.database.connection import get_db
from backend.permissions import has_permission

TOKEN_TTL_MINUTES = settings.access_token_expire_minutes
PBKDF2_ITERATIONS = 600_000

ROLE_LABELS = {
    "admin": "Admin",
    "manager": "Manager",
    "viewer": "Viewer",
}

VALID_ROLES = set(ROLE_LABELS)


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
    """Map HTTP operations to centralized permissions."""
    if path == "/api/auth/me":
        permission = "dashboard:view"
    elif path.startswith("/api/dashboard") or path == "/api/health":
        permission = "dashboard:view"
    elif path.startswith("/api/skus"):
        permission = (
            "sku:view" if method == "GET"
            else "sku:create" if method == "POST"
            else "sku:risk_override" if method == "PATCH" and path.endswith("/risk")
            else "sku:update" if method in {"PATCH", "PUT"}
            else "sku:delete" if method == "DELETE"
            else "sku:view"
        )
    elif path.startswith("/api/disruptions"):
        permission = "disruptions:view" if method == "GET" else "disruptions:manage"
    elif path.startswith("/api/signals"):
        permission = "signals:view" if method == "GET" else "signals:ingest"
    elif path.startswith("/api/nudges"):
        permission = "nudges:view" if method == "GET" else "nudges:manage"
    elif path.startswith("/api/analytics"):
        permission = "analytics:view"
    elif path.startswith("/api/agents/run-disruption"):
        permission = "disruption_agent:run"
    elif path.startswith("/api/agents/run-nudge"):
        permission = "nudge_agent:run"
    elif path.startswith("/api/customers"):
        permission = "customers:view" if method == "GET" else "customers:manage"
    elif path.startswith("/api/settings"):
        permission = "settings:view" if method == "GET" else "settings:manage"
    elif path.startswith("/api/users"):
        if path.endswith("/reset-password"):
            permission = "users:reset_password"
        elif path.endswith("/status"):
            permission = "users:deactivate"
        elif method == "POST":
            permission = "users:create"
        elif method == "PATCH":
            permission = "users:update"
        else:
            permission = "users:view"
    elif path.startswith("/api/audit"):
        permission = "audit_logs:view"
    else:
        return role == "admin"
    return has_permission(role, permission)


async def get_current_user(authorization: Optional[str] = Header(default=None), access_token: Optional[str] = None) -> dict[str, Any]:
    token = ""
    if authorization:
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        token = access_token or ""
    if not token:
        raise HTTPException(status_code=401, detail="Authentication required")
    payload = decode_access_token(token)
    user = await get_db()[USERS].find_one({"email": payload["sub"], "active": True})
    if not user:
        raise HTTPException(status_code=401, detail="Inactive or unknown user")
    if user["role"] != payload.get("role"):
        raise HTTPException(status_code=401, detail="Access token is stale; please sign in again")
    return {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "active": True,
    }


def require_permission(permission: str):
    async def dependency(current_user: dict[str, Any] = Depends(get_current_user)):
        if not has_permission(current_user["role"], permission):
            raise HTTPException(status_code=403, detail="You do not have permission to perform this action")
        return current_user
    return Depends(dependency)
