#!/usr/bin/env python3
"""Reproduce the nine historical raster audit; no leaderboard inference."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import rasterio
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.novelty import dot_overlap, is_duplicate, rank_correlation  # noqa: E402
from validate_raster import sha256_file, validate  # noqa: E402


def compare(a, b, mask):
    a, b, mask = np.asarray(a), np.asarray(b), np.asarray(mask, bool)
    if a.ndim != 2 or a.shape != b.shape or a.shape != mask.shape or not mask.any():
        raise ValueError("Aligned nonempty grids required")
    x, y = a[mask], b[mask]
    if not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Comparison requires finite values on the footprint")
    if np.ptp(x) == 0 or np.ptp(y) == 0:
        rho = None
    else:
        # A binary vector is affine to its average ranks.
        xr = x.astype(np.float64) if np.isin(x, [0, 1]).all() else rankdata(x)
        rho = rank_correlation(xr, y)
    overlap = dot_overlap((a > 0) & mask, (b > 0) & mask)["candidate_within_3px_of_reference"]
    return {"spearman_rho": rho, "fraction_a_dots_within_3px_of_b": overlap,
            "duplicate_gate": rho is None or overlap is None or is_duplicate(rho, overlap),
            "decoded_pixels_equal_inside_footprint": bool(np.array_equal(x, y))}


def main():
    records = json.loads((ROOT / "research/raster_manifest.json").read_text())
    template = ROOT / "data/sample_submission.tif"
    pins = json.loads((ROOT / "research/input_pins.json").read_text())["records"]
    sample_pin = next(row for row in pins if row["id"] == "sample_submission")
    if sha256_file(template) != sample_pin["sha256"]:
        raise ValueError("Sample does not match the pinned peer mirror")
    with rasterio.open(template) as src:
        mask = np.isfinite(src.read(1)) & (src.read_masks(1) > 0)
        grid = (src.shape, src.crs, src.transform)
        if src.count != 1 or src.crs is None or not mask.any():
            raise ValueError("Sample must be georeferenced with a nonempty footprint")
    if len({record["site"] for record in records}) != len(records):
        raise ValueError("Duplicate historical site IDs")
    arrays, reports = {}, []
    for record in records:
        path = ROOT / record["local"]
        if sha256_file(path) != record["sha256"]:
            raise ValueError(f"Registry checksum mismatch: {path}")
        report = validate(path, template)
        report["path"] = record["local"]
        reports.append({"site": record["site"], **report})
        with rasterio.open(path) as src:
            if (src.shape, src.crs, src.transform) != grid:
                raise ValueError(f"Registry grid mismatch: {path}")
            arrays[record["site"]] = src.read(1)
    pairs = []
    # Keep directional records explicit: distance overlap need not be symmetric.
    for a, arr_a in arrays.items():
        for b, arr_b in arrays.items():
            if a != b:
                pairs.append({"a": a, "b": b, **compare(arr_a, arr_b, mask)})
    out = {"scope": "Nine historical references only; not full registry; final dots only, not new candidate surfaces.",
           "format_note": "Whole-grid range/grid is separate from the published outside-footprint null/NaN requirement; template is a peer mirror.",
           "footprint_pixels": int(mask.sum()), "format_reports": reports, "directed_pairs": pairs}
    (ROOT / "research/raster_audit.json").write_text(json.dumps(out, indent=2, allow_nan=False) + "\n")
    print("Audited", len(reports), "historical rasters;", len(pairs), "directed comparisons;",
          sum(p["duplicate_gate"] for p in pairs), "literal duplicate-gate hits")


if __name__ == "__main__":
    main()
