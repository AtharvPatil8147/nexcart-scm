"""
NexCart — Signals Router
==========================
SSE stream, manual signal ingestion, and signal log history.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from backend.database.collections import SIGNAL_LOGS
from backend.database.connection import get_db
from backend.database.models import SignalLogBase, SignalLogResponse
from backend.utils.logger import get_logger

logger = get_logger("router.signals")
router = APIRouter(tags=["Signals"])


# ── Response Models ───────────────────────────────────────────────

class PaginatedSignalResponse(BaseModel):
    items: list[SignalLogResponse] = []
    total: int = 0
    page: int = 1
    limit: int = 50

class IngestResponse(BaseModel):
    message: str
    signal_id: str
    agent_triggered: bool = False


def _serialize_doc(doc: dict) -> dict:
    if doc.get("_id"):
        doc["_id"] = str(doc["_id"])

    # Extract display fields from raw_payload if missing at top level
    payload = doc.get("raw_payload", {})
    if not doc.get("title"):
        doc["title"] = payload.get("title") or payload.get("headline") or f"Signal from {doc.get('source', 'unknown')}"
    if not doc.get("description"):
        doc["description"] = payload.get("description", "")
    if not doc.get("severity"):
        doc["severity"] = payload.get("severity", 1)
    if not doc.get("affected_regions"):
        doc["affected_regions"] = payload.get("affected_regions") or ([payload["region"]] if payload.get("region") else [])
    if not doc.get("affected_sku_ids"):
        doc["affected_sku_ids"] = payload.get("affected_sku_ids", [])

    return doc


# ── SSE Stream ────────────────────────────────────────────────────

async def _signal_event_generator():
    """
    Poll MongoDB every 2 seconds for new signal_logs.
    Yield SSE-formatted events.
    """
    # Start slightly in the past so connecting clients immediately receive recent live signals
    last_check = datetime.now(timezone.utc) - timedelta(hours=2)

    while True:
        try:
            if get_db() is not None:
                cursor = (
                    get_db()[SIGNAL_LOGS]
                    .find({"processed_at": {"$gt": last_check}})
                    .sort("processed_at", -1)
                    .limit(20)
                )
                new_signals = await cursor.to_list(length=20)

                if new_signals:
                    last_check = datetime.now(timezone.utc)
                    for sig in reversed(new_signals):
                        sig = _serialize_doc(sig)
                        # Convert datetime for JSON serialization
                        if isinstance(sig.get("processed_at"), datetime):
                            sig["processed_at"] = sig["processed_at"].isoformat()
                        data = json.dumps(sig, default=str)
                        yield f"data: {data}\n\n"

            # Heartbeat to keep connection alive
            yield f": heartbeat {datetime.now(timezone.utc).isoformat()}\n\n"
            await asyncio.sleep(2)

        except asyncio.CancelledError:
            break
        except Exception as exc:
            logger.error(f"SSE stream error: {exc}")
            yield f"event: error\ndata: {json.dumps({'error': str(exc)})}\n\n"
            await asyncio.sleep(5)


# ── Endpoints ─────────────────────────────────────────────────────

@router.get("/signals/feed")
async def signal_feed():
    """Server-Sent Events stream of new signal logs in real time."""
    try:
        return StreamingResponse(
            _signal_event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    except Exception as exc:
        logger.error(f"signal_feed error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/signals/ingest", response_model=IngestResponse, status_code=201)
async def ingest_signal(signal: SignalLogBase):
    """Manually submit a signal payload."""
    try:
        database = get_db()

        doc = signal.model_dump()
        # Serialize enum
        if hasattr(doc.get("source"), "value"):
            doc["source"] = doc["source"].value

        await database[SIGNAL_LOGS].insert_one(doc)

        # Optionally trigger disruption agent for high-severity signals
        agent_triggered = False
        severity = doc.get("raw_payload", {}).get("severity", 0)
        if severity >= 4:
            try:
                from backend.agents.disruption_agent import run_disruption_agent
                asyncio.create_task(run_disruption_agent())
                agent_triggered = True
            except Exception as agent_exc:
                logger.warning(f"Failed to trigger agent: {agent_exc}")

        return IngestResponse(
            message="Signal ingested successfully",
            signal_id=signal.signal_id,
            agent_triggered=agent_triggered,
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"ingest_signal error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/signals/history", response_model=PaginatedSignalResponse)
async def signal_history(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    source: Optional[str] = Query(None, description="Filter by source"),
):
    """Paginated signal logs, newest first."""
    try:
        database = get_db()

        query: dict[str, Any] = {}
        if source:
            query["source"] = source

        total = await database[SIGNAL_LOGS].count_documents(query)
        skip = (page - 1) * limit
        cursor = database[SIGNAL_LOGS].find(query).sort("processed_at", -1).skip(skip).limit(limit)
        items = await cursor.to_list(length=limit)
        items = [_serialize_doc(doc) for doc in items]

        return PaginatedSignalResponse(
            items=items, total=total, page=page, limit=limit
        )

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"signal_history error: {exc}")
        raise HTTPException(status_code=500, detail=str(exc))


print("✓ signals.py router complete")
