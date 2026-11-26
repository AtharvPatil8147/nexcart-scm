"""Authentication endpoints and first-admin bootstrap."""

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from backend.database.collections import USERS
from backend.database.connection import get_db
from backend.core.settings import settings
from backend.security import ROLE_LABELS, create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=256)


class UserResponse(BaseModel):
    email: EmailStr
    name: str
    role: str


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
            "role": "platform_admin",
            "password_hash": hash_password(password),
            "active": True,
            "created_at": datetime.now(timezone.utc),
        })


@router.post("/login", response_model=LoginResponse)
async def login(credentials: LoginRequest):
    user = await get_db()[USERS].find_one({"email": credentials.email.lower(), "active": True})
    if not user or not verify_password(credentials.password, user.get("password_hash", "")):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    public_user = {"email": user["email"], "name": user["name"], "role": user["role"]}
    return LoginResponse(access_token=create_access_token(public_user), user=public_user)


@router.get("/roles")
async def list_roles():
    """Describe roles for the login and later user-admin screens."""
    return ROLE_LABELS
