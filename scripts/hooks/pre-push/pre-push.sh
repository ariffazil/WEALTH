#!/usr/bin/env bash
set -euo pipefail

REMOTE_NAME="${1:-origin}"
REMOTE_URL="${2:-$(git remote get-url "${1:-origin}")}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
GUARD="$SCRIPT_DIR/repo_guard.py"

if [[ ! -x "$GUARD" ]]; then
  echo "[WARN] repo_guard.py not executable; allowing push."
  exit 0
fi

python3 "$GUARD" --remote-name "$REMOTE_NAME" --remote-url "$REMOTE_URL"
