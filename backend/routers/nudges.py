"""
NexCart — Nudges, Analytics, Agents, & Customers Router
==========================================================
Nudge campaigns, analytics, agent triggers, and customer management.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from bson import ObjectId
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from backend.database.collections import (
    CUSTOMER_PROFILES, NUDGE_CAMPAIGNS, SKUS,
)
from backend.database.connection import get_db
from backend.database.models import (
    CustomerProfileBase, CustomerProfileResponse,
    NudgeCampaignResponse, NudgeStatus,
)
from backend.utils.logger import get_logger

logger = get_logger("router.nudges")
router = APIRouter(tags=["Nudges & Analytics"])


# ── Response Models ───────────────────────────────────────────────

class PaginatedNudgeResponse(BaseModel):
    items: list[NudgeCampaignResponse] = []
    total: int = 0
    page: int = 1
    limit: int = 20

class StatusUpdateRequest(BaseModel):
    status: NudgeStatus = Field(..., description="New status")
    revenue_recovered: Optional[float] = Field(None, ge=0, description="Revenue if converted")

class ConversionFunnel(BaseModel):
    sent: int = 0
    opened: int = 0
    converted: int = 0
    open_rate: float = 0.0
    conversion_rate: float = 0.0

class RiskTrendPoint(BaseModel):
    date: str
    avg_risk_score: float
    at_risk_count: int

class RiskTrendResponse(BaseModel):
    trend: list[RiskTrendPoint] = []

class AgentRunResponse(BaseModel):
    status: str
    started_at: str
    detail: Optional[str] = None

class NudgeAgentRequest(BaseModel):
    sku_ids: list[str] = Field(default_factory=list, description="SKU IDs to process")

class PaginatedCustomerResponse(BaseModel):
    items: list[CustomerProfileResponse] = []
    total: int = 0
    page: int = 1
    limit: int = 20

class MessageResponse(BaseModel):
    message: str
    id: Optional[str] = None


def _serialize_doc(doc: dict) -> dict:
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])
    return doc


# ══════════════════════════════════════════════════════════════════
# NUDGE CAMPAIGN ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/nudges", response_model=PaginatedNudgeResponse)
async def list_nudges(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    channel: Optional[str] = Query(None),
    sku_id: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None, description="ISO date string"),
    date_to: Optional[str] = Query(None, description="ISO date string"),
):
    """All nudge campaigns, paginated with filters."""
    try:
        database = get_db()

        query: dict[str, Any] = {}
        if status:
            query["status"] = status
        if channel:
            query["channel"] = channel
        if sku_id:
            query["sku_id"] = sku_id
        if date_from or date_to:
            date_filter: dict[str, Any] = {}
            if date_from:
                date_filter["$gte"] = datetime.fromisoformat(date_from)
            if date_to:
                date_filter["$lte"] = datetime.fromisoformat(date_to)
            query["sent_at"] = date_filter

        total = await database[NUDGE_CAMPAIGNS].count_documents(query)
        skip = (page - 1) * limit
        cursor = (
            database[NUDGE_CAMPAIGNS].find(query)
            .sort("sent_at", -1)
            .skip(skip)
            .limit(limit)
        )
        items = await cursor.to_list(length=limit)
        items = [_serialize_doc(doc) for doc in items]

        return PaginatedNudgeResponse(
            items=items, total=total, page=page, limit=limit
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"list_nudges error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/nudges/{campaign_id}", response_model=NudgeCampaignResponse)
async def get_nudge(campaign_id: str):
    """Single campaign detail."""
    try:
        database = get_db()

        doc = await database[NUDGE_CAMPAIGNS].find_one({"campaign_id": campaign_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

        return _serialize_doc(doc)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"get_nudge error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.patch("/nudges/{campaign_id}/status", response_model=NudgeCampaignResponse)
async def update_nudge_status(campaign_id: str, update: StatusUpdateRequest):
    """Update campaign status (opened, converted)."""
    try:
        database = get_db()

        doc = await database[NUDGE_CAMPAIGNS].find_one({"campaign_id": campaign_id})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")

        update_fields: dict[str, Any] = {"status": update.status.value}
        if update.status == NudgeStatus.OPENED:
            update_fields["opened_at"] = datetime.now(timezone.utc)
        if update.status == NudgeStatus.CONVERTED and update.revenue_recovered is not None:
            update_fields["revenue_recovered"] = update.revenue_recovered

        await database[NUDGE_CAMPAIGNS].update_one(
            {"campaign_id": campaign_id}, {"$set": update_fields}
        )

        updated = await database[NUDGE_CAMPAIGNS].find_one({"campaign_id": campaign_id})
        return _serialize_doc(updated)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"update_nudge_status error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ══════════════════════════════════════════════════════════════════
# ANALYTICS ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/analytics/nudge-conversion", response_model=ConversionFunnel)
async def nudge_conversion():
    """Campaign conversion funnel: sent, opened, converted counts + rates."""
    try:
        database = get_db()

        pipeline = [
            {"$group": {"_id": "$status", "count": {"$sum": 1}}}
        ]
        results = await database[NUDGE_CAMPAIGNS].aggregate(pipeline).to_list(10)

        counts = {r["_id"]: r["count"] for r in results}
        sent = counts.get("sent", 0) + counts.get("opened", 0) + counts.get("converted", 0)
        opened = counts.get("opened", 0) + counts.get("converted", 0)
        converted = counts.get("converted", 0)

        return ConversionFunnel(
            sent=sent,
            opened=opened,
            converted=converted,
            open_rate=round(opened / sent * 100, 1) if sent > 0 else 0.0,
            conversion_rate=round(converted / sent * 100, 1) if sent > 0 else 0.0,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"nudge_conversion error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/analytics/risk-trend", response_model=RiskTrendResponse)
async def risk_trend():
    """30-day risk score time series."""
    try:
        database = get_db()

        now = datetime.now(timezone.utc)
        thirty_days_ago = now - timedelta(days=30)

        # Use signal_logs to build a daily trend
        pipeline = [
            {"$match": {"processed_at": {"$gte": thirty_days_ago}}},
            {
                "$group": {
                    "_id": {
                        "$dateToString": {"format": "%Y-%m-%d", "date": "$processed_at"}
                    },
                    "avg_risk_delta": {"$avg": "$risk_delta"},
                    "count": {"$sum": 1},
                }
            },
            {"$sort": {"_id": 1}},
        ]
        results = await database["signal_logs"].aggregate(pipeline).to_list(31)

        # Also get current risk distribution for at_risk_count per day
        at_risk = await database[SKUS].count_documents(
            {"risk_level": {"$in": ["high", "critical"]}}
        )

        all_skus_pipeline = [
            {"$group": {"_id": None, "avg": {"$avg": "$risk_score"}}}
        ]
        avg_result = await database[SKUS].aggregate(all_skus_pipeline).to_list(1)
        current_avg = avg_result[0]["avg"] if avg_result else 0

        trend = []
        for r in results:
            trend.append(RiskTrendPoint(
                date=r["_id"],
                avg_risk_score=round(current_avg + r.get("avg_risk_delta", 0), 1),
                at_risk_count=at_risk,
            ))

        # Fill in missing days
        if not trend:
            for i in range(30):
                d = (now - timedelta(days=29 - i)).strftime("%Y-%m-%d")
                trend.append(RiskTrendPoint(
                    date=d, avg_risk_score=round(current_avg, 1), at_risk_count=at_risk
                ))

        return RiskTrendResponse(trend=trend)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"risk_trend error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ══════════════════════════════════════════════════════════════════
# AGENT TRIGGER ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.post("/agents/run-disruption", response_model=AgentRunResponse)
async def trigger_disruption_agent():
    """Trigger Layer 1 disruption agent manually."""
    try:
        from backend.agents.disruption_agent import run_disruption_agent

        started_at = datetime.now(timezone.utc).isoformat()
        # Run in background
        asyncio.create_task(run_disruption_agent())

        return AgentRunResponse(
            status="started",
            started_at=started_at,
            detail="Disruption agent pipeline started in background",
        )
    except Exception as exc:
        logger.error(f"trigger_disruption_agent error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/agents/run-nudge", response_model=AgentRunResponse)
async def trigger_nudge_agent(body: NudgeAgentRequest):
    """Trigger Layer 2 nudge agent manually."""
    try:
        from backend.agents.nudge_agent import run_nudge_agent

        started_at = datetime.now(timezone.utc).isoformat()
        asyncio.create_task(run_nudge_agent(sku_ids=body.sku_ids))

        return AgentRunResponse(
            status="started",
            started_at=started_at,
            detail=f"Nudge agent started for {len(body.sku_ids)} SKUs" if body.sku_ids else "Nudge agent started (auto-detect)",
        )
    except Exception as exc:
        logger.error(f"trigger_nudge_agent error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


# ══════════════════════════════════════════════════════════════════
# CUSTOMER ENDPOINTS
# ══════════════════════════════════════════════════════════════════

@router.get("/customers", response_model=PaginatedCustomerResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="Search by name or email"),
):
    """Paginated customer list."""
    try:
        database = get_db()

        query: dict[str, Any] = {}
        if search:
            query["$or"] = [
                {"name": {"$regex": search, "$options": "i"}},
                {"email": {"$regex": search, "$options": "i"}},
            ]

        total = await database[CUSTOMER_PROFILES].count_documents(query)
        skip = (page - 1) * limit
        cursor = database[CUSTOMER_PROFILES].find(query).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        items = [_serialize_doc(doc) for doc in items]

        return PaginatedCustomerResponse(
            items=items, total=total, page=page, limit=limit
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"list_customers error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/customers", response_model=MessageResponse, status_code=201)
async def create_customer(customer: CustomerProfileBase):
    """Create customer profile."""
    try:
        database = get_db()

        existing = await database[CUSTOMER_PROFILES].find_one(
            {"customer_id": customer.customer_id}
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Customer '{customer.customer_id}' already exists",
            )

        doc = customer.model_dump()
        result = await database[CUSTOMER_PROFILES].insert_one(doc)

        return MessageResponse(
            message=f"Customer '{customer.customer_id}' created",
            id=str(result.inserted_id),
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"create_customer error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


print("✓ nudges.py router complete")
