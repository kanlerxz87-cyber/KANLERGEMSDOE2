#!/usr/bin/env python3
"""Fail-closed stub for the retired PR #53 supplemental renderer.

The canonical site generator is ``scripts/build_site.py``. The retired renderer
could present an unapproved TIFF as a download. PR #53 changed the frozen dot
budget and did not replay a holdout; no page from that renderer is authoritative.
"""


def main() -> int:
    raise SystemExit(
        "Disabled: PR #53's supplemental renderer exposes an unapproved artifact. "
        "Use scripts/build_site.py; do not bypass the frozen 37,654-dot lattice stop."
    )


if __name__ == "__main__":
    raise SystemExit(main())
