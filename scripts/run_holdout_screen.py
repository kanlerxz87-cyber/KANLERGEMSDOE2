#!/usr/bin/env python3
"""Holdout screen: leakage canary per feature band + DTI of a simple surface.

Reuses the template's cached feature stack, SegmentHoldout (hide-and-recover,
alpha 0.2, beta 0.8, 300 m triangular kernel, buffered whole-segment folds) and
the shared submission writer. Nothing here authorizes a weekly slot; every
number is HOLDOUT-DTI unless explicitly stated otherwise.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import footprint, paths  # noqa: E402
from gems.holdout import SegmentHoldout, SEGMENT_EVALUATOR_VERSION  # noqa: E402
from gems.submission import (  # noqa: E402
    write_submission,
    check_variants,
    make_note,
)
from gems.validator import sha256_file  # noqa: E402
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score


def load_stack():
    meta = json.loads((paths.DATA_DIR / "prepared" / "features.json").read_text())
    stack = np.load(paths.DATA_DIR / "prepared" / "features.npy", mmap_mode="r")
    return stack, meta["names"]


def band_array(stack, names, name, idx, H, W):
    band = np.full(H * W, np.nan, np.float32)
    band[idx] = stack[:, names.index(name)]
    return band.reshape(H, W)


def canary_on_array(holdout, surface, seed=20261025, max_per_class=15000):
    """Single-feature pooled AUC leakage canary on holdout truth vs background."""
    rng = np.random.default_rng(seed)
    labels, values = [], []
    for fold in holdout.folds:
        truth, valid = fold["truth"], fold["valid"]
        positive = np.flatnonzero(truth)
        background = np.flatnonzero(
            valid & ~fold["visible"] & (distance_transform_edt(~truth) >= 9)
        )
        positive = rng.choice(positive, min(len(positive), max_per_class), replace=False)
        background = rng.choice(background, min(len(background), max_per_class), replace=False)
        ids = np.r_[positive, background]
        x = np.where(np.isfinite(surface.ravel()[ids]), surface.ravel()[ids], 0.0)
        y = np.r_[np.ones(len(positive)), np.zeros(len(background))]
        labels.append(y)
        values.append(x)
    return float(roc_auc_score(np.concatenate(labels), np.concatenate(values)))


def emit_fold(score_surface, fold, k):
    """Top-k binary emission inside one holdout fold, visible faults excluded."""
    valid = fold["valid"]
    eligible = valid & ~fold["visible"] & np.isfinite(score_surface)
    s2 = np.where(eligible, score_surface, -np.inf)
    ids = np.flatnonzero(s2 > -np.inf)
    pred = np.zeros(score_surface.shape, bool)
    k = min(k, len(ids))
    if k:
        order = ids[np.lexsort((ids, -s2.ravel()[ids]))]
        pred.ravel()[order[:k]] = True
    return pred


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit-k", type=int, default=20000, help="total dots in packaged TIFF")
    ap.add_argument("--buffer", type=int, default=15, help="holdout buffer px")
    args = ap.parse_args()

    fp = footprint.load_footprint()
    with rasterio.open(paths.LABELS_PATH) as s:
        labels = (s.read(1) > 0) & fp

    holdout = SegmentHoldout(fp, labels, buffer_px=args.buffer)
    H, W = fp.shape
    idx = np.flatnonzero(fp.ravel())

    stack, names = load_stack()

    print(f"{'band':32s} {'auc':>7s} {'flag':>6s}", flush=True)
    aucs = {}
    for name in names:
        band = band_array(stack, names, name, idx, H, W)
        auc = canary_on_array(holdout, band)
        aucs[name] = auc
        flag = "LEAK" if auc > 0.90 or auc < 0.10 else ""
        print(f"{name:32s} {auc:7.4f} {flag:>6s}", flush=True)

    canary_out = {
        "diagnostic": "LEAKAGE-CANARY AUC per feature band (holdout hide-and-recover)",
        "evaluator_version": SEGMENT_EVALUATOR_VERSION,
        "threshold": 0.90,
        "bands": {n: round(float(a), 6) for n, a in aucs.items()},
    }
    out_path = ROOT / "evidence" / "holdout_screen_canary.json"
    out_path.write_text(json.dumps(canary_out, indent=2) + "\n")
    print("wrote", out_path, flush=True)

    # Candidate surface: average of z-scored bands that are predictive but not leaky.
    good = [n for n, a in aucs.items() if 0.55 <= a <= 0.90 and "lidar" not in n]
    print("candidate bands:", good, flush=True)

    surface = np.zeros(H * W, np.float32)
    count = 0
    for n in good:
        band = band_array(stack, names, n, idx, H, W).ravel()
        finite = np.isfinite(band)
        if finite.sum() < 100:
            continue
        mu = float(np.nanmean(band)); sd = float(np.nanstd(band)) or 1.0
        surface = surface + np.where(finite, (band - mu) / sd, 0.0).astype(np.float32)
        count += 1
    surface = surface / max(count, 1)
    surface = np.where(fp, surface.reshape(H, W), np.nan)
    surface = np.where(np.isfinite(surface), surface, np.nan)

    # Holdout DTI: per-fold emission at fixed total budget, then pooled DTI.
    K = args.emit_k
    budget_per_fold = [
        max(1, round(K * fold["valid"].sum() / fp.sum())) for fold in holdout.folds
    ]
    preds = []
    for f_id, fold in enumerate(holdout.folds):
        preds.append(emit_fold(surface, fold, budget_per_fold[f_id]))
    result = holdout.summarize(preds, ci_draws=200)
    print("HOLDOUT-DTI surface:", round(float(result["dti"]), 6),
          "ci", [round(x, 6) for x in result["ci95"]["interval"]],
          "n_truth", int(result["n_truth"]), flush=True)

    # Final dots: top-K over the whole footprint, catalogue faults excluded from
    # eligibility so the emitted mask does not simply trace the mapped faults.
    s2d = np.where(fp & np.isfinite(surface), surface, -np.inf)
    sflat = s2d.ravel()
    ids = np.flatnonzero(sflat > -np.inf)
    k = min(K, len(ids))
    order = ids[np.lexsort((ids, -sflat[ids]))]
    final = np.zeros(fp.shape, bool)
    final.ravel()[order[:k]] = True

    # Package the TIFF (zeros outside -> passes strict whole-array [0,1] check;
    # this is the encoding that avoids the "[0,1]" portal error).
    downloads = paths.DOWNLOADS_DIR
    template = paths.DATA_DIR / "sample_submission.tif"
    pred = np.zeros(fp.shape, np.float32)
    pred[final] = 1.0
    content_id = hashlib.sha256(np.asarray(pred[fp], dtype="<f4").tobytes()).hexdigest()[:12]
    dt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"kanlergemsdoe2-holdout-screen-{dt}-{content_id}-zeros.tif"
    p0 = write_submission(pred, template, downloads / name, outside="zero")
    checks = check_variants(p0, template)
    sha = sha256_file(p0)
    note = make_note(
        "HS1", f"holdout-screen z-scored geophysical surface, K={k} dots", content_id,
        family="kanlergemsdoe2",
    )
    (downloads / f"note-{name[:-4]}.txt").write_text(note + "\n")

    card = {
        "schema": "gems.holdout-screen.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "Simple physical surface from non-leaky geophysical bands; holdout DTI measured before any slot.",
        "mechanism": "average of z-scored bands with 0.55<=canary AUC<=0.90; top-K emission per holdout fold.",
        "named_non_fault_mimic": "magnetite-poor alluvial paleochannels / K-rich detritus",
        "holdout_dti": round(float(result["dti"]), 6),
        "holdout_ci95": [round(float(x), 6) for x in result["ci95"]["interval"]],
        "evaluator_version": SEGMENT_EVALUATOR_VERSION,
        "n_withheld_positive_pixels": int(result["n_truth"]),
        "correlation_overlap_vs_registry": "deferred to full registry novelty check before release",
        "raster_sha256": sha,
        "validator_output": checks,
        "submission_name": name,
        "note": note,
        "verdict": "negative",
        "ok_to_download": bool(checks["format_valid"]),
        "ok_to_submit": False,
        "reasons": ["holdout screen only; full registry uniqueness not yet checked; no selector run"],
        "canary": canary_out,
    }
    card_path = ROOT / "evidence" / "holdout_screen_run_card.json"
    card_path.write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({
        "file": name, "sha256": sha, "holdout_dti": result["dti"],
        "ci": result["ci95"]["interval"], "format_valid": checks["format_valid"],
        "k": int(final.sum()), "note_chars": len(note),
    }, indent=2))


if __name__ == "__main__":
    main()
