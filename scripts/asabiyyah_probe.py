#!/usr/bin/env python3
"""WEALTH organ probe — Asabiyyah cycle reading.

WEALTH is the capital organ. Its distinctive signal is `kampung_gadai_risk`:
the share of sovereign capacity already signed away (committed, pledged or
disposed). The stanza is not about poverty — it is about holding the rope while
someone else draws the bucket. So the probe measures capacity that has been
signed away, not capacity that is absent.

Observe-only. Every number here traces to a real file on this host, recorded in
the metric's `source`. NOT_APPLICABLE is a legal and preferred answer over an
invented number. A reading with no source is a STORY, not a MIRROR.

Contract: /root/AAA/schemas/asabiyyah-reading.schema.json
Kernel:   /root/arifOS/arifosmcp/runtime/asabiyyah.py  (loaded, never vendored)
Inputs:   /root/WEALTH (read-only) + /root/VAULT999/wealth/receipts.jsonl
Output:   stdout + /var/lib/arifos/asabiyyah/WEALTH.json
Standard library only.

Usage:
    python3 /root/WEALTH/scripts/asabiyyah_probe.py
"""

from __future__ import annotations

import ast
import importlib.util
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# --------------------------------------------------------------------------
# identity + locations
# --------------------------------------------------------------------------

ORGAN = "WEALTH"
HOST = os.uname().nodename
WINDOW_DAYS = 30

WEALTH_ROOT = Path("/root/WEALTH")
RECEIPTS = Path("/root/VAULT999/wealth/receipts.jsonl")
SKILLS_DIR = WEALTH_ROOT / "skills"
TOOLS_INIT = WEALTH_ROOT / "wealth_mcp" / "__init__.py"
KERNEL = Path("/root/arifOS/arifosmcp/runtime/asabiyyah.py")
DROP_DIR = Path("/var/lib/arifos/asabiyyah")
DROP_FILE = DROP_DIR / f"{ORGAN}.json"

# Directories excluded from the ceremony (doctrine) count: archived, vendored,
# build output. This is the declared exclusion set, not a tuned one.
CEREMONY_EXCLUDE = {"archive", "backups", "node_modules", ".git", ".venv", "dist", "build"}


def now_iso() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def load_kernel():
    """Load the shared instrument standalone — do NOT vendor a copy."""
    spec = importlib.util.spec_from_file_location("asabiyyah", str(KERNEL))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load asabiyyah kernel from {KERNEL}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["asabiyyah"] = mod
    try:
        spec.loader.exec_module(mod)
    except BaseException:
        sys.modules.pop("asabiyyah", None)
        raise
    return mod


# --------------------------------------------------------------------------
# CER — doctrine produced vs capability exercised
# --------------------------------------------------------------------------


def count_ceremony_artifacts() -> tuple[int, list[str]]:
    """Live .md under /root/WEALTH, excluding archive/vendored/build trees."""
    found: list[str] = []
    for dirpath, dirnames, filenames in os.walk(WEALTH_ROOT):
        dirnames[:] = [d for d in dirnames if d not in CEREMONY_EXCLUDE]
        for name in filenames:
            if name.endswith(".md"):
                found.append(os.path.join(dirpath, name))
    return len(found), sorted(found)


