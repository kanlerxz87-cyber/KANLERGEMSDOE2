#!/usr/bin/env python3
"""Evaluate four *fold-specific* masks with the pinned shared SegmentHoldout.

This is a scoring adapter, not a model trainer. It cannot prove how predictions
were constructed: a globally trained raster must NOT be presented as OOF evidence.
The resulting evidence alone never authorizes a competition submission.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.holdout import SegmentHoldout  # noqa: E402
from validate_raster import sha256_file  # noqa: E402


def load_masks(path: Path, n: int) -> list[np.ndarray]:
    with np.load(path, allow_pickle=False) as archive:
        expected = {f"fold_{i}" for i in range(n)}
        if set(archive.files) != expected:
            raise ValueError(f"Expected exactly {sorted(expected)} in {path}")
        return [np.asarray(archive[f"fold_{i}"]) for i in range(n)]


def evaluate(sample: Path, labels: Path, predictions: Path, features: Path, *,
             buffer_px: int = 15, baseline: Path | None = None, ci_draws: int = 1999) -> dict:
    with rasterio.open(sample) as t, rasterio.open(labels) as ds:
        if t.count != 1 or ds.count != 1 or (t.shape, t.crs, t.transform) != (ds.shape, ds.crs, ds.transform):
            raise ValueError("Sample and label grids must match and be single-band")
        if (t.crs is None or t.crs.to_epsg() != 32611
                or (t.transform.a, t.transform.b, t.transform.d, t.transform.e) != (100, 0, 0, -100)):
            raise ValueError("The shared 300 m evaluator requires an EPSG:32611 100 m grid")
        if len(t.files) != 1 or len(ds.files) != 1:
            raise ValueError("Template and catalogue must not rely on external sidecars")
        footprint = np.isfinite(t.read(1)) & (t.read_masks(1) > 0)
        label_values = ds.read(1)
        if not footprint.any() or not np.isin(label_values[footprint], [0, 1]).all() or np.any(ds.read_masks(1)[footprint] == 0):
            raise ValueError("Catalogue must be unmasked and binary throughout a nonempty footprint")
        truth = (label_values > 0) & footprint
    ctx = SegmentHoldout(footprint, truth, buffer_px=buffer_px)
    with np.load(features, allow_pickle=False) as archive:
        if not archive.files:
            raise ValueError("At least one actual static feature is required for the holdout canary")
        feature_arrays = {name: np.asarray(archive[name]) for name in archive.files}
    canary = ctx.canary(feature_arrays)
    # The canary is a warning screen, never proof of no leakage. Stop before
    # scoring if any one-feature AUC is above the threshold or missing.
    if set(canary.get("features", {})) != set(feature_arrays) or canary.get("two_polarities_checked") is not True:
        raise ValueError("Incomplete shared canary results; cannot continue")
    aucs = []
    for row in canary["features"].values():
        if len(row.get("folds", [])) != len(ctx.folds):
            raise ValueError("Canary must report every held-out fold")
        for value in [row.get("pooled_auc"), *(x.get("auc") for x in row["folds"])]:
            if not isinstance(value, (int, float)) or not np.isfinite(value) or not 0 <= value <= 1:
                raise ValueError("Canary AUC is missing or invalid")
            aucs.append(max(value, 1 - value))
    canary["max_two_polarity_auc"] = max(aucs)
    if canary.get("passed") is not True or canary["max_two_polarity_auc"] > 0.90:
        return {"status": "stopped_leakage_canary", "canary": canary, "holdout": None,
                "eligible_for_selector": False}
    masks = load_masks(predictions, len(ctx.folds))
    result = ctx.summarize(masks, ci_draws=ci_draws)
    paired = None
    if baseline is not None:
        paired = ctx.compare_paired(masks, load_masks(baseline, len(ctx.folds)), ci_draws=ci_draws)
    return {
        "status": "diagnostic_only",
        "holdout": result,
        "paired_baseline": paired,
        "canary": canary,
        "input_sha256": {"sample": sha256_file(sample), "labels": sha256_file(labels),
                         "fold_predictions": sha256_file(predictions), "static_features": sha256_file(features),
                         "baseline": sha256_file(baseline) if baseline else None},
        "provenance_warning": "Adapter cannot verify model training or catalogue-derived features; fold-visible-only construction must be independently evidenced. Static feature arrays only; fold-specific catalogue features need a compatible shared canary.",
        "eligible_for_selector": False,
    }


def main() -> None:
    if len(sys.argv) == 1:
        print("BLOCKED: explicit independent fold predictions and feature canaries are required; no legacy run is authorized", file=sys.stderr)
        raise SystemExit(2)
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--sample", type=Path, default=ROOT / "data/sample_submission.tif")
    p.add_argument("--labels", type=Path, default=ROOT / "data/labels.tif")
    p.add_argument("--predictions", type=Path, required=True)
    p.add_argument("--features", type=Path, required=True)
    p.add_argument("--baseline", type=Path)
    p.add_argument("--buffer-px", type=int, default=15)
    p.add_argument("--ci-draws", type=int, default=1999)
    p.add_argument("--out", type=Path, required=True)
    a = p.parse_args()
    result = evaluate(a.sample, a.labels, a.predictions, a.features, buffer_px=a.buffer_px,
                      baseline=a.baseline, ci_draws=a.ci_draws)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"status": result["status"], "eligible_for_selector": False}, indent=2))
    if result["status"] != "diagnostic_only":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
