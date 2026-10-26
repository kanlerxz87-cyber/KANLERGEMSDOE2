#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Restores peer-mirrored data with immutable Git and SHA-256 pins. These bytes are
# NOT authenticated competition downloads and do not approve a submission.
PYTHON="${PYTHON:-python3}"
"$PYTHON" scripts/restore_inputs.py "$@"
if [[ $# -eq 0 ]]; then
  "$PYTHON" scripts/prepare_data.py
fi
