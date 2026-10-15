"""
NexCart — Pydantic v2 Models for All MongoDB Collections
==========================================================
Each collection has three model layers:
  - *Base:    fields for creation (no _id)
  - *Model:   full document with _id (for internal use)
  - *Response: serialisable response with id as string
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from bson import ObjectId
from pydantic import BaseModel, Field, field_validator, model_validator


# ══════════════════════════════════════════════════════════════════
# ENUMS
# ══════════════════════════════════════════════════════════════════

class RiskLevel(str, Enum):
    """Risk classification for SKUs."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NudgeChannel(str, Enum):
    """Delivery channel for nudge campaigns."""
    PUSH = "push"
    EMAIL = "email"


class NudgeStatus(str, Enum):
    """Lifecycle status of a nudge campaign."""
    PENDING = "pending"
    SENT = "sent"
    OPENED = "opened"
    CONVERTED = "converted"


class SignalSource(str, Enum):
    """Source type for external signals."""
    NEWS = "news"
    WEATHER = "weather"
    SHIPPING = "shipping"


class DisruptionSeverity(int, Enum):
    """Severity scale for disruption events (1–5)."""
    MINIMAL = 1
    LOW = 2
    MODERATE = 3
    HIGH = 4
    CRITICAL = 5


# ══════════════════════════════════════════════════════════════════
# HELPER: ObjectId ↔ string conversion
# ══════════════════════════════════════════════════════════════════

