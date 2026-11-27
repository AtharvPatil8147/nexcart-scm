"""Best-effort audit logging for administrative and operational actions."""

from datetime import datetime, timezone
from typing import Any, Optional

from backend.database.collections import AUDIT_LOGS
from backend.database.connection import get_db


async def record_audit(
    actor: Optional[dict[str, Any]],
    action: str,
    resource: str,
    resource_id: Optional[str] = None,
    metadata: Optional[dict[str, Any]] = None,
    success: bool = True,
) -> None:
    actor = actor or {}
    await get_db()[AUDIT_LOGS].insert_one({
        "actor_user_id": actor.get("id"),
        "actor_email": actor.get("email"),
        "actor_role": actor.get("role"),
        "action": action,
        "resource": resource,
        "resource_id": resource_id,
        "timestamp": datetime.now(timezone.utc),
        "metadata": metadata or {},
        "success": success,
    })
