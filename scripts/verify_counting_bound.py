#!/usr/bin/env python3
"""Independently recompute the pigeonhole duplicate bound from restored bytes.

For a space-filling registry control W (positives P_W), let U = footprint pixels
NOT within 3 px of any P_W. Any placement of N distinct in-footprint dots has at
least N - U dots within 3 px of P_W. The literal rule forbids > 70 % overlap, so
N is forced-duplicate when (N - U) / N > 0.70, i.e. N > U / 0.30.

Inputs: template sample_submission.tif (footprint = finite pixels) and the
pinned registry witness 13gems_20261001_r13-lattice-s5_v2_nan-outside.tif.
Writes evidence/counting_bound_20261029.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
WITNESS_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
LIMIT = 0.70
RADIUS_PX = 3


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def compute(template: Path, witness: Path) -> dict:
    with rasterio.open(template) as s, rasterio.open(witness) as w:
        assert s.shape == w.shape and s.crs == w.crs and s.transform == w.transform
        fp = np.isfinite(s.read(1))
        wv = w.read(1)
        pos = (np.nan_to_num(wv, nan=0.0) > 0.5) & fp
        crs = str(s.crs)
        shape = list(s.shape)
        transform = list(s.transform)[:6]
    dist = ndimage.distance_transform_edt(~pos)
    covered = (dist <= RADIUS_PX) & fp
    footprint = int(fp.sum())
    uncovered = int((fp & ~covered).sum())
    # largest N with (N - U)/N <= LIMIT  ->  N <= U / (1 - LIMIT)
    n_max = math.floor(uncovered / (1.0 - LIMIT) + 1e-9)
    n_ref = 37654
    return {
        "schema": "gems.counting-bound.v1",
        "generated_utc": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "template_sha256": sha256(template),
        "witness_sha256": sha256(witness),
        "witness_sha256_expected": WITNESS_SHA,
        "witness_sha256_match": sha256(witness) == WITNESS_SHA,
        "crs": crs,
        "shape": shape,
        "transform_first6": transform,
        "footprint_pixels": footprint,
        "witness_positive_pixels": int(pos.sum()),
        "covered_within_3px": int(covered.sum()),
        "uncovered_pixels": uncovered,
        "coverage_fraction": covered.sum() / footprint,
        "limit": LIMIT,
        "reference_budget": n_ref,
        "minimum_overlap_at_reference_budget": (n_ref - uncovered) / n_ref,
        "forced_duplicate_at_reference_budget": (n_ref - uncovered) / n_ref > LIMIT,
        "max_budget_not_forced_by_this_witness": n_max,
        "scope": "Single registry control only. Does NOT test the other 359 registry rasters, "
                 "surface rank correlation, holdout DTI, or organizer acceptance.",
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default=str(ROOT / "data" / "review_20261029"))
    ap.add_argument("--out", default=str(ROOT / "evidence" / "counting_bound_20261029.json"))
    a = ap.parse_args()
    d = Path(a.data_dir)
    res = compute(d / "sample_submission.tif", d / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif")
    Path(a.out).write_text(json.dumps(res, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
