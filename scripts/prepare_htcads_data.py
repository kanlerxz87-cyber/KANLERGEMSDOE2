#!/usr/bin/env python3
"""Prepare cached multi-physics feature stack and run Protocol Rule 4 Leakage Canary (`prepare_data.py`)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout, htcads  # noqa: E402
from gems32.paths import data_dir, evidence_dir, work_dir  # noqa: E402


def main() -> int:
    t0 = time.time()
    ddir = data_dir()
    wdir = work_dir()
    print(f"[prepare_data] Building 58-channel label-free HTCADS + EXT27 stack from {ddir} -> {wdir} ...")
    stack = htcads.build_static_feature_stack(ddir, wdir)
    stack["X_ext"] = htcads.build_ext27_feature_stack(ddir, wdir)
    t_feat = time.time() - t0
    print(f"[prepare_data] Feature stack ready in {t_feat:.1f}s (footprint={int(stack['foot'].sum()):,} px).")

    print("[prepare_data] Loading Hide-and-Recover holdout context & running Rule 4 Leakage Canary on all 62 features...")
    ctx = holdout.load_holdout_context(ddir)
    canary = htcads.run_leakage_canary(stack, ctx)
    canary["elapsed_seconds"] = round(time.time() - t0, 2)

    out_path = evidence_dir() / "leakage_canary.json"
    out_path.write_text(json.dumps(canary, indent=2) + "\n", encoding="utf-8")
    print(
        f"[prepare_data] Leakage Canary {'PASSED' if canary['passed'] else 'FAILED'}: "
        f"tested={canary['total_features_tested']} features, "
        f"max_oriented_AUC={canary['max_single_feature_auc']:.6f} ({canary['max_feature_name']}) <= 0.90"
    )
    if not canary["passed"]:
        raise SystemExit("LEAKAGE CANARY FAILED (AUC > 0.90)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
