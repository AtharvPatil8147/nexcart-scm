"""Platform-administrator user management and audit APIs."""

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field

from backend.audit import record_audit
from backend.database.collections import USERS, AUDIT_LOGS
from backend.database.connection import get_db
from backend.permissions import role_permissions
from backend.security import get_current_user, hash_password, require_permission

router = APIRouter(prefix="/users", tags=["User Management"])


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    role: str
    password: str = Field(min_length=12, max_length=256)


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[str] = None


class StatusRequest(BaseModel):
    active: bool


class PasswordResetRequest(BaseModel):
    password: str = Field(min_length=12, max_length=256)


def public_user(document: dict) -> dict:
    return {
        "id": str(document["_id"]),
        "name": document["name"],
        "email": document["email"],
        "role": document["role"],
        "active": document.get("active", True),
        "created_at": document.get("created_at"),
        "updated_at": document.get("updated_at"),
        "last_login": document.get("last_login"),
        "permissions": sorted(role_permissions(document["role"])),
    }


def validate_admin_role(role: str) -> None:
    if role not in role_permissions:
        raise HTTPException(status_code=422, detail="Unknown role")


@router.get("", dependencies=[require_permission("users:view")])
async def list_users(
    search: Optional[str] = Query(default=None),
    role: Optional[str] = Query(default=None),
    status_filter: Optional[str] = Query(default=None, alias="status"),
):
    query: dict = {}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
        ]
    if role:
        query["role"] = role
    if status_filter in {"active", "inactive"}:
        query["active"] = status_filter == "active"
    cursor = get_db()[USERS].find(query).sort("created_at", -1)
    documents = await cursor.to_list(length=500)
    return {"items": [public_user(document) for document in documents], "total": len(documents)}


@router.post("", status_code=201, dependencies=[require_permission("users:create")])
async def create_user(body: CreateUserRequest, current_user: dict = Depends(get_current_user)):
    validate_admin_role(body.role)
    email = body.email.lower()
    if await get_db()[USERS].find_one({"email": email}):
        raise HTTPException(status_code=409, detail="A user with this email already exists")
    now = datetime.now(timezone.utc)
    result = await get_db()[USERS].insert_one({
        "name": body.name.strip(),
        "email": email,
        "role": body.role,
        "password_hash": hash_password(body.password),
        "active": True,
        "created_at": now,
        "updated_at": now,
        "created_by": current_user["id"],
    })
    document = await get_db()[USERS].find_one({"_id": result.inserted_id})
    await record_audit(current_user, "user.created", "user", str(result.inserted_id), {"role": body.role, "email": email})
    return public_user(document)


@router.patch("/{user_id}", dependencies=[require_permission("users:update")])
async def update_user(user_id: str, body: UpdateUserRequest, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    target = await get_db()[USERS].find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    updates: dict = {}
    if body.name is not None:
        updates["name"] = body.name.strip()
    if body.email is not None:
        updates["email"] = body.email.lower()
        if await get_db()[USERS].find_one({"email": updates["email"], "_id": {"$ne": target["_id"]}}):
            raise HTTPException(status_code=409, detail="A user with this email already exists")
    if body.role is not None:
        validate_admin_role(body.role)
        updates["role"] = body.role
        if target.get("role") == "admin" and body.role != "admin" and target.get("active", True):
            active_admin_count = await get_db()[USERS].count_documents({"role": "admin", "active": True})
            if active_admin_count <= 1:
                raise HTTPException(status_code=409, detail="The last active administrator cannot lose administrator role")
    updates["updated_at"] = datetime.now(timezone.utc)
    await get_db()[USERS].update_one({"_id": target["_id"]}, {"$set": updates})
    updated = await get_db()[USERS].find_one({"_id": target["_id"]})
    await record_audit(current_user, "user.updated", "user", user_id, {"changes": list(updates.keys())})
    return public_user(updated)


@router.patch("/{user_id}/status", dependencies=[require_permission("users:deactivate")])
async def set_status(user_id: str, body: StatusRequest, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    target = await get_db()[USERS].find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if str(target["_id"]) == current_user["id"] and not body.active:
        raise HTTPException(status_code=409, detail="You cannot deactivate your own account")
    if target["role"] == "admin" and not body.active:
        active_admin_count = await get_db()[USERS].count_documents({"role": "admin", "active": True})
        if active_admin_count <= 1:
            raise HTTPException(status_code=409, detail="The last active administrator cannot be deactivated")
    await get_db()[USERS].update_one({"_id": target["_id"]}, {"$set": {"active": body.active, "updated_at": datetime.now(timezone.utc)}})
    await record_audit(current_user, "user.reactivated" if body.active else "user.deactivated", "user", user_id)
    return public_user(await get_db()[USERS].find_one({"_id": target["_id"]}))


@router.post("/{user_id}/reset-password", dependencies=[require_permission("users:reset_password")])
async def reset_password(user_id: str, body: PasswordResetRequest, current_user: dict = Depends(get_current_user)):
    from bson import ObjectId
    if not ObjectId.is_valid(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    target = await get_db()[USERS].find_one({"_id": ObjectId(user_id)})
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    await get_db()[USERS].update_one({"_id": target["_id"]}, {"$set": {
        "password_hash": hash_password(body.password),
        "updated_at": datetime.now(timezone.utc),
    }})
    await record_audit(current_user, "user.password_reset", "user", user_id)
    return {"message": "Password reset successfully"}


@router.get("/audit/logs", dependencies=[require_permission("audit_logs:view")])
async def audit_logs(limit: int = Query(default=100, ge=1, le=500)):
    cursor = get_db()[AUDIT_LOGS].find({}).sort("timestamp", -1).limit(limit)
    items = await cursor.to_list(length=limit)
    for item in items:
        item["_id"] = str(item["_id"])
    return {"items": items, "total": len(items)}
