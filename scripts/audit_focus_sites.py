#!/usr/bin/env python3
"""Compatibility entry point for the current pinned nine-site audit.

The older audit was superseded: it labeled user reports as organizer receipts
and made unsupported hidden-truth claims. Its source is preserved in
`evidence/archive/legacy_scripts/` for historical research, not execution.
"""
from audit_focus9 import main

if __name__ == "__main__":
    raise SystemExit(main())
