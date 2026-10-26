#!/usr/bin/env python3
"""Check pinned mirror inputs, grid and band semantics; never invent training data."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio

from restore_inputs import sha256_file

ROOT = Path(__file__).resolve().parents[1]
BAND_NAMES = [
    "mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope", "tc",
    "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15", "iso_grav_anom_vg",
    "det_elev", "iso_grav_anom", "tmi", "depth_to_base_surf", "ieq_n100a15",
    "cond_surf", "iso_grav_anom_hg", "det_elev_slope",
]


def inspect(root: Path = ROOT) -> dict:
    records = json.loads((root / "research/input_pins.json").read_text())["records"]
    required = [r for r in records if r["id"] != "calibration_lattice_s5"]
    errors, files = [], {}
    for row in required:
        path = root / row["destination"]
        item = {"path": row["destination"], "present": path.is_file(), "sha256_matches_pin": False}
        if path.is_file():
            item["sha256"] = sha256_file(path)
            item["bytes"] = path.stat().st_size
            item["sha256_matches_pin"] = item["sha256"] == row["sha256"] and item["bytes"] == row["bytes"]
        if not item["sha256_matches_pin"]:
            errors.append(f"missing or wrong pinned bytes: {row['id']}")
        files[row["id"]] = item
    report = {
        "schema_version": 1,
        "input_integrity_passed": False,
        "training_or_submission_authorized": False,
        "origin": "Public peer mirrors with pinned hashes; not authenticated organizer downloads.",
        "files": files,
        "errors": errors,
        "irregularities": [],
    }
    if errors:
        return report
    try:
        with rasterio.open(root / "data/sample_submission.tif") as t:
            sample = t.read(1)
            footprint = np.isfinite(sample) & (t.read_masks(1) > 0)
            grid = (t.shape, t.crs, t.transform)
            if t.count != 1 or t.dtypes != ("float32",) or t.crs is None or not footprint.any():
                errors.append("sample must be a nonempty, single-band, georeferenced float32 raster")
            report["grid"] = {
                "shape": list(t.shape), "crs": str(t.crs), "transform": list(t.transform)[:6],
                "footprint_pixels": int(footprint.sum()),
            }
        for row in required:
            with rasterio.open(root / row["destination"]) as ds:
                same = (ds.shape, ds.crs, ds.transform) == grid
                files[row["id"]]["grid_matches_template"] = same
                files[row["id"]]["band_count"] = ds.count
                if not same:
                    errors.append(f"grid mismatch: {row['id']}")
                if row["id"] == "training_features":
                    names = [ds.tags(i).get("band_name") for i in range(1, ds.count + 1)]
                    files[row["id"]]["band_names"] = names
                    files[row["id"]]["band_names_match_expected"] = names == BAND_NAMES
                    if names != BAND_NAMES or ds.dtypes != ("float32",) * len(BAND_NAMES):
                        errors.append("training feature names/order/dtypes do not match pinned 19-band contract")
                elif row["id"] in ("labels", "existing_faults", "sample_submission") and ds.count != 1:
                    errors.append(f"single band required: {row['id']}")
        with rasterio.open(root / "data/labels.tif") as ds:
            labels = ds.read(1)
            positive = labels > 0
            if positive.shape != footprint.shape or np.any(positive & ~footprint):
                errors.append("label positives fall outside the template footprint")
            else:
                report["label_positive_pixels"] = int((positive & footprint).sum())
                report["sample_ones_equal_known_faults"] = bool(np.array_equal((sample == 1) & footprint, positive & footprint))
                if report["sample_ones_equal_known_faults"] and positive.any():
                    report["irregularities"].append(
                        "Peer-mirrored sample contains known-fault ones, although the public problem page describes a total-fault-absence example. Use its geometry/footprint only, never its pixel values as features."
                    )
    except (OSError, ValueError, rasterio.errors.RasterioError) as exc:
        errors.append(f"raster inspection failed: {exc}")
    report["input_integrity_passed"] = not errors
    return report


def main() -> None:
    report = inspect()
    output = ROOT / "data/prepared_manifest.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report["input_integrity_passed"] else 1)


if __name__ == "__main__":
    main()
