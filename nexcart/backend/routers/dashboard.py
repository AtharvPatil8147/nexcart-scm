"""
NexCart — Dashboard & Health Router
=====================================
Endpoints: /api/health, /api/health/db, /api/dashboard/stats
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.database.collections import (
    CUSTOMER_PROFILES, DISRUPTION_EVENTS, NUDGE_CAMPAIGNS, SIGNAL_LOGS, SKUS,
)
from backend.database.connection import get_db, ping_database
from backend.utils.logger import get_logger

logger = get_logger("router.dashboard")
router = APIRouter(tags=["Dashboard & Health"])


# ── Response Models ───────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = Field(..., description="App status")
    version: str = Field(..., description="App version")
    environment: str = Field(..., description="Current environment")

class DBHealthResponse(BaseModel):
    status: str
    latency_ms: Optional[float] = None
    detail: Optional[str] = None

class RiskDistribution(BaseModel):
    low: int = 0
    medium: int = 0
    high: int = 0
    critical: int = 0

class DashboardStatsResponse(BaseModel):
    total_skus: int = 0
    at_risk_count: int = 0
    nudges_sent_today: int = 0
    revenue_recovered_7d: float = 0.0
    signal_events_24h: int = 0
    risk_distribution: RiskDistribution = Field(default_factory=RiskDistribution)


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse)
async def health_check():
    """App status + version."""
    try:
        return HealthResponse(
            status="ok",
            version="1.0.0",
            environment=os.getenv("APP_ENV", "development"),
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/health/db", response_model=DBHealthResponse)
async def db_health_check():
    """MongoDB ping + latency."""
    try:
        result = await ping_database()
        return DBHealthResponse(**result)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/dashboard/stats", response_model=DashboardStatsResponse)
async def dashboard_stats():
    """Aggregated KPI stats from all collections."""
    try:
        database = get_db()

        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seven_days_ago = now - timedelta(days=7)
        twenty_four_hours_ago = now - timedelta(hours=24)

        # Total SKUs
        total_skus = await database[SKUS].count_documents({})

        # At-risk count
        at_risk_count = await database[SKUS].count_documents(
            {"risk_level": {"$in": ["high", "critical"]}}
        )

        # Risk distribution
        dist = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        pipeline = [
            {"$group": {"_id": "$risk_level", "count": {"$sum": 1}}}
        ]
        async for doc in database[SKUS].aggregate(pipeline):
            level = doc["_id"]
            if level in dist:
                dist[level] = doc["count"]

        # Nudges sent today
        nudges_sent_today = await database[NUDGE_CAMPAIGNS].count_documents(
            {"sent_at": {"$gte": today_start}}
        )

        # Revenue recovered last 7 days
        rev_pipeline = [
            {"$match": {"sent_at": {"$gte": seven_days_ago}}},
            {"$group": {"_id": None, "total": {"$sum": "$revenue_recovered"}}},
        ]
        rev_result = await database[NUDGE_CAMPAIGNS].aggregate(rev_pipeline).to_list(1)
        revenue_7d = rev_result[0]["total"] if rev_result else 0.0

        # Signal events last 24h
        signal_events_24h = await database[SIGNAL_LOGS].count_documents(
            {"processed_at": {"$gte": twenty_four_hours_ago}}
        )

        return DashboardStatsResponse(
            total_skus=total_skus,
            at_risk_count=at_risk_count,
            nudges_sent_today=nudges_sent_today,
            revenue_recovered_7d=round(revenue_7d, 2),
            signal_events_24h=signal_events_24h,
            risk_distribution=RiskDistribution(**dist),
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Dashboard stats error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


print("✓ dashboard.py router complete")
