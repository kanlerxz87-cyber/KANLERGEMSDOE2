#!/usr/bin/env python3
"""Verification pass 2: reproducibility.

Rebuild the Experiment 2 candidate deterministically from the cached feature
stack (same fixed RNG seeds as scripts/build_unique_submission.py) WITHOUT
writing any file, and prove the published TIFF's pixel content is exactly
reproducible: the content hash embedded in its filename must match, and the
whole-file SHA-256 must match evidence/current_run_card.json.

Exit nonzero on any mismatch.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems import footprint, paths  # noqa: E402
from gems.emission import priority_poisson  # noqa: E402
from gems.validator import sha256_file  # noqa: E402

K = 20_000
N_UNCOVERED = 6_500
SEED = 20261029
SURFACE_BANDS = (
    "det_gradient",
    "geod_shearrate",
    "arc_det_elev",
    "arc_agreement",
    "iso_grav_anom_vg",
)


def zscore(a):
    m = np.isfinite(a)
    out = np.zeros_like(a)
    if m.any():
        mu = float(np.nanmean(a))
        sd = float(np.nanstd(a)) or 1.0
        out[m] = (a[m] - mu) / sd
    return out


def main():
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    tif = ROOT / "docs/downloads" / card["submission_name"]
    assert tif.is_file(), f"missing {tif}"
    expected_sha = card["raster_sha256"]

    fp = footprint.load_footprint()
    H, W = fp.shape
    idx = np.flatnonzero(fp.ravel())

    meta = json.loads((paths.DATA_DIR / "prepared" / "features.json").read_text())
    allnames = meta["names"]
    stack = np.load(paths.DATA_DIR / "prepared" / "features.npy", mmap_mode="r")
    surface = np.zeros(H * W, np.float32)
    for name in SURFACE_BANDS:
        band = np.full(H * W, np.nan, np.float32)
        band[idx] = stack[:, allnames.index(name)]
        surface = surface + zscore(band)
    surface = surface / len(SURFACE_BANDS)
    surface = np.where(fp, surface.reshape(H, W), np.nan)
    surface = np.where(np.isfinite(surface), surface, 0.0).astype(np.float32)

    with rasterio.open(paths.DATA_DIR / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif") as ds:
        lattice = ds.read(1)
    lattice_dots = fp & np.isfinite(lattice) & (lattice > 0)
    uncovered = fp & (distance_transform_edt(~lattice_dots) > 3.0)
    n_uncovered = int(uncovered.sum())
    assert n_uncovered >= N_UNCOVERED, f"only {n_uncovered} uncovered pixels"

    rng = np.random.default_rng(SEED)
    uy, ux = np.nonzero(uncovered)
    pick = rng.choice(len(uy), size=N_UNCOVERED, replace=False)
    dots = np.zeros(fp.shape, bool)
    dots[uy[pick], ux[pick]] = True

    remaining = K - N_UNCOVERED
    eligible = fp & ~dots & (surface > 0)
    dots |= priority_poisson(surface, eligible, remaining, min_dist=3.0)
    if int(dots.sum()) < K:
        need = K - int(dots.sum())
        fy, fx = np.nonzero(fp & ~dots)
        p2 = rng.choice(len(fy), size=min(need, len(fy)), replace=False)
        dots[fy[p2], fx[p2]] = True
    assert int(dots.sum()) == K, dots.sum()

    pred = np.zeros(fp.shape, np.float32)
    pred[dots] = 1.0
    content_id = hashlib.sha256(np.asarray(pred[fp], dtype="<f4").tobytes()).hexdigest()[:12]
    name_token = card["submission_name"].split("-")[-2]
    assert content_id == name_token, f"content id {content_id} not in filename token {name_token}"

    with rasterio.open(tif) as ds:
        actual = ds.read(1).astype(np.float32)
    actual_sha = sha256_file(tif)
    actual_content = hashlib.sha256(np.asarray(actual[fp], dtype="<f4").tobytes()).hexdigest()[:12]

    ok = (actual_sha == expected_sha) and (actual_content == content_id)
    print(f"published sha256:    {actual_sha}")
    print(f"expected sha256:     {expected_sha}")
    print(f"rebuilt content id:  {content_id}")
    print(f"file content id:     {actual_content}")
    print("PASS - deterministic rebuild matches published TIFF" if ok else "FAIL - rebuild does not match published TIFF")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
