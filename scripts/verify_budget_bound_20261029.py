#!/usr/bin/env python3
"""Independent receipt: single-witness duplicate bound vs dot budget (2026-10-29).

Re-derives, without importing the shared gems package, the counting bound used
by the 70% uniqueness gate:

* covered   = footprint cells whose Euclidean distance to any witness positive
              is <= 3 px (the user's "within 3 px" rule);
* uncovered = footprint cells NOT covered (a dot placed there cannot be near the witness);
* for B distinct in-footprint dots, at least max(0, B - uncovered) overlap the witness.

The result is a LOWER BOUND from ONE witness. It does not clear the full registry
and does not authorise any file. Inputs are SHA-pinned owner mirrors, not organizer
originals. Output is a receipt only; no raster is written.

Usage:
    python scripts/verify_budget_bound_20261029.py --data-dir data/review_20261029 \
        --out evidence/budget_bound_20261029.json
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

ROOT = Path(__file__).resolve().parents[1]
WITNESS = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
WITNESS_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
TEMPLATE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
LIMIT = 0.70
RADIUS_PX = 3.0
FROZEN_BUDGET = 37654  # GEMSDOE32's dot count, copied by the HTCADS lane


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()

    template = args.data_dir / "sample_submission.tif"
    witness = args.data_dir / "scored" / WITNESS
    for p, expected in ((template, TEMPLATE_SHA), (witness, WITNESS_SHA)):
        if not p.is_file() or sha256(p) != expected:
            raise SystemExit(f"Refusing: missing or hash-mismatched input {p}")

    with rasterio.open(template) as ds:
        foot = np.isfinite(ds.read(1))
        grid = (ds.shape, ds.transform, str(ds.crs))
    with rasterio.open(witness) as ds:
        if (ds.shape, ds.transform, str(ds.crs)) != grid:
            raise SystemExit("Refusing: witness grid differs from template grid")
        w = ds.read(1)
    wpos = np.isfinite(w) & (w > 0)
    dist = distance_transform_edt(~wpos)
    covered = int(((dist <= RADIUS_PX) & foot).sum())
    footprint = int(foot.sum())
    uncovered = footprint - covered

    def min_overlap_frac(b: int) -> float:
        return max(0, b - uncovered) / b

    max_budget = 0
    # Largest B with minimum forced overlap <= 70%: B - uncovered <= 0.7 B  <=>  B <= uncovered / 0.3
    max_budget = int(np.floor(uncovered / (1 - LIMIT) + 1e-9))
    assert min_overlap_frac(max_budget) <= LIMIT and min_overlap_frac(max_budget + 1) > LIMIT

    result = {
        "schema": "gems.budget-bound-receipt.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Single-witness lower bound. NOT a full-registry clearance. Authorises no file.",
        "provenance": "SHA-pinned owner mirrors; not organizer-authenticated.",
        "inputs": {
            "template_sha256": TEMPLATE_SHA,
            "witness_file": WITNESS,
            "witness_sha256": WITNESS_SHA,
            "grid": {"shape": list(grid[0]), "crs": grid[2], "transform": list(grid[1])[:6]},
        },
        "footprint_pixels": footprint,
        "witness_positive_pixels": int(wpos.sum()),
        "covered_within_3px": covered,
        "uncovered_pixels": uncovered,
        "limit": LIMIT,
        "frozen_budget": FROZEN_BUDGET,
        "min_overlap_at_frozen_budget": FROZEN_BUDGET - uncovered,
        "min_overlap_frac_at_frozen_budget": round(min_overlap_frac(FROZEN_BUDGET), 6),
        "frozen_budget_passes_single_witness_bound": min_overlap_frac(FROZEN_BUDGET) <= LIMIT,
        "max_budget_passing_single_witness_bound": max_budget,
        "decision_required": (
            "Budget reduction to <= max_budget is a LANE/PROTOCOL change and needs explicit user approval. "
            "The full registry, surface rank check, leakage canaries and holdout must still pass."
        ),
        "ok_to_submit": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in (
        "uncovered_pixels", "min_overlap_frac_at_frozen_budget",
        "frozen_budget_passes_single_witness_bound", "max_budget_passing_single_witness_bound")}, indent=2))


if __name__ == "__main__":
    main()
