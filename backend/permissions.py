"""Centralized NexCart role and permission registry."""

from enum import Enum


class Permission(str, Enum):
    DASHBOARD_VIEW = "dashboard:view"
    SKU_VIEW = "sku:view"
    SKU_CREATE = "sku:create"
    SKU_UPDATE = "sku:update"
    SKU_DELETE = "sku:delete"
    SKU_RISK_OVERRIDE = "sku:risk_override"
    DISRUPTIONS_VIEW = "disruptions:view"
    DISRUPTIONS_MANAGE = "disruptions:manage"
    DISRUPTION_AGENT_RUN = "disruption_agent:run"
    SIGNALS_VIEW = "signals:view"
    SIGNALS_INGEST = "signals:ingest"
    NUDGES_VIEW = "nudges:view"
    NUDGES_MANAGE = "nudges:manage"
    NUDGE_AGENT_RUN = "nudge_agent:run"
    ANALYTICS_VIEW = "analytics:view"
    SETTINGS_VIEW = "settings:view"
    SETTINGS_MANAGE = "settings:manage"
    USERS_VIEW = "users:view"
    USERS_CREATE = "users:create"
    USERS_UPDATE = "users:update"
    USERS_DEACTIVATE = "users:deactivate"
    USERS_ASSIGN_ROLE = "users:assign_role"
    USERS_RESET_PASSWORD = "users:reset_password"
    AUDIT_LOGS_VIEW = "audit_logs:view"
    CUSTOMERS_VIEW = "customers:view"
    CUSTOMERS_MANAGE = "customers:manage"


ALL_PERMISSIONS = {permission.value for permission in Permission}

ROLE_PERMISSIONS: dict[str, set[str]] = {
    "admin": ALL_PERMISSIONS,
    "manager": {
        Permission.DASHBOARD_VIEW,
        Permission.SKU_VIEW,
        Permission.SKU_CREATE,
        Permission.SKU_UPDATE,
        Permission.SKU_RISK_OVERRIDE,
        Permission.DISRUPTIONS_VIEW,
        Permission.DISRUPTIONS_MANAGE,
        Permission.DISRUPTION_AGENT_RUN,
        Permission.SIGNALS_VIEW,
        Permission.SIGNALS_INGEST,
        Permission.ANALYTICS_VIEW,
        Permission.SETTINGS_VIEW,
    },
    "viewer": {
        Permission.DASHBOARD_VIEW,
        Permission.SKU_VIEW,
        Permission.DISRUPTIONS_VIEW,
        Permission.SIGNALS_VIEW,
        Permission.ANALYTICS_VIEW,
    },
}


def role_permissions(role: str) -> set[str]:
    return set(ROLE_PERMISSIONS.get(role, set()))


def has_permission(role: str, permission: str | Permission) -> bool:
    value = permission.value if isinstance(permission, Permission) else permission
    return value in role_permissions(role)
