#!/usr/bin/env python3
"""Reopen the owner-mirror inputs and disclose the sample-label irregularity."""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.validator import sha256_file  # noqa: E402


def verify(data: Path) -> dict:
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text(encoding="utf-8"))
    core = [row for row in manifest["files"] if row["group"] == "core"]
    hashes = {}
    for row in core:
        p = data / row["dest"]
        actual = sha256_file(p)
        if actual != row["sha256"]:
            raise ValueError(f"input checksum mismatch: {row['dest']}")
        hashes[row["dest"]] = actual
    with rasterio.open(data / "sample_submission.tif") as sample, \
         rasterio.open(data / "labels.tif") as labels, \
         rasterio.open(data / "training_features.tif") as features:
        if any((d.shape, d.crs, d.transform) != (sample.shape, sample.crs, sample.transform)
               for d in (labels, features)):
            raise ValueError("input grids do not align")
        a, l = sample.read(1), labels.read(1)
        fp = np.isfinite(a)
        sample_pos, label_pos = fp & (a > 0), fp & (l > 0)
        grid = {"shape": list(sample.shape), "crs": str(sample.crs),
                "transform": list(sample.transform)[:6], "feature_band_count": features.count}
        return {
            "schema": "gems.input-audit.v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "provenance": "SHA-pinned owner mirrors; not independently authenticated organizer bytes",
            "core_hashes": hashes,
            "grid": grid,
            "footprint_pixels": int(fp.sum()),
            "sample_positive_pixels": int(sample_pos.sum()),
            "label_positive_pixels": int(label_pos.sum()),
            "sample_positive_xor_label_pixels": int((sample_pos ^ label_pos).sum()),
            "labels_and_existing_faults_byte_identical": hashes["labels.tif"] == hashes["existing_faults.tif"],
            "irregularity": "This mirrored sample contains the labelled faults, whereas the public problem description calls the sample a total-fault-absence prediction. Use it as a grid/footprint template only.",
            "official_description": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#submission-format",
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", type=Path, default=Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data")))
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/input_diagnostics_20261027.json")
    args = ap.parse_args()
    result = verify(args.data)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
