#!/usr/bin/env python3
"""Restore core/witness mirrors and verify the already tracked educational references.

Unlike the older API-based restore, this does not overwrite the corrected shared
vendor template or rewrite provenance manifests. It cannot authenticate mirrors.
"""
import json
from pathlib import Path

from restore_competition_data import CORE, EXTRA, MANIFEST, restore, sha256_file

ROOT = Path(__file__).resolve().parents[1]


def main():
    manifest = json.loads(MANIFEST.read_text())
    by_id = {item["id"]: item for item in manifest["files"]}
    restore([by_id[key] for key in CORE] + list(EXTRA), ROOT / "data")
    for row in json.loads((ROOT / "research/raster_manifest.json").read_text()):
        path = ROOT / row["local"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise SystemExit(f"Historical raster missing or checksum mismatch: {path}")
    for row in json.loads((ROOT / "vendor/template/pins.json").read_text())["files"]:
        path = ROOT / "vendor/template" / row["local"]
        if not path.is_file() or sha256_file(path) != row["sha256"]:
            raise SystemExit(f"Shared template missing or checksum mismatch: {path}")
    print("All pinned mirror, historical-reference and local template hashes pass.")


if __name__ == "__main__":
    main()
