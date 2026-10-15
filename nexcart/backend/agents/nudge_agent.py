"""
NexCart — Layer 2: GenAI Personalisation Agent (LangGraph)
=============================================================
LangGraph StateGraph that loads at-risk customers, finds substitute
SKUs, generates personalised offer copy via AWS Bedrock, dispatches
nudge notifications, and logs campaigns to MongoDB.

Nodes:
  load_at_risk_customers -> find_substitutes -> generate_offer_copy
      -> dispatch_nudges -> log_campaign
"""

import asyncio
import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from langgraph.graph import END, StateGraph

from backend.database.collections import CUSTOMER_PROFILES, NUDGE_CAMPAIGNS, SKUS
from backend.database.connection import get_db
from backend.services.notification import NotificationService
from backend.utils.logger import get_logger

logger = get_logger("nudge_agent")


def _get_database():
    try:
        return get_db()
    except Exception:
        return None

# ══════════════════════════════════════════════════════════════════
# AGENT STATE
# ══════════════════════════════════════════════════════════════════

@dataclass
class NudgeState:
    """Typed state for the personalisation nudge agent."""
    at_risk_sku_ids: list[str] = field(default_factory=list)
    at_risk_skus: list[dict[str, Any]] = field(default_factory=list)
    affected_customers: list[dict[str, Any]] = field(default_factory=list)
    substitutes: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    offer_copies: list[dict[str, Any]] = field(default_factory=list)
    dispatched_nudges: list[dict[str, Any]] = field(default_factory=list)
    logged_campaigns: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


# ══════════════════════════════════════════════════════════════════
# NODE 1: LOAD AT-RISK CUSTOMERS
# ══════════════════════════════════════════════════════════════════

async def load_at_risk_customers(state: NudgeState) -> NudgeState:
    """
    Query customer_profiles where purchase_history contains
    at-risk sku_ids.
    """
    logger.info("Node: load_at_risk_customers — querying affected customers...")

    database = _get_database()
    if database is None:
        state.errors.append("load_at_risk_customers: database not connected")
        return state

    try:
        # Load at-risk SKU details
        if state.at_risk_sku_ids:
            cursor = database[SKUS].find({"sku_id": {"$in": state.at_risk_sku_ids}})
            state.at_risk_skus = await cursor.to_list(length=500)
        else:
            # If no specific SKUs provided, find all high/critical SKUs
            cursor = database[SKUS].find(
                {"risk_level": {"$in": ["high", "critical"]}}
            )
            state.at_risk_skus = await cursor.to_list(length=500)
            state.at_risk_sku_ids = [s["sku_id"] for s in state.at_risk_skus]

        if not state.at_risk_sku_ids:
            logger.info("No at-risk SKUs found — nothing to process")
            return state

        # Find customers who purchased at-risk SKUs
        cursor = database[CUSTOMER_PROFILES].find(
            {"purchase_history.sku_id": {"$in": state.at_risk_sku_ids}}
        )
        state.affected_customers = await cursor.to_list(length=1000)

        logger.info(
            f"Found {len(state.affected_customers)} customers affected by "
            f"{len(state.at_risk_sku_ids)} at-risk SKUs"
        )

    except Exception as exc:
        logger.error(f"load_at_risk_customers error: {exc}")
        state.errors.append(f"load_at_risk_customers: {exc}")

    return state


# ══════════════════════════════════════════════════════════════════
# NODE 2: FIND SUBSTITUTES
# ══════════════════════════════════════════════════════════════════

