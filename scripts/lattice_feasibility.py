#!/usr/bin/env python3
"""A necessary-condition check *before* dot placement, not a novelty certificate.

For a fixed number N of distinct footprint cells and a registry raster, at most
B cells outside its three-pixel halo can avoid overlap. Thus at least max(0,N-B)
of the N cells are inside the halo, regardless of how a detector is built.
This cannot clear a candidate: all other surface/final registry checks remain.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

TEMPLATE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
REGISTRY_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
REGISTRY_SOURCE = ("https://github.com/buffedlizard55-lab/GEMSDOE24/blob/"
                   "07345ea0604953d7efb858d9cfbc21e20c7aca0b/inputs/calibration/"
                   "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def lower_bound(footprint: np.ndarray, registry_points: np.ndarray, budget: int,
                radius_px: float = 3.0) -> dict:
    """Exact lower bound for any binary N-dot placement; never uses a candidate."""
    footprint = np.asarray(footprint, dtype=bool)
    points = np.asarray(registry_points, dtype=bool).copy()
    if footprint.ndim != 2 or footprint.shape != points.shape or not footprint.any():
        raise ValueError("footprint and registry must be aligned, nonempty 2-D arrays")
    if isinstance(budget, bool) or not isinstance(budget, int) or budget < 1 or budget > int(footprint.sum()):
        raise ValueError("budget must be a positive integer not exceeding the footprint")
    if not np.isfinite(radius_px) or radius_px < 0:
        raise ValueError("radius must be finite and nonnegative")
    points &= footprint
    if points.any():
        inside_halo = footprint & (distance_transform_edt(~points) <= radius_px)
    else:
        inside_halo = np.zeros_like(footprint)
    outside = int(np.count_nonzero(footprint & ~inside_halo))
    within_min = max(0, budget - outside)
    # Compare integers: exact strict >70%, no rounding in the decision.
    impossible = within_min * 10 > budget * 7
    return {
        "candidate_budget": budget,
        "registry_points_in_footprint": int(points.sum()),
        "footprint_cells": int(footprint.sum()),
        "halo_radius_pixels_euclidean": radius_px,
        "footprint_cells_outside_halo": outside,
        "footprint_cells_inside_halo": int(inside_halo.sum()),
        "minimum_candidate_dots_inside_halo": within_min,
        "minimum_fraction_inside_halo": within_min / budget,
        "strict_more_than_70_percent_unavoidable": impossible,
        "verdict": "duplicate-stop" if impossible else "inconclusive-not-a-novelty-pass",
    }


def audit(template: Path, registry: Path, budget: int, *, verify_pins: bool = True) -> dict:
    template_hash, registry_hash = sha256(template), sha256(registry)
    if verify_pins and (template_hash != TEMPLATE_SHA or registry_hash != REGISTRY_SHA):
        raise ValueError("input hash does not match the pinned owner mirror or registry raster")
    with rasterio.open(template) as src:
        sample = src.read(1)
        footprint = np.isfinite(sample)
        grid = (src.height, src.width, src.crs, src.transform)
        grid_report = {"height": src.height, "width": src.width, "crs": str(src.crs),
                       "transform": list(src.transform)[:6], "footprint_rule": "finite sample values"}
    with rasterio.open(registry) as src:
        reg_grid = (src.height, src.width, src.crs, src.transform)
        if reg_grid != grid or src.count != 1:
            raise ValueError("registry must have one band and exactly match template CRS/shape/transform")
        arr = src.read(1)
    if np.any(~np.isfinite(arr[footprint])):
        raise ValueError("registry contains non-finite values inside footprint")
    points = np.isfinite(arr) & (arr > 0)
    result = lower_bound(footprint, points, budget)
    result.update({
        "template_sha256": template_hash,
        "registry_sha256": registry_hash,
        "registry_source": REGISTRY_SOURCE,
        "template_provenance": "owner-supplied mirror; hash-pinned, not organizer-authenticated",
        "grid": grid_report,
        "scope": "one pinned registry raster only; a pass cannot establish overall uniqueness",
        "surface_correlation": "not evaluated: geometric impossibility was detected before the surface was built" if result["strict_more_than_70_percent_unavoidable"] else "not evaluated",
        "actual_dot_overlap": "not evaluated: no dots were placed",
    })
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path)
    parser.add_argument("--registry", required=True, type=Path)
    parser.add_argument("--budget", required=True, type=int)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = audit(args.template, args.registry, args.budget)
    result["checked_utc"] = datetime.now(timezone.utc).isoformat()
    text = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
