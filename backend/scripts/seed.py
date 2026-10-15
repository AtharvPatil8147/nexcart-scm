"""
NexCart — Seed Data Script
============================
Generates realistic, practical seed data for all 5 MongoDB collections
with rich variety across risk levels (low, medium, high, critical).

Usage:
    python -m backend.scripts.seed          # seed (skip if data exists)
    python -m backend.scripts.seed --reset  # wipe all collections and reseed
"""

import argparse
import asyncio
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

# Ensure project root is on the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from dotenv import load_dotenv
load_dotenv()

from motor.motor_asyncio import AsyncIOMotorClient

from backend.database.collections import (
    CUSTOMER_PROFILES,
    DISRUPTION_EVENTS,
    NUDGE_CAMPAIGNS,
    SIGNAL_LOGS,
    SKUS,
)

# ══════════════════════════════════════════════════════════════════
# REALISTIC DATA DEFINITIONS WITH RISK VARIETY
# ══════════════════════════════════════════════════════════════════

CATEGORIES = ["Electronics", "Apparel", "Food", "Pharma", "Home Goods"]

# Explicit product definitions per category with balanced realistic inventory tiers:
# Low (~56%): Well-stocked, reliable suppliers, minimal risk (score 5-22)
# Medium (~26%): Watchlist, moderate stock, minor delay risk (score 28-48)
# High (~10%): Low stock, active regional disruption or supplier backlog (score 55-72)
# Critical (~8%): Critical stock, acute bottleneck or major port/weather crisis (score 78-95)

