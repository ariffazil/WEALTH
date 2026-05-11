"""
Bus health tracker for WEALTH ingestion layer.
Tracks per-adapter latency, success rate, cache age, and field completeness.
"""

import json
import math
import os
import tempfile
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from numbers import Real
from typing import Any, Dict, List, Optional


def _resolve_health_path() -> str:
    configured = os.environ.get(
        "WEALTH_HEALTH_PATH",
        os.path.join(os.getcwd(), "data", "ingest_health.json"),
    )
    try:
        os.makedirs(os.path.dirname(configured), exist_ok=True)
        with open(configured, "a", encoding="utf-8"):
            pass
        return configured
    except OSError:
        fallback_dir = os.path.join(tempfile.gettempdir(), "wealth", "data")
        os.makedirs(fallback_dir, exist_ok=True)
        return os.path.join(fallback_dir, "ingest_health.json")


HEALTH_PATH = _resolve_health_path()


def _sanitize_json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _sanitize_json_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_sanitize_json_value(item) for item in value]
    if isinstance(value, tuple):
        return [_sanitize_json_value(item) for item in value]
    if isinstance(value, bool) or value is None or isinstance(value, (str, int)):
        return value
    if isinstance(value, Real):
        numeric = float(value)
        return numeric if math.isfinite(numeric) else None
    return value


@dataclass
class AdapterHealth:
    adapter: str
    last_success: Optional[str] = None
    last_error: Optional[str] = None
    last_latency_ms: float = 0.0
    total_requests: int = 0
    success_count: int = 0
    cache_age_hours: Optional[float] = None
    field_completeness_rate: float = 0.0
    latest_observation_time: Optional[str] = None
    stale: bool = False
    flags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _sanitize_json_value(asdict(self))


class HealthTracker:
    """Thread-safe-ish (single-process) health tracker for ingestion adapters."""

    def __init__(self, path: str = HEALTH_PATH):
        self.path = path
        self._state: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    self._state = _sanitize_json_value(json.load(f))
            except Exception:
                self._state = {}
        else:
            try:
                os.makedirs(os.path.dirname(self.path), exist_ok=True)
            except OSError:
                self._state = {}
            self._state = {}

    def _save(self):
        try:
            sanitized = _sanitize_json_value(self._state)
            self._state = sanitized
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(sanitized, f, indent=2, allow_nan=False)
        except (OSError, ValueError):
            pass

    def record_attempt(
        self,
        adapter: str,
        success: bool,
        latency_ms: float,
        record_count: int = 0,
        field_completeness_rate: float = 0.0,
        latest_observation_time: Optional[str] = None,
        cache_age_hours: Optional[float] = None,
        stale: bool = False,
        flags: Optional[List[str]] = None,
        error_message: Optional[str] = None,
    ):
        now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        state = self._state.setdefault(adapter, {})
        state["total_requests"] = state.get("total_requests", 0) + 1
        state["last_latency_ms"] = _sanitize_json_value(latency_ms)
        state["field_completeness_rate"] = _sanitize_json_value(field_completeness_rate)
        state["latest_observation_time"] = latest_observation_time
        state["cache_age_hours"] = _sanitize_json_value(cache_age_hours)
        state["stale"] = stale
        state["flags"] = list(dict.fromkeys(flags or []))

        if success:
            state["last_success"] = now
            state["success_count"] = state.get("success_count", 0) + 1
        else:
            state["last_error"] = error_message or "UNKNOWN_ERROR"

        self._save()

    def get_health(self, adapter: Optional[str] = None) -> Dict[str, Any]:
        self._load()
        if adapter:
            return _sanitize_json_value(
                self._state.get(adapter, AdapterHealth(adapter=adapter).to_dict())
            )
        return _sanitize_json_value(dict(self._state))

    def all_adapters(self) -> List[str]:
        self._load()
        return list(self._state.keys())

    def flag_stale(self, adapter: str, series_id: str, reason: str):
        self._load()
        state = self._state.setdefault(adapter, {})
        flags = set(state.get("flags", []))
        flags.add(f"STALE:{series_id}:{reason}")
        state["flags"] = sorted(flags)
        self._save()

    def flag_missing(self, adapter: str, series_id: str, entity_code: str):
        self._load()
        state = self._state.setdefault(adapter, {})
        flags = set(state.get("flags", []))
        flags.add(f"MISSING:{series_id}:{entity_code}")
        state["flags"] = sorted(flags)
        self._save()

    def flag_divergence(self, adapter_a: str, adapter_b: str, signal: str, reason: str):
        self._load()
        key = f"reconcile:{adapter_a}:{adapter_b}"
        state = self._state.setdefault(key, {})
        flags = set(state.get("flags", []))
        flags.add(f"DIVERGENCE:{signal}:{reason}")
        state["flags"] = sorted(flags)
        self._save()


# Global singleton
_tracker = HealthTracker()


def get_tracker() -> HealthTracker:
    return _tracker
