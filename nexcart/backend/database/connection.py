"""
NexCart — MongoDB Async Connection (motor)
===========================================
Handles database lifecycle: connect, disconnect, ping, and
index creation for all 5 collections.
"""

import os
import time
from typing import Optional

import pymongo
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

from backend.database.collections import (
    CUSTOMER_PROFILES,
    DISRUPTION_EVENTS,
    NUDGE_CAMPAIGNS,
    SIGNAL_LOGS,
    SKUS,
)

# ══════════════════════════════════════════════════════════════════
# USER ENTRY POINT — paste your Atlas connection string in .env
# ══════════════════════════════════════════════════════════════════
MONGODB_URI: Optional[str] = os.getenv("MONGODB_URI")
# ↑ USER ENTRY POINT: set MONGODB_URI in your .env file

MONGODB_DB_NAME: str = os.getenv("MONGODB_DB_NAME", "nexcart")

# ── Global references (populated by connect_to_mongo) ─────────────
client: Optional[AsyncIOMotorClient] = None
db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo() -> None:
    """Establish MongoDB connection and create all required indexes."""
    global client, db

    uri = MONGODB_URI or os.getenv("MONGODB_URI")
    if not uri:
        raise ConnectionFailure(
            "\n══════════════════════════════════════════════════════════\n"
            "  ❌  MONGODB_URI is not set!\n"
            "  Please add your MongoDB Atlas connection string to .env:\n"
            "    MONGODB_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net\n"
            "══════════════════════════════════════════════════════════\n"
        )

    try:
        client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000, connectTimeoutMS=5000)
        await client.admin.command("ping")
        db = client[MONGODB_DB_NAME]
        print(f"✓ Connected to MongoDB database: {MONGODB_DB_NAME}")
        await _create_indexes()
    except (ConnectionFailure, ServerSelectionTimeoutError) as exc:
        print(
            "\n══════════════════════════════════════════════════════════\n"
            "  ❌  Failed to connect to MongoDB!\n"
            "  Please check your MONGODB_URI in .env.\n"
            f"  Error: {exc}\n"
            "══════════════════════════════════════════════════════════\n"
        )
        raise


async def close_mongo_connection() -> None:
    """Close the MongoDB connection gracefully."""
    global client, db
    if client is not None:
        client.close()
        client = None
        db = None
        print("✓ MongoDB connection closed")


def get_db() -> AsyncIOMotorDatabase:
    """
    Return the current database reference.

    All routers and agents should call ``get_db()`` instead of importing
    the module-level ``db`` variable directly, because a bare import
    captures the initial ``None`` value and never sees the reference
    that ``connect_to_mongo()`` assigns later.
    """
    if db is None:
        raise ConnectionFailure("MongoDB is not connected — call connect_to_mongo() first")
    return db


async def ping_database() -> dict:
    """Ping MongoDB and return status + latency."""
    if client is None:
        return {"status": "error", "detail": "MongoDB client not initialised"}
    try:
        start = time.perf_counter()
        await client.admin.command("ping")
        latency_ms = round((time.perf_counter() - start) * 1000, 2)
        return {"status": "ok", "latency_ms": latency_ms}
    except Exception as exc:
        return {"status": "error", "detail": str(exc)}


async def _create_indexes() -> None:
    """Create indexes for all 5 collections on first connect."""
    if db is None:
        return

    # skus: unique on sku_id, regular on risk_level
    skus_col = db[SKUS]
    await skus_col.create_index([("sku_id", pymongo.ASCENDING)], unique=True, name="idx_sku_id_unique")
    await skus_col.create_index([("risk_level", pymongo.ASCENDING)], name="idx_risk_level")

    # disruption_events: descending on created_at, regular on affected_sku_ids
    dis_col = db[DISRUPTION_EVENTS]
    await dis_col.create_index([("created_at", pymongo.DESCENDING)], name="idx_created_at_desc")
    await dis_col.create_index([("affected_sku_ids", pymongo.ASCENDING)], name="idx_affected_sku_ids")

    # customer_profiles: unique on customer_id, regular on email
    cust_col = db[CUSTOMER_PROFILES]
    await cust_col.create_index([("customer_id", pymongo.ASCENDING)], unique=True, name="idx_customer_id_unique")
    await cust_col.create_index([("email", pymongo.ASCENDING)], name="idx_email")

    # nudge_campaigns: regular on sku_id, status, sent_at
    nudge_col = db[NUDGE_CAMPAIGNS]
    await nudge_col.create_index([("sku_id", pymongo.ASCENDING)], name="idx_nudge_sku_id")
    await nudge_col.create_index([("status", pymongo.ASCENDING)], name="idx_nudge_status")
    await nudge_col.create_index([("sent_at", pymongo.ASCENDING)], name="idx_nudge_sent_at")

    # signal_logs: descending on processed_at
    sig_col = db[SIGNAL_LOGS]
    await sig_col.create_index([("processed_at", pymongo.DESCENDING)], name="idx_processed_at_desc")

    print("✓ All collection indexes ready")


print("✓ connection.py complete")
