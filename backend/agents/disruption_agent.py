"""
NexCart — Layer 1: Disruption Prediction Agent (LangGraph)
=============================================================
LangGraph StateGraph that ingests external signals, analyses risk
via AWS Bedrock, updates SKU scores in MongoDB, and publishes
disruption events to EventBridge.

Nodes:
  ingest_signals -> analyse_risk -> update_sku_scores
      -> flag_at_risk_skus -> publish_to_eventbridge
"""

import asyncio
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from langgraph.graph import END, StateGraph

from backend.database.collections import SIGNAL_LOGS, SKUS
from backend.database.connection import get_db
from backend.services.eventbridge import EventBridgeService
from backend.services.news_service import NewsService
from backend.services.shipping_service import ShippingService
from backend.services.weather_service import WeatherService
from backend.utils.logger import get_logger
from backend.utils.risk_scorer import RiskScorer

logger = get_logger("disruption_agent")


def _get_database():
    try:
        return get_db()
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════
# AGENT STATE
# ══════════════════════════════════════════════════════════════════

@dataclass
class DisruptionState:
    """Typed state for the disruption prediction agent."""
    raw_signals: list[dict[str, Any]] = field(default_factory=list)
    analysis_results: list[dict[str, Any]] = field(default_factory=list)
    updated_skus: list[dict[str, Any]] = field(default_factory=list)
    at_risk_skus: list[dict[str, Any]] = field(default_factory=list)
    published_events: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# NODE 1: INGEST SIGNALS
# ══════════════════════════════════════════════════════════════════

async def ingest_signals(state: DisruptionState) -> DisruptionState:
    """Pull signals from all three external services."""
    logger.info("Node: ingest_signals — fetching from all sources...")

    all_signals: list[dict[str, Any]] = []

    try:
        news_svc = NewsService()
        weather_svc = WeatherService()
        shipping_svc = ShippingService()

        news_signals, weather_signals, shipping_signals = await asyncio.gather(
            news_svc.fetch_signals(),
            weather_svc.fetch_signals(),
            shipping_svc.fetch_signals(),
            return_exceptions=True,
        )

        for name, result in [
            ("news", news_signals),
            ("weather", weather_signals),
            ("shipping", shipping_signals),
        ]:
            if isinstance(result, Exception):
                logger.error(f"Error fetching {name} signals: {result}")
                state.errors.append(f"ingest_{name}: {result}")
            elif isinstance(result, list):
                all_signals.extend(result)

        # Log raw signals to MongoDB
        database = _get_database()
        if database is not None and all_signals:
            signal_docs = []
            for i, sig in enumerate(all_signals):
                signal_docs.append({
                    "signal_id": f"SIG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{i:04d}",
                    "source": sig.get("source", "unknown"),
                    "raw_payload": sig,
                    "processed_at": datetime.now(timezone.utc),
                    "risk_delta": 0.0,
                    "triggered_agent_run": True,
                })
            try:
                await database[SIGNAL_LOGS].insert_many(signal_docs)
                logger.info(f"Logged {len(signal_docs)} signals to signal_logs")
            except Exception as exc:
                logger.error(f"Failed to log signals: {exc}")

        logger.info(f"Ingested {len(all_signals)} total signals")

    except Exception as exc:
        logger.error(f"ingest_signals error: {exc}")
        state.errors.append(f"ingest_signals: {exc}")

    state.raw_signals = all_signals
    return state


# ══════════════════════════════════════════════════════════════════
# NODE 2: ANALYSE RISK (Bedrock with heuristic fallback)
# ══════════════════════════════════════════════════════════════════

async def _call_bedrock(signals_text: str) -> Optional[dict]:
    """
    Call AWS Bedrock to analyse signals. Retries 3 times with
    exponential backoff. Returns parsed JSON or None on failure.
    """
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-4-5")
    region = os.getenv("AWS_REGION", "us-east-1")
    aws_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    if not aws_key or not aws_secret:
        logger.warning("AWS credentials missing — skipping Bedrock call")
        return None

    try:
        from langchain_aws import ChatBedrock
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatBedrock(
            model_id=model_id,
            region_name=region,
            credentials_profile_name=None,
            model_kwargs={"temperature": 0.1, "max_tokens": 2048},
        )

        system_prompt = (
            "You are NexCart's supply-chain risk analysis engine. "
            "Given a list of external signals (news, weather, shipping), "
            "identify which SKUs are affected and estimate risk impact.\n\n"
            "Return ONLY valid JSON with this structure:\n"
            "{\n"
            '  "analyses": [\n'
            "    {\n"
            '      "affected_sku_ids": ["SKU-ELEC-001", ...],\n'
            '      "risk_delta": 15,\n'
            '      "reasoning": "Port congestion in Shanghai...",\n'
            '      "estimated_impact_days": 7,\n'
            '      "confidence_score": 0.85\n'
            "    }\n"
            "  ]\n"
            "}"
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Analyse these signals:\n{signals_text}"),
        ]

        # Retry logic: 3 attempts with exponential backoff
        for attempt in range(3):
            try:
                response = await asyncio.to_thread(llm.invoke, messages)
                content = response.content.strip()

                # Extract JSON from response
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                return json.loads(content)

            except json.JSONDecodeError as je:
                logger.warning(f"Bedrock JSON parse error (attempt {attempt+1}): {je}")
            except Exception as exc:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Bedrock call failed (attempt {attempt+1}): {exc}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

    except ImportError:
        logger.error("langchain-aws not installed — cannot call Bedrock")
    except Exception as exc:
        logger.error(f"Bedrock setup error: {exc}")

    return None


