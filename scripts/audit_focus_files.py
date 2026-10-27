#!/usr/bin/env python3
"""Compatibility entry point for the pinned nine-site release audit.

The prior local-comparison audit excluded a registered lattice from its
promotion conclusion. The current audit checks a literal failure witness and
never uses local format validity as permission to submit.
"""
from __future__ import annotations

from audit_release import main


if __name__ == "__main__":
    raise SystemExit(main())
