#!/usr/bin/env python3
"""Verify an existing pinned shared feature cache; do not rebuild a private E1 stack."""
from __future__ import annotations

import json
from pathlib import Path

from validate_raster import sha256_file

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/prepared/features.npy"
META = ROOT / "data/prepared/features.json"


def main() -> None:
    if not CACHE.is_file() or not META.is_file():
        raise SystemExit(
            "Shared prepared feature cache absent. Do not use the withdrawn E1 cache builder. "
            "The original shared preparer is at "
            "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/scripts/prepare_data.py; "
            "its dependencies, input pins, footprint and resource needs must be restored and verified before a new experiment."
        )
    meta = json.loads(META.read_text())
    if sha256_file(CACHE) != meta.get("sha256"):
        raise SystemExit("Shared feature-cache checksum mismatch")
    inputs = meta.get("inputs")
    if not isinstance(inputs, dict) or not inputs:
        raise SystemExit("Shared feature cache has no input hashes")
    for path, expected in inputs.items():
        file = (ROOT / path).resolve()
        if ROOT.resolve() not in file.parents or not file.is_file() or sha256_file(file) != expected:
            raise SystemExit(f"Feature-cache input missing or changed: {path}")
    print(json.dumps({"feature_cache_integrity": "pass", "metadata": meta,
                      "training_or_submission_authorized": False}, indent=2))


if __name__ == "__main__":
    main()
