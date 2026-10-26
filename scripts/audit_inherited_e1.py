#!/usr/bin/env python3
"""Re-audit an inherited, quarantined E1 raster; never run or promote the model.

Uses the pinned shared novelty functions and the literal calibration-inclusive rule.
The ten-reference scope is NOT a complete registry. No candidate is generated.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.novelty import classify_space_filling_control, dot_overlap, is_duplicate, rank_correlation  # noqa: E402
from validate_raster import sha256_file, validate  # noqa: E402

CANDIDATE = ROOT / "research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif"
CANDIDATE_SHA = "8e35f810f2426f6e70e68f1075439352b363ba1059b40d6237ed306275f5b154"
NAMES = {24: "g24_best.tif", 25: "g25_best.tif", 27: "g27_best.tif", 28: "g28_best.tif", 30: "g30_best.tif", 31: "g31_best.tif", 32: "g32_champion.tif", 33: "g33_best.tif", 36: "g36_best.tif"}


def checked_grid(path: Path, grid: tuple, footprint: np.ndarray, sha256: str) -> np.ndarray:
    if sha256_file(path) != sha256:
        raise ValueError(f"Checksum mismatch: {path}")
    with rasterio.open(path) as dataset:
        if (dataset.shape, dataset.crs, dataset.transform) != grid or dataset.count != 1:
            raise ValueError(f"Grid mismatch: {path}")
        values = dataset.read(1)
    if not np.isfinite(values[footprint]).all():
        raise ValueError(f"Non-finite values inside footprint: {path}")
    return values


def run() -> dict:
    pins = json.loads((ROOT / "research/input_pins.json").read_text())["records"]
    by_id = {r["id"]: r for r in pins}
    template = ROOT / by_id["sample_submission"]["destination"]
    if sha256_file(template) != by_id["sample_submission"]["sha256"]:
        raise ValueError("Sample checksum mismatch")
    with rasterio.open(template) as sample:
        footprint = np.isfinite(sample.read(1)) & (sample.read_masks(1) > 0)
        grid = (sample.shape, sample.crs, sample.transform)
        if sample.count != 1 or sample.crs is None or not footprint.any():
            raise ValueError("Sample must be georeferenced with a nonempty footprint")
    candidate = checked_grid(CANDIDATE, grid, footprint, CANDIDATE_SHA)
    values = candidate[footprint]
    if not np.isin(values, [0, 1]).all() or not np.any(values == 1):
        raise ValueError("Inherited E1 must be a nonempty binary raster")
    candidate_mask = footprint & (candidate > 0)
    # Binary values are affine to their tied average ranks, so the template's
    # rank_correlation gets exactly the Spearman rho without ranking 5M ties.
    candidate_ranks = values.astype(np.float64)
    manifest = json.loads((ROOT / "research/raster_manifest.json").read_text())
    sources = {int(r["site"].removeprefix("GEMSDOE")): r for r in manifest}
    rows = []
    for number, file in NAMES.items():
        source = sources[number]
        ref = checked_grid(ROOT / "data/registry" / file, grid, footprint, source["sha256"])
        ranks_rho = rank_correlation(candidate_ranks, ref[footprint])
        overlap = dot_overlap(candidate_mask, footprint & (ref > 0))["candidate_within_3px_of_reference"]
        rows.append({"id": f"GEMSDOE{number}", "reference_sha256": source["sha256"],
                     "source_url": source["url"], "spearman_full_footprint": ranks_rho,
                     "candidate_fraction_within_3px": overlap,
                     "duplicate": ranks_rho is None or overlap is None or is_duplicate(ranks_rho, overlap)})
    rec = by_id["calibration_lattice_s5"]
    lattice = checked_grid(ROOT / rec["destination"], grid, footprint, rec["sha256"])
    lattice_mask = footprint & (lattice > 0)
    rho = rank_correlation(candidate_ranks, lattice[footprint])
    overlap = dot_overlap(candidate_mask, lattice_mask)["candidate_within_3px_of_reference"]
    calibration = classify_space_filling_control(footprint, lattice_mask, candidate_dot_count=int(candidate_mask.sum()))
    rows.append({"id": rec["id"], "reference_sha256": rec["sha256"],
                 "source_url": f"https://github.com/{rec['repository']}/blob/{rec['commit']}/{rec['paths'][0]}",
                 "spearman_full_footprint": rho, "candidate_fraction_within_3px": overlap,
                 "duplicate": rho is None or overlap is None or is_duplicate(rho, overlap)})
    uncovered = calibration["footprint_3px_uncovered_pixels"]
    # U uncovered cells imply overlap >= 1-U/K. Strict >70% is forced iff 3K > 10U.
    smallest_forced_duplicate = 10 * uncovered // 3 + 1
    validator = validate(CANDIDATE, template)
    validator["path"] = str(CANDIDATE.relative_to(ROOT))
    return {
        "audit_version": "e1-shared-novelty-reaudit-v1",
        "scope": "Nine historical priority rasters plus one calibration lattice; NOT the complete parallel registry.",
        "candidate": str(CANDIDATE.relative_to(ROOT)), "candidate_sha256": CANDIDATE_SHA,
        "surface_check": "UNAVAILABLE: inherited continuous score surface not preserved; cannot retroactively verify pre-placement.",
        "registry_complete": False,
        "rank_scope": "Exact Spearman on all footprint pixels; binary candidate ranks are affine to the tied ranks.",
        "overlap_scope": "All positive E1 pixels, Euclidean distance <= 3 pixels, candidate to reference.",
        "reference_comparisons": rows,
        "max_abs_spearman": max(abs(row["spearman_full_footprint"]) for row in rows if row["spearman_full_footprint"] is not None),
        "max_candidate_overlap_3px": max(row["candidate_fraction_within_3px"] for row in rows if row["candidate_fraction_within_3px"] is not None),
        "literal_duplicate_detected": any(row["duplicate"] for row in rows),
        "calibration_geometry": {**calibration, "minimum_dot_count_for_forced_overlap_above_70_percent": smallest_forced_duplicate,
            "reason": "At most U uncovered cells can be chosen, so overlap >= max(0, 1-U/K); strict >0.70 when 3K > 10U."},
        "validator": validator,
        "legacy_claims_withdrawn": [
            "The inherited E1 quadrant procedure does not hide whole connected components across fold boundaries.",
            "Its fixed-mask hide-and-recover analysis scores a globally fitted model trained on the full catalogue; it is not independent holdout evidence.",
            "Its recorded canary sampled the full catalogue rather than fold-local withheld positives.",
            "Its nine-site novelty audit used Manhattan dilation, excluded the lattice, and occurred after placement.",
            "The SGMC-anchored leaderboard projection is not a measured score and has no validated calibration."
        ],
        "experiments_run_in_this_reaudit": 0,
        "verdict": "negative",
        "ok_to_download_and_submit": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/e1_reaudit_20261026.json")
    args = parser.parse_args()
    result = run()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"literal_duplicate_detected": result["literal_duplicate_detected"],
                      "max_overlap_3px": result["max_candidate_overlap_3px"],
                      "calibration_geometry": result["calibration_geometry"],
                      "published_format_valid": result["validator"]["format_valid"],
                      "verdict": result["verdict"]}, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
