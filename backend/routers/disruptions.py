"""
NexCart — Disruptions Router
===============================
Endpoints for disruption events management.
"""

from datetime import datetime, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.database.collections import DISRUPTION_EVENTS
from backend.database.connection import get_db
from backend.database.models import DisruptionEventBase, DisruptionEventResponse
from backend.utils.logger import get_logger

logger = get_logger("router.disruptions")
router = APIRouter(tags=["Disruptions"])


# ── Response Models ───────────────────────────────────────────────

class PaginatedDisruptionResponse(BaseModel):
    items: list[DisruptionEventResponse] = []
    total: int = 0

class MessageResponse(BaseModel):
    message: str
    id: Optional[str] = None


def _serialize_doc(doc: dict) -> dict:
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])
    return doc


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/disruptions", response_model=PaginatedDisruptionResponse)
async def list_disruptions(
    source: Optional[str] = Query(None, description="Filter by source"),
    severity_min: Optional[int] = Query(None, ge=1, le=5, description="Minimum severity"),
    affected_region: Optional[str] = Query(None, description="Filter by affected region"),
    sku_id: Optional[str] = Query(None, description="Filter by affected SKU ID"),
    limit: int = Query(50, ge=1, le=100),
):
    """Last 50 disruption events, sorted by created_at descending."""
    try:
        database = get_db()

        query: dict[str, Any] = {}
        if source:
            query["source"] = source
        if severity_min:
            query["severity"] = {"$gte": severity_min}
        if affected_region:
            query["affected_regions"] = affected_region
        if sku_id:
            query["affected_sku_ids"] = sku_id

        total = await database[DISRUPTION_EVENTS].count_documents(query)
        cursor = database[DISRUPTION_EVENTS].find(query).sort("created_at", -1).limit(limit)
        items = await cursor.to_list(length=limit)
        items = [_serialize_doc(doc) for doc in items]

        return PaginatedDisruptionResponse(items=items, total=total)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"list_disruptions error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/disruptions/{event_id}", response_model=DisruptionEventResponse)
async def get_disruption(event_id: str):
    """Single disruption event by event_id."""
    try:
        database = get_db()

        doc = await database[DISRUPTION_EVENTS].find_one({"event_id": event_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Event '{event_id}' not found")

        return _serialize_doc(doc)

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_disruption error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/disruptions", response_model=MessageResponse, status_code=201)
async def create_disruption(event: DisruptionEventBase):
    """Manually create a disruption event."""
    try:
        database = get_db()

        doc = event.model_dump()
        # Serialize enum values
        if hasattr(doc.get("source"), "value"):
            doc["source"] = doc["source"].value
        if hasattr(doc.get("severity"), "value"):
            doc["severity"] = doc["severity"].value

        result = await database[DISRUPTION_EVENTS].insert_one(doc)

        return MessageResponse(
            message=f"Disruption event '{event.event_id}' created",
            id=str(result.inserted_id),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"create_disruption error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


print("✓ disruptions.py router complete")
