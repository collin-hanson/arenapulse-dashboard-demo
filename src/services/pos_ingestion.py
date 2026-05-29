from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.services.demo_data import get_pos_sample


ALLOWED_POS_FIELDS = (
    "venue_id",
    "event_id",
    "vendor_location",
    "section",
    "item_name",
    "item_category",
    "quantity",
    "timestamp",
    "packaging_type",
    "waste_stream",
    "compostable_flag",
    "recyclable_flag",
)
ALLOWED_POS_FIELD_SET = set(ALLOWED_POS_FIELDS)

SENSITIVE_FIELD_HINTS = {
    "amount",
    "card",
    "credit",
    "customer",
    "email",
    "loyalty",
    "money",
    "name",
    "payment",
    "phone",
    "price",
    "staff",
    "token",
    "transaction",
}


@dataclass(frozen=True)
class SanitizedPayload:
    accepted: dict[str, Any]
    dropped_fields: list[str]
    sensitive_drops: list[str]


def sanitize_pos_payload(payload: dict[str, Any]) -> SanitizedPayload:
    accepted = {key: payload[key] for key in ALLOWED_POS_FIELDS if key in payload}
    dropped = sorted(set(payload) - ALLOWED_POS_FIELD_SET)
    sensitive = [
        field
        for field in dropped
        if any(hint in field.lower().replace("_", "") for hint in SENSITIVE_FIELD_HINTS)
    ]
    return SanitizedPayload(accepted=accepted, dropped_fields=dropped, sensitive_drops=sensitive)


def get_demo_payload() -> dict[str, Any]:
    sample = get_pos_sample()
    return dict(zip(sample["field"], sample["value"]))
