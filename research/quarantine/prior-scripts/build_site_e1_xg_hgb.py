#!/usr/bin/env python3
"""Compatibility entry point; the historical E1 page is withdrawn.

Always regenerate the current fail-closed public site. This intentionally does
not rebuild any legacy candidate page or restore old download links.
"""
from build_site import build

if __name__ == "__main__":
    build()
