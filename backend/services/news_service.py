"""
NexCart — NewsAPI Signal Service
==================================
Fetches supply-chain disruption signals from NewsAPI.
Falls back to realistic mock data if NEWS_API_KEY is missing.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from backend.utils.logger import get_logger

logger = get_logger("news_service")

NEWS_API_BASE = "https://newsapi.org/v2/everything"
QUERY_TERMS = [
    "supply chain disruption",
    "port strike",
    "shipping delay",
    "factory closure",
    "trade tariff",
]

# Keyword → severity mapping
SEVERITY_KEYWORDS: dict[int, list[str]] = {
    5: ["critical", "closure", "strike", "shutdown", "catastrophe"],
    3: ["delay", "disruption", "shortage", "backlog", "congestion"],
    2: ["risk", "warning", "concern", "slowdown", "uncertainty"],
}

REGION_KEYWORDS: dict[str, list[str]] = {
    "East Asia": ["china", "shanghai", "shenzhen", "taiwan", "beijing"],
    "South Asia": ["india", "mumbai", "delhi", "bangladesh", "dhaka"],
    "Southeast Asia": ["vietnam", "indonesia", "jakarta", "malaysia", "thailand"],
    "Europe": ["germany", "rotterdam", "hamburg", "france", "italy", "poland"],
    "North America": ["los angeles", "new york", "united states", "mexico", "canada"],
    "Middle East": ["suez", "red sea", "gulf", "saudi", "dubai"],
    "Global": ["global", "worldwide", "international"],
}


class NewsService:
    """Fetches and normalises supply-chain news signals from NewsAPI."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("NEWS_API_KEY", "")

    @staticmethod
    def _score_severity(text: str) -> int:
        """Score severity 1–5 based on keyword presence in text."""
        text_lower = text.lower()
        for severity, keywords in SEVERITY_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    return severity
        return 1

    @staticmethod
    def _extract_regions(text: str) -> list[str]:
        """Extract affected regions from text via keyword matching."""
        text_lower = text.lower()
        regions: list[str] = []
        for region, keywords in REGION_KEYWORDS.items():
            for kw in keywords:
                if kw in text_lower:
                    regions.append(region)
                    break
        return regions if regions else ["Global"]

    async def fetch_signals(self) -> list[dict[str, Any]]:
        """
        Fetch supply-chain news signals.
        Returns list of normalised signal dicts.
        Falls back to mock data if API key is missing.
        """
        if not self.api_key:
            logger.warning("NEWS_API_KEY not set — returning mock signals")
            return self._mock_signals()

        signals: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for query in QUERY_TERMS:
                    response = await client.get(
                        NEWS_API_BASE,
                        params={
                            "q": query,
                            "language": "en",
                            "sortBy": "publishedAt",
                            "pageSize": 5,
                            "apiKey": self.api_key,
                        },
                    )

                    if response.status_code != 200:
                        logger.error(
                            f"NewsAPI error for query '{query}': {response.status_code}"
                        )
                        continue

                    data = response.json()
                    articles = data.get("articles", [])

                    for article in articles:
                        title = article.get("title", "") or ""
                        description = article.get("description", "") or ""
                        combined_text = f"{title} {description}"
                        published_str = article.get("publishedAt", "")

                        try:
                            published_at = datetime.fromisoformat(
                                published_str.replace("Z", "+00:00")
                            )
                        except (ValueError, AttributeError):
                            published_at = datetime.now(timezone.utc)

                        signals.append({
                            "source": "news",
                            "title": title,
                            "description": description,
                            "severity": self._score_severity(combined_text),
                            "affected_regions": self._extract_regions(combined_text),
                            "published_at": published_at,
                        })

            logger.info(f"Fetched {len(signals)} news signals from NewsAPI")

        except httpx.HTTPError as exc:
            logger.error(f"NewsAPI HTTP error: {exc}")
            return self._mock_signals()
        except Exception as exc:
            logger.error(f"NewsAPI unexpected error: {exc}")
            return self._mock_signals()

        return signals if signals else self._mock_signals()

    @staticmethod
    def _mock_signals() -> list[dict[str, Any]]:
        """Return 3 realistic mock news signals for demo mode."""
        now = datetime.now(timezone.utc)
        return [
            {
                "source": "news",
                "title": "Major port congestion at Shanghai delays electronics shipments",
                "description": "Severe congestion at Shanghai's Yangshan port has caused 7-day delays for container vessels, impacting electronics supply chains across East Asia.",
                "severity": 3,
                "affected_regions": ["East Asia", "Global"],
                "published_at": now - timedelta(hours=2),
            },
            {
                "source": "news",
                "title": "Factory closure in Guangdong province affects textile production",
                "description": "A major textile factory in Guangdong has been shut down due to safety violations, disrupting apparel supply for international retailers.",
                "severity": 5,
                "affected_regions": ["East Asia"],
                "published_at": now - timedelta(hours=6),
            },
            {
                "source": "news",
                "title": "New trade tariffs on pharmaceutical imports from India",
                "description": "Recent policy changes introduce 15% tariffs on pharmaceutical raw materials imported from India, raising concerns about drug pricing globally.",
                "severity": 2,
                "affected_regions": ["South Asia", "Global"],
                "published_at": now - timedelta(hours=12),
            },
        ]


print("✓ news_service.py complete")
