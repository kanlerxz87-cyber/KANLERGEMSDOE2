#!/usr/bin/env bash
# Restore the owner-provided competition-data bridge without DrivenData credentials.
# Hash equality verifies this bridge's identity, NOT independent organizer provenance.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
# The restore tool uses only the Python standard library. Honor an explicit
# interpreter, then a project venv, then system python3.
if [[ -n "${PYTHON_BIN:-}" ]]; then
  PYTHON="$PYTHON_BIN"
elif [[ -x "${ROOT}/.venv/bin/python" ]]; then
  PYTHON="${ROOT}/.venv/bin/python"
else
  PYTHON="python3"
fi
export GEMS_DATA_DIR="${GEMS_DATA_DIR:-${ROOT}/data}"
exec "$PYTHON" "${ROOT}/scripts/restore_data.py" "$@"
