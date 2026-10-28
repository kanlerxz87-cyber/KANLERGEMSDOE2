#!/usr/bin/env python3
"""Canonical Protocol Rule 2 holdout evaluator CLI & helper (`evaluate_holdout.py`).

Evaluates a GeoTIFF, `.npy` mask/probability field, or `.npz` per-cell OOF fold predictions using BOTH:
  1. `DESCRIPTIVE-DTI` using `GEMSDOE32-HIDE-RECOVER-v3.0`: withheld faults with a 1.5 km collar,
     visible-only pixel mask + optional `B` gate, pooled DTI (alpha=0.2, beta=0.8, 300 m
     triangular kernel) and 256-block spatial cluster-bootstrap 95% CI.
  2. `DESCRIPTIVE-DTI` using `GEMSDOE32-SGMC-CAL-v3.0`: off-catalogue USGS SGMC faults (>300 m from `labels.tif`)
     with 256-block spatial cluster-bootstrap 95% CI.
Supports both binary `{0, 1}` and soft/continuous `[0, 1]` rasters.
The CLI cannot prove how a static or purported per-cell prediction was trained,
or whether catalogue features used only visible faults. Its numeric output is
descriptive and cannot by itself establish an independent holdout or approve a
submission. GeoTIFF grids must match the owner-mirror sample exactly.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir  # noqa: E402


def _strip_internal(d: dict) -> dict:
    result = {k: v for k, v in d.items() if not k.startswith("_")}
    result["score_label"] = "DESCRIPTIVE-DTI (fold/model provenance not verified)"
    return result


_PROVENANCE_WARNING = (
    "The scoring code does not verify model training, feature provenance, or visible-only "
    "catalogue construction. A static or purported per-cell prediction is not an "
    "independent holdout or release authorization without separate replay."
)


def evaluate_path(path: Path, b_visible_px: float = 0.0, ddir: Path | None = None, name: str | None = None) -> dict:
    ddir = ddir or data_dir()
    ctx = holdout.load_holdout_context(ddir)
    cand_name = name or path.stem
    suf = path.suffix.lower()
    if suf == ".npz":
        with np.load(path) as zf:
            cells = {k: np.asarray(zf[k]) for k in zf.files if k.startswith("draw")}
            full_arr = np.asarray(zf["full"]) if "full" in zf.files else None
        hr = _strip_internal(holdout.evaluate_hide_and_recover(cells, ctx, b_visible_px=b_visible_px, name=cand_name))
        out = {
            "candidate_id": cand_name,
            "path": str(path),
            "mode": "per_cell_predictions_npz",
            "grid_identity_verified": False,
            "feature_and_training_provenance_verified": False,
            "eligible_for_promotion": False,
            "provenance_warning": _PROVENANCE_WARNING,
            "hide_and_recover": hr,
        }
        if full_arr is not None:
            out["sgmc_off_catalogue"] = _strip_internal(holdout.evaluate_sgmc_with_ci(full_arr, ctx, name=cand_name))
        return out
    grid_verified = False
    if suf == ".npy":
        arr = np.load(path, allow_pickle=False)
    else:
        with rasterio.open(path) as ds, rasterio.open(ddir / "sample_submission.tif") as template:
            if (ds.count != 1 or template.count != 1 or
                    (ds.shape, ds.crs, ds.transform) !=
                    (template.shape, template.crs, template.transform)):
                raise ValueError("GeoTIFF must be single-band and match the sample grid/CRS/transform")
            arr = ds.read(1)
            grid_verified = True
    if arr.shape != ctx.foot.shape:
        raise ValueError(f"Expected grid shape {ctx.foot.shape}, got {arr.shape}")
    pos = np.isfinite(arr) & (arr > 0) & ctx.foot
    hr = _strip_internal(holdout.evaluate_hide_and_recover(arr, ctx, b_visible_px=b_visible_px, name=cand_name))
    sg = _strip_internal(holdout.evaluate_sgmc_with_ci(arr, ctx, name=cand_name))
    return {
        "candidate_id": cand_name,
        "path": str(path),
        "mode": "static_full_map",
        "grid_identity_verified": grid_verified,
        "feature_and_training_provenance_verified": False,
        "eligible_for_promotion": False,
        "provenance_warning": _PROVENANCE_WARNING,
        "emitted_pixels": int(pos.sum()),
        "emitted_mass": float(np.where(pos, arr, 0.0).sum()),
        "hide_and_recover": hr,
        "sgmc_off_catalogue": sg,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("candidate", type=Path, help="GeoTIFF, .npy mask/probs, or .npz per-cell fold predictions")
    ap.add_argument("--b-visible-px", type=float, default=0.0, help="Visible-only B exclusion radius in pixels")
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--name", default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    res = evaluate_path(args.candidate, b_visible_px=args.b_visible_px, ddir=args.data_dir or data_dir(), name=args.name)
    txt = json.dumps(res, indent=2)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n")
    print(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
