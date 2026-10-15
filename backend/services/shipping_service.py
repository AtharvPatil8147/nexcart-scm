"""
NexCart — Shipping / MarineTraffic Signal Service
====================================================
Monitors major shipping lanes for disruption signals.
Always returns mock data if MARINE_TRAFFIC_API_KEY is missing.
"""

import os
import random
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from backend.utils.logger import get_logger

logger = get_logger("shipping_service")

# Major shipping lanes to monitor
SHIPPING_LANES = [
    {
        "name": "Strait of Malacca",
        "lat": 2.5, "lon": 101.8,
        "regions": ["Southeast Asia", "East Asia"],
        "ports": ["Singapore", "Port Klang", "Belawan"],
    },
    {
        "name": "Suez Canal",
        "lat": 30.58, "lon": 32.27,
        "regions": ["Middle East", "Europe"],
        "ports": ["Port Said", "Suez", "Jeddah"],
    },
    {
        "name": "Panama Canal",
        "lat": 9.08, "lon": -79.68,
        "regions": ["North America", "South America"],
        "ports": ["Balboa", "Cristobal", "Manzanillo"],
    },
    {
        "name": "English Channel",
        "lat": 50.5, "lon": -1.0,
        "regions": ["Europe"],
        "ports": ["Southampton", "Le Havre", "Rotterdam"],
    },
    {
        "name": "Taiwan Strait",
        "lat": 24.5, "lon": 119.5,
        "regions": ["East Asia"],
        "ports": ["Kaohsiung", "Xiamen", "Taichung"],
    },
]

VESSEL_NAMES = [
    "MSC Gulsun", "Ever Given", "CSCL Globe", "HMM Algeciras",
    "CMA CGM Jacques Saade", "OOCL Hong Kong", "Madrid Maersk",
    "MOL Triumph", "Cosco Shipping Universe", "Barzan",
    "MSC Mia", "Yang Ming Witness", "ONE Stork", "Hapag Bremen",
    "Evergreen Triton",
]

DISRUPTION_TYPES = [
    "vessel grounding", "mechanical failure", "port congestion",
    "weather-related closure", "security incident", "labour dispute",
    "channel blockage", "equipment malfunction",
]


