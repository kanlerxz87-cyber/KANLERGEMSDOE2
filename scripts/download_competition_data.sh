#!/usr/bin/env bash
# Compatibility entry point: uses the only available owner mirrors, not a DrivenData login.
set -euo pipefail
exec "$(dirname "$0")/bootstrap_template.sh" "$@"
