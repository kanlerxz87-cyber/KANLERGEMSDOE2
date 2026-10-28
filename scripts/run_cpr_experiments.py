#!/usr/bin/env python3
"""ARCHIVED / DISABLED: historical claims and gates are not current authorization.

KG2-CPR lane: Credit-Priced Regression — 3 pre-registered experiments (registry/preregistration_cpr.json).

CPR-1: soft DTI-credit regression target y=k(d) (official 300 m triangular kernel) +
       rank-product fusion (regressor x physical conduit x LiDAR specialist) +
       directional tip regressor, CELF at fixed 37,654 dots.
CPR-2: CPR-1 surface + OOF-priced dot budget (CELF prefix curve on hide-and-recover cells).
CPR-3: CPR-2 + 1-px crest snapping of the CELF order.

Reuses the shared template exactly (Protocol Rule 2): cached feature stack
(src/gems32/htcads.py), leak-free hide-and-recover evaluator (src/gems32/holdout.py),
CELF allocator with greedy-order recording, and the audited submission writer
(src/gems32/submission.py). Every metric is labeled HOLDOUT-DTI / ORGANIZER-CONFIRMED.
"""
from __future__ import annotations

import gc
import importlib.util
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout, htcads, submission  # noqa: E402
from gems32.metric import kernel  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402

# Reuse HTCADS physical-conduit builder + registry helpers from the shared experiment script.
_spec = importlib.util.spec_from_file_location("htcads_run", ROOT / "scripts" / "run_htcads_experiments.py")
htcads_run = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(htcads_run)  # type: ignore[union-attr]

SEED = 20261026  # same bootstrap seed as prior sessions -> paired deltas vs recorded references
BUDGETS = [18000, 24000, 30000, 34000, 37654, 42000, 46000]
MAX_DOTS = max(BUDGETS)
PRIOR_REPO_BEST_HR = 0.112353  # HTCADS EXP-2, HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0), evidence/htcads_experiments.json


def _rank01(v: np.ndarray) -> np.ndarray:
    r = rankdata(v, method="average").astype(np.float64)
    return (r / max(r.size, 1)).astype(np.float32)


def _predict_reg(model: lgb.LGBMRegressor, X: np.ndarray, cols: list[int], chunk: int = 1_100_000) -> np.ndarray:
    out = np.empty(X.shape[0], dtype=np.float32)
    for s in range(0, X.shape[0], chunk):
        e = min(s + chunk, X.shape[0])
        out[s:e] = model.predict(np.asarray(X[s:e, cols], dtype=np.float32)).astype(np.float32)
    return out


def _snap_order(order: np.ndarray, pi_2d: np.ndarray, elig_2d: np.ndarray) -> np.ndarray:
    """H-C3: relocate each ordered dot to the argmax-pi eligible pixel within Chebyshev 1."""
    H, W = pi_2d.shape
    taken = np.zeros(H * W, dtype=bool)
    snapped: list[int] = []
    elig_flat = elig_2d.ravel()
    pi_flat = pi_2d.ravel()
    for fidx in order:
        r, c = divmod(int(fidx), W)
        best, best_v = int(fidx), float(pi_flat[fidx]) if elig_flat[fidx] and not taken[fidx] else -1.0
        for dy in (-1, 0, 1):
            rr = r + dy
            if rr < 0 or rr >= H:
                continue
            base = rr * W
            for dx in (-1, 0, 1):
                cc = c + dx
                if cc < 0 or cc >= W:
                    continue
                j = base + cc
                if elig_flat[j] and not taken[j] and float(pi_flat[j]) > best_v:
                    best, best_v = j, float(pi_flat[j])
        if best_v < 0.0:
            continue  # original and all neighbours taken/ineligible: drop (coverage already served)
        taken[best] = True
        snapped.append(best)
    return np.asarray(snapped, dtype=np.int64)


