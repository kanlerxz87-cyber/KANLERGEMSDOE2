#!/usr/bin/env python3
"""Do not rerun the inherited E1 experiment after its literal duplicate stop."""
import sys

MESSAGE = (
    "BLOCKED: STOP: inherited E1 is a registered duplicate and its holdout was not "
    "whole-segment/fold-local. Source is preserved in research/quarantine/e1-20261026/. "
    "No experiment, GeoTIFF, or submission was created. A new preregistered single "
    "lane, complete registry and comparable baseline are required before a new run."
)

if __name__ == "__main__":
    print(MESSAGE, file=sys.stderr)
    raise SystemExit(2)