COUNTRY_REGION_MAP: dict[str, list[str]] = {
    "China": ["East Asia", "China"],
    "Japan": ["East Asia", "Japan"],
    "South Korea": ["East Asia", "South Korea"],
    "Taiwan": ["East Asia", "Taiwan"],
    "India": ["South Asia", "India"],
    "Bangladesh": ["South Asia", "Bangladesh"],
    "Vietnam": ["Southeast Asia", "Vietnam"],
    "Indonesia": ["Southeast Asia", "Indonesia"],
    "Malaysia": ["Southeast Asia", "Malaysia"],
    "Thailand": ["Southeast Asia", "Thailand"],
    "Germany": ["Europe", "Germany"],
    "Netherlands": ["Europe", "Netherlands"],
    "Poland": ["Europe", "Poland"],
    "Italy": ["Europe", "Italy"],
    "France": ["Europe", "France"],
    "Spain": ["Europe", "Spain"],
    "Turkey": ["Europe", "Turkey"],
    "United States": ["North America", "United States"],
    "Mexico": ["North America", "Mexico"],
    "Brazil": ["South America", "Brazil"],
}

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Electronics": ["electronics", "semiconductor", "chip", "battery", "lithium", "hardware"],
    "Apparel": ["textile", "apparel", "cotton", "clothing", "garment", "fabric"],
    "Food": ["food", "agricultural", "grain", "crop", "oil", "cocoa", "produce"],
    "Pharma": ["pharma", "drug", "medicine", "active ingredient", "healthcare"],
    "Home Goods": ["furniture", "plastic", "container", "packaging", "consumer goods"],
}


def _is_signal_relevant_to_sku(signal: dict, sku: dict) -> bool:
    """Check if a signal geographically and domain-wise impacts a specific SKU."""
    country = sku.get("supplier_country", "")
    sku_regions = COUNTRY_REGION_MAP.get(country, [country])
    sig_regions = [r.lower() for r in signal.get("affected_regions", [])]

    # Specific regional match
    has_specific_region_match = any(
        reg.lower() in sig_regions or any(reg.lower() in sr for sr in sig_regions)
        for reg in sku_regions
    )

    text = (signal.get("title", "") + " " + signal.get("description", "")).lower()
    sku_cat = sku.get("category", "")
    cat_kws = CATEGORY_KEYWORDS.get(sku_cat, [])
    has_category_match = any(kw in text for kw in cat_kws)

    # If it's a global signal without specific region match, it MUST match the SKU category
    if not has_specific_region_match:
        if "global" in sig_regions and has_category_match:
            return True
        return False

    # If there is a specific region match, ensure it's not explicitly about another category
    for cat, kws in CATEGORY_KEYWORDS.items():
        if cat != sku_cat and any(kw in text for kw in kws) and not has_category_match:
            return False

    return True