SKU_CATALOG: dict[str, list[dict]] = {
    "Electronics": [
        {"name": "Wireless Bluetooth Earbuds", "country": "China", "stock": 14, "reorder": 85, "score": 88, "tier": "critical"},
        {"name": "Noise-Cancelling Headphones", "country": "Taiwan", "stock": 42, "reorder": 65, "score": 64, "tier": "high"},
        {"name": "Portable Power Bank 20000mAh", "country": "Malaysia", "stock": 135, "reorder": 70, "score": 38, "tier": "medium"},
        {"name": "Smart Watch Series X", "country": "Indonesia", "stock": 110, "reorder": 60, "score": 42, "tier": "medium"},
        {"name": "USB-C Charging Hub", "country": "Japan", "stock": 380, "reorder": 40, "score": 12, "tier": "low"},
        {"name": "Smart LED Desk Lamp", "country": "Germany", "stock": 420, "reorder": 50, "score": 8, "tier": "low"},
        {"name": "Mechanical Gaming Keyboard", "country": "United States", "stock": 310, "reorder": 45, "score": 14, "tier": "low"},
        {"name": "4K Webcam Pro", "country": "Poland", "stock": 290, "reorder": 40, "score": 15, "tier": "low"},
        {"name": "Portable SSD 1TB", "country": "South Korea", "stock": 260, "reorder": 35, "score": 18, "tier": "low"},
        {"name": "Wireless Mouse Ergonomic", "country": "Germany", "stock": 450, "reorder": 50, "score": 6, "tier": "low"},
    ],
    "Apparel": [
        {"name": "Waterproof Hiking Jacket", "country": "Vietnam", "stock": 11, "reorder": 75, "score": 91, "tier": "critical"},
        {"name": "Slim Fit Denim Jeans", "country": "Bangladesh", "stock": 38, "reorder": 70, "score": 68, "tier": "high"},
        {"name": "Merino Wool Sweater", "country": "Turkey", "stock": 125, "reorder": 65, "score": 35, "tier": "medium"},
        {"name": "Quilted Puffer Vest", "country": "Turkey", "stock": 95, "reorder": 55, "score": 44, "tier": "medium"},
        {"name": "Cotton Crew Neck T-Shirt", "country": "Spain", "stock": 490, "reorder": 50, "score": 9, "tier": "low"},
        {"name": "Running Shorts Moisture-Wick", "country": "United States", "stock": 340, "reorder": 45, "score": 12, "tier": "low"},
        {"name": "Bamboo Fibre Socks 6-Pack", "country": "Poland", "stock": 410, "reorder": 60, "score": 11, "tier": "low"},
        {"name": "Linen Summer Dress", "country": "Italy", "stock": 280, "reorder": 35, "score": 16, "tier": "low"},
        {"name": "Stretch Yoga Leggings", "country": "Mexico", "stock": 320, "reorder": 50, "score": 14, "tier": "low"},
        {"name": "Oxford Button-Down Shirt", "country": "Germany", "stock": 270, "reorder": 40, "score": 15, "tier": "low"},
    ],
    "Food": [
        {"name": "Dark Chocolate 85% Cacao Bar", "country": "Brazil", "stock": 9, "reorder": 80, "score": 86, "tier": "critical"},
        {"name": "Manuka Honey UMF 15+", "country": "India", "stock": 32, "reorder": 50, "score": 58, "tier": "high"},
        {"name": "Japanese Matcha Powder 100g", "country": "Japan", "stock": 140, "reorder": 70, "score": 32, "tier": "medium"},
        {"name": "Freeze-Dried Strawberries", "country": "Poland", "stock": 110, "reorder": 55, "score": 38, "tier": "medium"},
        {"name": "Premium Basmati Rice 5kg", "country": "India", "stock": 95, "reorder": 60, "score": 46, "tier": "medium"},
        {"name": "Organic Cold-Press Olive Oil", "country": "Italy", "stock": 460, "reorder": 50, "score": 7, "tier": "low"},
        {"name": "Quinoa Grain Bag 2kg", "country": "Brazil", "stock": 380, "reorder": 45, "score": 11, "tier": "low"},
        {"name": "Himalayan Pink Salt Grinder", "country": "India", "stock": 430, "reorder": 40, "score": 10, "tier": "low"},
        {"name": "Organic Chia Seeds 500g", "country": "Mexico", "stock": 350, "reorder": 45, "score": 13, "tier": "low"},
        {"name": "Artisan Sourdough Bread Mix", "country": "United States", "stock": 310, "reorder": 35, "score": 12, "tier": "low"},
    ],
    "Pharma": [
        {"name": "Melatonin 5mg Sleep Aid", "country": "India", "stock": 36, "reorder": 65, "score": 62, "tier": "high"},
        {"name": "Probiotic 50 Billion CFU", "country": "Japan", "stock": 130, "reorder": 65, "score": 35, "tier": "medium"},
        {"name": "Collagen Peptides Powder", "country": "Brazil", "stock": 105, "reorder": 55, "score": 41, "tier": "medium"},
        {"name": "Turmeric Curcumin Extract", "country": "India", "stock": 88, "reorder": 60, "score": 48, "tier": "medium"},
        {"name": "Vitamin D3 5000 IU Softgels", "country": "United States", "stock": 480, "reorder": 45, "score": 8, "tier": "low"},
        {"name": "Omega-3 Fish Oil Capsules", "country": "Germany", "stock": 390, "reorder": 50, "score": 10, "tier": "low"},
        {"name": "Zinc Citrate 50mg Tablets", "country": "Germany", "stock": 420, "reorder": 40, "score": 9, "tier": "low"},
        {"name": "Magnesium Glycinate 400mg", "country": "United States", "stock": 360, "reorder": 45, "score": 12, "tier": "low"},
        {"name": "Iron Bisglycinate 25mg", "country": "Netherlands", "stock": 330, "reorder": 40, "score": 14, "tier": "low"},
        {"name": "Multivitamin Daily Complete", "country": "Germany", "stock": 450, "reorder": 50, "score": 7, "tier": "low"},
    ],
    "Home Goods": [
        {"name": "Bamboo Cutting Board Set", "country": "Vietnam", "stock": 12, "reorder": 70, "score": 84, "tier": "critical"},
        {"name": "Cast Iron Skillet 10-inch", "country": "China", "stock": 28, "reorder": 50, "score": 67, "tier": "high"},
        {"name": "Egyptian Cotton Bath Towel Set", "country": "Turkey", "stock": 120, "reorder": 60, "score": 36, "tier": "medium"},
        {"name": "Ceramic Plant Pot Trio", "country": "Spain", "stock": 105, "reorder": 55, "score": 39, "tier": "medium"},
        {"name": "LED String Lights 10m", "country": "Thailand", "stock": 85, "reorder": 50, "score": 45, "tier": "medium"},
        {"name": "Memory Foam Pillow Queen", "country": "United States", "stock": 370, "reorder": 45, "score": 11, "tier": "low"},
        {"name": "Stainless Steel Water Bottle 1L", "country": "Japan", "stock": 410, "reorder": 50, "score": 8, "tier": "low"},
        {"name": "Scented Soy Candle Lavender", "country": "France", "stock": 390, "reorder": 40, "score": 9, "tier": "low"},
        {"name": "Microfibre Cleaning Cloth 12-Pack", "country": "Poland", "stock": 460, "reorder": 50, "score": 7, "tier": "low"},
        {"name": "Non-Stick Silicone Baking Mat", "country": "Germany", "stock": 350, "reorder": 40, "score": 10, "tier": "low"},
    ],
}

FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "Lucas", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
    "Alexander", "Harper", "William", "Evelyn", "Henry", "Aria", "Sebastian",
    "Ella", "Jack", "Scarlett", "Daniel", "Grace", "Matthew", "Chloe", "Owen",
    "Victoria", "Samuel", "Riley", "David", "Zoey", "Joseph", "Nora", "Carter",
    "Lily", "Wyatt", "Eleanor", "John", "Hannah", "Luke", "Lillian", "Gabriel",
    "Addison", "Anthony", "Aubrey", "Dylan",
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts",
]

EMAIL_DOMAINS = ["gmail.com", "outlook.com", "yahoo.com", "protonmail.com", "icloud.com"]


def _uid(prefix: str) -> str:
    """Generate a short unique ID with a prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:8].upper()}"


def _random_dt(days_back: int = 30) -> datetime:
    """Generate a random datetime within the last N days."""
    delta = timedelta(
        days=random.randint(0, days_back),
        hours=random.randint(0, 23),
        minutes=random.randint(0, 59),
        seconds=random.randint(0, 59),
    )
    return datetime.now(timezone.utc) - delta


def _risk_level_from_score(score: int) -> str:
    if score <= 25:
        return "low"
    elif score <= 50:
        return "medium"
    elif score <= 75:
        return "high"
    else:
        return "critical"


# ══════════════════════════════════════════════════════════════════
# DATA GENERATORS
# ══════════════════════════════════════════════════════════════════

def generate_skus() -> list[dict]:
    """Generate realistic, practical SKU documents with structured risk variety."""
    skus = []

    for cat_idx, category in enumerate(CATEGORIES):
        items = SKU_CATALOG[category]
        for i, item in enumerate(items):
            score = item["score"]
            tier = item["tier"]

            skus.append({
                "sku_id": f"SKU-{category[:4].upper()}-{cat_idx * len(items) + i + 1:03d}",
                "name": item["name"],
                "category": category,
                "supplier_country": item["country"],
                "current_stock": item["stock"],
                "reorder_point": item["reorder"],
                "risk_score": score,
                "risk_level": tier,
                "last_updated": _random_dt(5),
            })

    return skus


def generate_customers(count: int = 200, skus: list[dict] = None) -> list[dict]:
    """Generate realistic customer profile documents linked to catalog SKUs."""
    skus = skus or []
    sku_ids = [s["sku_id"] for s in skus]
    customers = []
    used_emails: set[str] = set()

    for i in range(count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        email_base = f"{first.lower()}.{last.lower()}{random.randint(1, 999)}"
        domain = random.choice(EMAIL_DOMAINS)
        email = f"{email_base}@{domain}"

        while email in used_emails:
            email_base = f"{first.lower()}.{last.lower()}{random.randint(1, 9999)}"
            email = f"{email_base}@{domain}"
        used_emails.add(email)

        # Generate purchase history (1–6 purchases)
        purchase_count = random.randint(1, 6)
        purchase_history = []
        for _ in range(purchase_count):
            if sku_ids:
                purchase_history.append({
                    "sku_id": random.choice(sku_ids),
                    "quantity": random.randint(1, 4),
                    "date": _random_dt(90),
                })

        push_token = f"fcm_{uuid.uuid4().hex}" if random.random() > 0.4 else None
        pref_categories = random.sample(CATEGORIES, k=random.randint(1, 3))

        customers.append({
            "customer_id": f"CUST-{i + 1:04d}",
            "name": f"{first} {last}",
            "email": email,
            "push_token": push_token,
            "purchase_history": purchase_history,
            "preferences": {
                "categories": pref_categories,
                "brands": [],
            },
        })

    return customers


def generate_disruptions(skus: list[dict]) -> list[dict]:
    """Generate realistic disruption events targeted at high/critical SKUs."""
    # Group SKUs by risk level
    critical_skus = [s for s in skus if s["risk_level"] == "critical"]
    high_skus = [s for s in skus if s["risk_level"] == "high"]
    medium_skus = [s for s in skus if s["risk_level"] == "medium"]

    events = [
        # Major Acute Disruptions (Targeting Critical SKUs)
        {
            "source": "shipping",
            "title": "Severe Container Berth Congestion at Shanghai Yangshan Port",
            "description": "Vessel wait times have surged to 8-10 days at Yangshan terminal, creating critical backlogs for consumer electronics and export hardware.",
            "affected_regions": ["East Asia", "China"],
            "affected_sku_ids": [s["sku_id"] for s in critical_skus if s["supplier_country"] == "China"] +
                                [s["sku_id"] for s in high_skus if s["supplier_country"] == "China"],
            "severity": 5,
            "predicted_impact_days": 18,
            "created_at": _random_dt(3),
        },
        {
            "source": "weather",
            "title": "Severe Tropical Storm Flooding Shuts Industrial Corridors in Northern Vietnam",
            "description": "Heavy monsoon rains and flash floods inundated manufacturing zones in Bac Ninh and Haiphong, halting factory operations and road freight.",
            "affected_regions": ["Southeast Asia", "Vietnam"],
            "affected_sku_ids": [s["sku_id"] for s in critical_skus if s["supplier_country"] == "Vietnam"],
            "severity": 5,
            "predicted_impact_days": 14,
            "created_at": _random_dt(2),
        },
        {
            "source": "news",
            "title": "Drought and Crop Disease Cause Cacao Export Restrictions in South America",
            "description": "Prolonged dry weather coupled with fungal outbreaks in Bahia state has slashed raw cacao processing yields by 40%, triggering severe supplier delays.",
            "affected_regions": ["South America", "Brazil"],
            "affected_sku_ids": [s["sku_id"] for s in critical_skus if s["supplier_country"] == "Brazil"],
            "severity": 4,
            "predicted_impact_days": 21,
            "created_at": _random_dt(4),
        },
        {
            "source": "news",
            "title": "Advanced Semiconductor Packaging Allocation Bottleneck in Hsinchu",
            "description": "Foundry packaging capacity shortages have extended lead times by 6 weeks, impacting premium audio processors and smart peripherals.",
            "affected_regions": ["East Asia", "Taiwan"],
            "affected_sku_ids": [s["sku_id"] for s in high_skus if s["supplier_country"] == "Taiwan"],
            "severity": 4,
            "predicted_impact_days": 24,
            "created_at": _random_dt(6),
        },
        {
            "source": "shipping",
            "title": "Chittagong Port Yard Congestion and Customs Clearance Backlog",
            "description": "Apparel export processing delayed 10-12 days due to feeder vessel shortages and yard saturation at Chittagong Port.",
            "affected_regions": ["South Asia", "Bangladesh"],
            "affected_sku_ids": [s["sku_id"] for s in high_skus if s["supplier_country"] == "Bangladesh"],
            "severity": 4,
            "predicted_impact_days": 12,
            "created_at": _random_dt(5),
        },
        {
            "source": "news",
            "title": "API Raw Material Export Inspection Delays at Mumbai Jawaharlal Nehru Port",
            "description": "New regulatory compliance audits on pharmaceutical active ingredients have added 7-day inspection holds on outbound drug shipments.",
            "affected_regions": ["South Asia", "India"],
            "affected_sku_ids": [s["sku_id"] for s in high_skus if s["supplier_country"] == "India"],
            "severity": 3,
            "predicted_impact_days": 9,
            "created_at": _random_dt(7),
        },
        {
            "source": "shipping",
            "title": "Suez Canal Transit Routing Adjustments via Cape of Good Hope",
            "description": "Continued carrier rerouting around Africa adds 10-14 days transit time for Asia-to-Europe retail merchandise.",
            "affected_regions": ["Middle East", "Global"],
            "affected_sku_ids": [s["sku_id"] for s in medium_skus[:3]],
            "severity": 3,
            "predicted_impact_days": 15,
            "created_at": _random_dt(10),
        },
        {
            "source": "weather",
            "title": "Extreme Heat Advisory Slows Agricultural Freight across Central India",
            "description": "High daytime temperatures have triggered road freight transport restrictions during peak hours, creating moderate transit delays.",
            "affected_regions": ["South Asia", "India"],
            "affected_sku_ids": [s["sku_id"] for s in medium_skus if s["supplier_country"] == "India"],
            "severity": 2,
            "predicted_impact_days": 6,
            "created_at": _random_dt(12),
        },
        {
            "source": "news",
            "title": "Temporary Rail Freight Maintenance Slowdown across Central Germany",
            "description": "Scheduled track rehabilitation on key Rhine corridor tracks has induced minor 24-48 hour rail freight rerouting.",
            "affected_regions": ["Europe", "Germany"],
            "affected_sku_ids": [],
            "severity": 2,
            "predicted_impact_days": 4,
            "created_at": _random_dt(15),
        },
        {
            "source": "weather",
            "title": "Dense Sea Fog Causes Temporary Anchorage Hold at Port of Rotterdam",
            "description": "Pilotage services suspended for 16 hours due to visibility below 200m; container handling resumed normally after clearing.",
            "affected_regions": ["Europe", "Netherlands"],
            "affected_sku_ids": [],
            "severity": 1,
            "predicted_impact_days": 2,
            "created_at": _random_dt(18),
        },
    ]

    # Add historical resolved/low severity events to reach 20 events
    for idx in range(10):
        events.append({
            "event_id": _uid("EVT"),
            "source": random.choice(["news", "weather", "shipping"]),
            "title": f"Regional supply chain notice #{idx + 11}: Minor seasonal route adjustments",
            "description": f"Automated signal monitoring: routine seasonal variance detected. No critical impact to operations.",
            "affected_regions": [random.choice(["Europe", "North America", "East Asia", "Southeast Asia"])],
            "affected_sku_ids": [s["sku_id"] for s in random.sample(medium_skus, k=min(2, len(medium_skus)))],
            "severity": random.randint(1, 2),
            "predicted_impact_days": random.randint(2, 5),
            "created_at": _random_dt(25),
        })

    # Add event_ids
    for evt in events:
        if "event_id" not in evt:
            evt["event_id"] = _uid("EVT")

    return events


def generate_nudges(
    count: int = 100,
    skus: list[dict] = None,
    customers: list[dict] = None,
) -> list[dict]:
    """
    Generate realistic nudge campaigns.
    Targets AT-RISK SKUs (critical/high) and recommends HEALTHY LOW-RISK
    substitutes from the SAME category with high stock levels.
    """
    skus = skus or []
    customers = customers or []
    nudges = []

    # Map category -> list of healthy low-risk substitute SKUs
    category_healthy_subs: dict[str, list[dict]] = {}
    for s in skus:
        if s["risk_level"] == "low" and s["current_stock"] > s["reorder_point"] * 2:
            category_healthy_subs.setdefault(s["category"], []).append(s)

    # At-risk target SKUs
    at_risk_skus = [s for s in skus if s["risk_level"] in ("critical", "high")]
    if not at_risk_skus:
        at_risk_skus = skus[:5]

    channels = ["push", "email"]

    # Practical offer copy variations
    templates = [
        "Hi {first_name}, heads up — stock for '{product_name}' is critically low due to supplier delays. We recommend '{sub_name}' — ready to ship with next-day dispatch!",
        "Hey {first_name}! Notice you were eyeing '{product_name}'. It's currently in limited supply, but '{sub_name}' is in stock and highly rated by customers.",
        "{first_name}, supply alert: '{product_name}' may experience extended lead times. Check out '{sub_name}' — identical quality with immediate delivery.",
        "Dear {first_name}, your restock reminder: '{product_name}' inventory is running thin. Switch to '{sub_name}' for guaranteed express delivery.",
    ]

    for i in range(count):
        target_sku = random.choice(at_risk_skus)
        category = target_sku["category"]

        # Find healthy substitute from SAME category
        valid_subs = category_healthy_subs.get(category, [])
        if valid_subs:
            sub_sku = random.choice(valid_subs)
        else:
            # Fallback to any low-risk SKU
            sub_sku = [s for s in skus if s["risk_level"] == "low"][0]

        customer = random.choice(customers) if customers else {"customer_id": "CUST-0001", "name": "Customer User"}
        first_name = customer["name"].split()[0]

        # Funnel distribution: ~30% converted, ~30% opened, ~25% sent, ~15% pending
        r = random.random()
        if r < 0.30:
            status = "converted"
            sent_at = _random_dt(10)
            opened_at = sent_at + timedelta(hours=random.randint(1, 12))
            revenue = round(random.uniform(35.0, 185.0), 2)
        elif r < 0.60:
            status = "opened"
            sent_at = _random_dt(12)
            opened_at = sent_at + timedelta(hours=random.randint(1, 24))
            revenue = 0.0
        elif r < 0.85:
            status = "sent"
            sent_at = _random_dt(7)
            opened_at = None
            revenue = 0.0
        else:
            status = "pending"
            sent_at = None
            opened_at = None
            revenue = 0.0

        offer_text = random.choice(templates).format(
            first_name=first_name,
            product_name=target_sku["name"],
            sub_name=sub_sku["name"],
        )

        nudges.append({
            "campaign_id": _uid("NDG"),
            "sku_id": target_sku["sku_id"],
            "customer_id": customer["customer_id"],
            "substitute_sku_id": sub_sku["sku_id"],
            "offer_text": offer_text,
            "channel": random.choice(channels),
            "status": status,
            "sent_at": sent_at,
            "opened_at": opened_at,
            "revenue_recovered": revenue,
        })

    return nudges


def generate_signals(count: int = 500) -> list[dict]:
    """Generate signal log entries spread across the last 30 days."""
    signals = []
    sources = ["news", "weather", "shipping"]
    sample_countries = [
        "China", "Vietnam", "India", "Germany", "United States", "Taiwan",
        "Japan", "Brazil", "Bangladesh", "Turkey", "Poland", "Netherlands",
    ]

    for i in range(count):
        source = random.choice(sources)
        severity = random.choices([1, 2, 3, 4, 5], weights=[35, 30, 20, 10, 5])[0]

        signals.append({
            "signal_id": _uid("SIG"),
            "source": source,
            "raw_payload": {
                "headline": f"Signal #{i + 1} from {source}: logistical status update",
                "severity": severity,
                "region": random.choice(sample_countries),
                "confidence": round(random.uniform(0.65, 0.98), 2),
            },
            "processed_at": _random_dt(30),
            "risk_delta": round(random.uniform(-5.0, 15.0), 1),
            "triggered_agent_run": severity >= 4,
        })

    return signals


# ══════════════════════════════════════════════════════════════════
# MAIN SEED FUNCTION
# ══════════════════════════════════════════════════════════════════

async def seed(reset: bool = False) -> None:
    """Run the full seed process."""
    uri = os.getenv("MONGODB_URI")
    db_name = os.getenv("MONGODB_DB_NAME", "nexcart")

    if not uri:
        print("❌ MONGODB_URI not set in .env — cannot seed.")
        sys.exit(1)

    client = AsyncIOMotorClient(uri, serverSelectionTimeoutMS=5000)
    db = client[db_name]

    try:
        await client.admin.command("ping")
        print(f"✓ Connected to MongoDB: {db_name}")
    except Exception as exc:
        print(f"❌ MongoDB connection failed: {exc}")
        sys.exit(1)

    # ── Reset (wipe all) ──────────────────────────────────────────
    if reset:
        print("⚠ Resetting all collections...")
        for col_name in [SKUS, DISRUPTION_EVENTS, CUSTOMER_PROFILES, NUDGE_CAMPAIGNS, SIGNAL_LOGS]:
            result = await db[col_name].delete_many({})
            print(f"  Cleared {col_name}: {result.deleted_count} documents removed")

    # Check if SKUs already exist
    existing_skus = await db[SKUS].count_documents({})
    if existing_skus > 0 and not reset:
        print(f"SKUs already seeded ({existing_skus} found). Pass --reset to re-seed with fresh data.")
        client.close()
        return

    # ── Seed SKUs ─────────────────────────────────────────────────
    print("Seeding SKUs with realistic risk distribution...", end=" ", flush=True)
    skus = generate_skus()
    await db[SKUS].insert_many(skus)
    print(f"done ({len(skus)})")

    # ── Seed Customer Profiles ────────────────────────────────────
    print("Seeding customer profiles...", end=" ", flush=True)
    customers = generate_customers(200, skus=skus)
    await db[CUSTOMER_PROFILES].insert_many(customers)
    print(f"done ({len(customers)})")

    # ── Seed Disruption Events ────────────────────────────────────
    print("Seeding disruption events...", end=" ", flush=True)
    disruptions = generate_disruptions(skus=skus)
    await db[DISRUPTION_EVENTS].insert_many(disruptions)
    print(f"done ({len(disruptions)})")

    # ── Seed Nudge Campaigns ──────────────────────────────────────
    print("Seeding nudge campaigns...", end=" ", flush=True)
    nudges = generate_nudges(100, skus=skus, customers=customers)
    await db[NUDGE_CAMPAIGNS].insert_many(nudges)
    print(f"done ({len(nudges)})")

    # ── Seed Signal Logs ──────────────────────────────────────────
    print("Seeding signal logs...", end=" ", flush=True)
    signals = generate_signals(500)
    await db[SIGNAL_LOGS].insert_many(signals)
    print(f"done ({len(signals)})")

    # ── Summary ───────────────────────────────────────────────────
    counts_by_tier = {}
    for s in skus:
        counts_by_tier[s["risk_level"]] = counts_by_tier.get(s["risk_level"], 0) + 1

    print("\n══════════════════════════════════════════════════════════")
    print("  ✓ Seed complete!")
    print(f"    SKUs              : {len(skus)} {counts_by_tier}")
    print(f"    Customer Profiles : {len(customers)}")
    print(f"    Disruption Events : {len(disruptions)}")
    print(f"    Nudge Campaigns   : {len(nudges)}")
    print(f"    Signal Logs       : {len(signals)}")
    print("══════════════════════════════════════════════════════════")

    client.close()


# ══════════════════════════════════════════════════════════════════
# CLI ENTRY POINT
# ══════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="NexCart — Seed Database")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Wipe all collections before seeding",
    )
    args = parser.parse_args()

    asyncio.run(seed(reset=args.reset))


print("✓ seed.py complete")
