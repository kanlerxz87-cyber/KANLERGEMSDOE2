#!/usr/bin/env python3
"""Shared hide-and-recover holdout evaluator, leakage canary, and duplicate guard.

Implements the Parallel-Run Protocol Rule 1, Rule 2, Rule 3, and Rule 4:
  - Holdout = hide-and-recover: withhold whole fault segments with a buffer,
    derive every catalogue-based feature only from the visible faults,
    mask visible faults pixel-exactly, score pooled DTI (alpha=0.2, beta=0.8,
    300 m triangular kernel).
  - Label every holdout measurement as HOLDOUT-DTI with evaluator version,
    number of withheld positives, and 95% confidence interval.
  - Leakage canary: test each feature alone on the holdout before trusting any
    result; two-polarity ROC AUC > 0.90 flags leakage.
  - Duplicate guard: test both the continuous score surface before placement
    and the final emitted dots against all registry rasters (Spearman rho > 0.90
    or > 70% of candidate dots within 3 px of a registry raster's dots).
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Mapping

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.stats import spearmanr, t as student_t
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gems33.grid import catalogue_systems, fold_masks  # noqa: E402
from gems33.metric import ALPHA, BETA, EPS, RADIUS_PX, dti_binary, kernel_from_distance  # noqa: E402

EVALUATOR_VERSION = "GEMSDOE33-HIDE-AND-RECOVER-v1.0"
LEAKAGE_AUC_THRESHOLD = 0.90
DUPLICATE_RHO_THRESHOLD = 0.90
DUPLICATE_3PX_FRACTION_THRESHOLD = 0.70


@dataclass(frozen=True)
class HideAndRecoverFold:
    fold: int
    footprint: np.ndarray
    withheld_pos: np.ndarray
    collar_mask: np.ndarray
    visible_faults: np.ndarray
    known_mask_for_scoring: np.ndarray
    train_eligible_mask: np.ndarray


def evaluator_sha256() -> str:
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def build_hide_and_recover_folds(
    catalogue: np.ndarray,
    footprint: np.ndarray,
    *,
    system_buffer_px: int = 6,
    collar_px: int = 6,
    n_folds: int = 4,
) -> list[HideAndRecoverFold]:
    """Build whole-fault-segment buffered hide-and-recover folds.

    Connected catalogue segments within ``system_buffer_px`` (default 6 px = 600 m)
    are grouped into whole fault systems and assigned to spatial-block folds by
    system centroid so no fault segment is split across folds. Around each fold's
    withheld systems, a buffer collar of ``collar_px`` pixels is excluded from the
    visible training catalogue and training domain. During scoring, all non-withheld
    catalogue pixels (``catalogue & ~withheld_pos``) are masked pixel-exactly.
    """
    catalogue = np.asarray(catalogue, dtype=bool)
    footprint = np.asarray(footprint, dtype=bool)
    if catalogue.shape != footprint.shape or catalogue.ndim != 2:
        raise ValueError("catalogue and footprint must be equal-shaped 2D masks")
    cat_in_fp = catalogue & footprint
    sys_ids = catalogue_systems(cat_in_fp, buffer_px=system_buffer_px)
    raw_masks = fold_masks(sys_ids, n_folds=n_folds)

    struct = (
        np.ones((2 * collar_px + 1, 2 * collar_px + 1), dtype=bool)
        if collar_px > 0
        else None
    )
    folds: list[HideAndRecoverFold] = []
    for idx, m in enumerate(raw_masks):
        withheld = m & cat_in_fp
        if struct is not None and withheld.any():
            dilated = binary_dilation(withheld, structure=struct)
            collar = dilated & ~withheld & footprint
        else:
            collar = np.zeros_like(footprint)
        visible = cat_in_fp & ~withheld & ~collar
        known_scoring = cat_in_fp & ~withheld
        train_eligible = footprint & ~withheld & ~collar
        folds.append(
            HideAndRecoverFold(
                fold=idx,
                footprint=footprint,
                withheld_pos=withheld,
                collar_mask=collar,
                visible_faults=visible,
                known_mask_for_scoring=known_scoring,
                train_eligible_mask=train_eligible,
            )
        )
    return folds


def _tile_contributions_binary(
    pred_mask: np.ndarray,
    withheld_pos: np.ndarray,
    valid: np.ndarray,
    known_scoring: np.ndarray,
    tile_px: int = 100,
) -> dict[tuple[int, int], tuple[float, float, float]]:
    """Decompose a fold's exact TPw, FPw, FNw into spatial tiles (tile_row, tile_col)."""
    active = valid & ~known_scoring
    pb = np.asarray(pred_mask, dtype=bool) & active
    g = np.asarray(withheld_pos, dtype=bool) & active

    if pb.any():
        d_to_p = distance_transform_edt(~pb)
        tp_per_g = kernel_from_distance(d_to_p[g])
    else:
        tp_per_g = np.zeros(int(g.sum()), dtype=np.float64)

    if g.any():
        d_to_g = distance_transform_edt(~g)
        fp_per_p = 1.0 - kernel_from_distance(d_to_g[pb])
    else:
        fp_per_p = np.ones(int(pb.sum()), dtype=np.float64)

    fn_per_g = 1.0 - tp_per_g

    tiles: dict[tuple[int, int], list[float]] = {}
    gy, gx = np.nonzero(g)
    for r, c, tp_v, fn_v in zip(gy // tile_px, gx // tile_px, tp_per_g, fn_per_g):
        key = (int(r), int(c))
        if key not in tiles:
            tiles[key] = [0.0, 0.0, 0.0]
        tiles[key][0] += float(tp_v)
        tiles[key][2] += float(fn_v)

    py, px = np.nonzero(pb)
    for r, c, fp_v in zip(py // tile_px, px // tile_px, fp_per_p):
        key = (int(r), int(c))
        if key not in tiles:
            tiles[key] = [0.0, 0.0, 0.0]
        tiles[key][1] += float(fp_v)

    return {k: (v[0], v[1], v[2]) for k, v in tiles.items()}


def pooled_dti_from_totals(tpw: float, fpw: float, fnw: float) -> float:
    denom = tpw + ALPHA * fpw + BETA * fnw + EPS
    return float(tpw / denom) if denom > 0 else 0.0


def bootstrap_pooled_ci(
    cand_tiles: Mapping[tuple[int, int], tuple[float, float, float]],
    base_tiles: Mapping[tuple[int, int], tuple[float, float, float]] | None = None,
    *,
    n_boot: int = 1000,
    seed: int = 33,
) -> dict:
    """Spatial-tile bootstrap 95% confidence interval for pooled DTI (and paired delta)."""
    all_keys = sorted(set(cand_tiles.keys()) | (set(base_tiles.keys()) if base_tiles else set()))
    if not all_keys:
        return {
            "method": "spatial_tile_bootstrap_10km",
            "n_tiles": 0,
            "n_boot": n_boot,
            "candidate_ci95": [0.0, 0.0],
            "baseline_ci95": [0.0, 0.0] if base_tiles else None,
            "delta_ci95": [0.0, 0.0] if base_tiles else None,
        }
    cand_arr = np.array([cand_tiles.get(k, (0.0, 0.0, 0.0)) for k in all_keys], dtype=np.float64)
    rng = np.random.default_rng(seed)
    n_tiles = len(all_keys)
    idx = rng.integers(0, n_tiles, size=(n_boot, n_tiles))
    cand_sums = cand_arr[idx].sum(axis=1)
    cand_dtis = cand_sums[:, 0] / (
        cand_sums[:, 0] + ALPHA * cand_sums[:, 1] + BETA * cand_sums[:, 2] + EPS
    )
    cand_ci = [float(np.percentile(cand_dtis, 2.5)), float(np.percentile(cand_dtis, 97.5))]

    if base_tiles is None:
        return {
            "method": "spatial_tile_bootstrap_10km",
            "n_tiles": n_tiles,
            "n_boot": n_boot,
            "candidate_ci95": cand_ci,
            "baseline_ci95": None,
            "delta_ci95": None,
        }

    base_arr = np.array([base_tiles.get(k, (0.0, 0.0, 0.0)) for k in all_keys], dtype=np.float64)
    base_sums = base_arr[idx].sum(axis=1)
    base_dtis = base_sums[:, 0] / (
        base_sums[:, 0] + ALPHA * base_sums[:, 1] + BETA * base_sums[:, 2] + EPS
    )
    deltas = cand_dtis - base_dtis
    base_ci = [float(np.percentile(base_dtis, 2.5)), float(np.percentile(base_dtis, 97.5))]
    delta_ci = [float(np.percentile(deltas, 2.5)), float(np.percentile(deltas, 97.5))]
    return {
        "method": "spatial_tile_bootstrap_10km",
        "n_tiles": n_tiles,
        "n_boot": n_boot,
        "candidate_ci95": cand_ci,
        "baseline_ci95": base_ci,
        "delta_ci95": delta_ci,
    }


def evaluate_hide_and_recover(
    folds: list[HideAndRecoverFold],
    predict_candidate_fn: Callable[[HideAndRecoverFold], np.ndarray],
    predict_baseline_fn: Callable[[HideAndRecoverFold], np.ndarray] | None = None,
    *,
    tile_px: int = 100,
    n_boot: int = 1000,
    seed: int = 33,
) -> dict:
    """Run hide-and-recover evaluation across all folds and compute pooled HOLDOUT-DTI + 95% CI."""
    fold_reports = []
    cand_tp = cand_fp = cand_fn = 0.0
    base_tp = base_fp = base_fn = 0.0
    total_withheld = 0

    cand_tiles_all: dict[tuple[int, int], list[float]] = {}
    base_tiles_all: dict[tuple[int, int], list[float]] = {}

    for f in folds:
        pred_c = np.asarray(predict_candidate_fn(f), dtype=bool) & f.footprint & ~f.visible_faults
        res_c = dti_binary(pred_c.astype(np.float32), f.withheld_pos, valid=f.footprint, known=f.known_mask_for_scoring)
        cand_tp += res_c["TPw"]
        cand_fp += res_c["FPw"]
        cand_fn += res_c["FNw"]
        total_withheld += int(res_c["n_truth"])

        ct = _tile_contributions_binary(pred_c, f.withheld_pos, f.footprint, f.known_mask_for_scoring, tile_px=tile_px)
        for k, v in ct.items():
            if k not in cand_tiles_all:
                cand_tiles_all[k] = [0.0, 0.0, 0.0]
            cand_tiles_all[k][0] += v[0]
            cand_tiles_all[k][1] += v[1]
            cand_tiles_all[k][2] += v[2]

        fold_entry = {
            "fold": f.fold,
            "withheld_positives": int(res_c["n_truth"]),
            "visible_fault_pixels": int(f.visible_faults.sum()),
            "collar_pixels": int(f.collar_mask.sum()),
            "candidate_emitted": int(res_c["n_emitted"]),
            "candidate_tpw": float(res_c["TPw"]),
            "candidate_fpw": float(res_c["FPw"]),
            "candidate_fnw": float(res_c["FNw"]),
            "candidate_dti": float(res_c["dti"]),
        }

        if predict_baseline_fn is not None:
            pred_b = np.asarray(predict_baseline_fn(f), dtype=bool) & f.footprint & ~f.visible_faults
            res_b = dti_binary(pred_b.astype(np.float32), f.withheld_pos, valid=f.footprint, known=f.known_mask_for_scoring)
            base_tp += res_b["TPw"]
            base_fp += res_b["FPw"]
            base_fn += res_b["FNw"]
            bt = _tile_contributions_binary(pred_b, f.withheld_pos, f.footprint, f.known_mask_for_scoring, tile_px=tile_px)
            for k, v in bt.items():
                if k not in base_tiles_all:
                    base_tiles_all[k] = [0.0, 0.0, 0.0]
                base_tiles_all[k][0] += v[0]
                base_tiles_all[k][1] += v[1]
                base_tiles_all[k][2] += v[2]
            fold_entry.update({
                "baseline_emitted": int(res_b["n_emitted"]),
                "baseline_tpw": float(res_b["TPw"]),
                "baseline_fpw": float(res_b["FPw"]),
                "baseline_fnw": float(res_b["FNw"]),
                "baseline_dti": float(res_b["dti"]),
                "delta_dti": float(res_c["dti"] - res_b["dti"]),
            })
        fold_reports.append(fold_entry)

    pooled_cand_dti = pooled_dti_from_totals(cand_tp, cand_fp, cand_fn)
    cand_tiles_tuple = {k: (v[0], v[1], v[2]) for k, v in cand_tiles_all.items()}
    base_tiles_tuple = {k: (v[0], v[1], v[2]) for k, v in base_tiles_all.items()} if predict_baseline_fn else None
    boot = bootstrap_pooled_ci(cand_tiles_tuple, base_tiles_tuple, n_boot=n_boot, seed=seed)

    result = {
        "label": "HOLDOUT-DTI",
        "evaluator_version": EVALUATOR_VERSION,
        "evaluator_sha256": evaluator_sha256(),
        "alpha": ALPHA,
        "beta": BETA,
        "kernel_radius_m": 300.0,
        "kernel_radius_px": RADIUS_PX,
        "withheld_positives": total_withheld,
        "n_folds": len(folds),
        "pooled_candidate": {
            "tpw": cand_tp,
            "fpw": cand_fp,
            "fnw": cand_fn,
            "dti": pooled_cand_dti,
            "ci95": boot["candidate_ci95"],
        },
        "bootstrap": boot,
        "folds": fold_reports,
    }

    if predict_baseline_fn is not None:
        pooled_base_dti = pooled_dti_from_totals(base_tp, base_fp, base_fn)
        pooled_delta = pooled_cand_dti - pooled_base_dti
        fold_deltas = [r["delta_dti"] for r in fold_reports]
        mean_fold_delta = float(np.mean(fold_deltas))
        if len(fold_deltas) >= 2:
            sd = float(np.std(fold_deltas, ddof=1))
            se = sd / np.sqrt(len(fold_deltas))
            tcrit = float(student_t.ppf(0.975, df=len(fold_deltas) - 1))
            fold_t_ci = [mean_fold_delta - tcrit * se, mean_fold_delta + tcrit * se]
        else:
            fold_t_ci = [mean_fold_delta, mean_fold_delta]
        result["pooled_baseline"] = {
            "tpw": base_tp,
            "fpw": base_fp,
            "fnw": base_fn,
            "dti": pooled_base_dti,
            "ci95": boot["baseline_ci95"],
        }
        result["pooled_delta_dti"] = pooled_delta
        result["pooled_delta_ci95"] = boot["delta_ci95"]
        result["mean_fold_delta_dti"] = mean_fold_delta
        result["fold_student_t_ci95"] = fold_t_ci
        result["positive_folds"] = int(sum(1 for d in fold_deltas if d > 0))
    return result


def leakage_canary_auc(
    feature: np.ndarray,
    folds: list[HideAndRecoverFold],
    *,
    max_neg_per_fold: int = 50000,
    seed: int = 33,
) -> dict:
    """Test a single feature alone on the hide-and-recover holdout (two-polarity ROC AUC).

    AUC > 0.90 flags potential target leakage until proven otherwise (Protocol Rule 4).
    """
    feat = np.asarray(feature, dtype=np.float32)
    rng = np.random.default_rng(seed)
    all_pos = []
    all_neg = []
    fold_aucs = []

    for f in folds:
        pos_mask = f.withheld_pos & np.isfinite(feat)
        neg_mask = f.train_eligible_mask & ~f.visible_faults & np.isfinite(feat)
        pos_vals = feat[pos_mask]
        neg_idx = np.flatnonzero(neg_mask)
        if pos_vals.size == 0 or neg_idx.size == 0:
            continue
        if neg_idx.size > max_neg_per_fold:
            pick = rng.choice(neg_idx, size=max_neg_per_fold, replace=False)
            neg_vals = feat.ravel()[pick]
        else:
            neg_vals = feat.ravel()[neg_idx]
        y = np.concatenate([np.ones(pos_vals.size, dtype=np.uint8), np.zeros(neg_vals.size, dtype=np.uint8)])
        s = np.concatenate([pos_vals, neg_vals])
        raw_auc = float(roc_auc_score(y, s))
        two_sided = max(raw_auc, 1.0 - raw_auc)
        fold_aucs.append(two_sided)
        all_pos.append(pos_vals)
        all_neg.append(neg_vals)

    if not all_pos:
        return {"raw_auc": 0.5, "canary_auc": 0.5, "leakage_flag": False, "fold_aucs": []}

    pos_cat = np.concatenate(all_pos)
    neg_cat = np.concatenate(all_neg)
    y_pool = np.concatenate([np.ones(pos_cat.size, dtype=np.uint8), np.zeros(neg_cat.size, dtype=np.uint8)])
    s_pool = np.concatenate([pos_cat, neg_cat])
    raw_pool = float(roc_auc_score(y_pool, s_pool))
    canary_pool = max(raw_pool, 1.0 - raw_pool)
    return {
        "raw_auc": round(raw_pool, 6),
        "canary_auc": round(canary_pool, 6),
        "max_fold_auc": round(float(max(fold_aucs)), 6),
        "leakage_flag": bool(canary_pool > LEAKAGE_AUC_THRESHOLD or max(fold_aucs) > LEAKAGE_AUC_THRESHOLD),
        "threshold": LEAKAGE_AUC_THRESHOLD,
        "fold_aucs": [round(a, 6) for a in fold_aucs],
    }


def screen_against_registry(
    surface: np.ndarray,
    dots: np.ndarray,
    footprint: np.ndarray,
    registry_paths: Mapping[str, Path],
    *,
    rho_threshold: float = DUPLICATE_RHO_THRESHOLD,
    overlap_3px_threshold: float = DUPLICATE_3PX_FRACTION_THRESHOLD,
    subsample_step: int = 3,
) -> dict:
    """Check pre-placement score surface AND final dots against registry rasters (Protocol Rule 1).

    Triggers duplicate stop if:
      - pre-placement surface Spearman |rho| > 0.90 against any registry raster, OR
      - final dots Spearman rho > 0.90 against any registry raster, OR
      - > 70% of candidate dots fall within 3.0 px of any registry raster's positive dots.
    """
    footprint = np.asarray(footprint, dtype=bool)
    surf = np.asarray(surface, dtype=np.float32)
    dots_b = np.asarray(dots, dtype=bool) & footprint
    n_cand = int(dots_b.sum())

    # Subsample footprint deterministically for fast exact rank correlation on 5.16M cells
    fp_indices = np.flatnonzero(footprint)[::subsample_step]
    surf_sub = np.nan_to_num(surf.ravel()[fp_indices], nan=0.0)
    dots_sub = dots_b.ravel()[fp_indices].astype(np.float32)

    comparisons = []
    any_surface_dup = False
    any_dot_dup = False

    for label_name, path in sorted(registry_paths.items()):
        path = Path(path)
        if not path.is_file():
            continue
        with rasterio.open(path) as src:
            if (src.height, src.width) != footprint.shape:
                continue
            arr = src.read(1)
        reg_sub = np.nan_to_num(arr.ravel()[fp_indices], nan=0.0)
        reg_pos = np.isfinite(arr) & (arr > 0) & footprint
        n_reg = int(reg_pos.sum())

        if np.std(surf_sub) > 0 and np.std(reg_sub) > 0:
            rho_surf = float(spearmanr(surf_sub, reg_sub).statistic)
        else:
            rho_surf = 0.0

        reg_pos_sub = reg_pos.ravel()[fp_indices].astype(np.float32)
        if np.std(dots_sub) > 0 and np.std(reg_pos_sub) > 0:
            rho_dots = float(spearmanr(dots_sub, reg_pos_sub).statistic)
        else:
            rho_dots = 0.0

        if n_cand > 0 and n_reg > 0:
            d_reg = distance_transform_edt(~reg_pos)
            within_3px = int((d_reg[dots_b] <= 3.0).sum())
            frac_3px = float(within_3px / n_cand)
        else:
            within_3px = 0
            frac_3px = 0.0

        surf_trig = bool(abs(rho_surf) > rho_threshold)
        dot_trig = bool(rho_dots > rho_threshold or frac_3px > overlap_3px_threshold)
        any_surface_dup = any_surface_dup or surf_trig
        any_dot_dup = any_dot_dup or dot_trig

        comparisons.append({
            "registry_id": label_name,
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "registry_positive_pixels": n_reg,
            "surface_spearman_rho": round(rho_surf, 6),
            "surface_duplicate_trigger": surf_trig,
            "dots_spearman_rho": round(rho_dots, 6),
            "candidate_dots_within_3px": within_3px,
            "candidate_dots_total": n_cand,
            "fraction_within_3px": round(frac_3px, 6),
            "dots_duplicate_trigger": dot_trig,
            "duplicate_trigger": bool(surf_trig or dot_trig),
        })

    max_surf_rho = max((abs(c["surface_spearman_rho"]) for c in comparisons), default=0.0)
    max_dots_rho = max((c["dots_spearman_rho"] for c in comparisons), default=0.0)
    max_frac_3px = max((c["fraction_within_3px"] for c in comparisons), default=0.0)

    return {
        "candidate_positive_pixels": n_cand,
        "n_registry_rasters_checked": len(comparisons),
        "rho_threshold": rho_threshold,
        "overlap_3px_threshold": overlap_3px_threshold,
        "max_abs_surface_spearman_rho": round(max_surf_rho, 6),
        "max_dots_spearman_rho": round(max_dots_rho, 6),
        "max_fraction_within_3px": round(max_frac_3px, 6),
        "surface_duplicate_triggered": any_surface_dup,
        "dots_duplicate_triggered": any_dot_dup,
        "duplicate_triggered": bool(any_surface_dup or any_dot_dup),
        "comparisons": comparisons,
    }


if __name__ == "__main__":
    print(json.dumps({
        "evaluator_version": EVALUATOR_VERSION,
        "evaluator_sha256": evaluator_sha256(),
    }, indent=2))