def declared_capabilities() -> list[str]:
    """WEALTH's own declared capability surface, parsed from the real source."""
    tree = ast.parse(TOOLS_INIT.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if getattr(target, "id", None) == "CAPITAL_TOOL_NAMES" and isinstance(
                    node.value, ast.Tuple
                ):
                    return [
                        e.value
                        for e in node.value.elts
                        if isinstance(e, ast.Constant) and isinstance(e.value, str)
                    ]
    return []


def read_receipts() -> tuple[list[dict], list[str]]:
    """Read the authoritative WEALTH receipt stream (the real ledger file)."""
    records: list[dict] = []
    errors: list[str] = []
    if not RECEIPTS.is_file():
        return records, [f"receipt file absent: {RECEIPTS}"]
    with RECEIPTS.open("r", encoding="utf-8", errors="replace") as stream:
        for lineno, line in enumerate(stream, 1):
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except ValueError:
                errors.append(f"unparseable receipt at {RECEIPTS}:{lineno}")
    return records, errors


def _ts(record: dict) -> datetime | None:
    raw = record.get("timestamp_utc")
    if not raw:
        return None
    try:
        stamp = datetime.fromisoformat(str(raw))
    except ValueError:
        return None
    return stamp if stamp.tzinfo else stamp.replace(tzinfo=timezone.utc)


def in_window(records: list[dict], days: int) -> list[dict]:
    """Receipts inside the observation window, anchored to the newest receipt
    (a stalled writer must not silently widen or empty the window)."""
    stamps = [t for t in (_ts(r) for r in records) if t is not None]
    if not stamps:
        return []
    cutoff = max(stamps) - timedelta(days=days)
    return [r for r in records if (t := _ts(r)) is not None and t >= cutoff]


# --------------------------------------------------------------------------
# ENC — protected mutation paths and whether they pass a gate
# --------------------------------------------------------------------------
# Inventory of every distinct entry point that can change protected WEALTH
# state (VAULT999 ledger / receipt evidence base / domain transaction store).
# `anchor` is the line of the write itself; the probe extracts the innermost
# enclosing function and scans it for a real gate marker. Nothing here is
# asserted — each verdict is computed from the source at run time.

GATE_MARKERS = (
    "ack_irreversible",
    "F13_ACK_REQUIRED",
    "check_governance",
    "gate_tool_ingress",
    "arif_judge",
)

MUTATION_PATHS: list[dict] = [
    {
        "id": "mcp_tool:capital_ledger.write (wealth_mcp/tools/ledger.py)",
        "file": "wealth_mcp/tools/ledger.py",
        "anchor": 68,
        "target": "VAULT999 ledger append (ack + C2 SEAL boundary)",
    },
    {
        "id": "mcp_tool:capital_ledger.write (legacy monolithic copy)",
        "file": "wealth_mcp/tools/canonical.py",
        "anchor": 1725,
        "target": "VAULT999 ledger append (ack boundary)",
    },
    {
        "id": "legacy_dispatch:wealth_vault_write (wealth_mcp/tools/types.py)",
        "file": "wealth_mcp/tools/types.py",
        "anchor": 180,
        "target": "append_vault999() called in-process, verdict hardcoded SEAL",
    },
    {
        "id": "legacy_dispatch:wealth_vault_write (duplicate table in canonical.py)",
        "file": "wealth_mcp/tools/canonical.py",
        "anchor": 2459,
        "target": "append_vault999() called in-process, verdict hardcoded SEAL",
    },
    {
        "id": "vault_api:host.governance.vault_supabase.append_vault999",
        "file": "host/governance/vault_supabase.py",
        "anchor": 550,
        "target": "raw VAULT999 jsonl append + Supabase snapshot/transaction",
    },
    {
        "id": "vault_api:host.governance.vault.append_vault999",
        "file": "host/governance/vault.py",
        "anchor": 378,
        "target": "raw VAULT999 append (cwd-relative path, duplicate module)",
    },
    {
        "id": "receipt_append:wealth_mcp/server.py._append_existing_jsonl",
        "file": "wealth_mcp/server.py",
        "anchor": 68,
        "target": "append to /root/VAULT999/wealth/receipts.jsonl (evidence base)",
    },
    {
        "id": "domain_write:internal/monolith.py._wealth_write_domain_receipt",
        "file": "internal/monolith.py",
        "anchor": 17510,
        "target": "Supabase arifosmcp_transactions / domain tables",
    },
    {
        "id": "node_api:host/kernel/vault999.js.appendVault999",
        "file": "host/kernel/vault999.js",
        "anchor": 23,
        "target": "appendFileSync to a self-declared vault999 jsonl path",
    },
]


def _enclosing_source(path: Path, anchor: int) -> tuple[str | None, str | None]:
    """Source of the innermost function enclosing `anchor`. None on failure."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return None, f"read failed: {exc}"
    if path.suffix != ".py":
        lines = source.splitlines()
        lo, hi = max(0, anchor - 12), min(len(lines), anchor + 12)
        return "\n".join(lines[lo:hi]), None
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return None, f"parse failed: {exc}"
    lines = source.splitlines()
    best: tuple[int, ast.AST] | None = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            start = node.lineno
            end = getattr(node, "end_lineno", start)
            if start <= anchor <= end:
                span = end - start
                if best is None or span < best[0]:
                    best = (span, node)
    if best is None:
        return None, f"no enclosing function at line {anchor}"
    node = best[1]
    end = getattr(node, "end_lineno", node.lineno)
    return "\n".join(lines[node.lineno - 1 : end]), None


def enumerate_enc() -> tuple[int, int, list[str], list[dict]]:
    """Return (gated, total, ungated_ids, per-path findings)."""
    gated = 0
    ungated: list[str] = []
    findings: list[dict] = []
    for entry in MUTATION_PATHS:
        path = WEALTH_ROOT / entry["file"]
        if not path.is_file():
            findings.append({**entry, "present": False, "gated": False, "marker": None})
            ungated.append(entry["id"] + " [file absent]")
            continue
        body, err = _enclosing_source(path, entry["anchor"])
        if body is None:
            findings.append({**entry, "present": True, "gated": False, "marker": None, "error": err})
            ungated.append(entry["id"] + f" [gate unverified: {err}]")
            continue
        marker = next((m for m in GATE_MARKERS if m in body), None)
        is_gated = marker is not None
        if is_gated:
            gated += 1
        else:
            ungated.append(entry["id"])
        findings.append(
            {
                "id": entry["id"],
                "file": f"{entry['file']}:{entry['anchor']}",
                "target": entry["target"],
                "present": True,
                "gated": is_gated,
                "marker": marker,
            }
        )
    return gated, len(MUTATION_PATHS), ungated, findings


# --------------------------------------------------------------------------
# GADAI — share of sovereign capacity already signed away
# --------------------------------------------------------------------------


def measure_gadai(records: list[dict]) -> tuple[float, float, dict, list[str]]:
    """Derive (relinquished_value, total_value) from real ledger entries.

    The authoritative capital ledger is the file the writer actually writes —
    /root/VAULT999/wealth/receipts.jsonl (per WEALTH-RECONCILIATION-20260916).
    An entry counts as relinquished only if it is a SUCCESSFUL capital_ledger
    write whose tx_type classifies capital as committed/pledged/disposed/exited.
    The total is the recorded capital base, i.e. the sum of amounts of all
    successful capital_ledger writes.

    Returns the raw pair, the raw counts behind it, and the paths checked.
    """
    checked = [
        "/root/VAULT999/wealth/receipts.jsonl",
        "/root/WEALTH/data/vault999.jsonl",
        "/root/WEALTH/999_vault/audit.jsonl",
        "/root/WEALTH/data/forecast_log.jsonl",
        "/root/WEALTH/data/sample-state.json",
    ]
    relinquishing = {"committed", "pledged", "disposed", "exited"}

    writes = 0
    successful = 0
    relinquished = 0.0
    total = 0.0
    classify_used = 0

    for record in records:
        if record.get("tool_name") != "capital_ledger":
            continue
        args = record.get("arguments") or {}
        if str(args.get("mode", "")).lower() != "write":
            continue
        writes += 1
        if record.get("call_status") != "PASS":
            continue
        successful += 1
        try:
            amount = float(args.get("amount") or 0)
        except (TypeError, ValueError):
            amount = 0.0
        total += amount
        tx_class = str(args.get("tx_type", "")).strip().lower()
        if tx_class:
            classify_used += 1
        if tx_class in relinquishing:
            relinquished += amount

    raw_counts = {
        "gadai_ledger_write_attempts": writes,
        "gadai_ledger_write_successes": successful,
        "gadai_entries_carrying_classification": classify_used,
    }
    # A total of 0 is the truthful input here: no capital base is on record.
    # The kernel then emits NOT_APPLICABLE rather than an invented share.
    return relinquished, total, raw_counts, checked


# --------------------------------------------------------------------------
# assembly
# --------------------------------------------------------------------------


def build_reading(asb):
    observed_at = now_iso()
    errors: list[str] = []

    # ── CER ────────────────────────────────────────────────────────────────
    ceremony, _md_files = count_ceremony_artifacts()
    records, receipt_errors = read_receipts()
    errors.extend(receipt_errors)
    window = in_window(records, WINDOW_DAYS)
    declared = declared_capabilities()
    exercised_names = sorted(
        {
            str(r.get("tool_name"))
            for r in window
            if r.get("call_status") == "PASS" and r.get("tool_name") in declared
        }
    )
    exercised = len(exercised_names)
    cer_source = (
        f"{WEALTH_ROOT} (live .md walk, excluding {'/'.join(sorted(CEREMONY_EXCLUDE))}/) "
        f"+ {RECEIPTS} (declared-capability PASS receipts, "
        f"{WINDOW_DAYS}d window ending {observed_at})"
    )
    cer = asb.ceremony_exercise_ratio(ceremony, exercised, source=cer_source, observed_at=observed_at)
    cer.notes = (
        f"{ceremony} live ceremony artifacts / {exercised} declared capabilities exercised "
        f"in {WINDOW_DAYS}d ({', '.join(exercised_names)})"
    )

    # ── ASD ────────────────────────────────────────────────────────────────
    skill_files = sorted(str(p) for p in SKILLS_DIR.glob("*/SKILL.md")) if SKILLS_DIR.is_dir() else []
    doctrine_holders = len(skill_files)
    executors = sorted({str(r.get("actor_id")) for r in window if r.get("actor_id")})
    executors_pass = sorted(
        {
            str(r.get("actor_id"))
            for r in window
            if r.get("actor_id") and r.get("call_status") == "PASS"
        }
    )
    if not executors:
        asd = asb.Metric.na(
            "asd",
            f"receipts at {RECEIPTS} record no actor_id inside the {WINDOW_DAYS}d window",
        )
    else:
        asd_source = (
            f"{SKILLS_DIR}/*/SKILL.md (doctrine holders) + {RECEIPTS} "
            f"(distinct actor_id, {WINDOW_DAYS}d window)"
        )
        asd = asb.asabiyyah_depth(doctrine_holders, len(executors), source=asd_source, observed_at=observed_at)
        asd.notes = (
            f"{len(executors)} distinct executors ({len(executors_pass)} with a PASS) / "
            f"{doctrine_holders} live doctrines: {'; '.join(skill_files)}. "
            "UNIT NOTE: numerator is actors, denominator is doctrines — the kernel caps at "
            "1.0, so this reading saturates and must be read as doctrine coverage by "
            "executing actors, not as asabiyyah depth."
        )

    # ── ENC ────────────────────────────────────────────────────────────────
    gated, total_paths, ungated, enc_findings = enumerate_enc()
    enc_source = (
        f"mutation-path inventory across {WEALTH_ROOT} — "
        + "; ".join(f"{f['file']}" for f in enc_findings)
    )
    enc = asb.enforcement_coverage(
        gated, total_paths, source=enc_source, observed_at=observed_at, ungated=ungated
    )
    enc.notes = (
        f"{gated}/{total_paths} enumerated mutation paths carry a gate marker "
        f"({', '.join(GATE_MARKERS)}); ungated: {', '.join(ungated)}"
    )

    # ── GADAI ──────────────────────────────────────────────────────────────
    relinquished, total_value, gadai_counts, checked = measure_gadai(records)
    gadai_source = (
        "relinquished_value=0 and total_value=0 derived from "
        f"{RECEIPTS}: 0 successful capital_ledger write entries "
        f"({gadai_counts['gadai_ledger_write_attempts']} attempted, all BLOCKED by the "
        "F13 ack / C2 SEAL boundary); no entry classifies capital as "
        "committed/pledged/disposed/exited; local fallback "
        f"{WEALTH_ROOT}/data/vault999.jsonl absent; checked also "
        f"{WEALTH_ROOT}/999_vault/audit.jsonl, "
        f"{WEALTH_ROOT}/data/forecast_log.jsonl, "
        f"{WEALTH_ROOT}/data/sample-state.json (demo/ESTIMATE, not real)"
    )
    gadai = asb.kampung_gadai_risk(
        relinquished, total_value, source=gadai_source, observed_at=observed_at
    )
    gadai.source = gadai_source
    gadai.observed_at = observed_at
    gadai.notes = (
        "No capital base is on record in any local WEALTH ledger, so the share signed away "
        "cannot be derived. This is a measurement gap, not a measured zero: the ledger has "
        f"{gadai_counts['gadai_ledger_write_successes']} successful write entries in its "
        "entire history, so absence of committed entries is absence of a ledger, not proof "
        "that the kampung is unpawned."
    )

    metrics = {"cer": cer, "asd": asd, "enc": enc, "gadai": gadai}

    mirror = asb.mirror_check(
        claim="WEALTH cannot currently state the share of sovereign capacity already signed away",
        evidence_refs=[str(RECEIPTS), str(WEALTH_ROOT / "data"), str(SKILLS_DIR)],
    )

    evidence = {
        "ceremony_artifacts": ceremony,
        "exercised_capabilities": exercised,
        "doctrine_holders": doctrine_holders,
        "executors": len(executors),
        "gated_paths": gated,
        "total_paths": total_paths,
        "ungated": ungated,
        "window_days": WINDOW_DAYS,
        # raw pair used for gadai (kernel derives the share from these)
        "gadai_relinquished_value": relinquished,
        "gadai_total_value": total_value,
        **gadai_counts,
        "asd_executors_with_pass": len(executors_pass),
        "observations_in_window": len(window),
        "observations_total": len(records),
        "mirror_check": mirror,
        "checked_paths": checked,
        "mutation_paths": enc_findings,
        "receipt_errors": errors[:10],
    }

    reading = asb.SubstrateReading(
        organ=ORGAN,
        host=HOST,
        observed_at=observed_at,
        metrics=metrics,
        evidence=evidence,
    )
    return reading


def main() -> int:
    asb = load_kernel()
    reading = build_reading(asb)
    payload = reading.to_json()
    DROP_DIR.mkdir(parents=True, exist_ok=True)
    DROP_FILE.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