def _mask_from_order(order: np.ndarray, n: int, shape: tuple[int, int]) -> np.ndarray:
    m = np.zeros(shape[0] * shape[1], dtype=bool)
    m[order[:n]] = True
    return m.reshape(shape)


def _collect_registry(foot: np.ndarray, ddir: Path) -> tuple[list[dict], np.ndarray, set[str]]:
    """Registry = restored scored + scored_extra (focus-9 champions) + every docs/downloads TIF."""
    import glob
    import hashlib

    cand = sorted(set(
        glob.glob(str(ddir / "scored" / "*.tif"))
        + glob.glob(str(ddir / "scored_extra" / "*.tif"))
        + glob.glob(str(ROOT / "docs" / "downloads" / "*.tif"))
    ))
    H, W = foot.shape
    n_fp = int(foot.sum())
    rng = np.random.default_rng(20261026)
    sample_idx = np.sort(rng.choice(n_fp, size=80_000, replace=False))
    fy_all, fx_all = np.nonzero(foot)
    fy_cov, fx_cov = fy_all[sample_idx] + 3, fx_all[sample_idx] + 3
    del fy_all, fx_all
    scratch = np.zeros((H + 6, W + 6), dtype=bool)
    seen: dict[str, str] = {}
    shas: set[str] = set()
    records: list[dict] = []
    for p_str in cand:
        p = Path(p_str)
        try:
            shas.add(submission.sha256_file(p))
            with rasterio.open(p) as ds:
                if (ds.height, ds.width) != (H, W):
                    continue
                arr = ds.read(1)
        except Exception:
            continue
        af = np.where(np.isfinite(arr[foot]), arr[foot], 0.0).astype(np.float32)
        h_fp = hashlib.sha256(np.round(af, 5).tobytes()).hexdigest()[:16]
        if h_fp in seen:
            continue
        seen[h_fp] = p.name
        m_dots = foot & np.isfinite(arr) & (arr >= 0.5)
        ry, rx = np.nonzero(m_dots)
        cov3 = 0.0
        if ry.size:
            scratch[ry + 3, rx + 3] = True
            hit = np.zeros(sample_idx.size, dtype=bool)
            for dy, dx in htcads_run._D3_OFFS:
                hit |= scratch[fy_cov + dy, fx_cov + dx]
            cov3 = float(hit.mean())
            scratch[ry + 3, rx + 3] = False
        records.append({
            "name": p.name,
            "path": str(p),
            "is_continuous": int(np.sum((af > 1e-5) & (af < 1.0 - 1e-5))) > 1000,
            "is_calibration_lattice": bool(cov3 > 0.50 or "lattice-s5" in p.name),
            "n_dots": int(ry.size),
            "cov3_of_footprint": round(cov3, 5),
            "unit_rank": htcads_run._unit_rank_vec(af[sample_idx]),
            "ry": ry.astype(np.int16) if ry.size else None,
            "rx": rx.astype(np.int16) if ry.size else None,
        })
    return records, sample_idx, shas


def main() -> int:
    raise SystemExit(
        "Archived lane disabled; Archived runner disabled: the literal all-registry witness forces a duplicate "
        "at the frozen budget; fresh authorization and a safe replay path are required."
    )


