"""
NexCart — MongoDB Collection Name Constants
============================================
Centralised string constants for all 5 MongoDB collections.
Import these instead of using raw strings to avoid typos.
"""

# ── Collection Names ──────────────────────────────────────────────
SKUS: str = "skus"
DISRUPTION_EVENTS: str = "disruption_events"
CUSTOMER_PROFILES: str = "customer_profiles"
NUDGE_CAMPAIGNS: str = "nudge_campaigns"
SIGNAL_LOGS: str = "signal_logs"

# ── All collections as a list (used by connection.py for index setup)
ALL_COLLECTIONS: list[str] = [
    SKUS,
    DISRUPTION_EVENTS,
    CUSTOMER_PROFILES,
    NUDGE_CAMPAIGNS,
    SIGNAL_LOGS,
]

print("✓ collections.py complete")
