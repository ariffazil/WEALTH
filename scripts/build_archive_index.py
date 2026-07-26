#!/usr/bin/env python3
"""
build_archive_index.py — generate the WEALTH archive-index from real files.

This script is the SINGLE writer of `999_vault/archive/INDEX.json`. It scans
the canonical archive roots and emits a JSON index whose every entry points to
a file that actually exists on disk. It never fabricates a date or a path.

Discipline:
  - F2 TRUTH ≥ 0.99: an advertised archive date must equal a real file path.
  - F1 AMANAH: only append/update INDEX.json; never delete source files.
  - F11 AUDITABILITY: every entry records its scan-root and the absolute path
    it was verified against.

Run:
  python3 scripts/build_archive_index.py            # write INDEX.json
  python3 scripts/build_archive_index.py --check    # exit non-zero on drift
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Iterable

# Repository root (parent of this script's parent).
REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_PATH = REPO_ROOT / "999_vault" / "archive" / "INDEX.json"

# Canonical archive roots. Each entry is (root, kind, label). Anything outside
# these paths is NOT considered part of the archive-index.
ARCHIVE_ROOTS: list[tuple[Path, str, str]] = [
    (REPO_ROOT / "999_vault" / "archive", "seals", "VAULT999 sealed archive"),
    (
        REPO_ROOT / "contracts" / "archive",
        "contracts_legacy",
        "Legacy contract snapshots",
    ),
    (REPO_ROOT / "docs" / "archive", "docs", "Archived docs / memory / wiki / raw"),
    (REPO_ROOT / "GENESIS", "genesis_readme_archive", "Genesis README snapshots"),
]

SKIP_DIR_NAMES = {"__pycache__", ".git", ".ruff_cache", ".pytest_cache", "node_modules"}

# Files to skip at the scan level. INDEX.json self-reference would always
# drift (the act of writing it changes its own digest).
SKIP_FILE_NAMES = {"INDEX.json"}


def iter_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            yield Path(dirpath) / name


def sha256_short(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def extract_date(path: Path) -> str | None:
    """Pull a YYYY-MM-DD token from any path component.

    Handles:
      - 2026-06-12-bursa-global-forge.md   (prefix, dash-separated)
      - monolith-legacy-2026-05-19          (suffix, dash-separated)
      - README-archive-2026-06-27.md        (suffix, dash-separated)
      - RELEASE_NOTES_2026.05.16.md         (dot-separated, anywhere)
      - entropy-2026-07-15/                 (folder name, anywhere)
    Never invents a date — returns None when no YYYY-MM-DD token is present.
    """
    import re

    token_re = re.compile(r"(?<!\d)([12]\d{3})-(\d{2})-(\d{2})(?!\d)")
    alt_re = re.compile(r"(?<!\d)([12]\d{3})\.(\d{2})\.(\d{2})(?!\d)")

    candidates: list[tuple[int, str]] = []  # (priority, iso_date)

    def _valid(yyyy: str, mm: str, dd: str) -> str | None:
        try:
            y, m, d = int(yyyy), int(mm), int(dd)
        except ValueError:
            return None
        if not (1 <= m <= 12 and 1 <= d <= 31):
            return None
        # Sanity range — no dates outside our operational era.
        if not (2024 <= y <= 2030):
            return None
        return f"{y:04d}-{m:02d}-{d:02d}"

    for part in path.parts:
        # Dash form: prefer earliest match in the component.
        m = token_re.search(part)
        if m:
            iso = _valid(m.group(1), m.group(2), m.group(3))
            if iso:
                # Priority: prefix > suffix > middle.
                if part.startswith(m.group(0)):
                    candidates.append((0, iso))
                elif part.endswith(m.group(0)):
                    candidates.append((1, iso))
                else:
                    candidates.append((2, iso))
        # Dot form (less common but present in RELEASE_NOTES).
        m = alt_re.search(part)
        if m:
            iso = _valid(m.group(1), m.group(2), m.group(3))
            if iso:
                candidates.append((3, iso))

    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])
    return candidates[0][1]


def build_index() -> dict:
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    entries: list[dict] = []
    counts: dict[str, int] = {}

    for root, kind, label in ARCHIVE_ROOTS:
        counts[kind] = 0
        if not root.exists():
            continue
        for path in sorted(iter_files(root)):
            if path.name in SKIP_FILE_NAMES:
                continue
            try:
                rel = path.relative_to(REPO_ROOT)
                size = path.stat().st_size
                digest = sha256_short(path)
            except OSError:
                continue
            entry = {
                "kind": kind,
                "label": label,
                "path": str(rel),
                "absolute_path": str(path),
                "size_bytes": size,
                "sha256_short": digest,
                "extracted_date": extract_date(rel),
            }
            entries.append(entry)
            counts[kind] += 1

    index = {
        "schema_version": "1.0.0",
        "generated_at": now,
        "generator": "scripts/build_archive_index.py",
        "organ": "WEALTH",
        "parity_invariant": "Every entry in this index corresponds to a real file on disk. "
        "Dates are extracted from filenames only — never fabricated.",
        "advertised_dates": sorted(
            {e["extracted_date"] for e in entries if e["extracted_date"]}
        ),
        "counts_by_kind": counts,
        "total_entries": len(entries),
        "entries": entries,
    }
    return index


def write_index(index: dict) -> None:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(index, indent=2, sort_keys=False) + "\n")


def check_drift(index: dict) -> list[str]:
    """Return list of drift messages (empty == parity OK)."""
    drift: list[str] = []
    for entry in index["entries"]:
        p = Path(entry["absolute_path"])
        if not p.exists():
            drift.append(f"MISSING: {entry['path']}")
            continue
        try:
            actual_size = p.stat().st_size
            if actual_size != entry["size_bytes"]:
                drift.append(
                    f"SIZE_CHANGED: {entry['path']} ({entry['size_bytes']} → {actual_size})"
                )
            actual_digest = sha256_short(p)
            if actual_digest != entry["sha256_short"]:
                drift.append(
                    f"DIGEST_CHANGED: {entry['path']} ({entry['sha256_short']} → {actual_digest})"
                )
        except OSError as exc:
            drift.append(f"STAT_ERROR: {entry['path']} ({exc})")
    return drift


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify INDEX.json against disk and exit non-zero on drift.",
    )
    args = parser.parse_args()

    if args.check:
        if not OUTPUT_PATH.exists():
            print(
                f"DRIFT: {OUTPUT_PATH} missing — run without --check to seed.",
                file=sys.stderr,
            )
            return 2
        existing = json.loads(OUTPUT_PATH.read_text())
        drift = check_drift(existing)
        if drift:
            print("Archive-index DRIFT detected:", file=sys.stderr)
            for d in drift:
                print(f"  - {d}", file=sys.stderr)
            return 1
        print(f"OK — {existing['total_entries']} entries, parity holds.")
        return 0

    index = build_index()
    write_index(index)
    print(
        f"OK — wrote {OUTPUT_PATH} ({index['total_entries']} entries, "
        f"{len(index['advertised_dates'])} distinct dates)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
