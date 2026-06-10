"""
OrganBaseModel — Shared Pydantic v2 base for all arifOS Python organs.
========================================================================
Standardises datetime serialisation, JSON encoding, and validation
across WEALTH, WELL, and GEOX.

All domain-specific Pydantic models in each organ should inherit from
this base instead of `pydantic.BaseModel` directly.

DITEMPA BUKAN DIBERI — Forged, Not Given.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict, field_serializer


class OrganBaseModel(BaseModel):
    """Shared base for all arifOS organ Pydantic models.

    Features:
    - Consistent datetime serialisation (ISO 8601, UTC)
    - `serializable_dict()` for JSON-safe output
    - `populate_by_name` for alias-friendly construction
    - `validate_assignment` to catch mutation errors early
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",  # reject unknown fields by default
    )

    @field_serializer("*", when_used="json", check_fields=False)
    def _serialize_datetimes(self, value: Any) -> Any:
        """Normalise all datetime fields to ISO 8601 with explicit UTC offset."""
        if isinstance(value, datetime):
            if value.tzinfo is None:
                value = value.replace(tzinfo=ZoneInfo("UTC"))
            return value.strftime("%Y-%m-%dT%H:%M:%S%z")
        return value

    def serializable_dict(self, **kwargs: Any) -> dict[str, Any]:
        """Return a dict containing only JSON-serialisable fields.

        Uses FastAPI's `jsonable_encoder` under the hood, which handles
        datetime, Decimal, UUID, Enum, and other common types.
        """
        return jsonable_encoder(self.model_dump(**kwargs))
