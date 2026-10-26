#!/usr/bin/env python3
"""Independently reproduce the literal-registry stop witness; never generate predictions.

All rasters are integrity-pinned peer mirrors, not organizer-authenticated data.
The test uses the shared template's literal support definition: finite value > 0.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
REFERENCES = {
    "continuous_gemsdoe48": {
        "filename": "gemsdoe48-h58-continuous-pignistic-20261008T175914Z-e58.tif",
        "sha256": "59ef8e7d8374e228bc1e41376f03fc67dd5b8a5e6804885a1ae802f399140b89",
        "source": "https://github.com/buffedlizard55-lab/GEMSDOE48/blob/268ec599f51c517cc3485da077c24d83af5be81d/docs/downloads/gemsdoe48-h58-continuous-pignistic-20261008T175914Z-e58.tif",
        "registry_evidence": "https://github.com/buffedlizard55-lab/GEMSDOE31/blob/2a7cd0c8f1c30341a3a655a01a1ff5bff67b23d2/registry/shared_registry_57_snapshot.json",
    },
    "calibration_lattice": {
        "filename": "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
        "sha256": "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2",
        "source": "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
        "registry_evidence": "https://github.com/buffedlizard55-lab/GEMSDOE31/blob/2a7cd0c8f1c30341a3a655a01a1ff5bff67b23d2/registry/shared_registry_57_pin.json",
    },
}
PRIOR_REL = "research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif"
PRIOR_SHA = "8e35f810f2426f6e70e68f1075439352b363ba1059b40d6237ed306275f5b154"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for part in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(part)
    return h.hexdigest()


def measure(footprint, reference, candidate):
    """Exact Euclidean support coverage and candidate->reference overlap.

    Counts and overlap are audit measurements, not leaderboard scores. Only
    100% reference support proves that *every* nonempty candidate is blocked;
    high area coverage alone does not prove this for concentrated candidates.
    """
    fp = np.asarray(footprint, dtype=bool)
    ref, candidate = np.asarray(reference), np.asarray(candidate)
    if fp.ndim != 2 or ref.shape != fp.shape or candidate.shape != fp.shape or not fp.any():
        raise ValueError("Expected nonempty aligned 2D grids")
    if not np.isfinite(ref[fp]).all() or not np.isfinite(candidate[fp]).all():
        raise ValueError("Reference and candidate must be finite inside the footprint")
    if np.any((ref[fp] < 0) | (ref[fp] > 1)) or np.any((candidate[fp] < 0) | (candidate[fp] > 1)):
        raise ValueError("Reference and candidate must be in [0,1] inside the footprint")
    ref_support = fp & (ref > 0)
    cand_support = fp & (candidate > 0)
    if not ref_support.any() or not cand_support.any():
        raise ValueError("Empty positive supports cannot certify novelty")
    distances = distance_transform_edt(~ref_support)
    covered = fp & (distances <= 3.0)
    a = candidate[fp].astype(np.float64)
    b = ref[fp].astype(np.float64)
    if np.ptp(a) == 0 or np.ptp(b) == 0:
        rho = None
    else:
        # Binary values are affine in their average ranks. Other values need
        # explicit tie-aware ranks for exact full-footprint Spearman rho.
        ar = a if np.isin(a, (0, 1)).all() else rankdata(a)
        br = b if np.isin(b, (0, 1)).all() else rankdata(b)
        rho = float(np.corrcoef(ar, br)[0, 1])
    overlap = float(np.mean(distances[cand_support] <= 3.0))
    complete_positive_support = bool(np.all(ref[fp] > 0))
    return {
        "support_definition": "finite value > 0 inside the sample footprint",
        "radius_px": 3.0,
        "footprint_pixels": int(fp.sum()),
        "reference_positive_pixels": int(ref_support.sum()),
        "reference_positive_every_footprint_pixel": complete_positive_support,
        "footprint_within_radius_fraction": float(covered.sum() / fp.sum()),
        "candidate_positive_pixels": int(cand_support.sum()),
        "candidate_positive_outside_footprint": int(((candidate > 0) & ~fp).sum()),
        "candidate_within_radius_fraction": overlap,
        "full_footprint_spearman": rho,
        "candidate_fails_literal_rule": bool(overlap > 0.70 or (rho is not None and rho > 0.90)),
        "universal_nonempty_candidate_blocker": complete_positive_support,
    }


def load_grid(path, expected_grid):
    with rasterio.open(path) as ds:
        if (ds.crs, ds.shape, ds.transform, ds.count) != expected_grid:
            raise ValueError(f"Grid mismatch: {path}")
        return ds.read(1)


def audit(data_dir: Path = ROOT / "data", prior: Path = ROOT / PRIOR_REL):
    sample = data_dir / "sample_submission.tif"
    if sha256_file(sample) != SAMPLE_SHA or sha256_file(prior) != PRIOR_SHA:
        raise ValueError("Sample or prior candidate SHA-256 mismatch")
    with rasterio.open(sample) as ds:
        grid = (ds.crs, ds.shape, ds.transform, 1)
        fp = np.isfinite(ds.read(1))
        if ds.count != 1 or ds.crs is None or not fp.any():
            raise ValueError("Invalid sample")
    candidate = load_grid(prior, grid)
    rows = {}
    for key, entry in REFERENCES.items():
        path = data_dir / "registry" / "blockers" / entry["filename"]
        if sha256_file(path) != entry["sha256"]:
            raise ValueError(f"Registry SHA-256 mismatch: {path}")
        result = measure(fp, load_grid(path, grid), candidate)
        rows[key] = {**entry, **result}
    return {
        "evidence_class": "REGISTRY-AUDIT (geometric measurements, not scores)",
        "protocol": "literal >=0? No: positive means >0; candidate-directional Euclidean distance <=3 px; duplicate when overlap >0.70 or rho >0.90",
        "sample_sha256": SAMPLE_SHA,
        "prior_candidate_sha256": PRIOR_SHA,
        "prior_candidate": "E1 XG-HGB; archived, not a current submission",
        "references": rows,
        "surface_check": "not run: no new surface; universal support witness stops this lane before construction",
        "proof": "The registered continuous raster is strictly positive at every footprint pixel. Under the shared >0 support convention, each possible nonempty in-footprint dot lies on a registered positive pixel, so directional overlap is 1.0 regardless of model or placement. A semantic change to which rasters have dots is a protocol change, not an automatic exception.",
        "candidate_generation_permitted_under_literal_rule": False,
        "prior_e1_authorization": "withdrawn: literal final-dot duplicate; prior surface and holdout evidence not independently validated",
        "registry_scope": "Two pinned counterexamples; no claim that the full registry was downloaded or exhaustively compared.",
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", type=Path, default=ROOT / "data")
    p.add_argument("--output", type=Path, help="Optional JSON evidence path")
    args = p.parse_args()
    result = audit(args.data_dir)
    payload = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload)
    print(payload, end="")


if __name__ == "__main__":
    main()
