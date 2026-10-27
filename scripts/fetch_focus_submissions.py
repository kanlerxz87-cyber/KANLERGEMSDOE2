#!/usr/bin/env python3
"""Restore nine commit-pinned owner-hosted witnesses to the ignored data cache.

The previous fetcher read mutable main branches and called some variants
'portal-safe' without organizer evidence. Use the pinned manifest and re-audit
instead; existing tracked historical files remain research only.
"""
from __future__ import annotations

from restore_focus_sites import main


if __name__ == "__main__":
    raise SystemExit(main())
