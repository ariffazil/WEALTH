"""
OpenLineage Adapter — Emit OpenLineage events for WEALTH computations.

OpenLineage is the LF/ANSI standard for dataset + job lineage.
Every WEALTH computation can emit START / COMPLETE / FAIL events
with inputs, outputs, and the job that produced them.
"""

from __future__ import annotations

import time
import uuid
from typing import Any, Optional


class OpenLineageAdapter:
    """Adapter for OpenLineage event emission."""

    def __init__(self, namespace: str = "arifOS.WEALTH", endpoint: Optional[str] = None):
        self.namespace = namespace
        self.endpoint = endpoint  # If set, HTTP POST events here
        self._events: list[dict] = []  # local buffer

    def emit_start(
        self,
        job_name: str,
        inputs: list[dict[str, str]],
        outputs: list[dict[str, str]],
        run_id: Optional[str] = None,
    ) -> str:
        """Emit a START event. Returns run_id."""
        run_id = run_id or f"run-{uuid.uuid4()}"
        event = {
            "eventType": "START",
            "eventTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run": {
                "runId": run_id,
                "facets": {
                    "arifos": {
                        "_producer": "https://github.com/ariffazil/wealth",
                        "_schemaURL": "https://openlineage.io/spec/2-0-2/OpenLineage.json#/$defs/RunFacet",
                    }
                },
            },
            "job": {
                "namespace": self.namespace,
                "name": job_name,
            },
            "inputs": inputs,
            "outputs": outputs,
        }
        self._events.append(event)
        return run_id

    def emit_complete(
        self,
        run_id: str,
        job_name: str,
        outputs: list[dict[str, str]],
        metrics: Optional[dict[str, Any]] = None,
    ) -> None:
        """Emit a COMPLETE event."""
        event = {
            "eventType": "COMPLETE",
            "eventTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run": {"runId": run_id},
            "job": {"namespace": self.namespace, "name": job_name},
            "outputs": outputs,
        }
        if metrics:
            event["run"]["facets"] = {
                "stats": {
                    "rows": metrics.get("rows", 0),
                    "bytes": metrics.get("bytes", 0),
                    "duration_ms": metrics.get("duration_ms", 0),
                }
            }
        self._events.append(event)

    def emit_fail(
        self,
        run_id: str,
        job_name: str,
        error: str,
    ) -> None:
        """Emit a FAIL event."""
        event = {
            "eventType": "FAIL",
            "eventTime": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run": {
                "runId": run_id,
                "facets": {
                    "errorMessage": {
                        "message": error,
                        "programmingLanguage": "python",
                    }
                },
            },
            "job": {"namespace": self.namespace, "name": job_name},
        }
        self._events.append(event)

    def get_events(self) -> list[dict]:
        return list(self._events)

    def clear(self) -> None:
        self._events.clear()
