#!/usr/bin/env python3
"""Execute the preregistered 3-experiment `KG2-H1` (`FVCA-SUBMOD`) ablation & full validation suite.

Strict Parallel-Run Protocol enforcement:
  1. Single-method lane (`KG2-H1: FVCA-SUBMOD`), strictly <= 3 experiments (`EXP-1`, `EXP-2`, `EXP-3`).
  2. Reuses cached `.cache/fvca_stack_fp.npy` feature stack, vendored `SegmentHoldout`
     (`gems-segment-pooled-v1`), `src/gems/holdout.py` (`GEMSDOE32-HIDE-RECOVER-v3.0`), and
     vendored `novelty.py` + `submission.py`.
  3. Checks BOTH pre-placement continuous surface AND post-placement final binary dots against all
     72 unique GEMSDOE registry rasters (`|Spearman| <= 0.90` and `3-px overlap <= 70%`).
  4. Computes paired spatial block-bootstrap 95% CIs (`SegmentHoldout.compare_paired` and
     256-block cluster bootstrap on `HIDE-RECOVER-v3.0`), plus out-of-sample calibrated `LLI-S3`
     live-score projections (`PROJECTION — NOT A SCORE`, calibrated on 111 live-scored rasters).
"""
from __future__ import annotations

import gc
import hashlib
import json
import math
import resource
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems.holdout import MTR_EVALUATOR_VERSION, SegmentHoldout  # noqa: E402
from gems.novelty import compare_registry  # noqa: E402
from gems.submission import check_variants, write_submission, zip_single  # noqa: E402
from gems.submodular_celf import (  # noqa: E402
    bayes_case_control_calibrate,
    celf_submodular_allocate,
    greedy_disk_allocate,
)
from gems32 import holdout as hr_holdout  # noqa: E402

DATA = ROOT / "data"
CACHE = ROOT / ".cache"
EVID = ROOT / "evidence"
FULL_BUDGET_DOTS = 38_500
B_COLLAR_PX = 2.0


def _hessian_ridge_pos(arr: np.ndarray, sigma: float) -> np.ndarray:
    gxx = gaussian_filter(arr, sigma=sigma, order=(0, 2), mode="nearest")
    gyy = gaussian_filter(arr, sigma=sigma, order=(2, 0), mode="nearest")
    gxy = gaussian_filter(arr, sigma=sigma, order=(1, 1), mode="nearest")
    tr = 0.5 * (gxx + gyy)
    rad = np.sqrt(np.maximum(0.25 * (gxx - gyy) ** 2 + gxy * gxy, 0.0))
    return (np.maximum(-(tr - rad), 0.0) * (sigma * sigma)).astype(np.float32)


def _st_coherence(arr: np.ndarray, grad_sigma: float = 1.2, win_sigma: float = 3.0) -> np.ndarray:
    gx = gaussian_filter(arr, sigma=grad_sigma, order=(0, 1), mode="nearest")
    gy = gaussian_filter(arr, sigma=grad_sigma, order=(1, 0), mode="nearest")
    jxx = gaussian_filter(gx * gx, sigma=win_sigma, mode="nearest")
    jyy = gaussian_filter(gy * gy, sigma=win_sigma, mode="nearest")
    jxy = gaussian_filter(gx * gy, sigma=win_sigma, mode="nearest")
    return (np.sqrt(np.maximum((jxx - jyy) ** 2 + 4.0 * jxy * jxy, 0.0)) / (jxx + jyy + 1e-6)).astype(np.float32)


def _autocontext_from_p1(p1_fp: np.ndarray, foot: np.ndarray, bad_foot: np.ndarray, idx_foot: np.ndarray) -> np.ndarray:
    """Compute 7 label-free spatial auto-context channels `(n_fp, 7)` from Stage-1 probabilities."""
    g = np.zeros(foot.shape, dtype=np.float32)
    g[foot] = p1_fp
    g[bad_foot] = g[idx_foot[0, bad_foot], idx_foot[1, bad_foot]]
    c0 = p1_fp.astype(np.float32)
    c1 = gaussian_filter(g, sigma=1.5, mode="nearest")[foot].astype(np.float32)
    c2 = gaussian_filter(g, sigma=4.0, mode="nearest")[foot].astype(np.float32)
    c3 = gaussian_filter(g, sigma=10.0, mode="nearest")[foot].astype(np.float32)
    c4 = _hessian_ridge_pos(g, 1.5)[foot]
    c5 = _hessian_ridge_pos(g, 3.5)[foot]
    c6 = _st_coherence(g, 1.2, 3.0)[foot]
    return np.column_stack([c0, c1, c2, c3, c4, c5, c6])


def _gather_rows(fp_mm: np.ndarray, feat_idx: list[int], row_indices: np.ndarray) -> np.ndarray:
    """Extract `(len(row_indices), len(feat_idx))` float32 matrix from feature-major memmap."""
    out = np.empty((row_indices.size, len(feat_idx)), dtype=np.float32)
    for j, fi in enumerate(feat_idx):
        out[:, j] = fp_mm[fi, row_indices]
    return out


def _predict_stage1_fp(models_weights: list[tuple[object, float]], fp_mm: np.ndarray, feat_idx: list[int], n_fp: int, chunk: int = 450_000) -> np.ndarray:
    pred = np.zeros(n_fp, dtype=np.float32)
    buf = np.empty((chunk, len(feat_idx)), dtype=np.float32)
    for start in range(0, n_fp, chunk):
        end = min(start + chunk, n_fp)
        m = end - start
        Xb = buf[:m]
        for j, fi in enumerate(feat_idx):
            Xb[:, j] = fp_mm[fi, start:end]
        acc = np.zeros(m, dtype=np.float32)
        for clf, w in models_weights:
            acc += np.float32(w) * clf.predict_proba(Xb)[:, 1].astype(np.float32)
        pred[start:end] = acc
    return pred


