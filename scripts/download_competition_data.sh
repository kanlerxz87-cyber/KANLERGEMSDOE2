#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Restores SHA-256-pinned public peer mirrors, not organizer-authenticated files.
# Large artifacts remain under ignored data/. No credentials and no synthetic data.
python scripts/restore_competition_data.py
python scripts/prepare_data.py
