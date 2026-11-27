"""Authentication endpoints and first-admin bootstrap."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, EmailStr, Field

from backend.database.collections import USERS
from backend.database.connection import get_db
from backend.core.settings import settings
from backend.security import ROLE_LABELS, create_access_token, hash_password, verify_password, get_current_user
from backend.permissions import role_permissions

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    id: str | None = None
    email: EmailStr
    name: str
    role: str
    active: bool = True
    permissions: list[str] = []


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


async def bootstrap_admin() -> None:
    """Create the first admin once when explicit bootstrap credentials are supplied."""
    email = settings.bootstrap_admin_email
    password = settings.bootstrap_admin_password
    if not email or not password:
        return
    if len(password) < 12:
        raise RuntimeError("BOOTSTRAP_ADMIN_PASSWORD must contain at least 12 characters")
    database = get_db()
    if await database[USERS].count_documents({}) == 0:
        await database[USERS].insert_one({
            "email": email,
            "name": settings.bootstrap_admin_name,
            "role": "admin",
            "password_hash": hash_password(password),
            "active": True,
            "created_at": datetime.now(timezone.utc),
        })


async def bootstrap_demo_accounts() -> None:
    """Create local demonstration accounts for the three supported roles."""
    if settings.app_env == "production":
        return

    database = get_db()
    now = datetime.now(timezone.utc)
    demo_accounts = [
        {
            "name": "Demo Administrator",
            "email": "admin@nexcart.com",
            "role": "admin",
            "password": "Admin@123456",
        },
        {
            "name": "Demo Manager",
            "email": "manager@nexcart.com",
            "role": "manager",
            "password": "Manager@123456",
        },
        {
            "name": "Demo Viewer",
            "email": "viewer@nexcart.com",
            "role": "viewer",
            "password": "Viewer@123456",
        },
    ]

    for account in demo_accounts:
        existing = await database[USERS].find_one({"email": account["email"]})
        if existing:
            await database[USERS].update_one(
                {"_id": existing["_id"]},
                {"$set": {
                    "name": account["name"],
                    "role": account["role"],
                    "password_hash": hash_password(account["password"]),
                    "active": True,
                    "updated_at": now,
                }},
            )
        else:
            await database[USERS].insert_one({
                "name": account["name"],
                "email": account["email"],
                "role": account["role"],
                "password_hash": hash_password(account["password"]),
                "active": True,
                "created_at": now,
                "updated_at": now,
                "created_by": "system",
            })


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    user = await get_db()[USERS].find_one({"email": credentials.email.lower(), "active": True})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    await get_db()[USERS].update_one(
        {"_id": user["_id"]},
        {"$set": {"last_login": datetime.now(timezone.utc), "updated_at": datetime.now(timezone.utc)}},
    )
    public_user = {
        "id": str(user["_id"]),
        "email": user["email"],
        "name": user["name"],
        "role": user["role"],
        "active": user.get("active", True),
        "permissions": sorted(role_permissions(user["role"])),
    }
    return LoginResponse(access_token=create_access_token(public_user), user=public_user)


@router.get("/me", response_model=UserResponse)
async def current_user(current_user: dict = Depends(get_current_user)):
    current_user["permissions"] = sorted(role_permissions(current_user["role"]))
    return UserResponse(**current_user)


@router.get("/roles")
async def list_roles():
    """Describe roles for the login and later user-admin screens."""
    return ROLE_LABELS