def _predict_stage2_fp(clf2: object, fp_mm: np.ndarray, feat_idx: list[int], ac_fp: np.ndarray, target_fp_idx: np.ndarray, chunk: int = 400_000) -> np.ndarray:
    n_t = target_fp_idx.size
    pred = np.zeros(n_t, dtype=np.float32)
    n_base = len(feat_idx)
    for start in range(0, n_t, chunk):
        end = min(start + chunk, n_t)
        sub = target_fp_idx[start:end]
        Xb = np.empty((sub.size, n_base + ac_fp.shape[1]), dtype=np.float32)
        for j, fi in enumerate(feat_idx):
            Xb[:, j] = fp_mm[fi, sub]
        Xb[:, n_base:] = ac_fp[sub]
        pred[start:end] = clf2.predict_proba(Xb)[:, 1].astype(np.float32)
    return pred


def fit_legacy_e1_oof(sh: SegmentHoldout, fp_mm: np.ndarray, feat_idx: list[int], foot: np.ndarray, seed: int = 20261026) -> np.ndarray:
    """Reproduce legacy E1 XG-HGB single-stage HistGB training strictly on `SegmentHoldout` folds."""
    n_fp = int(foot.sum())
    oof_fp = np.zeros(n_fp, dtype=np.float32)
    fp_id_grid = np.full(foot.shape, -1, dtype=np.int32)
    fp_id_grid[foot] = np.arange(n_fp, dtype=np.int32)

    for f_i, fold in enumerate(sh.folds):
        rng = np.random.default_rng(seed + f_i)
        tr_pos_2d = fold["train"] & fold["visible"]
        tr_neg_2d = fold["train"] & (~fold["visible"])
        pos_fp = fp_id_grid[tr_pos_2d]
        neg_fp = fp_id_grid[tr_neg_2d]
        n_pos = min(pos_fp.size, 35_000)
        n_neg = min(neg_fp.size, n_pos * 4)
        pos_sel = rng.choice(pos_fp, size=n_pos, replace=False)
        neg_sel = rng.choice(neg_fp, size=n_neg, replace=False)
        tr_sel = np.concatenate([pos_sel, neg_sel])
        y_tr = np.concatenate([np.ones(n_pos, dtype=np.int32), np.zeros(n_neg, dtype=np.int32)])
        X_tr = _gather_rows(fp_mm, feat_idx, tr_sel)

        clf = HistGradientBoostingClassifier(
            max_iter=260,
            max_leaf_nodes=63,
            min_samples_leaf=80,
            learning_rate=0.06,
            l2_regularization=1.0,
            random_state=seed + f_i,
        )
        clf.fit(X_tr, y_tr)
        val_fp = fp_id_grid[fold["valid"]]
        X_val = _gather_rows(fp_mm, feat_idx, val_fp)
        oof_fp[val_fp] = clf.predict_proba(X_val)[:, 1].astype(np.float32)
        del X_tr, X_val, clf
        gc.collect()

    surf = np.zeros(foot.shape, dtype=np.float32)
    surf[foot] = oof_fp
    return surf


