#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Restores peer-mirrored data with immutable Git and SHA-256 pins. These bytes are
# NOT authenticated competition downloads and do not approve a submission.
exec python3 scripts/restore_inputs.py "$@"
