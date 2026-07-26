"""
tests/test_archive_index.py — archive-index generation parity.

Verifies that 999_vault/archive/INDEX.json, written by
scripts/build_archive_index.py, satisfies the F2 TRUTH / F11 AUDIT invariant:

    every entry in the index points to a real file with the recorded
    size + sha256_short; no entry is fabricated.

Also ensures that no entry advertises a date that cannot be located in
any of the canonical archive roots.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
INDEX = REPO / "999_vault" / "archive" / "INDEX.json"
GENERATOR = REPO / "scripts" / "build_archive_index.py"


def _load() -> dict:
    assert INDEX.exists(), (
        f"archive-index missing — run `python3 {GENERATOR}` to seed it"
    )
    return json.loads(INDEX.read_text())


def test_index_is_well_formed():
    index = _load()
    for key in (
        "schema_version",
        "generated_at",
        "parity_invariant",
        "advertised_dates",
        "counts_by_kind",
        "total_entries",
        "entries",
    ):
        assert key in index, f"INDEX.json missing key: {key}"


def test_index_every_entry_has_real_file():
    index = _load()
    assert index["total_entries"] == len(index["entries"]), (
        "total_entries must equal entries length"
    )
    for entry in index["entries"]:
        path = Path(entry["absolute_path"])
        assert path.exists(), f"index entry points at missing file: {entry['path']}"
        assert path.stat().st_size == entry["size_bytes"], (
            f"size drift for {entry['path']}"
        )


def test_index_advertised_dates_match_real_files():
    """Every advertised date must appear in the entry list — no phantom dates."""
    index = _load()
    advertised = set(index["advertised_dates"])
    found = {e["extracted_date"] for e in index["entries"] if e["extracted_date"]}
    assert advertised == found, (
        f"advertised_dates drift: advertised-only={advertised - found}, "
        f"found-only={found - advertised}"
    )
    # No None slips into advertised_dates.
    assert None not in advertised, "advertised_dates contains None"


def test_index_generator_check_passes():
    """Re-run the generator in --check mode and require it to exit 0."""
    proc = subprocess.run(
        [sys.executable, str(GENERATOR), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, (
        f"archive-index --check failed:\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
    )