async def analyse_risk(state: DisruptionState) -> DisruptionState:
    """
    Analyse ingested signals using Bedrock LLM.
    Falls back to heuristic RiskScorer if Bedrock is unavailable.
    """
    logger.info("Node: analyse_risk — processing signals...")

    if not state.raw_signals:
        logger.info("No signals to analyse")
        return state

    # Format signals for Bedrock
    signals_text = json.dumps(
        [
            {
                "source": s.get("source"),
                "title": s.get("title"),
                "severity": s.get("severity"),
                "regions": s.get("affected_regions"),
            }
            for s in state.raw_signals
        ],
        indent=2,
    )

    # Try Bedrock first
    bedrock_result = await _call_bedrock(signals_text)

    if bedrock_result and "analyses" in bedrock_result:
        state.analysis_results = bedrock_result["analyses"]
        logger.info(
            f"Bedrock analysis complete: {len(state.analysis_results)} results"
        )
    else:
        # Fallback: heuristic analysis using RiskScorer
        logger.info("Using heuristic RiskScorer as fallback")
        scorer = RiskScorer()
        database = _get_database()

        if database is not None:
            try:
                skus_cursor = database[SKUS].find({})
                all_skus = await skus_cursor.to_list(length=500)

                for sku in all_skus:
                    # Only match signals that specifically affect this SKU's region/domain
                    relevant_signals = [
                        s for s in state.raw_signals
                        if s.get("severity", 0) >= 2 and _is_signal_relevant_to_sku(s, sku)
                    ]

                    # Cap to top 2 most severe relevant signals
                    relevant_signals = sorted(
                        relevant_signals, key=lambda s: s.get("severity", 1), reverse=True
                    )[:2]

                    if relevant_signals:
                        assessment = scorer.assess(relevant_signals, sku)
                        target_score = assessment["risk_score"]
                        current_score = sku.get("risk_score", 0)

                        if target_score > current_score or target_score >= 50:
                            state.analysis_results.append({
                                "affected_sku_ids": [sku["sku_id"]],
                                "target_score": target_score,
                                "risk_delta": target_score - current_score,
                                "reasoning": (
                                    f"Heuristic analysis: {len(relevant_signals)} active disruption(s) "
                                    f"affecting {sku.get('supplier_country', 'supplier region')} "
                                    f"({relevant_signals[0].get('title', 'Disruption')})"
                                ),
                                "estimated_impact_days": max([s.get("severity", 2) * 3 for s in relevant_signals]),
                                "confidence_score": 0.85,
                            })
            except Exception as exc:
                logger.error(f"Heuristic analysis error: {exc}")
                state.errors.append(f"analyse_risk_heuristic: {exc}")

        logger.info(
            f"Heuristic analysis: {len(state.analysis_results)} results"
        )

    return state


# ══════════════════════════════════════════════════════════════════
# NODE 3: UPDATE SKU SCORES
# ══════════════════════════════════════════════════════════════════

async def update_sku_scores(state: DisruptionState) -> DisruptionState:
    """Write updated risk_score + risk_level to MongoDB skus collection."""
    logger.info("Node: update_sku_scores — writing to MongoDB...")

    database = _get_database()
    if database is None:
        state.errors.append("update_sku_scores: database not connected")
        return state

    scorer = RiskScorer()

    for analysis in state.analysis_results:
        sku_ids = analysis.get("affected_sku_ids", [])
        risk_delta = analysis.get("risk_delta", 0)
        target_score = analysis.get("target_score")

        for sku_id in sku_ids:
            try:
                sku_doc = await database[SKUS].find_one({"sku_id": sku_id})
                if not sku_doc:
                    logger.warning(f"SKU {sku_id} not found in database")
                    continue

                current_score = sku_doc.get("risk_score", 0)
                if target_score is not None:
                    new_score = max(0, min(100, int(target_score)))
                else:
                    new_score = max(0, min(100, int(current_score + risk_delta)))
                new_level = scorer.get_risk_level(new_score)

                await database[SKUS].update_one(
                    {"sku_id": sku_id},
                    {
                        "$set": {
                            "risk_score": new_score,
                            "risk_level": new_level,
                            "last_updated": datetime.now(timezone.utc),
                        }
                    },
                )

                state.updated_skus.append({
                    "sku_id": sku_id,
                    "old_score": current_score,
                    "new_score": new_score,
                    "risk_level": new_level,
                })

                logger.info(
                    f"Updated {sku_id}: score {current_score} -> {new_score} "
                    f"({new_level})"
                )

            except Exception as exc:
                logger.error(f"Failed to update SKU {sku_id}: {exc}")
                state.errors.append(f"update_sku_{sku_id}: {exc}")

    logger.info(f"Updated {len(state.updated_skus)} SKUs")
    return state


# ══════════════════════════════════════════════════════════════════
# NODE 4: FLAG AT-RISK SKUS
# ══════════════════════════════════════════════════════════════════

async def flag_at_risk_skus(state: DisruptionState) -> DisruptionState:
    """Query SKUs with risk_level high or critical."""
    logger.info("Node: flag_at_risk_skus — querying high-risk SKUs...")

    database = _get_database()
    if database is None:
        state.errors.append("flag_at_risk_skus: database not connected")
        return state

    try:
        cursor = database[SKUS].find(
            {"risk_level": {"$in": ["high", "critical"]}}
        )
        at_risk = await cursor.to_list(length=500)

        state.at_risk_skus = [
            {
                "sku_id": sku["sku_id"],
                "name": sku.get("name", ""),
                "risk_score": sku.get("risk_score", 0),
                "risk_level": sku.get("risk_level", ""),
                "category": sku.get("category", ""),
                "current_stock": sku.get("current_stock", 0),
            }
            for sku in at_risk
        ]

        logger.info(f"Flagged {len(state.at_risk_skus)} at-risk SKUs")

    except Exception as exc:
        logger.error(f"flag_at_risk_skus error: {exc}")
        state.errors.append(f"flag_at_risk_skus: {exc}")

    return state


