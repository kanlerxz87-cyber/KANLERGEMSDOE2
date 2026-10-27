#!/usr/bin/env bash
# Restore the public owner-mirror data bridge, not an authenticated organizer download.
# SHA-256 verifies mirror identity, NOT official provenance or licensing.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON="$PYTHON_BIN"
elif [[ -x "$ROOT/.venv/bin/python" ]]; then
  PYTHON="$ROOT/.venv/bin/python"
else
  PYTHON=python3
fi
# Keep all reproducible bulk inputs under ignored data/ by default.
export GEMS_DATA_DIR="${GEMS_DATA_DIR:-$ROOT/data}"
exec "$PYTHON" "$ROOT/scripts/restore_data.py" "$@"
