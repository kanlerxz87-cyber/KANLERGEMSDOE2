#!/usr/bin/env python3
"""Compatibility entry point for the current fail-closed comparison pages.

The earlier generator extrapolated scores and exempted a registered lattice.
That table was withdrawn. The shared site builder now regenerates this URL and
its JSON from the current audited negative decision only.
"""
from __future__ import annotations

from build_site import main


if __name__ == "__main__":
    main()
