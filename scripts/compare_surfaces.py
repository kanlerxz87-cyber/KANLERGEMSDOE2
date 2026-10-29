#!/usr/bin/env python3
"""Comparison (read-only, writes to evidence/ only): holdout DTI of two surfaces.

A. geophysical-only (catalogue-independent, used for the unique submission).
B. fault-proximity (public USGS/INGENIOUS catalogue distance kernel -- the
   historical H19-5 dotted strategy).

Both are evaluated with the SAME SegmentHoldout (hide-and-recover, alpha 0.2,
beta 0.8, 300 m) so the DTI estimates are directly comparable. A leakage canary
is run on each. This quantifies why the high-scoring historical family is not
submit-able (non-unique) and what the compliant unique alternative estimates.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import footprint, paths  # noqa: E402
from gems.holdout import SegmentHoldout, SEGMENT_EVALUATOR_VERSION  # noqa: E402
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score

K = 20_000
BUFFER_PX = 15


def zscore(a):
    m = np.isfinite(a)
    out = np.zeros_like(a)
    if m.any():
        mu = float(np.nanmean(a)); sd = float(np.nanstd(a)) or 1.0
        out[m] = (a[m] - mu) / sd
    return out


def canary_auc(holdout, surface, seed=20261025, max_per_class=15000):
    rng = np.random.default_rng(seed)
    ys, xs = [], []
    for fold in holdout.folds:
        truth, valid = fold["truth"], fold["valid"]
        pos = np.flatnonzero(truth)
        neg = np.flatnonzero(
            valid & ~fold["visible"] & (distance_transform_edt(~truth) >= 9)
        )
        pos = rng.choice(pos, min(len(pos), max_per_class), replace=False)
        neg = rng.choice(neg, min(len(neg), max_per_class), replace=False)
        ids = np.r_[pos, neg]
        x = np.where(np.isfinite(surface.ravel()[ids]), surface.ravel()[ids], 0.0)
        ys.append(x)
        xs.append(np.r_[np.ones(len(pos)), np.zeros(len(neg))])
    return float(roc_auc_score(np.concatenate(xs), np.concatenate(ys)))


def emit(holdout, surface, K):
    budget = [max(1, round(K * f["valid"].sum() / holdout.footprint.sum()))
              for f in holdout.folds]
    preds = []
    for fold, k in zip(holdout.folds, budget):
        s2 = np.where(fold["valid"] & ~fold["visible"], surface, -np.inf)
        ids = np.flatnonzero(s2 > -np.inf)
        pred = np.zeros(holdout.footprint.shape, bool)
        k = min(k, len(ids))
        if k:
            order = ids[np.lexsort((ids, -s2.ravel()[ids]))]
            pred.ravel()[order[:k]] = True
        preds.append(pred)
    return holdout.summarize(preds, ci_draws=200)


def main():
    fp = footprint.load_footprint()
    H, W = fp.shape
    idx = np.flatnonzero(fp.ravel())
    with rasterio.open(paths.LABELS_PATH) as s:
        labels = (s.read(1) > 0) & fp
    holdout = SegmentHoldout(fp, labels, buffer_px=BUFFER_PX)

    meta = json.loads((paths.DATA_DIR / "prepared" / "features.json").read_text())
    allnames = meta["names"]
    stack = np.load(paths.DATA_DIR / "prepared" / "features.npy", mmap_mode="r")

    def band(name):
        b = np.full(H * W, np.nan, np.float32)
        b[idx] = stack[:, allnames.index(name)]
        return b.reshape(H, W)

    # Surface A: geophysical-only composite.
    geo = np.zeros(H * W, np.float32)
    for n in ("det_gradient", "geod_shearrate", "arc_det_elev", "arc_agreement",
              "iso_grav_anom_vg"):
        geo = geo + zscore(band(n).ravel())
    geo = np.where(fp, (geo / 5).reshape(H, W), np.nan)
    geo = np.where(np.isfinite(geo), geo, 0.0).astype(np.float32)

    # Surface B: fault-proximity kernel (triangular, 300 m) of the FULL catalogue.
    dist = distance_transform_edt(~labels)
    fault_prox = np.maximum(1.0 - dist / 3.0, 0.0).astype(np.float32)
    fault_prox = np.where(fp, fault_prox, 0.0)

    for label, surface in (("A_geophysical_only", geo), ("B_fault_proximity", fault_prox)):
        auc = canary_auc(holdout, surface)
        res = emit(holdout, surface, K)
        print(json.dumps({
            "surface": label,
            "leakage_canary_auc": round(float(auc), 4),
            "holdout_dti": round(float(res["dti"]), 6),
            "holdout_ci95": [round(float(x), 6) for x in res["ci95"]["interval"]],
            "n_truth": int(res["n_truth"]),
            "evaluator": SEGMENT_EVALUATOR_VERSION,
        }), flush=True)


if __name__ == "__main__":
    main()
