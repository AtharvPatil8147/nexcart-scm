from datetime import datetime, timedelta, timezone

import pytest

from backend.permissions import has_permission
from backend.security import ROLE_LABELS, allows, create_access_token


def test_only_three_role_identifiers_are_supported():
    assert set(ROLE_LABELS) == {"admin", "manager", "viewer"}
    assert not has_permission("platform_admin", "users:view")
    assert not has_permission("operations_manager", "sku:update")


def test_all_roles_can_retrieve_their_authenticated_profile():
    for role in ("admin", "manager", "viewer"):
        assert allows(role, "GET", "/api/auth/me")


def test_admin_has_all_core_permissions():
    assert has_permission("admin", "users:view")
    assert has_permission("admin", "sku:create")
    assert has_permission("admin", "nudge_agent:run")


def test_manager_permissions():
    assert has_permission("manager", "sku:update")
    assert has_permission("manager", "disruption_agent:run")
    assert not has_permission("manager", "nudge_agent:run")
    assert not has_permission("manager", "users:view")
    assert allows("manager", "PATCH", "/api/skus/SKU-OPS-001")
    assert not allows("viewer", "PATCH", "/api/skus/SKU-OPS-001")


def test_viewer_is_read_only():
    assert has_permission("viewer", "dashboard:view")
    assert not has_permission("viewer", "sku:create")
    assert not has_permission("viewer", "nudge_agent:run")
    assert not has_permission("viewer", "users:view")


def test_access_token_contains_role_and_expiry():
    token = create_access_token({
        "email": "admin@nexcart.com",
        "name": "Admin",
        "role": "admin",
    })
    assert isinstance(token, str)
    assert token.count(".") == 2
