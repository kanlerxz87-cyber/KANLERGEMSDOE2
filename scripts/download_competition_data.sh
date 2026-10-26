#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Pinned public peer mirrors, not organizer-authenticated. Large artifacts remain
# under ignored data/. No credentials, synthetic fallback, or competition upload.
PYTHON="${PYTHON:-python}"
"$PYTHON" scripts/restore_core_data.py --include-external
"$PYTHON" scripts/restore_competition_data.py
"$PYTHON" scripts/prepare_data.py
