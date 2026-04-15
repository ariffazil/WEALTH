"""
VAULT999 append-only audit trail for WEALTH governance decisions.
Mirrors JS host/kernel/vault999.js semantics.
"""

import hashlib
import json
import os
from datetime import datetime
from typing import Any, Dict

DEFAULT_VAULT_PATH = os.path.join(os.getcwd(), "data", "vault999.jsonl")


def ensure_vault_dir(path: str = DEFAULT_VAULT_PATH) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def append_vault999(record: Dict[str, Any], path: str = DEFAULT_VAULT_PATH) -> Dict[str, Any]:
    vault_path = ensure_vault_dir(path)
    epoch = record.get("epoch") or (datetime.utcnow().isoformat() + "Z")
    payload = {
        **record,
        "epoch": epoch,
        "vault_seal": "VAULT999",
    }
    integrity = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:16]
    entry = {
        **payload,
        "integrity": integrity,
    }
    with open(vault_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return entry