async def find_substitutes(state: NudgeState) -> NudgeState:
    """
    For each at-risk SKU, find top 3 substitute SKUs in the same
    category with risk_level='low' and stock above reorder_point.
    """
    logger.info("Node: find_substitutes — searching for alternatives...")

    database = _get_database()
    if database is None:
        state.errors.append("find_substitutes: database not connected")
        return state

    try:
        for sku in state.at_risk_skus:
            category = sku.get("category", "")
            sku_id = sku.get("sku_id", "")

            cursor = database[SKUS].find(
                {
                    "category": category,
                    "risk_level": "low",
                    "sku_id": {"$ne": sku_id},
                    "$expr": {"$gt": ["$current_stock", "$reorder_point"]},
                }
            ).sort("risk_score", 1).limit(3)

            subs = await cursor.to_list(length=3)

            if not subs:
                # Relax criteria: any low/medium risk in same category
                cursor = database[SKUS].find(
                    {
                        "category": category,
                        "risk_level": {"$in": ["low", "medium"]},
                        "sku_id": {"$ne": sku_id},
                    }
                ).sort("risk_score", 1).limit(3)
                subs = await cursor.to_list(length=3)

            state.substitutes[sku_id] = [
                {
                    "sku_id": s["sku_id"],
                    "name": s.get("name", ""),
                    "category": s.get("category", ""),
                    "current_stock": s.get("current_stock", 0),
                    "risk_score": s.get("risk_score", 0),
                }
                for s in subs
            ]

            logger.info(
                f"Found {len(subs)} substitutes for {sku_id} ({category})"
            )

    except Exception as exc:
        logger.error(f"find_substitutes error: {exc}")
        state.errors.append(f"find_substitutes: {exc}")

    return state


# ══════════════════════════════════════════════════════════════════
# NODE 3: GENERATE OFFER COPY (Bedrock)
# ══════════════════════════════════════════════════════════════════

BEDROCK_SYSTEM_PROMPT = (
    "You are NexCart's personalisation engine. Given a customer's "
    "purchase history and an at-risk product, write a warm, concise "
    "personalised message (max 80 words) offering a substitute product. "
    "Mention the customer's name, why they might need this now, and "
    "make it feel helpful not alarming. Return ONLY valid JSON: "
    '{"subject": "string", "body": "string", "cta_text": "string"}'
)


