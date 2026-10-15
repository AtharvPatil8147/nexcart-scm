"""
NexCart — SKU Router
======================
CRUD + risk management endpoints for SKUs.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.database.collections import DISRUPTION_EVENTS, SIGNAL_LOGS, SKUS
from backend.database.connection import get_db
from backend.database.models import (
    RiskLevel, SKUBase, SKUResponse, SignalSource,
)
from backend.utils.logger import get_logger
from backend.utils.risk_scorer import RiskScorer

logger = get_logger("router.skus")
router = APIRouter(tags=["SKUs"])


# ── Response Models ───────────────────────────────────────────────

class PaginatedSKUResponse(BaseModel):
    items: list[SKUResponse] = []
    total: int = 0
    page: int = 1
    limit: int = 20
    pages: int = 0

class SKUDetailResponse(BaseModel):
    sku: SKUResponse
    recent_disruptions: list[dict[str, Any]] = []

class RiskOverrideRequest(BaseModel):
    risk_score: int = Field(..., ge=0, le=100, description="New risk score")
    risk_level: RiskLevel = Field(..., description="New risk level")
    reason: str = Field("Manual override", description="Reason for override")

class MessageResponse(BaseModel):
    message: str
    id: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────

def _serialize_doc(doc: dict) -> dict:
    """Convert MongoDB doc ObjectIds to strings."""
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])
    return doc


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/skus", response_model=PaginatedSKUResponse)
async def list_skus(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    category: Optional[str] = Query(None, description="Filter by category"),
    risk_level: Optional[str] = Query(None, description="Filter by risk level"),
    search: Optional[str] = Query(None, description="Search by name"),
):
    """Paginated SKU list, sorted by risk_score descending."""
    try:
        database = get_db()

        query: dict[str, Any] = {}
        if category:
            query["category"] = category
        if risk_level:
            query["risk_level"] = risk_level
        if search:
            query["name"] = {"$regex": search, "$options": "i"}

        total = await database[SKUS].count_documents(query)
        skip = (page - 1) * limit

        cursor = database[SKUS].find(query).sort("risk_score", -1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        items = [_serialize_doc(doc) for doc in items]

        return PaginatedSKUResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            pages=(total + limit - 1) // limit if limit > 0 else 0,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"list_skus error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/skus/{sku_id}", response_model=SKUDetailResponse)
async def get_sku(sku_id: str):
    """Single SKU + last 10 disruption events referencing it."""
    try:
        database = get_db()

        sku = await database[SKUS].find_one({"sku_id": sku_id})
        if not sku:
            raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' not found")

        sku = _serialize_doc(sku)

        cursor = (
            database[DISRUPTION_EVENTS]
            .find({"affected_sku_ids": sku_id})
            .sort("created_at", -1)
            .limit(10)
        )
        disruptions = await cursor.to_list(length=10)
        disruptions = [_serialize_doc(d) for d in disruptions]

        return SKUDetailResponse(sku=sku, recent_disruptions=disruptions)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_sku error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/skus", response_model=MessageResponse, status_code=201)
async def create_sku(sku: SKUBase):
    """Create a new SKU."""
    try:
        database = get_db()

        existing = await database[SKUS].find_one({"sku_id": sku.sku_id})
        if existing:
            raise HTTPException(
                status_code=409, detail=f"SKU '{sku.sku_id}' already exists"
            )

        doc = sku.model_dump()
        result = await database[SKUS].insert_one(doc)

        return MessageResponse(
            message=f"SKU '{sku.sku_id}' created successfully",
            id=str(result.inserted_id),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"create_sku error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/skus/{sku_id}/risk", response_model=SKUResponse)
async def override_risk(sku_id: str, override: RiskOverrideRequest):
    """Manually override risk level and score, log to signal_logs."""
    try:
        database = get_db()

        sku = await database[SKUS].find_one({"sku_id": sku_id})
        if not sku:
            raise HTTPException(status_code=404, detail=f"SKU '{sku_id}' not found")

        old_score = sku.get("risk_score", 0)

        await database[SKUS].update_one(
            {"sku_id": sku_id},
            {
                "$set": {
                    "risk_score": override.risk_score,
                    "risk_level": override.risk_level.value,
                    "last_updated": datetime.now(timezone.utc),
                }
            },
        )

        # Log the manual override to signal_logs
        await database[SIGNAL_LOGS].insert_one({
            "signal_id": f"MANUAL-{sku_id}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
            "source": "news",  # Using a valid SignalSource value
            "raw_payload": {
                "type": "manual_override",
                "sku_id": sku_id,
                "old_score": old_score,
                "new_score": override.risk_score,
                "new_level": override.risk_level.value,
                "reason": override.reason,
            },
            "processed_at": datetime.now(timezone.utc),
            "risk_delta": override.risk_score - old_score,
            "triggered_agent_run": False,
        })

        updated = await database[SKUS].find_one({"sku_id": sku_id})
        return _serialize_doc(updated)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"override_risk error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


print("✓ skus.py router complete")
