"""
Ingest registry and bus manager.
Handles 4 buses: slow, daily, fast, archive.
Provides caching and series metadata registry.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from host.ingest.schema import DataRecord, validate_record

CACHE_DIR = os.environ.get("WEALTH_CACHE_DIR", os.path.join(os.getcwd(), "data", "ingest_cache"))
os.makedirs(CACHE_DIR, exist_ok=True)

BUS_TTL_HOURS = {
    "slow": 24 * 7,      # weekly refresh for macro
    "daily": 24,         # daily refresh for rates/FX
    "fast": 1,           # hourly refresh for energy grid
    "archive": 24 * 30,  # monthly refresh for vintages
}


def _cache_path(series_id: str, source: str, entity_code: str) -> str:
    safe = f"{source}_{entity_code}_{series_id}".replace("/", "_").replace(":", "_")
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _is_fresh(path: str, bus: str) -> bool:
    if not os.path.exists(path):
        return False
    mtime = datetime.fromtimestamp(os.path.getmtime(path))
    ttl = timedelta(hours=BUS_TTL_HOURS.get(bus, 24))
    return datetime.utcnow() - mtime < ttl


def load_cache(series_id: str, source: str, entity_code: str, bus: str) -> Optional[List[DataRecord]]:
    path = _cache_path(series_id, source, entity_code)
    if not _is_fresh(path, bus):
        return None
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return [DataRecord(**item) for item in raw]


def save_cache(records: List[DataRecord]) -> None:
    if not records:
        return
    first = records[0]
    path = _cache_path(first.series_id, first.source_system, first.entity_code)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in records], f, indent=2)


class IngestRegistry:
    """Unified registry for fetching, caching, and validating data records."""

    def __init__(self):
        self._adapters: Dict[str, Any] = {}
        self._register_defaults()

    def _register_defaults(self):
        try:
            from host.ingest.adapters import fred
            self._adapters["FRED"] = fred
        except Exception:
            pass
        try:
            from host.ingest.adapters import worldbank
            self._adapters["WorldBank"] = worldbank
        except Exception:
            pass
        try:
            from host.ingest.adapters import ecb
            self._adapters["ECB"] = ecb
        except Exception:
            pass
        try:
            from host.ingest.adapters import ember
            self._adapters["Ember"] = ember
        except Exception:
            pass
        try:
            from host.ingest.adapters import owid
            self._adapters["OWID"] = owid
        except Exception:
            pass

    def available_sources(self) -> List[str]:
        return list(self._adapters.keys())

    def fetch(
        self,
        source: str,
        series_id: str,
        entity_code: str,
        use_cache: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        adapter = self._adapters.get(source)
        if adapter is None:
            return {
                "records": [],
                "flags": [f"ADAPTER_NOT_FOUND:{source}"],
                "count": 0,
            }

        bus = kwargs.get("bus", "slow")
        if use_cache:
            cached = load_cache(series_id, source, entity_code, bus)
            if cached is not None:
                return {
                    "records": [r.to_dict() for r in cached],
                    "flags": [],
                    "count": len(cached),
                    "cached": True,
                }

        try:
            if source == "FRED":
                records = adapter.fetch_series(series_id, entity_code, **kwargs)
            elif source == "WorldBank":
                records = adapter.fetch_indicator(series_id, entity_code, **kwargs)
            elif source == "ECB":
                records = adapter.fetch_series(series_id, entity_code=entity_code, **kwargs)
            elif source == "Ember":
                records = adapter.fetch_electricity_data(entity_code=entity_code, **kwargs)
            elif source == "OWID":
                records = adapter.fetch_series(series_id, entity_code=entity_code)
            else:
                records = []
        except Exception as exc:
            return {
                "records": [],
                "flags": [f"FETCH_ERROR:{source}:{exc}"],
                "count": 0,
            }

        # Validate
        flags = []
        for r in records:
            flags.extend(validate_record(r))
        flags = list(dict.fromkeys(flags))

        if records and use_cache:
            save_cache(records)

        return {
            "records": [r.to_dict() for r in records],
            "flags": flags,
            "count": len(records),
            "cached": False,
        }

    def snapshot(self, entity_code: str, sources: Optional[List[str]] = None) -> Dict[str, Any]:
        """Fetch a cross-source snapshot for a given geography."""
        sources = sources or self.available_sources()
        snapshot: Dict[str, Any] = {}
        all_flags: List[str] = []

        # Minimum viable snapshot — key series per source
        specs = {
            "WorldBank": [
                {"series_id": "NY.GDP.MKTP.KD.ZG", "kwargs": {}},  # GDP growth
                {"series_id": "FP.CPI.TOTL.ZG", "kwargs": {}},     # CPI inflation
                {"series_id": "SL.UEM.TOTL.ZS", "kwargs": {}},     # Unemployment
            ],
            "OWID": [
                {"series_id": "carbon-intensity-electricity", "kwargs": {}},
            ],
            "Ember": [
                {"series_id": "demand", "kwargs": {"variable": "Demand"}},
                {"series_id": "generation", "kwargs": {"variable": "Generation"}},
            ],
        }

        for source in sources:
            source_specs = specs.get(source, [])
            for spec in source_specs:
                result = self.fetch(source, spec["series_id"], entity_code, **spec.get("kwargs", {}))
                key = f"{source}:{spec['series_id']}"
                # Keep only latest observation per series for snapshot
                latest = None
                if result["records"]:
                    latest = max(result["records"], key=lambda r: r.get("observation_time", ""))
                snapshot[key] = latest
                all_flags.extend(result["flags"])

        all_flags = list(dict.fromkeys(all_flags))
        return {
            "entity_code": entity_code,
            "snapshot": snapshot,
            "flags": all_flags,
            "coverage": len([v for v in snapshot.values() if v is not None]),
        }


# Global singleton
_registry = IngestRegistry()


def get_registry() -> IngestRegistry:
    return _registry