def _legacy_main_archived() -> int:
    """Historical implementation retained for audit; not a safe execution path."""
    t_start = time.time()
    ddir, wdir, edir = data_dir(), work_dir(), evidence_dir()

    canary = json.loads((edir / "leakage_canary.json").read_text(encoding="utf-8"))
    if not canary.get("passed"):
        raise SystemExit("Leakage canary not passed — run scripts/prepare_htcads_data.py first.")
    print(f"[CPR] Rule 4 canary PASSED (max AUC {canary['max_single_feature_auc']:.4f}, {canary['max_feature_name']})", flush=True)

    stack = htcads.build_static_feature_stack(ddir, wdir)
    foot, X_sub, X_lid = stack["foot"], stack["X_sub"], stack["X_lid"]
    lidar_valid_fp = stack["lidar_valid_fp"]
    n_fp = int(foot.sum())
    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(n_fp, dtype=np.int32)

    ctx = holdout.load_holdout_context(ddir)
    sharp_cols = [i for i in range(len(htcads.SUBSURF_FEATURE_NAMES)) if i not in htcads_run._REGIONAL_BLOB_COLS]
    _, phys_fp = htcads_run._build_physical_conduit_scores(X_sub, X_lid, lidar_valid_fp)

    # ---------- Reference: 0.2778 champion on identical evaluators ----------
    d28_path = ddir / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
    with rasterio.open(d28_path) as ds:
        a = ds.read(1)
    d28_mask = foot & np.isfinite(a) & (a >= 0.5)
    del a
    b2_path = ddir / "scored_extra" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    with rasterio.open(b2_path) as ds:
        a = ds.read(1)
    b2_mask = foot & np.isfinite(a) & (a >= 0.5)
    del a
    ref_hr = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, n_boot=1000, seed=SEED, name="GEMSDOE32_B2_ref")
    ref_sg = holdout.evaluate_sgmc_with_ci(b2_mask, ctx, n_boot=1000, seed=SEED, name="GEMSDOE32_B2_ref")
    print(f"[CPR] REF 0.2778 champion: HR={ref_hr['pooled_dti']:.6f} CI{ref_hr['ci95_cluster_bootstrap']} SGMC-CAL={ref_sg['sgmc_prevalence_calibrated_dti']:.6f} (dots={int(b2_mask.sum())})", flush=True)
    del d28_mask, b2_mask

    # ---------- STEP 1: quadrant-OOF soft-credit regressors (blind + LiDAR) ----------
    rng = np.random.default_rng(20261027)
    reg_blind_oof = np.zeros(n_fp, dtype=np.float32)
    reg_blind_full = np.zeros(n_fp, dtype=np.float32)
    reg_lid_oof = np.zeros(n_fp, dtype=np.float32)
    reg_lid_full = np.zeros(n_fp, dtype=np.float32)
    blind_imp = np.zeros(len(sharp_cols), dtype=np.float64)
    lid_imp = np.zeros(X_lid.shape[1], dtype=np.float64)
    lidar_valid_2d = np.zeros(foot.shape, dtype=bool)
    lidar_valid_2d[foot] = lidar_valid_fp

    for fold in holdout.FOLDS:
        t0 = time.time()
        collar = binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar
        train_labels = ctx.labels & tdom
        y_soft_2d = kernel(distance_transform_edt(~train_labels)).astype(np.float32)  # H-C1 target
        y_fp = y_soft_2d[foot]
        tdom_fp = tdom[foot]
        q_fp = fp_idx_2d[(ctx.quad == fold) & foot]

        pos_idx = np.flatnonzero(tdom_fp & (y_fp > 0))
        neg_idx = np.flatnonzero(tdom_fp & (y_fp <= 0))
        if pos_idx.size > 260_000:
            pos_idx = rng.choice(pos_idx, 260_000, replace=False)
        neg_sub = rng.choice(neg_idx, min(neg_idx.size, pos_idx.size * 2), replace=False)
        tr = np.concatenate([pos_idx, neg_sub])
        reg = lgb.LGBMRegressor(n_estimators=170, learning_rate=0.06, num_leaves=31, min_child_samples=100,
                                subsample=0.8, subsample_freq=1, colsample_bytree=0.75, reg_alpha=1.0,
                                reg_lambda=5.0, random_state=700 + fold, n_jobs=4, verbose=-1)
        reg.fit(np.asarray(X_sub[tr][:, sharp_cols], dtype=np.float32), y_fp[tr])
        blind_imp += reg.feature_importances_
        pred = _predict_reg(reg, X_sub, sharp_cols)
        reg_blind_oof[q_fp] = pred[q_fp]
        reg_blind_full += 0.25 * pred
        del reg, pred

        tr_lid = tr[lidar_valid_fp[tr]]
        regl = lgb.LGBMRegressor(n_estimators=140, learning_rate=0.06, num_leaves=23, min_child_samples=80,
                                 subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=1.0,
                                 reg_lambda=5.0, random_state=800 + fold, n_jobs=4, verbose=-1)
        regl.fit(np.asarray(X_lid[tr_lid], dtype=np.float32), y_fp[tr_lid])
        lid_imp += regl.feature_importances_
        lid_cols = list(range(X_lid.shape[1]))
        pred_l = _predict_reg(regl, X_lid, lid_cols)
        reg_lid_oof[q_fp] = pred_l[q_fp]
        reg_lid_full += 0.25 * pred_l
        del regl, pred_l, y_soft_2d, y_fp
        gc.collect()
        print(f"[CPR] Fold {fold} soft-credit regressors done in {time.time()-t0:.1f}s", flush=True)

    def _fuse(reg_b: np.ndarray, reg_l: np.ndarray) -> np.ndarray:
        """Rank-product fusion: blind regressor^0.5 x physical conduit^0.3 x LiDAR regressor^0.2."""
        rb = _rank01(np.maximum(reg_b, 0.0))
        rp = _rank01(phys_fp)
        rl = np.full(n_fp, 0.5, dtype=np.float32)
        lv = lidar_valid_fp
        rl[lv] = _rank01(np.maximum(reg_l[lv], 0.0))
        fused = (rb ** 0.5) * (rp ** 0.3) * (rl ** 0.2)
        scale = 0.045 / (float(np.percentile(fused, 99.2)) + 1e-9)
        return np.clip(fused * scale, 0.0, 0.12).astype(np.float32)

    pi_blind_oof = _fuse(reg_blind_oof, reg_lid_oof)
    pi_blind_full = _fuse(reg_blind_full, reg_lid_full)
    del reg_blind_oof, reg_blind_full, reg_lid_oof, reg_lid_full
    gc.collect()

    # ---------- STEP 2: directional tip regressor per cell + CELF orders ----------
    X_vis_full_cat, aux_full = htcads.compute_visible_catalogue_features(ctx.labels, foot)
    X_vis_full_dir = X_vis_full_cat[:, [1, 2]].copy()
    tip_env_full = (np.clip(np.maximum(X_vis_full_dir[:, 0], X_vis_full_dir[:, 1]), 0, 1) ** 0.65).astype(np.float32)
    d_full_2d = aux_full["d_vis"]
    elig_live = foot & (d_full_2d > 2.0)
    del X_vis_full_cat, aux_full

    def _to_2d(v: np.ndarray) -> np.ndarray:
        g = np.zeros(foot.shape, dtype=np.float32)
        g[foot] = v
        return g

    p_tip_live = np.zeros(n_fp, dtype=np.float32)
    cell_orders: dict[str, np.ndarray] = {}
    cell_orders_snapped: dict[str, np.ndarray] = {}
    cell_bboxes = {c.key: c.bbox for c in ctx.cells}
    n_live_tip_models = 0

    for idx_c, cell in enumerate(ctx.cells):
        t0 = time.time()
        collar = binary_dilation(ctx.quad == cell.fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar
        X_vis_cell, aux_cell = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
        X_vis_dir = X_vis_cell[:, [1, 2]].copy()
        del X_vis_cell
        tip_env = (np.clip(np.maximum(X_vis_dir[:, 0], X_vis_dir[:, 1]), 0, 1) ** 0.65).astype(np.float32)
        d_vis_2d = aux_cell["d_vis"]
        elig_c = foot & (d_vis_2d > 2.0)
        del aux_cell

        hid_core = (ctx.labels & tdom) & ~cell.visible_full
        y_tip_2d = kernel(distance_transform_edt(~hid_core)).astype(np.float32)
        zone_2d = tdom & (d_vis_2d > 1.4)
        zone_fp = zone_2d[foot] & (tip_env > 0.02)
        y_tip_fp = y_tip_2d[foot]
        pos = np.flatnonzero(zone_fp & (y_tip_fp > 0))
        neg = np.flatnonzero(zone_fp & (y_tip_fp <= 0))
        neg_sub = rng.choice(neg, min(neg.size, max(pos.size * 5, 1000)), replace=False)
        tr = np.concatenate([pos, neg_sub])
        regt = lgb.LGBMRegressor(n_estimators=130, learning_rate=0.06, num_leaves=23, min_child_samples=60,
                                 subsample=0.8, subsample_freq=1, colsample_bytree=0.8, reg_alpha=1.0,
                                 reg_lambda=5.0, random_state=900 + idx_c, n_jobs=4, verbose=-1)
        regt.fit(np.hstack([np.asarray(X_sub[tr][:, sharp_cols], dtype=np.float32), X_vis_dir[tr]]), y_tip_fp[tr])

        nz = np.flatnonzero(tip_env > 0.02)
        raw = regt.predict(np.hstack([np.asarray(X_sub[nz][:, sharp_cols], dtype=np.float32), X_vis_dir[nz]])).astype(np.float32)
        raw = np.maximum(raw, 0.0)
        p99 = float(np.percentile(raw, 99.2)) + 1e-9
        pi_tip = np.zeros(n_fp, dtype=np.float32)
        pi_tip[nz] = np.clip(0.045 * (raw / p99) * tip_env[nz], 0.0, 0.05)

        if cell.seed == 20:
            nz_live = np.flatnonzero(tip_env_full > 0.02)
            raw_lv = regt.predict(np.hstack([np.asarray(X_sub[nz_live][:, sharp_cols], dtype=np.float32), X_vis_full_dir[nz_live]])).astype(np.float32)
            raw_lv = np.maximum(raw_lv, 0.0)
            p_tip_live[nz_live] += 0.25 * np.clip(0.045 * (raw_lv / p99) * tip_env_full[nz_live], 0.0, 0.05)
            n_live_tip_models += 1
            del raw_lv
        del regt, raw, y_tip_2d, y_tip_fp, X_vis_dir, tip_env, hid_core

        pi_cell_2d = _to_2d(1.0 - (1.0 - pi_tip) * (1.0 - pi_blind_oof))
        del pi_tip
        _, order = htcads.emit_submodular_celf(pi_cell_2d, elig_c, max_dots=MAX_DOTS, marginal_bar=0.0, return_order=True)
        cell_orders[cell.key] = order
        cell_orders_snapped[cell.key] = _snap_order(order, pi_cell_2d, elig_c)
        del pi_cell_2d, elig_c, d_vis_2d
        gc.collect()
        print(f"[CPR] Cell {cell.key}: tip regressor + CELF order ({order.size} dots) + snap in {time.time()-t0:.1f}s", flush=True)

    # ---------- STEP 3: evaluate budget curves (CPR-1/2) and snapping (CPR-3) ----------
    def _cells_from_orders(orders: dict[str, np.ndarray], n: int) -> dict[str, np.ndarray]:
        return {k: _mask_from_order(o, n, foot.shape)[cell_bboxes[k]].copy() for k, o in orders.items()}

    def _eval_hr(cells: dict, name: str) -> dict:
        ev = holdout.evaluate_hide_and_recover(cells, ctx, b_visible_px=0.0, n_boot=1000, seed=SEED, name=name)
        d_ref = holdout.paired_bootstrap_delta(ev, ref_hr, boot_key="_boots")
        return {"ev": ev, "d_ref": d_ref}

    curve: list[dict] = []
    hr_by_variant: dict[str, dict] = {}
    for b in BUDGETS:
        r = _eval_hr(_cells_from_orders(cell_orders, b), f"CPR_budget{b}")
        hr_by_variant[f"raw@{b}"] = r
        curve.append({"budget": b, "pooled_dti": round(r["ev"]["pooled_dti"], 6),
                      "ci95": [round(r["ev"]["ci95_cluster_bootstrap"][0], 6), round(r["ev"]["ci95_cluster_bootstrap"][1], 6)]})
        print(f"[CPR] budget {b}: HR={r['ev']['pooled_dti']:.6f} delta_vs_ref={r['d_ref']['delta']:+.6f} CI[{r['d_ref']['ci95'][0]:+.5f},{r['d_ref']['ci95'][1]:+.5f}]", flush=True)

    n_star = max(curve, key=lambda d: d["pooled_dti"])["budget"]
    snap_curve: list[dict] = []
    for b in sorted({37654, n_star}):
        r = _eval_hr(_cells_from_orders(cell_orders_snapped, b), f"CPR_snap{b}")
        hr_by_variant[f"snap@{b}"] = r
        d_ctrl = holdout.paired_bootstrap_delta(r["ev"], hr_by_variant[f"raw@{b}"]["ev"], boot_key="_boots")
        snap_curve.append({"budget": b, "pooled_dti": round(r["ev"]["pooled_dti"], 6),
                           "ci95": [round(r["ev"]["ci95_cluster_bootstrap"][0], 6), round(r["ev"]["ci95_cluster_bootstrap"][1], 6)],
                           "paired_delta_vs_unsnapped_same_budget": round(d_ctrl["delta"], 6),
                           "paired_delta_vs_unsnapped_ci95": [round(d_ctrl["ci95"][0], 6), round(d_ctrl["ci95"][1], 6)]})
        print(f"[CPR] snapped budget {b}: HR={r['ev']['pooled_dti']:.6f} (snap delta {d_ctrl['delta']:+.6f})", flush=True)

    # Candidate variants: CPR-1 = raw@37654, CPR-2 = raw@N*, CPR-3 = snap@N* (snap@37654 kept as ablation row)
    variants = {
        "CPR-1": ("raw", 37654),
        "CPR-2": ("raw", n_star),
        "CPR-3": ("snap", n_star),
    }
    if n_star != 37654:
        variants["CPR-3-ablation-snap37654"] = ("snap", 37654)

    # ---------- STEP 4: live surfaces, SGMC, uniqueness ----------
    pi_live_2d = _to_2d(1.0 - (1.0 - p_tip_live) * (1.0 - pi_blind_full))
    np.save(wdir / "cpr_live_pi.npy", pi_live_2d)
    _, live_order = htcads.emit_submodular_celf(pi_live_2d, elig_live, max_dots=MAX_DOTS, marginal_bar=0.0, return_order=True)
    live_order_snap = _snap_order(live_order, pi_live_2d, elig_live)
    np.savez_compressed(wdir / "cpr_orders.npz", live=live_order, live_snap=live_order_snap,
                        **{f"cell_{k}": v for k, v in cell_orders.items()},
                        **{f"cellsnap_{k}": v for k, v in cell_orders_snapped.items()})

    registry, reg_idx, reg_shas = _collect_registry(foot, ddir)
    print(f"[CPR] Registry: {len(registry)} footprint-distinct rasters", flush=True)

    exp_rows: list[dict] = []
    live_masks: dict[str, np.ndarray] = {}
    for vid, (kind, b) in variants.items():
        key = f"{kind}@{b}"
        r = hr_by_variant[key]
        live_mask = _mask_from_order(live_order_snap if kind == "snap" else live_order, b, foot.shape)
        live_masks[vid] = live_mask
        ev_sg = holdout.evaluate_sgmc_with_ci(live_mask, ctx, n_boot=1000, seed=SEED, name=vid)
        d_sg = holdout.paired_bootstrap_delta(ev_sg, ref_sg, boot_key="_cal_boots")
        uniq = htcads_run._check_uniqueness(pi_live_2d, live_mask, foot, registry, reg_idx)
        dk = d_full_2d[live_mask]
        exp_rows.append({
            "experiment_id": vid,
            "kind": kind,
            "budget_dots": b,
            "emitted_dots_live": int(live_mask.sum()),
            "structural_invariants": {
                "median_d_known_px": round(float(np.median(dk)), 2),
                "pct_le_2px_known": round(100.0 * float((dk <= 2.0).mean()), 2),
                "pct_le_10px_known": round(100.0 * float((dk <= 10.0).mean()), 2),
                "pct_in_lidar": round(100.0 * float(lidar_valid_2d[live_mask].mean()), 2),
            },
            "holdout_hide_recover": {
                "pooled_dti": round(r["ev"]["pooled_dti"], 6),
                "ci95": [round(r["ev"]["ci95_cluster_bootstrap"][0], 6), round(r["ev"]["ci95_cluster_bootstrap"][1], 6)],
                "per_quadrant_dti": {k: round(v, 6) for k, v in r["ev"]["per_quadrant_dti"].items()},
                "n_withheld_positives": r["ev"]["n_withheld_positives"],
                "paired_delta_vs_0p2778_ref": round(r["d_ref"]["delta"], 6),
                "paired_delta_ci95": [round(r["d_ref"]["ci95"][0], 6), round(r["d_ref"]["ci95"][1], 6)],
                "win_prob_vs_ref": round(r["d_ref"]["win_prob"], 4),
                "ci95_strictly_positive": r["d_ref"]["ci95_strictly_positive"],
                "prior_repo_best_htcads_exp2_same_evaluator": PRIOR_REPO_BEST_HR,
                "beats_prior_repo_best_point": bool(r["ev"]["pooled_dti"] > PRIOR_REPO_BEST_HR),
                "label": f"HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N={r['ev']['n_withheld_positives']} withheld positives, 95% CI [{r['ev']['ci95_cluster_bootstrap'][0]:.4f}, {r['ev']['ci95_cluster_bootstrap'][1]:.4f}])",
            },
            "holdout_sgmc_offcat": {
                "sgmc_prevalence_calibrated_dti": round(ev_sg["sgmc_prevalence_calibrated_dti"], 6),
                "ci95": [round(ev_sg["sgmc_calibrated_ci95"][0], 6), round(ev_sg["sgmc_calibrated_ci95"][1], 6)],
                "paired_delta_vs_0p2778_ref": round(d_sg["delta"], 6),
                "paired_delta_ci95": [round(d_sg["ci95"][0], 6), round(d_sg["ci95"][1], 6)],
                "label": f"HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N={ev_sg['n_withheld_positives']} off-catalogue SGMC positives, 95% CI [{ev_sg['sgmc_calibrated_ci95'][0]:.4f}, {ev_sg['sgmc_calibrated_ci95'][1]:.4f}])",
            },
            "uniqueness_audit": uniq,
        })
        print(f"[CPR] {vid} ({kind}@{b}): HR={r['ev']['pooled_dti']:.6f} SGMC={ev_sg['sgmc_prevalence_calibrated_dti']:.6f} "
              f"max3px={uniq['final_dots_max_detector_3px_overlap']:.4f} ({uniq['final_dots_closest_3px_detector_peer']}) uniq={uniq['passed']}", flush=True)

    # ---------- STEP 5: selection under pre-registered gates ----------
    main_rows = [r for r in exp_rows if r["experiment_id"] in ("CPR-1", "CPR-2", "CPR-3")]
    eligible = [r for r in main_rows
                if r["uniqueness_audit"]["passed"]
                and r["holdout_hide_recover"]["beats_prior_repo_best_point"]
                and r["holdout_hide_recover"]["ci95_strictly_positive"]]
    selected = max(eligible, key=lambda r: r["holdout_hide_recover"]["pooled_dti"]) if eligible else None

    bundle = None
    if selected is not None:
        vid = selected["experiment_id"]
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        hr = selected["holdout_hide_recover"]["pooled_dti"]
        snap_tag = "+crestsnap" if selected["kind"] == "snap" else ""
        note = f"KANLERGEMS2 CPR soft-credit regression rank-product CELF{snap_tag} ({selected['budget_dots']} dots, HR={hr:.4f})"[:140]
        bundle = submission.write_submission_bundle(
            mask_or_probs=live_masks[vid].astype(np.float32),
            foot=foot, labels=ctx.labels,
            template_tif=ddir / "sample_submission.tif",
            out_dir=downloads_dir(),
            slug=f"cpr-{vid.lower()}-{selected['budget_dots']}dots",
            timestamp_tag=ts,
            candidate_meta={"candidate_id": vid,
                            "description": "KG2-CPR soft DTI-credit regression + rank-product fusion + directional tip regressor + OOF-priced CELF budget + crest snapping (per variant flags)",
                            "submission_note": note},
            prefix="kanlergems2",
        )
        selected["bundle"] = bundle
        tif_sha = bundle["zeros_tif"]["sha256"]
        selected["exact_sha256_unique_vs_registry"] = bool(tif_sha not in reg_shas)
        comp_reg = json.loads((ROOT / "registry" / "comparison_registry.json").read_text(encoding="utf-8"))
        comp_shas = {e["sha256"] for e in comp_reg["entries"]}
        selected["exact_sha256_unique_vs_comparison_registry_360"] = bool(tif_sha not in comp_shas)
        print(f"[CPR] PROMOTED {vid}: {bundle['zeros_tif']['filename']} sha={tif_sha[:16]} note({len(note)})={note}", flush=True)
    else:
        print("[CPR] No variant passed all gates -> verdict negative; prior HTCADS EXP-2 remains promoted.", flush=True)

    sharp_names = [htcads.SUBSURF_FEATURE_NAMES[i] for i in sharp_cols]
    out = {
        "schema": "kanlergemsdoe2.cpr_experiments.v1",
        "lane_id": "KG2-CPR",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "total_wall_seconds": round(time.time() - t_start, 2),
        "within_protocol_budget": {"experiments_run": 3, "max_experiments_allowed": 3,
                                    "wall_hours": round((time.time() - t_start) / 3600.0, 4), "max_wall_hours_allowed": 2.0},
        "preregistration": "registry/preregistration_cpr.json",
        "reference_0p2778_benchmark": {
            "name": "GEMSDOE32 h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros (0.2778 ORGANIZER-CONFIRMED)",
            "holdout_hide_recover_uncensored_dti": round(ref_hr["pooled_dti"], 6),
            "holdout_hide_recover_ci95": [round(ref_hr["ci95_cluster_bootstrap"][0], 6), round(ref_hr["ci95_cluster_bootstrap"][1], 6)],
            "holdout_sgmc_calibrated_dti": round(ref_sg["sgmc_prevalence_calibrated_dti"], 6),
            "holdout_sgmc_ci95": [round(ref_sg["sgmc_calibrated_ci95"][0], 6), round(ref_sg["sgmc_calibrated_ci95"][1], 6)],
        },
        "budget_curve_hide_recover": curve,
        "oof_optimal_budget_n_star": n_star,
        "crest_snap_ablation_hide_recover": snap_curve,
        "experiments": exp_rows,
        "selected_experiment": selected["experiment_id"] if selected else None,
        "verdict": "promote" if selected else "negative",
        "blind_regressor_feature_gain_ranking": sorted(zip(sharp_names, [round(float(x), 2) for x in blind_imp]), key=lambda t: t[1], reverse=True),
        "lidar_regressor_feature_gain_ranking": sorted(zip(htcads.LIDAR_FEATURE_NAMES, [round(float(x), 2) for x in lid_imp]), key=lambda t: t[1], reverse=True),
        "registry_rasters_checked": len(registry),
    }
    (edir / "cpr_experiments.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"[CPR] Done in {time.time()-t_start:.0f}s verdict={out['verdict']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