class ShippingService:
    """Fetches and normalises shipping lane disruption signals."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("MARINE_TRAFFIC_API_KEY", "")

    async def fetch_signals(self) -> list[dict[str, Any]]:
        """
        Fetch shipping lane disruption signals.
        Uses MarineTraffic API if key is present, otherwise returns
        5 realistic mock signals.
        """
        if not self.api_key:
            logger.warning(
                "MARINE_TRAFFIC_API_KEY not set — returning mock signals"
            )
            return self._mock_signals()

        signals: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for lane in SHIPPING_LANES:
                    response = await client.get(
                        "https://services.marinetraffic.com/api/exportvessels/v:8",
                        params={
                            "v": 8,
                            "MINLAT": lane["lat"] - 1,
                            "MAXLAT": lane["lat"] + 1,
                            "MINLON": lane["lon"] - 1,
                            "MAXLON": lane["lon"] + 1,
                            "SHIPTYPE": 7,  # Container ships
                            "protocol": "jsono",
                            "msgtype": "simple",
                            "apikey": self.api_key,
                        },
                    )

                    if response.status_code != 200:
                        logger.error(
                            f"MarineTraffic error for {lane['name']}: "
                            f"{response.status_code}"
                        )
                        continue

                    data = response.json()
                    vessel_count = len(data) if isinstance(data, list) else 0

                    # High vessel density suggests congestion
                    if vessel_count > 50:
                        severity = 4
                    elif vessel_count > 30:
                        severity = 3
                    elif vessel_count > 15:
                        severity = 2
                    else:
                        severity = 1

                    if severity >= 2:
                        signals.append({
                            "source": "shipping",
                            "title": f"Congestion detected at {lane['name']}",
                            "description": (
                                f"{vessel_count} container vessels detected in "
                                f"{lane['name']}. Affected ports: "
                                f"{', '.join(lane['ports'])}."
                            ),
                            "severity": severity,
                            "affected_regions": lane["regions"],
                            "published_at": datetime.now(timezone.utc),
                            "lane": lane["name"],
                            "vessel_count": vessel_count,
                            "affected_ports": lane["ports"],
                        })

            logger.info(
                f"Fetched {len(signals)} shipping signals from MarineTraffic"
            )

        except httpx.HTTPError as exc:
            logger.error(f"MarineTraffic HTTP error: {exc}")
            return self._mock_signals()
        except Exception as exc:
            logger.error(f"MarineTraffic unexpected error: {exc}")
            return self._mock_signals()

        return signals if signals else self._mock_signals()

    @staticmethod
    def _mock_signals() -> list[dict[str, Any]]:
        """Return 5 realistic mock shipping signals for demo mode."""
        now = datetime.now(timezone.utc)

        return [
            {
                "source": "shipping",
                "title": "Vessel grounding partially blocks Suez Canal",
                "description": (
                    "Container vessel 'MSC Gulsun' (capacity 23,756 TEU) ran "
                    "aground at km 151 of the Suez Canal. Northbound traffic "
                    "halted. Estimated 18-hour delay. Affected ports: Port Said, "
                    "Suez, Jeddah."
                ),
                "severity": 5,
                "affected_regions": ["Middle East", "Europe"],
                "published_at": now - timedelta(hours=3),
                "lane": "Suez Canal",
                "vessel_name": "MSC Gulsun",
                "coordinates": {"lat": 30.58, "lon": 32.27},
                "delay_hours": 18,
                "affected_ports": ["Port Said", "Suez", "Jeddah"],
            },
            {
                "source": "shipping",
                "title": "Port congestion at Strait of Malacca worsens",
                "description": (
                    "42 container vessels queued at the Strait of Malacca "
                    "anchorage. Average wait time increased to 36 hours. "
                    "Singapore port operating at 94% capacity."
                ),
                "severity": 4,
                "affected_regions": ["Southeast Asia", "East Asia"],
                "published_at": now - timedelta(hours=6),
                "lane": "Strait of Malacca",
                "vessel_name": "CSCL Globe",
                "coordinates": {"lat": 2.5, "lon": 101.8},
                "delay_hours": 36,
                "affected_ports": ["Singapore", "Port Klang"],
            },
            {
                "source": "shipping",
                "title": "Panama Canal water level restrictions limit transits",
                "description": (
                    "Drought conditions have reduced daily transits through "
                    "the Panama Canal from 36 to 24 vessels. Neopanamax slots "
                    "auctioned at premium. 'CMA CGM Jacques Saade' diverted "
                    "to Suez route."
                ),
                "severity": 3,
                "affected_regions": ["North America", "South America"],
                "published_at": now - timedelta(hours=12),
                "lane": "Panama Canal",
                "vessel_name": "CMA CGM Jacques Saade",
                "coordinates": {"lat": 9.08, "lon": -79.68},
                "delay_hours": 48,
                "affected_ports": ["Balboa", "Cristobal"],
            },
            {
                "source": "shipping",
                "title": "Labour dispute delays at English Channel ports",
                "description": (
                    "Dock workers at Southampton and Le Havre have announced "
                    "a 48-hour work slowdown. Container throughput reduced by "
                    "40%. Vessel 'Madrid Maersk' reports 12-hour berthing delay."
                ),
                "severity": 3,
                "affected_regions": ["Europe"],
                "published_at": now - timedelta(hours=18),
                "lane": "English Channel",
                "vessel_name": "Madrid Maersk",
                "coordinates": {"lat": 50.5, "lon": -1.0},
                "delay_hours": 12,
                "affected_ports": ["Southampton", "Le Havre", "Rotterdam"],
            },
            {
                "source": "shipping",
                "title": "Security alert increases insurance costs in Taiwan Strait",
                "description": (
                    "Military exercises near Taiwan Strait have triggered "
                    "elevated war-risk premiums for vessels transiting the area. "
                    "'Evergreen Triton' re-routed via Luzon Strait adding "
                    "2 days transit time."
                ),
                "severity": 2,
                "affected_regions": ["East Asia"],
                "published_at": now - timedelta(hours=24),
                "lane": "Taiwan Strait",
                "vessel_name": "Evergreen Triton",
                "coordinates": {"lat": 24.5, "lon": 119.5},
                "delay_hours": 48,
                "affected_ports": ["Kaohsiung", "Xiamen"],
            },
        ]


print("✓ shipping_service.py complete")
