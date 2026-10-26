#!/usr/bin/env python3
"""Audit actual data placement, integrity and aligned grids; never synthesize inputs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import rasterio

if __package__:
    from .restore_competition_data import sha256_file
else:
    from restore_competition_data import sha256_file

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "research/snapshots/GEMSDOE32/registry/data_manifest.json"
CORE = ("training_features", "labels", "existing_faults", "sample_submission")
OPTIONAL = ("ext_geodawn_rad_u8", "ext_geodawn_extensions_u8", "ext_lidar_scarp_features_u8")


def inspect(data_dir: Path, manifest: dict) -> dict:
    by_id = {row["id"]: row for row in manifest["files"]}
    checks = {}
    for key in CORE + OPTIONAL:
        row = by_id[key]
        path = data_dir / row["dest"]
        exists = path.is_file()
        checks[key] = {
            "path": row["dest"], "exists": exists,
            "bytes_match": exists and path.stat().st_size == row["bytes"],
            "sha256_match": exists and sha256_file(path) == row["sha256"],
            "expected_sha256": row["sha256"],
        }
    errors = []
    for key in CORE:
        if not checks[key]["exists"] or not checks[key]["bytes_match"] or not checks[key]["sha256_match"]:
            errors.append(f"{key}: missing or integrity mismatch")
    detail = {}
    sample_path = data_dir / by_id["sample_submission"]["dest"]
    if checks["sample_submission"]["sha256_match"]:
        with rasterio.open(sample_path) as template:
            grid = (template.crs, template.shape, template.transform)
            sample = template.read(1)
            foot = np.isfinite(sample)
            detail["sample"] = {
                "single_band": template.count == 1,
                "dtype": template.dtypes[0],
                "crs": str(template.crs),
                "shape": list(template.shape),
                "transform": list(template.transform)[:6],
                "finite_footprint_pixels": int(foot.sum()),
                "positive_inside_footprint": int((foot & (sample > 0)).sum()),
            }
            if template.count != 1 or template.crs is None or not foot.any():
                errors.append("sample_submission: invalid template")
        for key in CORE + OPTIONAL:
            if key == "sample_submission" or not checks[key]["sha256_match"]:
                continue
            with rasterio.open(data_dir / by_id[key]["dest"]) as src:
                match = (src.crs, src.shape, src.transform) == grid
                checks[key]["grid_matches_sample"] = match
                checks[key]["band_count"] = src.count
                checks[key]["band_descriptions"] = list(src.descriptions)
                if key in CORE and not match:
                    errors.append(f"{key}: sample-grid mismatch")
                if key == "training_features" and src.count != 19:
                    errors.append("training_features: expected 19 peer-mirror bands")
                if key in ("labels", "existing_faults") and src.count != 1:
                    errors.append(f"{key}: expected one band")
                if key == "labels" and match and src.count == 1:
                    labels = src.read(1)
                    positives = labels > 0
                    detail["labels"] = {
                        "positive_inside_footprint": int((foot & positives).sum()),
                        "positive_outside_footprint": int((~foot & positives).sum()),
                        "sample_positive_mask_equals_labels": bool(np.array_equal(foot & (sample > 0), foot & positives)),
                    }
                    if detail["labels"]["positive_outside_footprint"]:
                        errors.append("labels: positive values outside sample footprint")
    else:
        errors.append("sample_submission: no trusted grid available")
    core_ready = not errors
    return {
        "evidence_class": "DATA-INTEGRITY (not an organizer score)",
        "core_mirror_ready": core_ready,
        "ready": core_ready,
        "organizer_authenticated": False,
        "scientific_promotion_ready": False,
        "scientific_promotion_reason": "Data placement alone cannot establish lane, leakage, holdout improvement, complete-registry novelty or selector approval.",
        "provenance": "Byte-for-byte match to pinned public peer manifests only; independent organizer-origin verification is not established.",
        "checks": checks,
        "details": detail,
        "irregularities": [
            "The mirrored sample contains positive values, contrary to the organizer page's description of a total-absence sample. Its values must never be used as model features or hidden truth; use it only for the footprint/grid.",
            "External rasters are peer-derived caches; matching their hashes does not verify every processing step or license for a final competition entry.",
        ],
        "errors": errors,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--output", type=Path, default=ROOT / "data/prepared_manifest.json")
    args = parser.parse_args()
    result = inspect(args.data_dir, json.loads(MANIFEST.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    if not result["core_mirror_ready"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