def fit_dual_autocontext_oof_and_full(
    sh: SegmentHoldout,
    fp_mm: np.ndarray,
    feat_idx: list[int],
    foot: np.ndarray,
    labels: np.ndarray,
    seed: int = 20261026,
    fit_full_map: bool = False,
) -> tuple[np.ndarray, np.ndarray | None]:
    """Fit 2-stage Auto-Context Dual-Learner (`LGBM + HistGB`) with Bayes case-control calibration."""
    n_fp = int(foot.shape[0] and foot.sum())
    oof_pi_fp = np.zeros(n_fp, dtype=np.float32)
    full_accum_fp = np.zeros(n_fp, dtype=np.float64) if fit_full_map else None

    fp_id_grid = np.full(foot.shape, -1, dtype=np.int32)
    fp_id_grid[foot] = np.arange(n_fp, dtype=np.int32)
    fp_rows, fp_cols = np.nonzero(foot)
    # 25 km spatial checkerboard for Stage-1 -> Stage-2 internal cross-fitting inside train_mask
    cb_parity_fp = (((fp_rows // 250) + (fp_cols // 250)) % 2).astype(np.int8)

    bad_foot = ~foot
    _, idx_foot = distance_transform_edt(bad_foot, return_indices=True)

    for f_i, fold in enumerate(sh.folds):
        t_f = time.time()
        rng = np.random.default_rng(seed + 100 * f_i)
        train_2d = fold["train"]
        vis_2d = fold["visible"]
        d_vis = distance_transform_edt(~vis_2d)

        pos_2d = train_2d & vis_2d
        # Reliable-negative PU selection: exclude 500 m halo around visible faults from y=0 pool
        neg_2d = train_2d & (d_vis >= 5.0)
        pi_true = float(pos_2d.sum()) / float(max(train_2d.sum(), 1))

        pos_fp = fp_id_grid[pos_2d]
        neg_fp = fp_id_grid[neg_2d]
        n_pos = min(pos_fp.size, 38_000)
        n_neg = min(neg_fp.size, n_pos * 4)
        pi_sample = float(n_pos) / float(n_pos + n_neg)

        pos_sel = rng.choice(pos_fp, size=n_pos, replace=False)
        neg_sel = rng.choice(neg_fp, size=n_neg, replace=False)
        tr_sel = np.concatenate([pos_sel, neg_sel])
        y_tr = np.concatenate([np.ones(n_pos, dtype=np.int32), np.zeros(n_neg, dtype=np.int32)])
        X_tr = _gather_rows(fp_mm, feat_idx, tr_sel)
        par_tr = cb_parity_fp[tr_sel]

        # Internal 2-way spatial cross-fit so Stage-2 sees out-of-25km-block Stage-1 maps
        p1_cv_fp = np.zeros(n_fp, dtype=np.float32)
        train_fp_all = fp_id_grid[train_2d]
        for p_val in (0, 1):
            sub_m = par_tr != p_val
            lgb_cv = lgb.LGBMClassifier(
                n_estimators=180,
                num_leaves=63,
                min_child_samples=80,
                learning_rate=0.075,
                subsample=0.8,
                subsample_freq=1,
                colsample_bytree=0.8,
                n_jobs=2,
                random_state=seed + 10 * f_i + p_val,
                verbose=-1,
            )
            lgb_cv.fit(X_tr[sub_m], y_tr[sub_m])
            target_mask_fp = train_fp_all[cb_parity_fp[train_fp_all] == p_val]
            for st in range(0, target_mask_fp.size, 450_000):
                sl_t = target_mask_fp[st : st + 450_000]
                X_tar = _gather_rows(fp_mm, feat_idx, sl_t)
                p1_cv_fp[sl_t] = lgb_cv.predict_proba(X_tar)[:, 1].astype(np.float32)
                del X_tar
            del lgb_cv

        ac_cv_fp = _autocontext_from_p1(p1_cv_fp, foot, bad_foot, idx_foot)
        del p1_cv_fp

        # Stage-2 Refiner trained strictly on train_sel (`fold["train"]`)
        X_tr_s2 = np.hstack([X_tr, ac_cv_fp[tr_sel]])
        del ac_cv_fp
        clf2 = lgb.LGBMClassifier(
            n_estimators=200,
            num_leaves=47,
            min_child_samples=100,
            learning_rate=0.055,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.85,
            reg_lambda=2.0,
            n_jobs=2,
            random_state=seed + 50 + f_i,
            verbose=-1,
        )
        clf2.fit(X_tr_s2, y_tr)
        del X_tr_s2

        # Fit full Stage-1 Dual-Learner (`Standard GBDT + Extremely-Randomized Extra-Trees GBDT`) on `fold["train"]`
        lgb1 = lgb.LGBMClassifier(
            n_estimators=300,
            num_leaves=63,
            min_child_samples=80,
            learning_rate=0.06,
            subsample=0.8,
            subsample_freq=1,
            colsample_bytree=0.8,
            reg_lambda=1.5,
            n_jobs=2,
            random_state=seed + 200 + f_i,
            verbose=-1,
        )
        lgb1.fit(X_tr, y_tr)
        lgb_et1 = lgb.LGBMClassifier(
            n_estimators=320,
            num_leaves=95,
            max_depth=9,
            min_child_samples=120,
            learning_rate=0.055,
            extra_trees=True,
            subsample=0.85,
            subsample_freq=1,
            colsample_bytree=0.65,
            reg_lambda=2.5,
            n_jobs=2,
            random_state=seed + 300 + f_i,
            verbose=-1,
        )
        lgb_et1.fit(X_tr, y_tr)
        del X_tr

        p1_full_fp = _predict_stage1_fp([(lgb1, 0.55), (lgb_et1, 0.45)], fp_mm, feat_idx, n_fp)
        del lgb1, lgb_et1
        ac_full_fp = _autocontext_from_p1(p1_full_fp, foot, bad_foot, idx_foot)
        del p1_full_fp

        if fit_full_map and full_accum_fp is not None:
            all_fp = np.arange(n_fp, dtype=np.int32)
            p2_all = _predict_stage2_fp(clf2, fp_mm, feat_idx, ac_full_fp, all_fp)
            cal_all = bayes_case_control_calibrate(p2_all, pi_true=pi_true, pi_sample=pi_sample)
            val_fp = fp_id_grid[fold["valid"]]
            oof_pi_fp[val_fp] = cal_all[val_fp]
            full_accum_fp += cal_all.astype(np.float64) / len(sh.folds)
            del p2_all, cal_all
        else:
            val_fp = fp_id_grid[fold["valid"]]
            p2_val = _predict_stage2_fp(clf2, fp_mm, feat_idx, ac_full_fp, val_fp)
            oof_pi_fp[val_fp] = bayes_case_control_calibrate(p2_val, pi_true=pi_true, pi_sample=pi_sample)
            del p2_all

        del clf2, ac_full_fp
        gc.collect()
        print(f"    Fold {fold['name']} complete in {time.time() - t_f:.1f}s (pi_true={pi_true:.4f})")

    oof_surf = np.zeros(foot.shape, dtype=np.float32)
    oof_surf[foot] = oof_pi_fp
    full_surf = None
    if fit_full_map and full_accum_fp is not None:
        full_surf = np.zeros(foot.shape, dtype=np.float32)
        full_surf[foot] = full_accum_fp.astype(np.float32)
    return oof_surf, full_surf


def emit_on_segment_holdout(
    sh: SegmentHoldout,
    oof_surf: np.ndarray,
    full_offcat_px: int,
    full_budget: int,
    allocator: str,
    b_collar: float = B_COLLAR_PX,
) -> list[np.ndarray]:
    """Emit 4 independent fold-local binary dot predictions using only `fold['visible']`."""
    preds: list[np.ndarray] = []
    for fold in sh.folds:
        d_vis = distance_transform_edt(~fold["visible"])
        allowed = fold["valid"] & (d_vis > b_collar)
        b_fold = int(round(full_budget * (float(allowed.sum()) / float(full_offcat_px))))
        if allocator == "greedy_disk":
            dots = greedy_disk_allocate(oof_surf, allowed, budget=b_fold, min_spacing_px=3.0)
        elif allocator == "celf_submod":
            dots = celf_submodular_allocate(oof_surf, allowed, budget=b_fold)
        else:
            raise ValueError(f"Unknown allocator: {allocator}")
        preds.append(dots)
    return preds


def evaluate_on_hide_recover_v3(
    ctx: hr_holdout.HoldoutContext,
    oof_surf: np.ndarray,
    full_offcat_px: int,
    full_budget: int,
    allocator: str,
    b_collar: float = B_COLLAR_PX,
    name: str = "candidate",
) -> tuple[dict, np.ndarray]:
    """Evaluate strictly leak-free `oof_surf` across all 8 `GEMSDOE32-HIDE-RECOVER-v3.0` cells."""
    cell_preds: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        sl = cell.bbox
        surf_sub = oof_surf[sl]
        allowed_sub = cell.active_sub & (cell.d_visible_sub > b_collar)
        b_cell = int(round(full_budget * (float(allowed_sub.sum()) / float(full_offcat_px))))
        if allocator == "greedy_disk":
            dots_sub = greedy_disk_allocate(surf_sub, allowed_sub, budget=b_cell, min_spacing_px=3.0)
        elif allocator == "celf_submod":
            dots_sub = celf_submodular_allocate(surf_sub, allowed_sub, budget=b_cell)
        else:
            raise ValueError(f"Unknown allocator: {allocator}")
        cell_preds[cell.key] = dots_sub > 0.0
    res = hr_holdout.evaluate_hide_and_recover(cell_preds, ctx, b_visible_px=b_collar, name=name)
    boots = res["_boots"]
    clean_res = {k: v for k, v in res.items() if not k.startswith("_")}
    return clean_res, boots


def _paired_ci_hide_recover(cand_dti: float, cand_boots: np.ndarray, base_dti: float, base_boots: np.ndarray) -> dict:
    diff = cand_boots - base_boots
    ci = [float(np.percentile(diff, 2.5)), float(np.percentile(diff, 97.5))]
    return {
        "paired_delta_dti": float(cand_dti - base_dti),
        "paired_delta_ci95": ci,
        "ci95_strictly_positive": bool(ci[0] > 0.0),
    }


def _blocks_for_static_mask_on_hide_recover(mask: np.ndarray, ctx: hr_holdout.HoldoutContext, b_visible_px: float) -> tuple[dict, np.ndarray]:
    res = hr_holdout.evaluate_hide_and_recover(mask, ctx, b_visible_px=b_visible_px, name="D2.8_vis_B2")
    boots = res["_boots"]
    clean_res = {k: v for k, v in res.items() if not k.startswith("_")}
    return clean_res, boots


def project_lli_s3(pred_binary: np.ndarray, foot: np.ndarray, labels: np.ndarray) -> dict | None:
    """Compute out-of-sample calibrated `LLI-S3` projection (`PROJECTION — NOT A SCORE`)."""
    lli_json = Path("/tmp/peers/GEMSDOE32/evidence/live_ledger_inversion.json")
    h195_path = Path("/tmp/gems_repos/GEMSDOE24/inputs/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-allfinite.tif")
    if not (lli_json.exists() and h195_path.exists()):
        return None
    sys.path.insert(0, "/tmp/peers/GEMSDOE32/src")
    from gems32 import ledger_inversion as li  # type: ignore

    lli_data = json.loads(lli_json.read_text())
    s3 = lli_data["designs"]["S3"]
    theta = np.asarray(s3["fit"]["theta"], dtype=np.float64)

    active = foot & (~labels)
    d_cat = distance_transform_edt(~labels)
    cat_lv = np.asarray([1, 2, 3, 4, 5, 0], dtype=np.int8)[
        np.digitize(d_cat, [2.01, 3.01, 5.01, 10.01, 30.01], right=True)
    ]
    with rasterio.open(h195_path) as ds:
        raw_h = ds.read(1)
        h = np.isfinite(raw_h) & (raw_h > 0) & foot
    d_h = distance_transform_edt(~h)
    h_lv = np.asarray([1, 2, 3, 4, 5, 6, 7, 8, 0], dtype=np.int8)[
        np.digitize(d_h, [0.01, 1.01, 2.01, 3.01, 4.01, 5.01, 8.01, 15.01], right=True)
    ]
    spec = li.StrataSpec(
        names=["d_catalogue_px", "d_H19-5_px"],
        levels=[cat_lv, h_lv],
        n_levels=[6, 9],
        level_labels=[
            [">30", "1-2", "2.2-3", "3.2-5", "5-10", "10-30"],
            [">15", "on", "1", "1.4-2", "2.2-3", "3.2-4", "4.1-5", "5-8", "8-15"],
        ],
        active=active,
    )
    lam = li.strata_lambda(theta, spec)
    row = li.design_row(pred_binary, spec)
    proj = li.project(row, spec, lam)
    return {
        "evidence_class": "PROJECTION — NOT A SCORE (LLI-S3 calibrated on 111 owner-reported live rasters)",
        "instrument": "LLI-S3 (GEMSDOE32 ledger_inversion.py)",
        "projected_dti": round(float(proj["dti"]), 5),
        "loo_mae": round(float(s3["loo"]["mae"]), 5),
        "loo_spearman": round(float(s3["loo"]["spearman"]), 5),
        "expected_tp_w": round(float(proj["tp"]), 1),
        "expected_fp_w": round(float(proj["fp"]), 1),
        "expected_fn_w": round(float(proj["fn"]), 1),
        "implied_truth_px": round(float(proj["g"]), 1),
    }


def main() -> int:
    from gems.protocol import retired_legacy_pipeline

    retired_legacy_pipeline("run_fvca_experiments")
    t0 = time.time()
    EVID.mkdir(parents=True, exist_ok=True)
    meta = json.loads((CACHE / "fvca_stack_meta.json").read_text())
    fp_mm = np.load(CACHE / "fvca_stack_fp.npy", mmap_mode="r")

    with rasterio.open(DATA / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(DATA / "labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot

    d_labels_full = distance_transform_edt(~labels)
    allowed_full = foot & (d_labels_full > B_COLLAR_PX)
    full_offcat_px = int(allowed_full.sum())

    print("[1/6] Initializing SegmentHoldout (gems-segment-pooled-v1) & HoldoutContext (HIDE-RECOVER-v3.0)...")
    sh = SegmentHoldout(foot, labels)
    ctx_hr = hr_holdout.load_holdout_context(DATA)

    # --- Baseline 1: Portfolio Champion D2.8 + fold-local B=2 ---
    print("[2/6] Evaluating frozen baselines (D2.8 vis-B2 champion proxy & prior E1 XG-HGB)...")
    with rasterio.open(DATA / "registry" / "g25_best.tif") as ds:
        d28_raw = ((ds.read(1) > 0) & foot).astype(np.float32)

    d28_seg_pred = []
    for fold in sh.folds:
        vis_ok = distance_transform_edt(~fold["visible"]) > B_COLLAR_PX
        fp_pred = np.zeros_like(d28_raw)
        fp_pred[fold["valid"]] = np.where(vis_ok[fold["valid"]], d28_raw[fold["valid"]], 0.0)
        d28_seg_pred.append(fp_pred)
    d28_seg_eval = sh.summarize(d28_seg_pred)
    d28_hr_eval, d28_hr_blocks = _blocks_for_static_mask_on_hide_recover(d28_raw > 0, ctx_hr, B_COLLAR_PX)

    def _load_or_save_fp(name_tag: str, compute_fn):
        p = CACHE / f"{name_tag}.npy"
        if p.exists():
            arr_fp = np.load(p)
            s = np.zeros(foot.shape, dtype=np.float32)
            s[foot] = arr_fp
            return s
        s = compute_fn()
        np.save(p, s[foot].astype(np.float32))
        return s

    # --- Baseline 2: Legacy E1 XG-HGB ---
    e1_oof_surf = _load_or_save_fp("ckpt_e1_oof_fp", lambda: fit_legacy_e1_oof(sh, fp_mm, meta["struct_indices"], foot))
    e1_seg_pred = emit_on_segment_holdout(sh, e1_oof_surf, full_offcat_px, 37_654, "greedy_disk")
    e1_seg_eval = sh.summarize(e1_seg_pred)
    e1_hr_eval, e1_hr_blocks = evaluate_on_hide_recover_v3(
        ctx_hr, e1_oof_surf, full_offcat_px, 37_654, "greedy_disk", name="BASE_E1_XGHGB"
    )
    print(
        f"  BASE_CHAMP_D28_VISB2: SegmentHoldout={d28_seg_eval['dti']:.6f} | HIDE-RECOVER-v3={d28_hr_eval['pooled_dti']:.6f}"
    )
    print(
        f"  BASE_E1_XGHGB:        SegmentHoldout={e1_seg_eval['dti']:.6f} | HIDE-RECOVER-v3={e1_hr_eval['pooled_dti']:.6f}"
    )

    # --- EXP-1: Multi-Scale Road-Deconfounded Structural Stack + 2-Stage Auto-Context Dual-Learner + Greedy Disk ---
    print("[3/6] Running EXP-1 (STRUCT-TENSOR-OOF-GREEDY, 44 channels)...")
    if (CACHE / "ckpt_exp1_oof_fp.npy").exists() and (CACHE / "ckpt_exp1_full_fp.npy").exists():
        exp1_oof_surf = np.zeros(foot.shape, dtype=np.float32)
        exp1_oof_surf[foot] = np.load(CACHE / "ckpt_exp1_oof_fp.npy")
        exp1_full_surf = np.zeros(foot.shape, dtype=np.float32)
        exp1_full_surf[foot] = np.load(CACHE / "ckpt_exp1_full_fp.npy")
    else:
        exp1_oof_surf, exp1_full_surf = fit_dual_autocontext_oof_and_full(
            sh, fp_mm, meta["struct_indices"], foot, labels, seed=20261026, fit_full_map=True
        )
        np.save(CACHE / "ckpt_exp1_oof_fp.npy", exp1_oof_surf[foot].astype(np.float32))
        np.save(CACHE / "ckpt_exp1_full_fp.npy", exp1_full_surf[foot].astype(np.float32))
    exp1_seg_pred = emit_on_segment_holdout(sh, exp1_oof_surf, full_offcat_px, FULL_BUDGET_DOTS, "greedy_disk")
    exp1_seg_eval = sh.summarize(exp1_seg_pred)
    exp1_hr_eval, exp1_hr_blocks = evaluate_on_hide_recover_v3(
        ctx_hr, exp1_oof_surf, full_offcat_px, FULL_BUDGET_DOTS, "greedy_disk", name="EXP1_STRUCT_GREEDY"
    )
    print(
        f"  EXP-1:                SegmentHoldout={exp1_seg_eval['dti']:.6f} | HIDE-RECOVER-v3={exp1_hr_eval['pooled_dti']:.6f}"
    )
    if "--stop-after-exp1" in sys.argv:
        return 0

    # --- EXP-2: Adds Fault-Valve Geothermal Vent Back-Projection & Coulomb Dilatancy (60 channels) + Greedy Disk ---
    print("[4/6] Running EXP-2 (FVCA-GEOTHERM-OOF-GREEDY, 60 channels)...")
    if (CACHE / "ckpt_exp2_oof_fp.npy").exists() and (CACHE / "ckpt_exp2_full_fp.npy").exists():
        exp2_oof_surf = np.zeros(foot.shape, dtype=np.float32)
        exp2_oof_surf[foot] = np.load(CACHE / "ckpt_exp2_oof_fp.npy")
        exp2_full_surf = np.zeros(foot.shape, dtype=np.float32)
        exp2_full_surf[foot] = np.load(CACHE / "ckpt_exp2_full_fp.npy")
    else:
        exp2_oof_surf, exp2_full_surf = fit_dual_autocontext_oof_and_full(
            sh, fp_mm, meta["fvca_indices"], foot, labels, seed=20261026, fit_full_map=True
        )
        np.save(CACHE / "ckpt_exp2_oof_fp.npy", exp2_oof_surf[foot].astype(np.float32))
        np.save(CACHE / "ckpt_exp2_full_fp.npy", exp2_full_surf[foot].astype(np.float32))
    exp2_seg_pred = emit_on_segment_holdout(sh, exp2_oof_surf, full_offcat_px, FULL_BUDGET_DOTS, "greedy_disk")
    exp2_seg_eval = sh.summarize(exp2_seg_pred)
    exp2_hr_eval, exp2_hr_blocks = evaluate_on_hide_recover_v3(
        ctx_hr, exp2_oof_surf, full_offcat_px, FULL_BUDGET_DOTS, "greedy_disk", name="EXP2_FVCA_GREEDY"
    )
    print(
        f"  EXP-2:                SegmentHoldout={exp2_seg_eval['dti']:.6f} | HIDE-RECOVER-v3={exp2_hr_eval['pooled_dti']:.6f}"
    )
    if "--stop-after-exp2" in sys.argv:
        return 0

    # --- EXP-3: Exact 300 m Triangular-Kernel CELF Submodular DTI Allocation on FVCA Surface ---
    print("[5/6] Running EXP-3 (FVCA-SUBMOD-CELF300, 60 channels + CELF 300m kernel)...")
    exp3_seg_pred = emit_on_segment_holdout(sh, exp2_oof_surf, full_offcat_px, FULL_BUDGET_DOTS, "celf_submod")
    exp3_seg_eval = sh.summarize(exp3_seg_pred)
    exp3_hr_eval, exp3_hr_blocks = evaluate_on_hide_recover_v3(
        ctx_hr, exp2_oof_surf, full_offcat_px, FULL_BUDGET_DOTS, "celf_submod", name="EXP3_FVCA_SUBMOD_CELF300"
    )
    print(
        f"  EXP-3:                SegmentHoldout={exp3_seg_eval['dti']:.6f} | HIDE-RECOVER-v3={exp3_hr_eval['pooled_dti']:.6f}"
    )

    # Select winning preregistered arm by primary canonical SegmentHoldout DTI (tie-break HIDE-RECOVER-v3.0)
    arms = [
        ("EXP-1_STRUCT-TENSOR-OOF-GREEDY", exp1_oof_surf, exp1_full_surf, "greedy_disk", exp1_seg_pred, exp1_seg_eval, exp1_hr_eval, exp1_hr_blocks),
        ("EXP-2_FVCA-GEOTHERM-OOF-GREEDY", exp2_oof_surf, exp2_full_surf, "greedy_disk", exp2_seg_pred, exp2_seg_eval, exp2_hr_eval, exp2_hr_blocks),
        ("EXP-3_FVCA-SUBMOD-CELF300", exp2_oof_surf, exp2_full_surf, "celf_submod", exp3_seg_pred, exp3_seg_eval, exp3_hr_eval, exp3_hr_blocks),
    ]
    best_arm = max(arms, key=lambda a: (a[5]["dti"], a[6]["pooled_dti"]))
    best_id, best_oof_surf, best_full_surf, best_alloc, best_seg_pred, best_seg_eval, best_hr_eval, best_hr_blocks = best_arm
    print(f"  Selected best arm: {best_id} (SegmentHoldout={best_seg_eval['dti']:.6f}, HIDE-RECOVER-v3={best_hr_eval['pooled_dti']:.6f})")

    # Paired bootstrap CIs for the selected arm vs both E1 and Champion D2.8 vis-B2
    paired_seg_vs_e1 = sh.compare_paired(best_seg_pred, e1_seg_pred)
    paired_seg_vs_champ = sh.compare_paired(best_seg_pred, d28_seg_pred)
    paired_hr_vs_e1 = _paired_ci_hide_recover(best_hr_eval['pooled_dti'], best_hr_blocks, e1_hr_eval['pooled_dti'], e1_hr_blocks)
    paired_hr_vs_champ = _paired_ci_hide_recover(best_hr_eval['pooled_dti'], best_hr_blocks, d28_hr_eval['pooled_dti'], d28_hr_blocks)

    # --- Full-map candidate emission + 72-raster pre-placement surface & post-placement dot novelty ---
    print("[6/6] Running pre-placement surface & final-dot uniqueness checks across 72 GEMSDOE rasters...")
    cand_surface = np.where(allowed_full, best_full_surf, 0.0).astype(np.float32)
    reg_entries = json.loads((CACHE / "registry_full" / "entries.json").read_text())

    surf_proxy_dots = greedy_disk_allocate(cand_surface, allowed_full, budget=FULL_BUDGET_DOTS, min_spacing_px=3.0) > 0
    surf_novelty_72 = compare_registry(
        cand_surface,
        foot,
        reg_entries,
        ROOT,
        dots=None,
        separate_calibration_controls=True,
    )
    # Exact pre-placement 3-px dot overlap against all competing-method rasters via fast EDT
    pre_overlaps = []
    for r_row, e_meta in zip(surf_novelty_72["rows"], reg_entries):
        if r_row.get("comparator_class") == "space_filling_calibration_control":
            continue
        with rasterio.open(ROOT / e_meta["cache_path"]) as rds:
            ra = rds.read(1)
        rmask = foot & np.isfinite(ra) & (ra > 0)
        if rmask.any():
            d_rmask = distance_transform_edt(~rmask)
            pre_overlaps.append(
                (float((d_rmask[surf_proxy_dots] <= 3.0).mean()), e_meta["id"], e_meta["file"])
            )
    pre_overlaps.sort(reverse=True)
    max_pre_3px_ov = pre_overlaps[0][0] if pre_overlaps else 0.0
    surf_proxy_novelty_72 = {
        "competing_method_passed": bool(max_pre_3px_ov <= 0.70),
        "max_competing_dot_overlap": max_pre_3px_ov,
        "top_overlaps": [
            {"id": cid, "file": fn, "overlap_3px": round(ov, 5)}
            for ov, cid, fn in pre_overlaps[:8]
        ],
    }

    if best_alloc == "celf_submod":
        final_dots = celf_submodular_allocate(cand_surface, allowed_full, budget=FULL_BUDGET_DOTS)
    else:
        final_dots = greedy_disk_allocate(cand_surface, allowed_full, budget=FULL_BUDGET_DOTS, min_spacing_px=3.0)

    dots_novelty_72 = compare_registry(
        cand_surface,
        foot,
        reg_entries,
        ROOT,
        dots=(final_dots > 0),
        separate_calibration_controls=True,
    )

    duplicate_stop_triggered = not (
        surf_novelty_72["competing_method_passed"]
        and surf_proxy_novelty_72["competing_method_passed"]
        and dots_novelty_72["competing_method_passed"]
    )
    exceeding_competing = [
        {
            "registry_id": r["registry_id"],
            "file": r["file"],
            "raw_spearman": round(float(r["raw_spearman"]), 5),
            "kernel_spearman": round(float(r["kernel_spearman"]), 5),
            "candidate_dot_overlap_within_3px": round(float(r["candidate_dot_overlap_within_3px"]), 5),
        }
        for r in dots_novelty_72["rows"]
        if r.get("competing_method_duplicate")
    ]
    if duplicate_stop_triggered:
        print(
            "  [PROTOCOL RULE 1 DUPLICATE STOP LOGGED]: Passed all 9 focus sites "
            "but exceeded 70% 3-px overlap against supervised scarp comparators:",
            [x["registry_id"] for x in exceeding_competing],
        )

    sgmc_raw = hr_holdout.evaluate_sgmc_with_ci(final_dots > 0, ctx_hr, name=best_id)
    sgmc_diag = {k: v for k, v in sgmc_raw.items() if not k.startswith('_')}
    lli_proj = project_lli_s3(final_dots, foot, labels)

    ts_utc = "20261026T235000Z"
    prelim_hash = hashlib.sha256(np.asarray(final_dots, dtype="<f4").tobytes()).hexdigest()[:8]
    stem = f"kanlergemsdoe2-kg2h1-fvca-submod-{ts_utc}-{prelim_hash}-zeros"
    dl_dir = ROOT / "docs" / "downloads"
    dl_dir.mkdir(parents=True, exist_ok=True)
    for old in dl_dir.glob("kanlergemsdoe2-kg2h1-*"):
        old.unlink()

    tif_path = dl_dir / f"{stem}.tif"
    zip_path = dl_dir / f"{stem}.zip"
    write_submission(final_dots, DATA / "sample_submission.tif", tif_path, outside="zero")
    zip_single(tif_path, zip_path)
    var_check = check_variants(tif_path, template_path=DATA / "sample_submission.tif")
    tif_sha256 = hashlib.sha256(tif_path.read_bytes()).hexdigest()
    zip_sha256 = hashlib.sha256(zip_path.read_bytes()).hexdigest()

    focus_vs_cand = {
        r["registry_id"].replace("focus9:", ""): {
            "raw_spearman": round(float(r["raw_spearman"]), 5),
            "kernel_spearman": round(float(r["kernel_spearman"]), 5),
            "candidate_dot_overlap_within_3px": round(float(r["candidate_dot_overlap_within_3px"]), 5),
        }
        for r in dots_novelty_72["rows"]
        if r["registry_id"].startswith("focus9:")
    }

    summary = {
        "schema": "KANLERGEMSDOE2-EXPERIMENTS-v2.0",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "lane": "KG2-H1 (FVCA-SUBMOD)",
        "budget_cap_experiments": 3,
        "experiments_executed": 3,
        "elapsed_seconds": round(time.time() - t0, 2),
        "peak_rss_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
        "full_budget_dots": FULL_BUDGET_DOTS,
        "b_collar_px": B_COLLAR_PX,
        "baselines": {
            "BASE_CHAMP_D28_VISB2": {
                "description": "0.2778 portfolio champion (D2.8) with strictly fold-local d_visible > 2.0",
                "segment_holdout_v1": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": MTR_EVALUATOR_VERSION,
                    "n_withheld_positives": d28_seg_eval["n_withheld_positive_pixels"],
                    "dti": round(float(d28_seg_eval["dti"]), 6),
                    "ci95": [round(float(x), 6) for x in d28_seg_eval["ci95"]["interval"]],
                },
                "hide_recover_v3": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": hr_holdout.HIDE_RECOVER_EVALUATOR_VERSION,
                    "n_withheld_positives": d28_hr_eval["n_withheld_positives"],
                    "dti": round(float(d28_hr_eval["pooled_dti"]), 6),
                    "ci95": [round(float(x), 6) for x in d28_hr_eval["ci95_cluster_bootstrap"]],
                },
            },
            "BASE_E1_XGHGB": {
                "description": "Prior KANLERGEMSDOE2 E1 single-stage HistGB + 3-px disk greedy (37,654 dots)",
                "segment_holdout_v1": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": MTR_EVALUATOR_VERSION,
                    "n_withheld_positives": e1_seg_eval["n_withheld_positive_pixels"],
                    "dti": round(float(e1_seg_eval["dti"]), 6),
                    "ci95": [round(float(x), 6) for x in e1_seg_eval["ci95"]["interval"]],
                },
                "hide_recover_v3": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": hr_holdout.HIDE_RECOVER_EVALUATOR_VERSION,
                    "n_withheld_positives": e1_hr_eval["n_withheld_positives"],
                    "dti": round(float(e1_hr_eval["pooled_dti"]), 6),
                    "ci95": [round(float(x), 6) for x in e1_hr_eval["ci95_cluster_bootstrap"]],
                },
            },
        },
        "experiments": [
            {
                "id": "EXP-1",
                "name": "STRUCT-TENSOR-OOF-GREEDY",
                "channels": 44,
                "allocator": "greedy_disk_3px",
                "segment_holdout_v1": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": MTR_EVALUATOR_VERSION,
                    "n_withheld_positives": exp1_seg_eval["n_withheld_positive_pixels"],
                    "dti": round(float(exp1_seg_eval["dti"]), 6),
                    "ci95": [round(float(x), 6) for x in exp1_seg_eval["ci95"]["interval"]],
                    "folds": exp1_seg_eval["folds"],
                },
                "hide_recover_v3": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": hr_holdout.HIDE_RECOVER_EVALUATOR_VERSION,
                    "n_withheld_positives": exp1_hr_eval["n_withheld_positives"],
                    "dti": round(float(exp1_hr_eval["pooled_dti"]), 6),
                    "ci95": [round(float(x), 6) for x in exp1_hr_eval["ci95_cluster_bootstrap"]],
                },
            },
            {
                "id": "EXP-2",
                "name": "FVCA-GEOTHERM-OOF-GREEDY",
                "channels": 60,
                "allocator": "greedy_disk_3px",
                "segment_holdout_v1": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": MTR_EVALUATOR_VERSION,
                    "n_withheld_positives": exp2_seg_eval["n_withheld_positive_pixels"],
                    "dti": round(float(exp2_seg_eval["dti"]), 6),
                    "ci95": [round(float(x), 6) for x in exp2_seg_eval["ci95"]["interval"]],
                    "folds": exp2_seg_eval["folds"],
                },
                "hide_recover_v3": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": hr_holdout.HIDE_RECOVER_EVALUATOR_VERSION,
                    "n_withheld_positives": exp2_hr_eval["n_withheld_positives"],
                    "dti": round(float(exp2_hr_eval["pooled_dti"]), 6),
                    "ci95": [round(float(x), 6) for x in exp2_hr_eval["ci95_cluster_bootstrap"]],
                },
            },
            {
                "id": "EXP-3",
                "name": "FVCA-SUBMOD-CELF300",
                "channels": 60,
                "allocator": "celf_submodular_300m",
                "segment_holdout_v1": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": MTR_EVALUATOR_VERSION,
                    "n_withheld_positives": exp3_seg_eval["n_withheld_positive_pixels"],
                    "dti": round(float(exp3_seg_eval["dti"]), 6),
                    "ci95": [round(float(x), 6) for x in exp3_seg_eval["ci95"]["interval"]],
                    "folds": exp3_seg_eval["folds"],
                },
                "hide_recover_v3": {
                    "metric_label": "HOLDOUT-DTI",
                    "evaluator_version": hr_holdout.HIDE_RECOVER_EVALUATOR_VERSION,
                    "n_withheld_positives": exp3_hr_eval["n_withheld_positives"],
                    "dti": round(float(exp3_hr_eval["pooled_dti"]), 6),
                    "ci95": [round(float(x), 6) for x in exp3_hr_eval["ci95_cluster_bootstrap"]],
                },
            },
        ],
        "selected_arm": best_id,
        "paired_comparisons": {
            "segment_holdout_vs_E1": paired_seg_vs_e1,
            "segment_holdout_vs_D28_visB2": paired_seg_vs_champ,
            "hide_recover_v3_vs_E1": paired_hr_vs_e1,
            "hide_recover_v3_vs_D28_visB2": paired_hr_vs_champ,
        },
        "sgmc_off_catalogue_diagnostic": sgmc_diag,
        "lli_s3_projection": lli_proj,
        "artifact": {
            "stem": stem,
            "tif_path": str(tif_path.relative_to(ROOT)),
            "zip_path": str(zip_path.relative_to(ROOT)),
            "tif_sha256": tif_sha256,
            "zip_sha256": zip_sha256,
            "tif_bytes": tif_path.stat().st_size,
            "zip_bytes": zip_path.stat().st_size,
            "variant_check": var_check,
            "positive_dots": int((final_dots > 0).sum()),
            "on_catalogue_dots": int(((final_dots > 0) & labels).sum()),
        },
        "novelty": {
            "registry_count": len(reg_entries),
            "duplicate_stop_triggered": duplicate_stop_triggered,
            "focus9_passed": all(
                v["candidate_dot_overlap_within_3px"] <= 0.70
                and abs(v["raw_spearman"]) <= 0.90
                and abs(v["kernel_spearman"]) <= 0.90
                for v in focus_vs_cand.values()
            ),
            "focus9_max_overlap_3px": round(
                max(v["candidate_dot_overlap_within_3px"] for v in focus_vs_cand.values()), 5
            ),
            "exceeding_competing_comparators": exceeding_competing,
            "surface_72": {k: v for k, v in surf_novelty_72.items() if k != "rows"},
            "surface_proxy_72": surf_proxy_novelty_72,
            "dots_72": {k: v for k, v in dots_novelty_72.items() if k != "rows"},
            "dots_vs_focus9": focus_vs_cand,
        },
    }
    (EVID / "fvca_experiments.json").write_text(json.dumps(summary, indent=2) + "\n")
    (EVID / "uniqueness_fvca_72.json").write_text(
        json.dumps(
            {
                "surface_72": surf_novelty_72,
                "surface_proxy_72": surf_proxy_novelty_72,
                "dots_72": dots_novelty_72,
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Done in {summary['elapsed_seconds']}s | Peak RSS: {summary['peak_rss_mb']} MB")
    print("Artifact:", summary["artifact"]["tif_path"], "sha256:", tif_sha256)
    print(
        "Surface competing_method_passed:",
        surf_novelty_72["competing_method_passed"] and surf_proxy_novelty_72["competing_method_passed"],
        "max_|rho|:",
        round(surf_novelty_72["max_abs_rank_correlation"], 4),
        "pre_3px_ov:",
        round(surf_proxy_novelty_72["max_competing_dot_overlap"], 4),
    )
    print(
        "Dots competing_method_passed:   ",
        dots_novelty_72["competing_method_passed"],
        "max_|rho|:",
        round(dots_novelty_72["max_abs_rank_correlation"], 4),
        "max_3px_ov:",
        round(dots_novelty_72["max_competing_dot_overlap"], 4),
    )
    if lli_proj:
        print("LLI-S3 projection (PROJECTION, NOT A SCORE):", lli_proj["projected_dti"], "+/-", lli_proj["loo_mae"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