# ══════════════════════════════════════════════════════════════════
# NODE 5: PUBLISH TO EVENTBRIDGE
# ══════════════════════════════════════════════════════════════════

async def publish_to_eventbridge(state: DisruptionState) -> DisruptionState:
    """Emit a DisruptionDetected event for each flagged SKU."""
    logger.info("Node: publish_to_eventbridge — emitting events...")

    eb_service = EventBridgeService()

    for sku in state.at_risk_skus:
        try:
            reasoning = ""
            for analysis in state.analysis_results:
                if sku["sku_id"] in analysis.get("affected_sku_ids", []):
                    reasoning = analysis.get("reasoning", "Risk threshold exceeded")
                    break

            if not reasoning:
                reasoning = (
                    f"SKU {sku['sku_id']} flagged with risk_level="
                    f"{sku['risk_level']} (score={sku['risk_score']})"
                )

            success = await eb_service.publish_disruption_event(
                sku_id=sku["sku_id"],
                risk_score=sku["risk_score"],
                risk_level=sku["risk_level"],
                reasoning=reasoning,
            )

            if success:
                state.published_events.append(sku["sku_id"])

        except Exception as exc:
            logger.error(
                f"EventBridge publish failed for {sku['sku_id']}: {exc}"
            )
            state.errors.append(f"publish_{sku['sku_id']}: {exc}")

    logger.info(f"Published {len(state.published_events)} EventBridge events")
    return state


# ══════════════════════════════════════════════════════════════════
# BUILD THE LANGGRAPH
# ══════════════════════════════════════════════════════════════════

def build_disruption_graph() -> StateGraph:
    """Build and compile the Layer 1 disruption prediction graph."""
    graph = StateGraph(DisruptionState)

    graph.add_node("ingest_signals", ingest_signals)
    graph.add_node("analyse_risk", analyse_risk)
    graph.add_node("update_sku_scores", update_sku_scores)
    graph.add_node("flag_at_risk_skus", flag_at_risk_skus)
    graph.add_node("publish_to_eventbridge", publish_to_eventbridge)

    graph.set_entry_point("ingest_signals")
    graph.add_edge("ingest_signals", "analyse_risk")
    graph.add_edge("analyse_risk", "update_sku_scores")
    graph.add_edge("update_sku_scores", "flag_at_risk_skus")
    graph.add_edge("flag_at_risk_skus", "publish_to_eventbridge")
    graph.add_edge("publish_to_eventbridge", END)

    return graph


# Compiled graph instance
disruption_graph = build_disruption_graph().compile()


# ══════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════

async def run_disruption_agent() -> dict[str, Any]:
    """
    Run the full disruption prediction pipeline.
    Returns a summary dict of the run results.
    """
    logger.info("=== Disruption Agent: Starting pipeline ===")

    initial_state = DisruptionState()

    try:
        final_state = await disruption_graph.ainvoke(initial_state)

        summary = {
            "status": "completed",
            "signals_ingested": len(final_state.get("raw_signals", [])),
            "analyses_produced": len(final_state.get("analysis_results", [])),
            "skus_updated": len(final_state.get("updated_skus", [])),
            "at_risk_skus": len(final_state.get("at_risk_skus", [])),
            "events_published": len(final_state.get("published_events", [])),
            "errors": final_state.get("errors", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"=== Disruption Agent: Complete === Summary: {summary}")
        return summary

    except Exception as exc:
        logger.error(f"Disruption Agent pipeline error: {exc}")
        return {
            "status": "error",
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ══════════════════════════════════════════════════════════════════
# SCHEDULER (APScheduler)
# ══════════════════════════════════════════════════════════════════

_scheduler = None


def start_disruption_scheduler() -> None:
    """
    Start the APScheduler that runs the disruption agent
    every SIGNAL_POLL_INTERVAL_SECONDS seconds.
    Call this on FastAPI app startup.
    """
    global _scheduler

    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    interval = int(os.getenv("SIGNAL_POLL_INTERVAL_SECONDS", "300"))

    _scheduler = AsyncIOScheduler()
    _scheduler.add_job(
        run_disruption_agent,
        "interval",
        seconds=interval,
        id="disruption_agent_poll",
        name="NexCart Disruption Agent",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info(
        f"Disruption agent scheduler started (interval: {interval}s)"
    )


def stop_disruption_scheduler() -> None:
    """Stop the APScheduler gracefully on app shutdown."""
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
        logger.info("Disruption agent scheduler stopped")


print("✓ disruption_agent.py complete")
