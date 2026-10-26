#!/usr/bin/env python3
"""Guarded CLI for the single shared SegmentHoldout evaluator (no private metric).

The CLI consumes already constructed independent fold predictions. It cannot
establish from arrays alone that a model or a catalogue-derived feature was
trained using only fold.visible. Its outputs are diagnostics, not promotion.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.holdout import SegmentHoldout  # noqa: E402
if __package__:
    from .registry_guard import require_candidate_generation_allowed
    from .restore_competition_data import sha256_file
else:
    from registry_guard import require_candidate_generation_allowed
    from restore_competition_data import sha256_file

LABELS_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"


def load_predictions(directory: Path, count: int):
    return [np.load(directory / f"fold{index}.npy", allow_pickle=False) for index in range(count)]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--predictions", type=Path, required=True, help="directory of fold0.npy ... fold3.npy")
    p.add_argument("--baseline", type=Path, required=True, help="same-fold baseline predictions")
    p.add_argument("--baseline-id", required=True)
    p.add_argument("--features", type=Path, required=True, help="JSON list of label-free feature paths and SHA-256 hashes")
    p.add_argument("--data-dir", type=Path, default=ROOT / "data")
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    require_candidate_generation_allowed(args.data_dir)
    if not args.baseline_id.strip():
        raise ValueError("A frozen baseline identity is required")
    labels_path = args.data_dir / "labels.tif"
    if sha256_file(labels_path) != LABELS_SHA:
        raise ValueError("Labels hash mismatch")
    with rasterio.open(args.data_dir / "sample_submission.tif") as sample, rasterio.open(labels_path) as labels:
        if (sample.shape, sample.crs, sample.transform) != (labels.shape, labels.crs, labels.transform) or labels.count != 1:
            raise ValueError("Labels and sample grids differ")
        foot = np.isfinite(sample.read(1))
        truth = labels.read(1) > 0
    context = SegmentHoldout(foot, truth, buffer_px=15)
    specs = json.loads(args.features.read_text())
    if not isinstance(specs, list) or not specs:
        raise ValueError("Every actual model feature needs a canary specification")
    features = {}
    for spec in specs:
        # A global static array may be used only for genuinely catalogue-independent
        # features. Catalogue-derived features require fold-local canaries and are
        # intentionally rejected here rather than accidentally tested globally.
        if spec.get("label_free") is not True or not spec.get("name") or spec["name"] in features:
            raise ValueError("Features must have distinct names and explicitly be label-free")
        path = Path(spec["path"])
        if sha256_file(path) != spec.get("sha256"):
            raise ValueError(f"Feature hash mismatch: {path}")
        features[spec["name"]] = np.load(path, mmap_mode="r", allow_pickle=False)
    canaries = context.canary(features)
    output = {"canaries": canaries, "authorized_to_submit": False,
              "provenance_warning": "CLI cannot independently certify fold-local model construction or complete registry coverage."}
    if canaries["passed"]:
        candidate = load_predictions(args.predictions, len(context.folds))
        baseline = load_predictions(args.baseline, len(context.folds))
        output["holdout"] = context.summarize(candidate)
        output["baseline"] = {"id": args.baseline_id, **context.summarize(baseline)}
        output["paired_comparison"] = context.compare_paired(candidate, baseline)
    else:
        output["stop"] = "At least one feature-alone AUC exceeded 0.90; no holdout score calculated."
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    if not canaries["passed"]:
        raise SystemExit(1)
    print(json.dumps(output, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