class PyObjectId(str):
    """Custom type that accepts both ObjectId and string."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v: Any) -> str:
        if isinstance(v, ObjectId):
            return str(v)
        if isinstance(v, str) and ObjectId.is_valid(v):
            return v
        raise ValueError(f"Invalid ObjectId: {v}")


# ══════════════════════════════════════════════════════════════════
# 1. SKU MODELS
# ══════════════════════════════════════════════════════════════════

class SKUBase(BaseModel):
    """Fields required to create a new SKU."""
    sku_id: str = Field(..., description="Unique SKU identifier (e.g. 'SKU-ELEC-001')")
    name: str = Field(..., description="Human-readable product name")
    category: str = Field(..., description="Product category (Electronics, Apparel, Food, Pharma, Home Goods)")
    supplier_country: str = Field(..., description="Country where the primary supplier is located")
    current_stock: int = Field(0, ge=0, description="Current stock quantity in warehouse")
    reorder_point: int = Field(10, ge=0, description="Stock threshold that triggers reorder")
    risk_score: int = Field(0, ge=0, le=100, description="Composite risk score (0–100)")
    risk_level: RiskLevel = Field(RiskLevel.LOW, description="Risk classification derived from risk_score")
    last_updated: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp of last risk score update"
    )

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "sku_id": "SKU-ELEC-001",
                "name": "Wireless Bluetooth Earbuds",
                "category": "Electronics",
                "supplier_country": "China",
                "current_stock": 150,
                "reorder_point": 30,
                "risk_score": 42,
                "risk_level": "medium",
            }
        },
    }


class SKUModel(SKUBase):
    """Full SKU document as stored in MongoDB (includes _id)."""
    id: Optional[Any] = Field(None, alias="_id", description="MongoDB ObjectId")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    def to_dict(self) -> dict:
        """Convert to dictionary with ObjectId serialised to string."""
        data = self.model_dump(by_alias=True)
        if data.get("_id") is not None:
            data["_id"] = str(data["_id"])
        if isinstance(data.get("last_updated"), datetime):
            data["last_updated"] = data["last_updated"].isoformat()
        if isinstance(data.get("risk_level"), RiskLevel):
            data["risk_level"] = data["risk_level"].value
        return data


class SKUResponse(BaseModel):
    """API response model for SKU (id as string)."""
    id: Optional[str] = Field(None, alias="_id", description="Document ID as string")
    sku_id: str
    name: str
    category: str
    supplier_country: str
    current_stock: int
    reorder_point: int
    risk_score: int
    risk_level: RiskLevel
    last_updated: datetime

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, v: Any) -> Optional[str]:
        if isinstance(v, ObjectId):
            return str(v)
        return v


# ══════════════════════════════════════════════════════════════════
# 2. DISRUPTION EVENT MODELS
# ══════════════════════════════════════════════════════════════════

class DisruptionEventBase(BaseModel):
    """Fields required to create a disruption event."""
    event_id: str = Field(..., description="Unique event identifier")
    source: SignalSource = Field(..., description="Signal source (news/weather/shipping)")
    title: str = Field(..., description="Short headline of the disruption")
    description: str = Field("", description="Detailed description of the event")
    affected_regions: list[str] = Field(default_factory=list, description="List of affected geographic regions")
    affected_sku_ids: list[str] = Field(default_factory=list, description="List of SKU IDs impacted by this event")
    severity: DisruptionSeverity = Field(DisruptionSeverity.MODERATE, description="Severity rating (1–5)")
    predicted_impact_days: int = Field(0, ge=0, le=365, description="Estimated days until full impact")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when the event was detected"
    )

    model_config = {
        "populate_by_name": True,
    }


class DisruptionEventModel(DisruptionEventBase):
    """Full disruption event document with MongoDB _id."""
    id: Optional[Any] = Field(None, alias="_id", description="MongoDB ObjectId")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    def to_dict(self) -> dict:
        """Convert to dictionary with ObjectId serialised to string."""
        data = self.model_dump(by_alias=True)
        if data.get("_id") is not None:
            data["_id"] = str(data["_id"])
        if isinstance(data.get("created_at"), datetime):
            data["created_at"] = data["created_at"].isoformat()
        if isinstance(data.get("source"), SignalSource):
            data["source"] = data["source"].value
        if isinstance(data.get("severity"), DisruptionSeverity):
            data["severity"] = data["severity"].value
        return data


class DisruptionEventResponse(BaseModel):
    """API response model for disruption events."""
    id: Optional[str] = Field(None, alias="_id")
    event_id: str
    source: SignalSource
    title: str
    description: str
    affected_regions: list[str]
    affected_sku_ids: list[str]
    severity: DisruptionSeverity
    predicted_impact_days: int
    created_at: datetime

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, v: Any) -> Optional[str]:
        if isinstance(v, ObjectId):
            return str(v)
        return v


# ══════════════════════════════════════════════════════════════════
# 3. CUSTOMER PROFILE MODELS
# ══════════════════════════════════════════════════════════════════

class PurchaseHistoryItem(BaseModel):
    """Single purchase record within a customer profile."""
    sku_id: str = Field(..., description="SKU ID of the purchased product")
    quantity: int = Field(1, ge=1, description="Quantity purchased")
    date: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Date of purchase"
    )


class CustomerPreferences(BaseModel):
    """Customer preference settings."""
    categories: list[str] = Field(default_factory=list, description="Preferred product categories")
    brands: list[str] = Field(default_factory=list, description="Preferred brands")


class CustomerProfileBase(BaseModel):
    """Fields required to create a customer profile."""
    customer_id: str = Field(..., description="Unique customer identifier")
    name: str = Field(..., description="Customer full name")
    email: str = Field(..., description="Customer email address")
    push_token: Optional[str] = Field(None, description="Firebase push notification token")
    purchase_history: list[PurchaseHistoryItem] = Field(
        default_factory=list,
        description="List of past purchases"
    )
    preferences: CustomerPreferences = Field(
        default_factory=CustomerPreferences,
        description="Customer category and brand preferences"
    )

    model_config = {
        "populate_by_name": True,
    }


class CustomerProfileModel(CustomerProfileBase):
    """Full customer profile document with MongoDB _id."""
    id: Optional[Any] = Field(None, alias="_id", description="MongoDB ObjectId")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    def to_dict(self) -> dict:
        """Convert to dictionary with ObjectId serialised to string."""
        data = self.model_dump(by_alias=True)
        if data.get("_id") is not None:
            data["_id"] = str(data["_id"])
        # Serialise nested datetime objects in purchase_history
        for item in data.get("purchase_history", []):
            if isinstance(item.get("date"), datetime):
                item["date"] = item["date"].isoformat()
        return data


class CustomerProfileResponse(BaseModel):
    """API response model for customer profiles."""
    id: Optional[str] = Field(None, alias="_id")
    customer_id: str
    name: str
    email: str
    push_token: Optional[str] = None
    purchase_history: list[PurchaseHistoryItem]
    preferences: CustomerPreferences

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, v: Any) -> Optional[str]:
        if isinstance(v, ObjectId):
            return str(v)
        return v


# ══════════════════════════════════════════════════════════════════
# 4. NUDGE CAMPAIGN MODELS
# ══════════════════════════════════════════════════════════════════

class NudgeCampaignBase(BaseModel):
    """Fields required to create a nudge campaign."""
    campaign_id: str = Field(..., description="Unique campaign identifier")
    sku_id: str = Field(..., description="At-risk SKU this campaign addresses")
    customer_id: str = Field(..., description="Target customer ID")
    substitute_sku_id: Optional[str] = Field(None, description="Recommended substitute SKU ID")
    offer_text: str = Field("", description="Personalised offer message generated by AI")
    channel: NudgeChannel = Field(NudgeChannel.EMAIL, description="Delivery channel (push/email)")
    status: NudgeStatus = Field(NudgeStatus.PENDING, description="Campaign lifecycle status")
    sent_at: Optional[datetime] = Field(None, description="Timestamp when nudge was sent")
    opened_at: Optional[datetime] = Field(None, description="Timestamp when nudge was opened")
    revenue_recovered: float = Field(0.0, ge=0.0, description="Revenue recovered from this campaign (USD)")

    model_config = {
        "populate_by_name": True,
    }


class NudgeCampaignModel(NudgeCampaignBase):
    """Full nudge campaign document with MongoDB _id."""
    id: Optional[Any] = Field(None, alias="_id", description="MongoDB ObjectId")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    def to_dict(self) -> dict:
        """Convert to dictionary with ObjectId serialised to string."""
        data = self.model_dump(by_alias=True)
        if data.get("_id") is not None:
            data["_id"] = str(data["_id"])
        for dt_field in ("sent_at", "opened_at"):
            if isinstance(data.get(dt_field), datetime):
                data[dt_field] = data[dt_field].isoformat()
        if isinstance(data.get("channel"), NudgeChannel):
            data["channel"] = data["channel"].value
        if isinstance(data.get("status"), NudgeStatus):
            data["status"] = data["status"].value
        return data


class NudgeCampaignResponse(BaseModel):
    """API response model for nudge campaigns."""
    id: Optional[str] = Field(None, alias="_id")
    campaign_id: str
    sku_id: str
    customer_id: str
    substitute_sku_id: Optional[str] = None
    offer_text: str
    channel: NudgeChannel
    status: NudgeStatus
    sent_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    revenue_recovered: float

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, v: Any) -> Optional[str]:
        if isinstance(v, ObjectId):
            return str(v)
        return v


# ══════════════════════════════════════════════════════════════════
# 5. SIGNAL LOG MODELS
# ══════════════════════════════════════════════════════════════════

class SignalLogBase(BaseModel):
    """Fields required to create a signal log entry."""
    signal_id: str = Field(..., description="Unique signal identifier")
    source: SignalSource = Field(..., description="Signal source (news/weather/shipping)")
    raw_payload: dict = Field(default_factory=dict, description="Raw data from the signal source API")
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp when signal was processed"
    )
    risk_delta: float = Field(0.0, description="Change in risk score caused by this signal")
    triggered_agent_run: bool = Field(False, description="Whether this signal triggered an agent run")

    model_config = {
        "populate_by_name": True,
    }


class SignalLogModel(SignalLogBase):
    """Full signal log document with MongoDB _id."""
    id: Optional[Any] = Field(None, alias="_id", description="MongoDB ObjectId")

    model_config = {
        "populate_by_name": True,
        "arbitrary_types_allowed": True,
    }

    def to_dict(self) -> dict:
        """Convert to dictionary with ObjectId serialised to string."""
        data = self.model_dump(by_alias=True)
        if data.get("_id") is not None:
            data["_id"] = str(data["_id"])
        if isinstance(data.get("processed_at"), datetime):
            data["processed_at"] = data["processed_at"].isoformat()
        if isinstance(data.get("source"), SignalSource):
            data["source"] = data["source"].value
        return data


class SignalLogResponse(BaseModel):
    """API response model for signal logs."""
    id: Optional[str] = Field(None, alias="_id")
    signal_id: str
    source: SignalSource
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[int] = None
    affected_regions: list[str] = Field(default_factory=list)
    affected_sku_ids: list[str] = Field(default_factory=list)
    raw_payload: dict = Field(default_factory=dict)
    processed_at: datetime
    risk_delta: float
    triggered_agent_run: bool

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("id", mode="before")
    @classmethod
    def convert_objectid(cls, v: Any) -> Optional[str]:
        if isinstance(v, ObjectId):
            return str(v)
        return v


print("✓ models.py complete")
