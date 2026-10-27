#!/usr/bin/env bash
set -euo pipefail

# Autonomous SHA-256 verified restoration of competition, external (USGS GeoDAWN,
# USGS 3DEP 1m LiDAR, DOE GDR 1391 INGENIOUS, USGS SGMC), and historical scored rasters.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PY_BIN="${ROOT_DIR}/.venv/bin/python"
if [[ ! -x "${PY_BIN}" ]]; then
  PY_BIN="python3"
fi

echo "[KANLERGEMSDOE2] Restoring & SHA-256 verifying competition + external data..."
"${PY_BIN}" "${ROOT_DIR}/scripts/restore_data.py" \
  --manifest "${ROOT_DIR}/registry/data_manifest.json" \
  --target-dir "${ROOT_DIR}/.cache/gems_data"
echo "[KANLERGEMSDOE2] Data restoration complete and SHA-256 verified."
