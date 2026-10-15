"""
NexCart — OpenWeatherMap Signal Service
=========================================
Fetches weather-based disruption signals for key supplier regions.
Falls back to realistic mock data if OPENWEATHER_API_KEY is missing.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx

from backend.utils.logger import get_logger

logger = get_logger("weather_service")

OPENWEATHER_BASE = "https://api.openweathermap.org/data/2.5/weather"

# Default supplier regions to monitor
MONITORED_CITIES: list[dict[str, Any]] = [
    {"name": "Shanghai", "lat": 31.2304, "lon": 121.4737, "region": "East Asia"},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777, "region": "South Asia"},
    {"name": "Rotterdam", "lat": 51.9244, "lon": 4.4777, "region": "Europe"},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437, "region": "North America"},
    {"name": "Jakarta", "lat": -6.2088, "lon": 106.8456, "region": "Southeast Asia"},
]


class WeatherService:
    """Fetches and normalises weather disruption signals from OpenWeatherMap."""

    def __init__(self) -> None:
        self.api_key: str = os.getenv("OPENWEATHER_API_KEY", "")

    @staticmethod
    def _score_severity(weather_data: dict) -> int:
        """
        Score severity 1–5 based on weather conditions.
        wind_speed > 20 m/s = 5, heavy rain = 3, mild storm = 2, else = 1.
        """
        wind_speed = weather_data.get("wind", {}).get("speed", 0)
        weather_main = ""
        if weather_data.get("weather"):
            weather_main = weather_data["weather"][0].get("main", "").lower()
        weather_desc = ""
        if weather_data.get("weather"):
            weather_desc = weather_data["weather"][0].get("description", "").lower()

        if wind_speed > 20:
            return 5
        if "thunderstorm" in weather_main or "tornado" in weather_desc:
            return 5
        if "heavy" in weather_desc and "rain" in weather_desc:
            return 3
        if "storm" in weather_desc or "squall" in weather_main:
            return 2
        if "rain" in weather_main or "drizzle" in weather_main:
            return 1
        return 1

    @staticmethod
    def _build_title(city_name: str, weather_data: dict) -> str:
        """Build a human-readable signal title from weather data."""
        weather_desc = "unknown conditions"
        if weather_data.get("weather"):
            weather_desc = weather_data["weather"][0].get("description", "unknown")
        temp = weather_data.get("main", {}).get("temp", 0)
        wind = weather_data.get("wind", {}).get("speed", 0)
        return (
            f"Weather alert in {city_name}: {weather_desc} "
            f"(temp: {temp:.0f}C, wind: {wind:.1f}m/s)"
        )

    async def fetch_signals(self) -> list[dict[str, Any]]:
        """
        Fetch weather signals for all monitored supplier regions.
        Returns list of normalised signal dicts.
        """
        if not self.api_key:
            logger.warning("OPENWEATHER_API_KEY not set — returning mock signals")
            return self._mock_signals()

        signals: list[dict[str, Any]] = []

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                for city in MONITORED_CITIES:
                    response = await client.get(
                        OPENWEATHER_BASE,
                        params={
                            "lat": city["lat"],
                            "lon": city["lon"],
                            "appid": self.api_key,
                            "units": "metric",
                        },
                    )

                    if response.status_code != 200:
                        logger.error(
                            f"OpenWeatherMap error for {city['name']}: "
                            f"{response.status_code}"
                        )
                        continue

                    data = response.json()
                    severity = self._score_severity(data)

                    # Only report signals with severity >= 2
                    if severity >= 2:
                        signals.append({
                            "source": "weather",
                            "title": self._build_title(city["name"], data),
                            "description": (
                                f"Weather disruption detected in {city['name']} "
                                f"({city['region']}). Wind speed: "
                                f"{data.get('wind', {}).get('speed', 0):.1f}m/s, "
                                f"Humidity: {data.get('main', {}).get('humidity', 0)}%."
                            ),
                            "severity": severity,
                            "affected_regions": [city["region"]],
                            "published_at": datetime.now(timezone.utc),
                            "city": city["name"],
                            "raw_weather": data,
                        })

            logger.info(f"Fetched {len(signals)} weather signals from OpenWeatherMap")

        except httpx.HTTPError as exc:
            logger.error(f"OpenWeatherMap HTTP error: {exc}")
            return self._mock_signals()
        except Exception as exc:
            logger.error(f"OpenWeatherMap unexpected error: {exc}")
            return self._mock_signals()

        return signals if signals else self._mock_signals()

    @staticmethod
    def _mock_signals() -> list[dict[str, Any]]:
        """Return 3 realistic mock weather signals for demo mode."""
        now = datetime.now(timezone.utc)
        return [
            {
                "source": "weather",
                "title": "Weather alert in Shanghai: heavy intensity rain (temp: 18C, wind: 22.5m/s)",
                "description": "Severe storm system over Shanghai port area with sustained high winds exceeding 20m/s. Container operations likely suspended for 12-24 hours.",
                "severity": 5,
                "affected_regions": ["East Asia"],
                "published_at": now - timedelta(hours=1),
                "city": "Shanghai",
            },
            {
                "source": "weather",
                "title": "Weather alert in Mumbai: moderate rain (temp: 31C, wind: 8.2m/s)",
                "description": "Heavy monsoon rain expected in Mumbai over the next 48 hours. Port operations may experience delays due to reduced visibility.",
                "severity": 3,
                "affected_regions": ["South Asia"],
                "published_at": now - timedelta(hours=4),
                "city": "Mumbai",
            },
            {
                "source": "weather",
                "title": "Weather alert in Rotterdam: light storm (temp: 8C, wind: 15.0m/s)",
                "description": "Mild storm passing through the North Sea affecting Rotterdam harbour. Minor delays expected for incoming vessels.",
                "severity": 2,
                "affected_regions": ["Europe"],
                "published_at": now - timedelta(hours=8),
                "city": "Rotterdam",
            },
        ]


print("✓ weather_service.py complete")
