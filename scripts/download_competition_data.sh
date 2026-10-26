#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# This restores only the pinned sample/catalogue and educational historical references.
# It deliberately does NOT claim that the training features or external caches are restored.
python scripts/restore_audit.py
if [[ ! -s data/training_features.tif ]]; then
  echo 'BLOCKED: training_features.tif absent. See pinned peer data manifest; no synthetic fallback is authorized.' >&2
  exit 1
fi
echo 'Training file exists; verify grid, checksum and origin separately with prepare_data.py and the source manifest.'
