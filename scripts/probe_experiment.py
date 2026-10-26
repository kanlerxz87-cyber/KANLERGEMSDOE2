#!/usr/bin/env python3
"""Run the preregistered H1 *research-only* geology/novelty feasibility probe.

Uses the pinned shared template stack, evaluator and writer. It never calls the
competition or authorizes a submission. A duplicate or canary failure stops the
experiment before output. Inputs are owner mirrors and are not organizer-authenticated.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from scripts.novelty import compare

NOTE = "KANLER H1 signed-field doublets; lattice-constrained research probe; NEGATIVE - DO NOT SUBMIT"
assert len(NOTE) <= 140


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def atomic_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def fields(stack: np.ndarray, foot: np.ndarray, features) -> dict[str, np.ndarray]:
    """Gaussian derivatives of the pre-existing template stack, with safe edge extension."""
    raw_m = np.asarray(stack[:, :, 1], dtype=np.float32)
    m, idx = features._fill_nearest(raw_m, foot)
    raw_g = np.asarray(stack[:, :, 12], dtype=np.float32)
    g, _ = features._fill_nearest(raw_g, foot, foot, idx)
    raw_e = np.asarray(stack[:, :, 11], dtype=np.float32)
    e, _ = features._fill_nearest(raw_e, foot, foot, idx)
    del idx, raw_m, raw_g, raw_e
    out = {}
    for key, arr in (("m", m), ("g", g), ("e", e)):
        out[key + "x"] = ndi.gaussian_filter(arr, 2.0, order=(0, 1), mode="nearest")
        out[key + "y"] = ndi.gaussian_filter(arr, 2.0, order=(1, 0), mode="nearest")
        if key != "e":
            out[key + "xx"] = ndi.gaussian_filter(arr, 2.0, order=(0, 2), mode="nearest")
            out[key + "xy"] = ndi.gaussian_filter(arr, 2.0, order=(1, 1), mode="nearest")
            out[key + "yy"] = ndi.gaussian_filter(arr, 2.0, order=(2, 0), mode="nearest")
    return out


def field_at(f: dict[str, np.ndarray], ys: np.ndarray, xs: np.ndarray) -> dict[str, np.ndarray]:
    """Evaluate fixed signed pair-of-inflection features at selected locations."""
    mx, my = f["mx"][ys, xs].astype(np.float64), f["my"][ys, xs].astype(np.float64)
    gx, gy = f["gx"][ys, xs].astype(np.float64), f["gy"][ys, xs].astype(np.float64)
    mn = np.hypot(mx, my)
    gn = np.hypot(gx, gy)
    nx = np.divide(mx, mn, out=np.zeros_like(mx), where=mn > 1e-12)
    ny = np.divide(my, mn, out=np.zeros_like(my), where=mn > 1e-12)
    coords_l = np.array([ys - 3.0 * ny, xs - 3.0 * nx])
    coords_r = np.array([ys + 3.0 * ny, xs + 3.0 * nx])

    def doublet(prefix: str) -> np.ndarray:
        vals = []
        for coords in (coords_l, coords_r):
            xx = ndi.map_coordinates(f[prefix + "xx"], coords, order=1, mode="nearest", prefilter=False)
            xy = ndi.map_coordinates(f[prefix + "xy"], coords, order=1, mode="nearest", prefilter=False)
            yy = ndi.map_coordinates(f[prefix + "yy"], coords, order=1, mode="nearest", prefilter=False)
            vals.append(nx * nx * xx + 2 * nx * ny * xy + ny * ny * yy)
        product = vals[0] * vals[1]
        return np.maximum(0.0, -product) / (1.0 + np.abs(product))

    mag = doublet("m")
    grav = doublet("g")
    align = np.divide((mx * gx + my * gy) ** 2, (mn * gn) ** 2,
                      out=np.zeros_like(mx), where=(mn > 1e-12) & (gn > 1e-12))
    align = np.clip(align, 0.0, 1.0)
    relief = 1.0 / (1.0 + 0.01 * np.hypot(f["ex"][ys, xs], f["ey"][ys, xs]))
    combined = np.sqrt(mag * grav) * align * relief
    return {"magnetic_doublet": mag, "gravity_doublet": grav,
            "gradient_alignment": align, "relief_factor": relief, "combined": combined}


def leakage_canaries(f: dict[str, np.ndarray], ctx, holes: np.ndarray) -> dict:
    rng = np.random.default_rng(20261026)
    records = {}
    for cell in ctx.cells:
        sy, sx = cell.bbox
        ty, tx = cell.truth_coords
        truth = np.zeros(cell.active_sub.shape, dtype=bool)
        truth[ty, tx] = True
        neg = np.flatnonzero(cell.active_sub & ~truth)
        if len(ty) == 0 or len(neg) == 0:
            raise ValueError(f"Insufficient positive/negative samples in holdout cell {cell.key}")
        neg = rng.choice(neg, size=min(20000, len(neg)), replace=False)
        ny, nx = np.unravel_index(neg, truth.shape)
        ys = np.concatenate((ty, ny)) + int(sy.start)
        xs = np.concatenate((tx, nx)) + int(sx.start)
        y = np.r_[np.ones(len(ty), dtype=np.uint8), np.zeros(len(ny), dtype=np.uint8)]
        vals = field_at(f, ys, xs)
        vals["masked_surface"] = vals["combined"] * holes[ys, xs]
        records[cell.key] = {}
        for name, value in vals.items():
            if not np.isfinite(value).all():
                raise ValueError(f"Non-finite canary values: {name}")
            auc = float(roc_auc_score(y, value))
            records[cell.key][name] = max(auc, 1.0 - auc)
    worst = max((v, c, n) for c, row in records.items() for n, v in row.items())
    return {"method": "two-sided per-feature ROC-AUC per shared holdout cell; 20,000 sampled active non-truth cells max per cell",
            "seed": 20261026, "threshold": 0.9, "worst_auc": worst[0],
            "worst_cell": worst[1], "worst_feature": worst[2],
            "passed": worst[0] <= 0.9, "cells": records}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--template", type=Path, default=ROOT / ".cache/template32")
    ap.add_argument("--data", type=Path, default=ROOT / ".cache/audit/core")
    ap.add_argument("--stack", type=Path, default=ROOT / ".cache/audit/work/feature_stack.npy")
    ap.add_argument("--registry", type=Path, default=ROOT / ".cache/audit/verified-registry.json")
    args = ap.parse_args()
    existing = ROOT / "docs/data/run-card.json"
    if existing.exists():
        prior = json.loads(existing.read_text())
        if str(prior.get("stop_reason", "")).startswith("DUPLICATE_LANE"):
            raise SystemExit("This lane already hit a duplicate stop. Do not rerun or retune it.")
    start = time.monotonic()
    start_utc = now()
    if not (ROOT / "knowledge/01_preregistration_2026-10-26.md").exists():
        raise SystemExit("Missing preregistration")
    sys.path[:0] = [str(args.template / "src"), str(args.template / "scripts")]
    from gems32 import features, holdout
    import submission_writer

    registry = json.loads(args.registry.read_text())
    sample = args.data / "sample_submission.tif"
    lab = args.data / "labels.tif"
    lattice = ROOT / ".cache/audit/lattice.tif"
    with rasterio.open(sample) as ds:
        foot = np.isfinite(ds.read(1))
        grid = (ds.shape, ds.crs, ds.transform)
    with rasterio.open(lattice) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid:
            raise ValueError("Lattice/template grid mismatch")
        a = ds.read(1)
        lattice_mask = np.isfinite(a) & (a > 0) & foot
    check = np.zeros(foot.shape, dtype=bool)
    check[::5, ::5] = True
    check &= foot
    if not np.array_equal(lattice_mask, check):
        raise ValueError("Lattice is not the registered fault-blind geometric grid")
    holes = foot & (ndi.distance_transform_edt(~lattice_mask) > 3.0)
    del check, a
    stack = np.load(args.stack, mmap_mode="r")
    if stack.shape != (*foot.shape, 35):
        raise ValueError("Unexpected shared template feature stack")
    f = fields(stack, foot, features)
    del stack
    ctx = holdout.load_holdout_context(args.data)
    if any(cell.n_truth <= 0 for cell in ctx.cells):
        raise RuntimeError("Shared evaluator has an uncorrected empty-truth-fold FP pooling defect; aborting")
    canary = leakage_canaries(f, ctx, holes)
    print("canary:", canary["worst_auc"], canary["worst_cell"], canary["worst_feature"], flush=True)
    card = {"hypothesis": "H1 signed paired magnetic and gravity inflections in subdued terrain",
            "mechanism": "Fixed-scale cross-profile potential-field doublets; support restricted to calibration-lattice gaps for literal novelty",
            "named_non_fault_mimic": "Lithological contacts and edge-of-survey interpolation artifacts",
            "started_utc": start_utc, "evaluator_version": holdout.HIDE_RECOVER_EVALUATOR_VERSION,
            "leakage_canary": canary, "holdout_dti": None, "correlation_overlap_vs_registry": None,
            "raster_sha256": None, "validator_output": None, "submission_name": None,
            "submission_note": NOTE, "verdict": "negative", "ok_to_submit": False,
            "slots_used": 0, "experiment_count": 1,
            "limitations": ["Mirror inputs are hash-pinned but not organizer-authenticated",
                            "Lattice-gap support is an artificial spatial constraint, not a geological prior",
                            "Public frozen registry cannot cover private or future submissions",
                            "No assigned method lane was identified in the supplied prompt"]}
    if not canary["passed"]:
        card["stop_reason"] = "LEAKAGE_CANARY_FAIL"
        atomic_json(ROOT / "docs/data/run-card.json", card)
        return 0
    ys, xs = np.nonzero(holes)
    v = field_at(f, ys, xs)["combined"]
    surface = np.zeros(foot.shape, dtype=np.float32)
    surface[ys, xs] = v.astype(np.float32)
    if not np.any(surface > 0):
        card["stop_reason"] = "EMPTY_SURFACE"
        atomic_json(ROOT / "docs/data/run-card.json", card)
        return 0
    pre = compare(surface, foot, sample, registry, args.template, stage="pre-placement surface")
    atomic_json(ROOT / "evidence/novelty_surface.json", pre)
    print("surface novelty:", pre["passed"], pre.get("max_overlap"), pre.get("max_abs_spearman"), flush=True)
    if not pre["passed"]:
        card["correlation_overlap_vs_registry"] = {"surface": {k: v for k, v in pre.items() if k != "rows"}, "surface_audit": "../../evidence/novelty_surface.json", "final": None}
        card["stop_reason"] = "DUPLICATE_LANE_SURFACE"
        atomic_json(ROOT / "docs/data/run-card.json", card)
        return 0
    order = np.lexsort((xs, ys, -v))
    good = order[v[order] > 0][:4000]
    raw = np.zeros(foot.shape, dtype=bool)
    raw[ys[good], xs[good]] = True
    # Release mask uses the full known catalogue only at inference, never to build
    # the holdout mask or geological features.
    release = raw & ~ctx.labels
    final = compare(release.astype(np.float32), foot, sample, registry, args.template, stage="final dots")
    atomic_json(ROOT / "evidence/novelty_final.json", final)
    print("final novelty:", final["passed"], final.get("max_overlap"), final.get("max_abs_spearman"), flush=True)
    if not final["passed"]:
        card["correlation_overlap_vs_registry"] = {"surface": {k: v for k, v in pre.items() if k != "rows"}, "final": {k: v for k, v in final.items() if k != "rows"}, "surface_audit": "../../evidence/novelty_surface.json", "final_audit": "../../evidence/novelty_final.json"}
        card["stop_reason"] = "DUPLICATE_LANE_FINAL"
        atomic_json(ROOT / "docs/data/run-card.json", card)
        return 0
    # The pre-registered surface is label-free and the shared evaluator masks each
    # split's visible faults. Do not substitute `release` (which used all labels).
    result = holdout.evaluate_hide_and_recover(raw, ctx, b_visible_px=0.0, name="KANLER-H1-boundary-gap")
    result = {k: v for k, v in result.items() if not k.startswith("_")}
    card["holdout_dti"] = result
    print("holdout:", result["pooled_dti"], result["ci95_cluster_bootstrap"], result["n_withheld_positives"], flush=True)
    if time.monotonic() - start > 2 * 60 * 60:
        card["stop_reason"] = "TWO_HOUR_BUDGET_EXCEEDED"
        atomic_json(ROOT / "docs/data/run-card.json", card)
        return 0
    meta = {"candidate_id": "KANLER-H1-BOUNDARY-GAP", "description": "Signed multiphysics doublet, lattice-gap research-only negative probe",
            "submission_note_zeros": NOTE, "submission_note_nan": NOTE, "slot_decision": "HOLD-DO-NOT-SUBMIT"}
    bundle = submission_writer.write_validated_submission(release, "kanler-h1-boundary-gap", meta,
                                                           ddir=args.data, out_dir=ROOT / "docs/downloads")
    card["correlation_overlap_vs_registry"] = {
        "scope": registry["scope"],
        "surface": {k: v for k, v in pre.items() if k != "rows"},
        "final": {k: v for k, v in final.items() if k != "rows"}}
    card["raster_filename"] = bundle["nan_tif"]["filename"]
    card["raster_sha256"] = bundle["nan_tif"]["sha256"]
    card["all_finite_research_filename"] = bundle["zeros_tif"]["filename"]
    card["all_finite_research_sha256"] = bundle["zeros_tif"]["sha256"]
    card["validator_output"] = {"nan_outside": bundle["nan_tif"], "zero_outside": bundle["zeros_tif"],
        "caveat": "Local template checks only; zero-outside differs from the written null/NaN-outside specification and neither variant has a portal receipt."}
    card["submission_name"] = "KANLER-H1-BOUNDARY-GAP-" + bundle["nan_tif"]["sha256"][:12].upper()
    card["stop_reason"] = "RESEARCH_ONLY_NO_SELECTOR_APPROVAL"
    card["elapsed_seconds"] = round(time.monotonic() - start, 2)
    atomic_json(ROOT / "docs/data/run-card.json", card)
    print("Wrote research-only output:", card["raster_filename"], card["raster_sha256"], flush=True)
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
