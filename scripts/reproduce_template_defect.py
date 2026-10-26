#!/usr/bin/env python3
"""Reproduce a shared evaluator zero-truth fold false-positive pooling defect.

No real data, experiment, or leaderboard score is produced. This diagnostic uses
synthetic arrays solely to test the evaluator's bookkeeping, and deliberately
asserts the observed defect until the upstream tool is repaired.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import sys
from types import SimpleNamespace
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
template = ROOT / ".cache/template32"
sys.path.insert(0, str(template / "src"))
from gems32 import holdout

shape = (8, 8)
foot = np.ones(shape, bool)
cells, masks = [], {}
for seed in (20, 21):
    for fold in range(4):
        key = f"draw{seed}_fold{fold}"
        empty = seed == 20 and fold == 0
        yy = np.array([], int) if empty else np.array([3], int)
        xx = np.array([], int) if empty else np.array([3], int)
        active = np.ones(shape, bool)
        m = np.zeros(shape, bool)
        if empty:
            m[7, 7] = 1  # one false-positive prediction in an empty-truth fold
        elif seed == 20 and fold == 1:
            m[3, 3] = 1  # one exact true-positive in a different fold
        masks[key] = m
        truth_kernel = np.zeros(shape)
        if not empty:
            truth_kernel[3, 3] = 1.0
        cells.append(SimpleNamespace(key=key, bbox=(slice(0, 8), slice(0, 8)), active_sub=active,
                                     d_vis_sub=None, n_truth=len(yy), truth_coords=(yy, xx),
                                     k_dg_sub=truth_kernel))
ctx = SimpleNamespace(foot=foot, cells=cells)
r = holdout.evaluate_hide_and_recover(masks, ctx, grid_n=2, n_boot=20)
fold_fp = sum(x["fp"] for x in r["folds"].values())
pooled_fp = float(r["_block_totals"][1].sum())
result = {"evaluator": holdout.HIDE_RECOVER_EVALUATOR_VERSION,
          "source_sha256": hashlib.sha256((template / "src/gems32/holdout.py").read_bytes()).hexdigest(),
          "kind": "synthetic bookkeeping diagnostic, not a holdout or leaderboard score",
          "empty_truth_cell": "draw20_fold0", "fold_false_positive_mass": fold_fp,
          "pooled_false_positive_mass": pooled_fp, "defect_reproduced": bool(fold_fp > pooled_fp)}
assert result["defect_reproduced"], "Upstream behavior changed: inspect before running experiments"
print(json.dumps(result, indent=2))
