"""
NexCart — Composite Risk Score Calculator
==========================================
Calculates a 0–100 risk score for a SKU based on current stock
levels and incoming signal severity.
"""

from backend.database.models import RiskLevel


class RiskScorer:
    """
    Calculates composite risk scores for SKUs.

    Score composition:
      - Base score: derived from stock-to-reorder-point ratio
      - Signal weight: added from each signal's severity and source type
    """

    # Weight multipliers for signal source types
    SOURCE_WEIGHTS: dict[str, float] = {
        "news": 1.0,
        "weather": 1.2,
        "shipping": 1.5,
    }

    # Severity multipliers (severity 1–5 mapped to risk contribution)
    SEVERITY_MULTIPLIERS: dict[int, float] = {
        1: 2.0,
        2: 4.0,
        3: 6.0,
        4: 9.0,
        5: 12.0,
    }

    @staticmethod
    def _calculate_base_score(current_stock: int, reorder_point: int) -> float:
        """
        Calculate the base risk score from stock vs reorder point ratio.

        When stock is at or below reorder point → high base score.
        When stock is well above reorder point → low base score.
        """
        if reorder_point <= 0:
            return 0.0

        ratio = current_stock / reorder_point

        if ratio <= 0:
            # No stock at all — maximum base risk
            return 50.0
        elif ratio <= 0.5:
            # Stock is critically low (less than half of reorder point)
            return 45.0
        elif ratio <= 1.0:
            # Stock is at or below reorder point
            return 35.0
        elif ratio <= 2.0:
            # Stock is between 1x and 2x reorder point
            return 20.0
        elif ratio <= 5.0:
            # Comfortable stock level
            return 10.0
        else:
            # Very well stocked
            return 5.0

    def calculate_risk_score(self, signals: list, sku: dict) -> int:
        """
        Calculate a composite risk score for a SKU.

        Args:
            signals: List of signal dicts, each with 'source' and 'severity' keys.
                     Example: [{"source": "news", "severity": 3}, ...]
            sku: Dict with at least 'current_stock' and 'reorder_point' keys.

        Returns:
            int: Risk score clamped to 0–100.
        """
        current_stock = sku.get("current_stock", 0)
        reorder_point = sku.get("reorder_point", 10)

        # Step 1: Base score from stock ratio
        score = self._calculate_base_score(current_stock, reorder_point)

        # Step 2: Add signal weights
        for signal in signals:
            source = signal.get("source", "news")
            severity = signal.get("severity", 1)

            # Clamp severity to valid range
            severity = max(1, min(5, int(severity)))

            source_weight = self.SOURCE_WEIGHTS.get(source, 1.0)
            severity_mult = self.SEVERITY_MULTIPLIERS.get(severity, 2.0)

            signal_contribution = source_weight * severity_mult
            score += signal_contribution

        # Step 3: Clamp to 0–100
        score = max(0, min(100, int(round(score))))

        return score

    @staticmethod
    def get_risk_level(score: int) -> str:
        """
        Map a numeric risk score to a risk level string.

        Args:
            score: Risk score (0–100)

        Returns:
            str: One of 'low', 'medium', 'high', 'critical'
        """
        if score <= 25:
            return RiskLevel.LOW.value
        elif score <= 50:
            return RiskLevel.MEDIUM.value
        elif score <= 75:
            return RiskLevel.HIGH.value
        else:
            return RiskLevel.CRITICAL.value

    def assess(self, signals: list, sku: dict) -> dict:
        """
        Convenience method: calculate score and return both score and level.

        Returns:
            dict: {"risk_score": int, "risk_level": str}
        """
        score = self.calculate_risk_score(signals, sku)
        level = self.get_risk_level(score)
        return {"risk_score": score, "risk_level": level}


print("✓ risk_scorer.py complete")
