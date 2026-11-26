"""
NexCart — NewsAPI Signal Service
==================================
Fetches supply-chain disruption signals from NewsAPI.
Falls back to realistic mock data if NEWS_API_KEY is missing.
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from backend.utils.logger import get_logger
from backend.core.settings import settings

logger = get_logger("news_service")

NEWS_API_BASE = "https://newsapi.org/v2/everything"
QUERY_TERMS = [
    "supply chain disruption",
    "port strike",
    "shipping delay",
    "factory closure",
    "trade tariff",
]

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search"

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
        self.api_key: str = settings.news_api_key

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
        signals: list[dict[str, Any]] = []

        if self.api_key:
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
                            logger.error(f"NewsAPI error for query '{query}': {response.status_code}")
                            continue
                        for article in response.json().get("articles", []):
                            title = article.get("title", "") or ""
                            description = article.get("description", "") or ""
                            published_str = article.get("publishedAt", "")
                            try:
                                published_at = datetime.fromisoformat(published_str.replace("Z", "+00:00"))
                            except (ValueError, AttributeError):
                                published_at = datetime.now(timezone.utc)
                            signals.append({
                                "source": "news", "title": title, "description": description,
                                "severity": self._score_severity(f"{title} {description}"),
                                "affected_regions": self._extract_regions(f"{title} {description}"),
                                "published_at": published_at,
                                "evidence_sources": [{"provider": "NewsAPI", "outlet": (article.get("source") or {}).get("name", "Unknown"), "url": article.get("url", "")}],
                            })
            except httpx.HTTPError as exc:
                logger.error(f"NewsAPI HTTP error: {exc}")
            except Exception as exc:
                logger.error(f"NewsAPI unexpected error: {exc}")
        else:
            logger.warning("NEWS_API_KEY not set — using Google News RSS plus demo fallback")

        signals.extend(await self._fetch_google_news())
        return self._corroborate(signals) if signals else self._mock_signals()

    async def _fetch_google_news(self) -> list[dict[str, Any]]:
        """Use Google News RSS as an independent, keyless corroboration source."""
        signals: list[dict[str, Any]] = []
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                for query in QUERY_TERMS[:3]:
                    response = await client.get(GOOGLE_NEWS_RSS, params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"})
                    response.raise_for_status()
                    root = ET.fromstring(response.text)
                    for item in root.findall("./channel/item")[:5]:
                        title = item.findtext("title", "")
                        description = item.findtext("description", "")
                        outlet = item.findtext("source", "Google News")
                        link = item.findtext("link", "")
                        combined = f"{title} {description}"
                        signals.append({
                            "source": "news", "title": title, "description": description,
                            "severity": self._score_severity(combined),
                            "affected_regions": self._extract_regions(combined),
                            "published_at": datetime.now(timezone.utc),
                            "evidence_sources": [{"provider": "Google News RSS", "outlet": outlet, "url": link}],
                        })
        except (httpx.HTTPError, ET.ParseError) as exc:
            logger.warning(f"Google News RSS unavailable: {exc}")
        return signals

    @staticmethod
    def _title_words(title: str) -> set[str]:
        return {word for word in re.findall(r"[a-z]{4,}", title.lower()) if word not in {"news", "supply", "chain"}}

    def _corroborate(self, signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Merge matching headlines and expose a transparent genuineness assessment."""
        grouped: list[dict[str, Any]] = []
        for signal in signals:
            words = self._title_words(signal["title"])
            match = next((candidate for candidate in grouped if words and len(words & self._title_words(candidate["title"])) / max(1, len(words | self._title_words(candidate["title"]))) >= 0.45), None)
            if match:
                match["evidence_sources"].extend(signal["evidence_sources"])
                match["severity"] = max(match["severity"], signal["severity"])
                match["affected_regions"] = sorted(set(match["affected_regions"] + signal["affected_regions"]))
            else:
                grouped.append(signal)
        for signal in grouped:
            distinct_outlets = {item["outlet"].lower() for item in signal["evidence_sources"] if item.get("outlet")}
            coverage = len(distinct_outlets)
            signal["source_count"] = coverage
            signal["genuineness_score"] = min(100, 35 + coverage * 30)
            signal["verification_status"] = "confirmed" if coverage >= 2 else "single_source"
        logger.info(f"Collected {len(grouped)} corroborated news signals")
        return grouped

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
                "evidence_sources": [{"provider": "Demo", "outlet": "Demo data", "url": ""}],
                "source_count": 1, "genuineness_score": 0, "verification_status": "demo",
            },
            {
                "source": "news",
                "title": "Factory closure in Guangdong province affects textile production",
                "description": "A major textile factory in Guangdong has been shut down due to safety violations, disrupting apparel supply for international retailers.",
                "severity": 5,
                "affected_regions": ["East Asia"],
                "published_at": now - timedelta(hours=6),
                "evidence_sources": [{"provider": "Demo", "outlet": "Demo data", "url": ""}],
                "source_count": 1, "genuineness_score": 0, "verification_status": "demo",
            },
            {
                "source": "news",
                "title": "New trade tariffs on pharmaceutical imports from India",
                "description": "Recent policy changes introduce 15% tariffs on pharmaceutical raw materials imported from India, raising concerns about drug pricing globally.",
                "severity": 2,
                "affected_regions": ["South Asia", "Global"],
                "published_at": now - timedelta(hours=12),
                "evidence_sources": [{"provider": "Demo", "outlet": "Demo data", "url": ""}],
                "source_count": 1, "genuineness_score": 0, "verification_status": "demo",
            },
        ]


print("✓ news_service.py complete")
