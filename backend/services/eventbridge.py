"""
NexCart — AWS EventBridge Publisher
=====================================
Publishes DisruptionDetected events to EventBridge.
Gracefully degrades if AWS credentials are missing.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError

from backend.utils.logger import get_logger

logger = get_logger("eventbridge")


class EventBridgeService:
    """Publishes disruption events to AWS EventBridge."""

    def __init__(self) -> None:
        self.bus_name: str = os.getenv("EVENTBRIDGE_BUS_NAME", "nexcart-events")
        self.source: str = os.getenv("EVENTBRIDGE_SOURCE", "com.nexcart.signals")
        self.region: str = os.getenv("AWS_REGION", "us-east-1")
        self._client = None

    def _get_client(self) -> Any:
        """Lazily initialise the EventBridge boto3 client."""
        if self._client is None:
            aws_key = os.getenv("AWS_ACCESS_KEY_ID", "")
            aws_secret = os.getenv("AWS_SECRET_ACCESS_KEY", "")

            if not aws_key or not aws_secret:
                return None

            self._client = boto3.client(
                "events",
                region_name=self.region,
                aws_access_key_id=aws_key,
                aws_secret_access_key=aws_secret,
            )
        return self._client

    async def publish_disruption_event(
        self,
        sku_id: str,
        risk_score: int,
        risk_level: str,
        reasoning: str,
    ) -> bool:
        """
        Publish a DisruptionDetected event to EventBridge.

        Args:
            sku_id: The affected SKU identifier
            risk_score: Calculated risk score (0–100)
            risk_level: Risk classification (low/medium/high/critical)
            reasoning: AI-generated reasoning for the risk assessment

        Returns:
            bool: True if published successfully (or gracefully degraded)
        """
        client = self._get_client()

        if client is None:
            logger.warning(
                "AWS credentials not configured — skipping EventBridge publish. "
                f"Event: DisruptionDetected for SKU {sku_id} "
                f"(score={risk_score}, level={risk_level})"
            )
            return True  # Graceful degradation

        detail = json.dumps({
            "sku_id": sku_id,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "reasoning": reasoning,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        try:
            response = client.put_events(
                Entries=[
                    {
                        "Source": self.source,
                        "DetailType": "DisruptionDetected",
                        "Detail": detail,
                        "EventBusName": self.bus_name,
                    }
                ]
            )

            failed_count = response.get("FailedEntryCount", 0)
            if failed_count > 0:
                logger.error(
                    f"EventBridge: {failed_count} entries failed to publish. "
                    f"Response: {response}"
                )
                return False

            logger.info(
                f"EventBridge: Published DisruptionDetected for SKU {sku_id} "
                f"(score={risk_score}, level={risk_level})"
            )
            return True

        except NoCredentialsError:
            logger.warning(
                "AWS credentials not found — skipping EventBridge publish"
            )
            return True  # Graceful degradation
        except (BotoCoreError, ClientError) as exc:
            logger.error(f"EventBridge publish error: {exc}")
            return False
        except Exception as exc:
            logger.error(f"EventBridge unexpected error: {exc}")
            return False


print("✓ eventbridge.py complete")