async def _generate_copy_bedrock(
    customer_name: str,
    at_risk_sku_name: str,
    substitute_details: str,
    last_purchase_date: str,
) -> Optional[dict]:
    """Call Bedrock to generate personalised offer copy with retry."""
    model_id = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-opus-4-5")
    aws_key = os.getenv("AWS_ACCESS_KEY_ID", "")
    aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")

    if not aws_key or not aws_secret:
        return None

    try:
        from langchain_aws import ChatBedrock
        from langchain_core.messages import HumanMessage, SystemMessage

        llm = ChatBedrock(
            model_id=model_id,
            region_name=os.getenv("AWS_REGION", "us-east-1"),
            credentials_profile_name=None,
            model_kwargs={"temperature": 0.7, "max_tokens": 512},
        )

        user_prompt = (
            f"Customer name: {customer_name}\n"
            f"At-risk product: {at_risk_sku_name}\n"
            f"Substitute product details: {substitute_details}\n"
            f"Last purchase date: {last_purchase_date}\n"
        )

        messages = [
            SystemMessage(content=BEDROCK_SYSTEM_PROMPT),
            HumanMessage(content=user_prompt),
        ]

        # Retry logic: 3 attempts with exponential backoff
        for attempt in range(3):
            try:
                response = await asyncio.to_thread(llm.invoke, messages)
                content = response.content.strip()

                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()

                return json.loads(content)

            except json.JSONDecodeError:
                logger.warning(f"Bedrock JSON parse error (attempt {attempt+1})")
            except Exception as exc:
                wait_time = 2 ** attempt
                logger.warning(
                    f"Bedrock call failed (attempt {attempt+1}): {exc}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)

    except ImportError:
        logger.error("langchain-aws not installed")
    except Exception as exc:
        logger.error(f"Bedrock setup error: {exc}")

    return None


def _generate_copy_fallback(
    customer_name: str,
    at_risk_sku_name: str,
    substitute_name: str,
) -> dict:
    """Generate fallback offer copy without LLM."""
    return {
        "subject": f"Quick heads-up about your {at_risk_sku_name}, {customer_name}",
        "body": (
            f"Hi {customer_name}, we noticed that {at_risk_sku_name} you love "
            f"may face a brief supply delay. Great news — we found "
            f"{substitute_name} as a perfect alternative! It's in stock and "
            f"ready to ship. We wanted to let you know before it sells out."
        ),
        "cta_text": f"Shop {substitute_name} Now",
    }


async def generate_offer_copy(state: NudgeState) -> NudgeState:
    """Generate personalised offer messages for each customer-SKU pair."""
    logger.info("Node: generate_offer_copy — creating personalised messages...")

    for customer in state.affected_customers:
        customer_name = customer.get("name", "Customer")
        purchase_history = customer.get("purchase_history", [])

        for purchase in purchase_history:
            sku_id = purchase.get("sku_id", "")
            if sku_id not in state.at_risk_sku_ids:
                continue

            subs = state.substitutes.get(sku_id, [])
            if not subs:
                continue

            substitute = subs[0]
            at_risk_sku = next(
                (s for s in state.at_risk_skus if s.get("sku_id") == sku_id),
                {"name": sku_id},
            )
            at_risk_name = at_risk_sku.get("name", sku_id)
            sub_name = substitute.get("name", substitute["sku_id"])

            purchase_date = purchase.get("date", "")
            if hasattr(purchase_date, "isoformat"):
                purchase_date = purchase_date.isoformat()

            # Try Bedrock, fallback to template
            copy = await _generate_copy_bedrock(
                customer_name=customer_name,
                at_risk_sku_name=at_risk_name,
                substitute_details=(
                    f"{sub_name} (SKU: {substitute['sku_id']}, "
                    f"stock: {substitute.get('current_stock', 'N/A')})"
                ),
                last_purchase_date=str(purchase_date),
            )

            if copy is None:
                copy = _generate_copy_fallback(
                    customer_name, at_risk_name, sub_name
                )

            state.offer_copies.append({
                "customer_id": customer.get("customer_id", ""),
                "customer_name": customer_name,
                "customer_email": customer.get("email", ""),
                "push_token": customer.get("push_token"),
                "sku_id": sku_id,
                "substitute_sku_id": substitute["sku_id"],
                "subject": copy.get("subject", ""),
                "body": copy.get("body", ""),
                "cta_text": copy.get("cta_text", "Shop Now"),
            })

    logger.info(f"Generated {len(state.offer_copies)} offer copies")
    return state


# ══════════════════════════════════════════════════════════════════
# NODE 4: DISPATCH NUDGES
# ══════════════════════════════════════════════════════════════════

async def dispatch_nudges(state: NudgeState) -> NudgeState:
    """
    Send nudge notifications. Channel selection:
    push_token exists -> push, else -> email.
    """
    logger.info("Node: dispatch_nudges — sending notifications...")

    notifier = NotificationService()

    for offer in state.offer_copies:
        try:
            push_token = offer.get("push_token")
            channel = "push" if push_token else "email"

            if channel == "push":
                success = await notifier.send_push(
                    push_token=push_token,
                    title=offer["subject"],
                    body=offer["body"],
                    data={
                        "sku_id": offer["sku_id"],
                        "substitute_sku_id": offer["substitute_sku_id"],
                    },
                )
            else:
                success = await notifier.send_email(
                    to_email=offer["customer_email"],
                    subject=offer["subject"],
                    body=offer["body"],
                    cta_text=offer["cta_text"],
                )

            state.dispatched_nudges.append({
                **offer,
                "channel": channel,
                "success": success,
                "sent_at": datetime.now(timezone.utc),
            })

        except Exception as exc:
            logger.error(
                f"Dispatch failed for customer {offer.get('customer_id')}: {exc}"
            )
            state.errors.append(
                f"dispatch_{offer.get('customer_id')}: {exc}"
            )

    logger.info(f"Dispatched {len(state.dispatched_nudges)} nudges")
    return state


# ══════════════════════════════════════════════════════════════════
# NODE 5: LOG CAMPAIGN
# ══════════════════════════════════════════════════════════════════

async def log_campaign(state: NudgeState) -> NudgeState:
    """Insert nudge campaigns into MongoDB with status='sent'."""
    logger.info("Node: log_campaign — recording campaigns in MongoDB...")

    database = _get_database()
    if database is None:
        state.errors.append("log_campaign: database not connected")
        return state

    for nudge in state.dispatched_nudges:
        try:
            campaign_doc = {
                "campaign_id": f"NDG-{uuid.uuid4().hex[:8].upper()}",
                "sku_id": nudge["sku_id"],
                "customer_id": nudge["customer_id"],
                "substitute_sku_id": nudge.get("substitute_sku_id"),
                "offer_text": nudge.get("body", ""),
                "channel": nudge.get("channel", "email"),
                "status": "sent" if nudge.get("success") else "pending",
                "sent_at": nudge.get("sent_at", datetime.now(timezone.utc)),
                "opened_at": None,
                "revenue_recovered": 0.0,
            }

            result = await database[NUDGE_CAMPAIGNS].insert_one(campaign_doc)
            state.logged_campaigns.append(str(result.inserted_id))

        except Exception as exc:
            logger.error(
                f"Failed to log campaign for {nudge.get('customer_id')}: {exc}"
            )
            state.errors.append(
                f"log_campaign_{nudge.get('customer_id')}: {exc}"
            )

    logger.info(f"Logged {len(state.logged_campaigns)} campaigns to MongoDB")
    return state


# ══════════════════════════════════════════════════════════════════
# BUILD THE LANGGRAPH
# ══════════════════════════════════════════════════════════════════

def build_nudge_graph() -> StateGraph:
    """Build and compile the Layer 2 personalisation graph."""
    graph = StateGraph(NudgeState)

    graph.add_node("load_at_risk_customers", load_at_risk_customers)
    graph.add_node("find_substitutes", find_substitutes)
    graph.add_node("generate_offer_copy", generate_offer_copy)
    graph.add_node("dispatch_nudges", dispatch_nudges)
    graph.add_node("log_campaign", log_campaign)

    graph.set_entry_point("load_at_risk_customers")
    graph.add_edge("load_at_risk_customers", "find_substitutes")
    graph.add_edge("find_substitutes", "generate_offer_copy")
    graph.add_edge("generate_offer_copy", "dispatch_nudges")
    graph.add_edge("dispatch_nudges", "log_campaign")
    graph.add_edge("log_campaign", END)

    return graph


# Compiled graph instance
nudge_graph = build_nudge_graph().compile()


# ══════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════

async def run_nudge_agent(sku_ids: list[str] = None) -> dict[str, Any]:
    """
    Run the full personalisation nudge pipeline.

    Args:
        sku_ids: Optional list of at-risk SKU IDs to process.
                 If None, the agent will find all high/critical SKUs.

    Returns:
        dict: Summary of the run results.
    """
    logger.info(
        f"=== Nudge Agent: Starting pipeline "
        f"(sku_ids={sku_ids or 'auto-detect'}) ==="
    )

    initial_state = NudgeState(
        at_risk_sku_ids=sku_ids or [],
    )

    try:
        final_state = await nudge_graph.ainvoke(initial_state)

        summary = {
            "status": "completed",
            "at_risk_skus": len(final_state.get("at_risk_sku_ids", [])),
            "customers_affected": len(final_state.get("affected_customers", [])),
            "offers_generated": len(final_state.get("offer_copies", [])),
            "nudges_dispatched": len(final_state.get("dispatched_nudges", [])),
            "campaigns_logged": len(final_state.get("logged_campaigns", [])),
            "errors": final_state.get("errors", []),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        logger.info(f"=== Nudge Agent: Complete === Summary: {summary}")
        return summary

    except Exception as exc:
        logger.error(f"Nudge Agent pipeline error: {exc}")
        return {
            "status": "error",
            "detail": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


print("✓ nudge_agent.py complete")
