#!/usr/bin/env python3
"""Execute pre-registered H-K1 HTCADS experiments (EXP-1, EXP-2, EXP-3), uniqueness audit, and Run Card.

Strictly obeys Parallel-Run Protocol Rules 1-6:
  - Rule 1: Checks continuous surface BEFORE placement AND final dots AFTER placement against the entire
            local GEMSDOE raster registry (rank-correlation < 0.90 AND <= 70% 3-px dot overlap).
  - Rule 2: Uses shared cached feature stack + leak-free Hide-and-Recover holdout (whole fault segments
            withheld with 1.5 km collar; training strictly >5 km outside test quadrant; catalogue features
            and collars derived strictly from fold-visible faults).
  - Rule 3: Every metric strictly labeled HOLDOUT-DTI (evaluator, N withheld positives, 95% CI) or
            ORGANIZER-CONFIRMED. Never writes a projection as a score.
  - Rule 4: Verifies Leakage Canary passed (all 50 features <= 0.90 AUC) prior to training.
  - Rule 5-6: Stops at 3 pre-registered experiments (< 2 hours), emits JSON Run Card, and runs automated
              5-gate GeoTIFF validator without human inspection.
"""
from __future__ import annotations

import gc
import glob
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt, gaussian_filter
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import holdout, htcads, submission  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402

# Exact 29 integer offsets (dy, dx) satisfying Euclidean distance <= 3.0 px (dy^2 + dx^2 <= 9)
_D3_OFFS: list[tuple[int, int]] = [
    (dy, dx) for dy in range(-3, 4) for dx in range(-3, 4) if dy * dy + dx * dx <= 9
]

# Smooth >25-km regional fields & tpi_1200m valley-only bias excluded from local centerline tree splits
# (used only as a bounded smooth tectonic-geothermal favorability multiplier so trees cannot memorize coarse lat/lon blobs)
_REGIONAL_BLOB_COLS = {20, 21, 22, 24, 25, 26, 27, 33, 35}


def _predict_chunked(model: lgb.LGBMClassifier, X: np.ndarray, cols: list[int] | None = None, chunk: int = 1_100_000) -> np.ndarray:
    n = X.shape[0]
    out = np.empty(n, dtype=np.float32)
    for start in range(0, n, chunk):
        end = min(start + chunk, n)
        sub = np.asarray(X[start:end] if cols is None else X[start:end, cols], dtype=np.float32)
        out[start:end] = model.predict_proba(sub)[:, 1].astype(np.float32)
    return out


def _logit(p: np.ndarray, eps: float = 1e-6) -> np.ndarray:
    pc = np.clip(p, eps, 1.0 - eps)
    return np.log(pc / (1.0 - pc)).astype(np.float32)


def _sigmoid(x: np.ndarray) -> np.ndarray:
    xc = np.clip(x, -20.0, 20.0)
    return (1.0 / (1.0 + np.exp(-xc))).astype(np.float32)


def _unit_rank_vec(v: np.ndarray) -> np.ndarray | None:
    r = rankdata(v, method="average").astype(np.float64)
    r -= r.mean()
    nrm = float(np.linalg.norm(r))
    if nrm < 1e-12:
        return None
    return (r / nrm).astype(np.float32)


def _build_physical_conduit_scores(X_sub: np.ndarray, X_lid: np.ndarray, lidar_valid_fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """First-principles label-free Multi-Physics Conduit score (immunizes against Qfaults valley-floor selection bias).

    Returns:
      - phys_exp1 (LiDAR-blind, excludes grav_updip_proj col 4)
      - phys_exp2 (adds H-K2 FFT updip-projected gravity col 4 + zero-mean contour-orthogonal 1 m LiDAR scarp enhancement)
    """
    n = X_sub.shape[0]
    p1 = np.empty(n, dtype=np.float32)
    p2 = np.empty(n, dtype=np.float32)
    chunk = 1_100_000

    # Precompute zero-mean LiDAR scarp enhancement inside lidar_valid_fp
    lid_w = np.asarray(X_lid[:, 8], dtype=np.float32)  # 500 m contour-orthogonal LiDAR scarp worm
    lid_c = np.asarray(X_lid[:, 9], dtype=np.float32)  # subsurface-corroborated LiDAR scarp
    lid_raw = 0.65 * lid_w + 0.35 * lid_c
    lid_mean = float(np.mean(lid_raw[lidar_valid_fp]))
    lid_zero_mean = np.where(lidar_valid_fp, lid_raw - lid_mean, 0.0).astype(np.float32)
    del lid_w, lid_c, lid_raw

    for s in range(0, n, chunk):
        e = min(s + chunk, n)
        b = np.asarray(X_sub[s:e], dtype=np.float32)

        # Geomorphic scarp-slope, piedmont toe concavity & slope-ridge centerline (100 m DEM)
        l_geom = 0.34 * b[:, 31] + 0.24 * b[:, 30] + 0.14 * b[:, 29] + 0.12 * b[:, 34]

        # Subsurface potential-field & basement ridges (EXP-1 excludes col 4 grav_updip_proj; EXP-2 includes it)
        l_sub_1 = np.maximum.reduce([b[:, 1], b[:, 2], b[:, 3], b[:, 6], b[:, 8], b[:, 9], b[:, 10]])
        l_sub_2 = np.maximum.reduce([l_sub_1, 1.15 * b[:, 4]])

        # Hydrothermal demagnetization, K/Th metasomatism, U/Th redox & MT clay-cap lateral boundary
        l_hydro_alt = np.maximum.reduce([b[:, 14], b[:, 15], b[:, 16], b[:, 17], b[:, 18], b[:, 23]])

        # Bounded smooth regional tectonic-geothermal favorability (GDR 1391 2m F2mDAB/geotherm + GPS transtension + seismicity)
        reg_fav = 1.0 + 0.16 * np.tanh(
            0.45 * b[:, 20] + 0.35 * b[:, 21] + 0.35 * b[:, 22] + 0.30 * b[:, 24] + 0.20 * np.maximum(b[:, 27], 0.0)
        )

        base_1 = (l_geom + 0.11 * l_sub_1 + 0.09 * l_hydro_alt) * reg_fav
        base_2 = (l_geom + 0.12 * l_sub_2 + 0.09 * l_hydro_alt + 0.075 * lid_zero_mean[s:e]) * reg_fav

        p1[s:e] = np.clip(base_1, 0.0, 1.0).astype(np.float32)
        p2[s:e] = np.clip(base_2, 0.0, 1.0).astype(np.float32)

    # Normalize onto matching [0, 0.12] expected-inclusion scale
    p1 *= 0.045 / (float(np.percentile(p1, 99.2)) + 1e-6)
    p2 *= 0.045 / (float(np.percentile(p2, 99.2)) + 1e-6)
    return np.clip(p1, 0.0, 0.12), np.clip(p2, 0.0, 0.12)


def _collect_registry_rasters(foot: np.ndarray) -> tuple[list[dict], np.ndarray, set[str]]:
    """Load and deduplicate all valid-grid local GEMSDOE registry rasters in <50 MB RAM with pre-ranked vectors."""
    ddir = data_dir()
    cand_paths = sorted(set(
        glob.glob(str(ddir / "scored" / "*.tif"))
        + glob.glob(str(ddir / "scored_extra" / "*.tif"))
        + glob.glob("/tmp/explore/GEMSDOE*/docs/downloads/*.tif")
        + glob.glob("/tmp/explore/GEMSDOE*/submissions/*.tif")
    ))
    H, W = foot.shape
    n_fp = int(foot.sum())
    seen_fp_hash: dict[str, str] = {}
    all_file_shas: set[str] = set()
    records: list[dict] = []

    rng = np.random.default_rng(20261026)
    sample_idx = rng.choice(n_fp, size=80_000, replace=False)
    sample_idx.sort()

    scratch_pad = np.zeros((H + 6, W + 6), dtype=bool)
    fy_samp, fx_samp = np.nonzero(foot)
    fy_cov = fy_samp[sample_idx] + 3
    fx_cov = fx_samp[sample_idx] + 3
    del fy_samp, fx_samp

    for p_str in cand_paths:
        p = Path(p_str)
        try:
            all_file_shas.add(submission.sha256_file(p))
            with rasterio.open(p) as ds:
                if (ds.height, ds.width) != (H, W):
                    continue
                arr = ds.read(1)
        except Exception:
            continue

        af = np.where(np.isfinite(arr[foot]), arr[foot], 0.0).astype(np.float32)
        h_fp = hashlib.sha256(np.round(af, 5).tobytes()).hexdigest()[:16]
        if h_fp in seen_fp_hash:
            continue
        seen_fp_hash[h_fp] = p.name

        n_frac = int(np.sum((af > 1e-5) & (af < 1.0 - 1e-5)))
        is_cont = n_frac > 1000
        m_dots = foot & np.isfinite(arr) & (arr >= 0.5)
        ry, rx = np.nonzero(m_dots)
        n_dots = int(ry.size)
        if n_dots == 0 and not is_cont:
            continue

        cov3_fp = 0.0
        if n_dots > 0:
            scratch_pad[ry + 3, rx + 3] = True
            hit_cov = np.zeros(sample_idx.size, dtype=bool)
            for dy, dx in _D3_OFFS:
                hit_cov |= scratch_pad[fy_cov + dy, fx_cov + dx]
            cov3_fp = float(hit_cov.mean())
            scratch_pad[ry + 3, rx + 3] = False

        is_uniform_calibration_lattice = bool(cov3_fp > 0.50 or "lattice-s5" in p.name)
        records.append({
            "name": p.name,
            "path": str(p),
            "is_continuous": is_cont,
            "is_calibration_lattice": is_uniform_calibration_lattice,
            "n_dots": n_dots,
            "cov3_of_footprint": round(cov3_fp, 5),
            "unit_rank": _unit_rank_vec(af[sample_idx]),
            "ry": ry.astype(np.int16) if n_dots > 0 else None,
            "rx": rx.astype(np.int16) if n_dots > 0 else None,
        })
    return records, sample_idx, all_file_shas


def _check_uniqueness(
    pi_full_2d: np.ndarray,
    dots_2d: np.ndarray,
    foot: np.ndarray,
    registry: list[dict],
    sample_idx: np.ndarray,
) -> dict:
    """Protocol Rule 1: Check rank-correlation < 0.90 AND 3-px dot overlap <= 0.70 on BOTH continuous & final dots."""
    H, W = foot.shape
    u_pi = _unit_rank_vec(pi_full_2d[foot][sample_idx])
    u_dots = _unit_rank_vec(dots_2d[foot][sample_idx].astype(np.float32))

    oy, ox = np.nonzero(dots_2d)
    n_our = int(oy.size)
    oy_p = oy + 3
    ox_p = ox + 3
    our_d3 = distance_transform_edt(~dots_2d) <= 3.0
    scratch_pad = np.zeros((H + 6, W + 6), dtype=bool)

    max_cont_spearman = -1.0
    max_cont_peer = ""
    max_dots_spearman = -1.0
    max_dots_spearman_peer = ""
    max_asym_3px_detector = -1.0
    max_asym_3px_peer = ""
    max_sym_3px_all = -1.0
    max_sym_3px_peer = ""
    calibration_probes_logged = []
    top_peers = []

    for rec in registry:
        ur = rec["unit_rank"]
        if ur is not None and u_pi is not None and u_dots is not None:
            rc_cont = abs(float(np.dot(u_pi, ur)))
            rc_dots = abs(float(np.dot(u_dots, ur)))
        else:
            rc_cont, rc_dots = 0.0, 0.0

        if rc_cont > max_cont_spearman:
            max_cont_spearman = rc_cont
            max_cont_peer = rec["name"]
        if rc_dots > max_dots_spearman:
            max_dots_spearman = rc_dots
            max_dots_spearman_peer = rec["name"]

        if rec["ry"] is not None and rec["n_dots"] > 0:
            ry = rec["ry"].astype(np.int32)
            rx = rec["rx"].astype(np.int32)
            scratch_pad[ry + 3, rx + 3] = True
            hit = np.zeros(n_our, dtype=bool)
            for dy, dx in _D3_OFFS:
                hit |= scratch_pad[oy_p + dy, ox_p + dx]
            scratch_pad[ry + 3, rx + 3] = False

            ov_our_in_reg = float(hit.sum()) / max(n_our, 1)
            ov_reg_in_our = float(our_d3[ry, rx].sum()) / max(rec["n_dots"], 1)
            sym_ov = (
                2.0 * ov_our_in_reg * ov_reg_in_our / (ov_our_in_reg + ov_reg_in_our)
                if (ov_our_in_reg + ov_reg_in_our) > 0
                else 0.0
            )
            if sym_ov > max_sym_3px_all:
                max_sym_3px_all = sym_ov
                max_sym_3px_peer = rec["name"]

            if rec["is_calibration_lattice"]:
                calibration_probes_logged.append({
                    "name": rec["name"],
                    "n_dots": rec["n_dots"],
                    "footprint_3px_coverage": rec["cov3_of_footprint"],
                    "asym_frac_in_3px": round(ov_our_in_reg, 6),
                    "reverse_frac_reg_in_our_3px": round(ov_reg_in_our, 6),
                    "harmonic_3px_overlap": round(sym_ov, 6),
                    "note": "Uniform 5-px calibration lattice covering 99.87% of footprint within 3 px (IR-REG-LATTICE-03); non-detector probe.",
                })
            else:
                if ov_our_in_reg > max_asym_3px_detector:
                    max_asym_3px_detector = ov_our_in_reg
                    max_asym_3px_peer = rec["name"]
                top_peers.append({
                    "peer": rec["name"],
                    "peer_dots": rec["n_dots"],
                    "asym_3px_overlap": round(ov_our_in_reg, 6),
                    "harmonic_3px_overlap": round(sym_ov, 6),
                    "continuous_spearman": round(rc_cont, 6),
                    "final_dots_spearman": round(rc_dots, 6),
                })

    top_peers.sort(key=lambda d: d["asym_3px_overlap"], reverse=True)
    passed = bool(
        max_cont_spearman < 0.90
        and max_dots_spearman < 0.90
        and max_asym_3px_detector <= 0.70
        and max_sym_3px_all <= 0.70
    )
    return {
        "passed": passed,
        "unique_rasters_checked": len(registry),
        "pre_placement_surface_max_abs_spearman": round(max_cont_spearman, 6),
        "pre_placement_closest_peer": max_cont_peer,
        "final_dots_max_abs_spearman": round(max_dots_spearman, 6),
        "final_dots_closest_spearman_peer": max_dots_spearman_peer,
        "final_dots_max_detector_3px_overlap": round(max_asym_3px_detector, 6),
        "final_dots_closest_3px_detector_peer": max_asym_3px_peer,
        "final_dots_max_harmonic_3px_overlap_all": round(max_sym_3px_all, 6),
        "final_dots_closest_harmonic_peer": max_sym_3px_peer,
        "calibration_lattice_probes_logged": calibration_probes_logged,
        "top_10_closest_detector_peers": top_peers[:10],
    }


def main() -> int:
    t_start = time.time()
    ddir = data_dir()
    wdir = work_dir()
    edir = evidence_dir()

    frozen_experiment_path = edir / "htcads_experiments.json"
    if frozen_experiment_path.exists():
        frozen = json.loads(frozen_experiment_path.read_text(encoding="utf-8"))
        used = int(frozen.get("within_protocol_budget", {}).get("experiments_run", len(frozen.get("experiments", []))))
        limit = int(frozen.get("within_protocol_budget", {}).get("max_experiments_allowed", 3))
        if used >= limit:
            raise SystemExit(
                f"HTCADS experiment cap exhausted ({used}/{limit}); reruns are disabled. "
                "Use scripts/evaluate_holdout.py only for a separately authorized evaluation."
            )

    canary_path = edir / "leakage_canary.json"
    if not canary_path.exists():
        raise SystemExit("Missing evidence/leakage_canary.json — run scripts/prepare_data.py first.")
    canary = json.loads(canary_path.read_text(encoding="utf-8"))
    if not canary.get("passed"):
        raise SystemExit("Leakage canary did not pass; aborting experiments.")
    print(f"[HTCADS] Verified Rule 4 Leakage Canary PASSED (max single-feature AUC = {canary['max_single_feature_auc']:.4f} <= 0.90).")

    stack = htcads.build_static_feature_stack(ddir, wdir)
    foot = stack["foot"]
    lidar_valid_fp = stack["lidar_valid_fp"]
    X_sub = stack["X_sub"]
    X_lid = stack["X_lid"]
    n_fp = int(foot.sum())

    ctx = holdout.load_holdout_context(ddir)
    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(n_fp, dtype=np.int32)

    with rasterio.open(ddir / "scored" / "GEMSDOE25__gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        a_d28 = ds.read(1)
        d28_mask = foot & np.isfinite(a_d28) & (a_d28 >= 0.5)
        del a_d28
    with rasterio.open(ddir / "scored" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as ds:
        a_b2 = ds.read(1)
        b2_static_mask = foot & np.isfinite(a_b2) & (a_b2 >= 0.5)
        del a_b2

    ref_hr = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, n_boot=1000, seed=20261026, name="GEMSDOE32_B2_0p2778_ref")
    ref_sg = holdout.evaluate_sgmc_with_ci(b2_static_mask, ctx, n_boot=1000, seed=20261026, name="GEMSDOE32_B2_0p2778_ref")
    del d28_mask, b2_static_mask
    print(
        f"[HTCADS] Reference 0.2778 Champion benchmark: "
        f"Hide-and-Recover={ref_hr['pooled_dti']:.6f} (95% CI [{ref_hr['ci95_cluster_bootstrap'][0]:.4f}, {ref_hr['ci95_cluster_bootstrap'][1]:.4f}]), "
        f"SGMC-CAL={ref_sg['sgmc_prevalence_calibrated_dti']:.6f}"
    )

    # Scale-separated sharp 100 m - 1.5 km conduit features (fixes IR-KG2-BUG-02 coarse lat/lon blob overfitting)
    sharp_cols_exp2 = [i for i in range(len(htcads.SUBSURF_FEATURE_NAMES)) if i not in _REGIONAL_BLOB_COLS]
    sharp_cols_exp1 = [i for i in sharp_cols_exp2 if i != 4]  # EXP-1 excludes grav_updip_proj (col 4)

    phys_exp1_fp, phys_exp2_fp = _build_physical_conduit_scores(X_sub, X_lid, lidar_valid_fp)

    rng = np.random.default_rng(20261026)
    labels_dil3 = binary_dilation(ctx.labels, structure=np.ones((3, 3), bool), iterations=3)

    gbdt_blind_exp1_oof = np.zeros(n_fp, dtype=np.float32)
    gbdt_blind_exp1_full = np.zeros(n_fp, dtype=np.float32)
    gbdt_blind_exp2_oof = np.zeros(n_fp, dtype=np.float32)
    gbdt_blind_exp2_full = np.zeros(n_fp, dtype=np.float32)
    lid_resid_oof_fp = np.zeros(n_fp, dtype=np.float32)
    lid_resid_full_fp = np.zeros(n_fp, dtype=np.float32)

    blind_importances = np.zeros(len(sharp_cols_exp2), dtype=np.float64)
    lidar_importances = np.zeros(len(htcads.LIDAR_FEATURE_NAMES), dtype=np.float64)

    for fold in holdout.FOLDS:
        t0 = time.time()
        q_mask = (ctx.quad == fold) & foot
        q_fp = fp_idx_2d[q_mask]
        collar = binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar

        pos_2d = binary_dilation(ctx.labels & tdom, structure=np.ones((3, 3), bool), iterations=1) & tdom
        neg_2d = tdom & ~labels_dil3
        pos_idx = fp_idx_2d[pos_2d]
        neg_idx = fp_idx_2d[neg_2d]

        if pos_idx.size > 38_000:
            pos_idx = rng.choice(pos_idx, size=38_000, replace=False)
        neg_sub = rng.choice(neg_idx, size=min(neg_idx.size, pos_idx.size * 4), replace=False)
        tr_idx = np.concatenate([pos_idx, neg_sub])
        y_tr = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_sub.size, dtype=np.int8)])

        clf_b1 = lgb.LGBMClassifier(
            n_estimators=125,
            learning_rate=0.065,
            num_leaves=31,
            min_child_samples=100,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.75,
            reg_alpha=2.0,
            reg_lambda=8.0,
            random_state=100 + fold,
            n_jobs=4,
            verbose=-1,
        )
        clf_b1.fit(np.asarray(X_sub[tr_idx][:, sharp_cols_exp1], dtype=np.float32), y_tr)
        pred_b1_all = _predict_chunked(clf_b1, X_sub, cols=sharp_cols_exp1)
        gbdt_blind_exp1_oof[q_fp] = pred_b1_all[q_fp]
        gbdt_blind_exp1_full += 0.25 * pred_b1_all
        del clf_b1, pred_b1_all

        clf_b2 = lgb.LGBMClassifier(
            n_estimators=135,
            learning_rate=0.065,
            num_leaves=31,
            min_child_samples=100,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.75,
            reg_alpha=2.0,
            reg_lambda=8.0,
            random_state=200 + fold,
            n_jobs=4,
            verbose=-1,
        )
        clf_b2.fit(np.asarray(X_sub[tr_idx][:, sharp_cols_exp2], dtype=np.float32), y_tr)
        blind_importances += 0.25 * clf_b2.booster_.feature_importance(importance_type="gain")
        pred_b2_all = _predict_chunked(clf_b2, X_sub, cols=sharp_cols_exp2)
        gbdt_blind_exp2_oof[q_fp] = pred_b2_all[q_fp]
        gbdt_blind_exp2_full += 0.25 * pred_b2_all
        del clf_b2, pred_b2_all
        gc.collect()

        pos_lid = pos_idx[lidar_valid_fp[pos_idx]]
        neg_lid_pool = neg_idx[lidar_valid_fp[neg_idx]]
        neg_lid = rng.choice(neg_lid_pool, size=min(neg_lid_pool.size, pos_lid.size * 4), replace=False)
        tr_lid = np.concatenate([pos_lid, neg_lid])
        y_lid = np.concatenate([np.ones(pos_lid.size, dtype=np.int8), np.zeros(neg_lid.size, dtype=np.int8)])

        clf_lid = lgb.LGBMClassifier(
            n_estimators=115,
            learning_rate=0.065,
            num_leaves=23,
            min_child_samples=100,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.85,
            reg_alpha=2.5,
            reg_lambda=8.0,
            random_state=300 + fold,
            n_jobs=4,
            verbose=-1,
        )
        clf_lid.fit(np.asarray(X_lid[tr_lid], dtype=np.float32), y_lid)
        lidar_importances += 0.25 * clf_lid.booster_.feature_importance(importance_type="gain")
        raw_lid_all = _predict_chunked(clf_lid, X_lid, cols=None)
        log_lid = _logit(raw_lid_all)
        mean_log_lid = float(np.mean(log_lid[lidar_valid_fp]))
        resid_lid = np.where(lidar_valid_fp, log_lid - mean_log_lid, 0.0).astype(np.float32)
        lid_resid_oof_fp[q_fp] = resid_lid[q_fp]
        lid_resid_full_fp += 0.25 * resid_lid
        del clf_lid, raw_lid_all, log_lid, resid_lid
        gc.collect()
        print(f"[HTCADS] Trained Quadrant {fold} Blind + LiDAR specialists in {time.time()-t0:.1f}s")

    # Normalize supervised GBDT blind probabilities onto the same [0, 0.12] expected-inclusion scale as phys_conduit
    def _scale_blind(p_gbdt: np.ndarray, phys_fp: np.ndarray, lid_res: np.ndarray | None = None) -> np.ndarray:
        if lid_res is not None:
            p_g = _sigmoid(_logit(p_gbdt) + 0.55 * lid_res)
        else:
            p_g = p_gbdt
        p_g_norm = np.clip(p_g * (0.045 / (float(np.percentile(p_g, 99.2)) + 1e-6)), 0.0, 0.12)
        # 45% supervised out-of-quadrant GBDT + 55% label-free first-principles Multi-Physics Conduit
        return (0.45 * p_g_norm + 0.55 * phys_fp).astype(np.float32)

    pi_blind_exp1_oof = _scale_blind(gbdt_blind_exp1_oof, phys_exp1_fp, lid_res=None)
    pi_blind_exp1_full = _scale_blind(gbdt_blind_exp1_full, phys_exp1_fp, lid_res=None)
    pi_blind_exp2_oof = _scale_blind(gbdt_blind_exp2_oof, phys_exp2_fp, lid_res=lid_resid_oof_fp)
    pi_blind_exp2_full = _scale_blind(gbdt_blind_exp2_full, phys_exp2_fp, lid_res=lid_resid_full_fp)
    del gbdt_blind_exp1_oof, gbdt_blind_exp1_full, gbdt_blind_exp2_oof, gbdt_blind_exp2_full, phys_exp1_fp, phys_exp2_fp
    gc.collect()

    # -------------------------------------------------------------------------
    # STEP 2: Purely Directional Tip & Step-Over Specialist (`P_tip`)
    # Fixes IR-KG2-BUG-01: Uses ONLY [vis_tip_cone, vis_relay_bridge] (cols 1, 2 — ZERO isotropic d_vis!),
    # AND strictly multiplies output by `tip_env = max(vis_tip_cone, vis_relay_bridge)^0.65`, so P_tip is
    # IDENTICALLY ZERO along all planar fault flanks and cannot form a d=3 px annulus ring!
    # -------------------------------------------------------------------------
    print("[HTCADS] Computing full-catalogue directional tip/relay features for live deployment surface...")
    X_vis_full_cat, aux_full_cat = htcads.compute_visible_catalogue_features(ctx.labels, foot)
    vis_cols_pure_dir = [1, 2]  # ONLY vis_tip_cone and vis_relay_bridge!
    X_vis_full_dir = X_vis_full_cat[:, vis_cols_pure_dir].copy()
    tip_env_full_fp = (np.clip(np.maximum(X_vis_full_dir[:, 0], X_vis_full_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
    del X_vis_full_cat

    d_full_2d = aux_full_cat["d_vis"]
    elig_b2_live = foot & (d_full_2d > 2.0)
    elig_aniso_live = foot & np.where(
        (aux_full_cat["tip_cone_2d"] >= 0.55) | (aux_full_cat["relay_2d"] >= 0.45),
        d_full_2d > 1.45,
        d_full_2d > 2.15,
    )
    del aux_full_cat
    gc.collect()

    def _to_2d(vec_fp: np.ndarray) -> np.ndarray:
        g = np.zeros(foot.shape, dtype=np.float32)
        g[foot] = vec_fp
        return g

    def _axial_enhance_2d(pi_2d: np.ndarray, foot_m: np.ndarray) -> np.ndarray:
        """Gentle strike-preserving ridge continuity filter applied BEFORE eligibility collar masking."""
        sm = gaussian_filter(pi_2d, sigma=0.50, mode="nearest")
        out = (0.86 * pi_2d + 0.14 * sm).astype(np.float32)
        out[~foot_m] = 0.0
        return out

    cell_em_by_exp: dict[str, dict[str, np.ndarray]] = {"EXP-1": {}, "EXP-2": {}, "EXP-3": {}}
    p_tip_exp1_live_fp = np.zeros(n_fp, dtype=np.float32)
    p_tip_exp2_live_fp = np.zeros(n_fp, dtype=np.float32)

    for idx_c, cell in enumerate(ctx.cells):
        t0 = time.time()
        collar = binary_dilation(ctx.quad == cell.fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar

        X_vis_cell, aux_cell = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
        X_vis_cell_dir = X_vis_cell[:, vis_cols_pure_dir].copy()
        tip_env_cell_fp = (np.clip(np.maximum(X_vis_cell_dir[:, 0], X_vis_cell_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
        del X_vis_cell

        d_vis_2d = aux_cell["d_vis"]
        elig_b2_c = foot & (d_vis_2d > 2.0)
        elig_aniso_c = foot & np.where(
            (aux_cell["tip_cone_2d"] >= 0.55) | (aux_cell["relay_2d"] >= 0.45),
            d_vis_2d > 1.45,
            d_vis_2d > 2.15,
        )
        del aux_cell

        # Train P_tip STRICTLY inside active tip/relay corridors (tip_env > 0.02) in tdom so it learns
        # which forward tip cones & relay ramps actually host blind fault continuations vs inactive tips!
        active_tip_zone_fp = tip_env_cell_fp > 0.02
        active_tip_2d = np.zeros(foot.shape, dtype=bool)
        active_tip_2d[foot] = active_tip_zone_fp

        hid_train_core = (ctx.labels & tdom) & ~cell.visible_full
        hid_train_pos_2d = binary_dilation(hid_train_core, structure=np.ones((3, 3), bool), iterations=1) & tdom & (d_vis_2d > 1.4) & active_tip_2d
        neg_tip_2d = tdom & ~labels_dil3 & (d_vis_2d > 1.4) & active_tip_2d
        pos_fp = fp_idx_2d[hid_train_pos_2d]
        neg_cand_fp = fp_idx_2d[neg_tip_2d]
        del d_vis_2d, hid_train_core, hid_train_pos_2d, neg_tip_2d, active_tip_2d

        neg_fp = rng.choice(neg_cand_fp, size=min(neg_cand_fp.size, pos_fp.size * 5), replace=False)
        tr_fp = np.concatenate([pos_fp, neg_fp])
        y_tr = np.concatenate([np.ones(pos_fp.size, dtype=np.int8), np.zeros(neg_fp.size, dtype=np.int8)])
        X_vis_dir_tr = X_vis_cell_dir[tr_fp]

        do_live = cell.seed == 20
        nz_cell = np.flatnonzero(active_tip_zone_fp)
        nz_live = np.flatnonzero(tip_env_full_fp > 0.02) if do_live else None

        # EXP-1 Tip/Relay model (ONLY predicts on active tip/relay pixels ~7% of footprint -> 14x faster!)
        clf_t1 = lgb.LGBMClassifier(
            n_estimators=115,
            learning_rate=0.06,
            num_leaves=23,
            min_child_samples=60,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.80,
            reg_alpha=2.0,
            reg_lambda=8.0,
            random_state=400 + idx_c,
            n_jobs=4,
            verbose=-1,
        )
        clf_t1.fit(np.hstack([np.asarray(X_sub[tr_fp][:, sharp_cols_exp1], dtype=np.float32), X_vis_dir_tr]), y_tr)

        pi_t1_c = np.zeros(n_fp, dtype=np.float32)
        raw_t1_nz = clf_t1.predict_proba(
            np.hstack([np.asarray(X_sub[nz_cell][:, sharp_cols_exp1], dtype=np.float32), X_vis_cell_dir[nz_cell]])
        )[:, 1].astype(np.float32)
        pi_t1_c[nz_cell] = np.clip(0.028 * raw_t1_nz * tip_env_cell_fp[nz_cell], 0.0, 0.036)

        if do_live and nz_live is not None:
            raw_t1_lv = clf_t1.predict_proba(
                np.hstack([np.asarray(X_sub[nz_live][:, sharp_cols_exp1], dtype=np.float32), X_vis_full_dir[nz_live]])
            )[:, 1].astype(np.float32)
            p_tip_exp1_live_fp[nz_live] += 0.25 * np.clip(0.028 * raw_t1_lv * tip_env_full_fp[nz_live], 0.0, 0.036)
        del clf_t1, raw_t1_nz

        # Emit EXP-1 cropped OOF mask
        pi_e1_2d = _to_2d(1.0 - (1.0 - pi_t1_c) * (1.0 - pi_blind_exp1_oof))
        del pi_t1_c
        em1_full = htcads.emit_submodular_celf(pi_e1_2d, elig_b2_c, max_dots=37654, marginal_bar=0.0)
        cell_em_by_exp["EXP-1"][cell.key] = em1_full[cell.bbox].copy()
        del pi_e1_2d, em1_full

        # EXP-2/3 Tip/Relay model
        clf_t2 = lgb.LGBMClassifier(
            n_estimators=125,
            learning_rate=0.06,
            num_leaves=23,
            min_child_samples=60,
            subsample=0.80,
            subsample_freq=1,
            colsample_bytree=0.80,
            reg_alpha=2.0,
            reg_lambda=8.0,
            random_state=500 + idx_c,
            n_jobs=4,
            verbose=-1,
        )
        clf_t2.fit(np.hstack([np.asarray(X_sub[tr_fp][:, sharp_cols_exp2], dtype=np.float32), X_vis_dir_tr]), y_tr)

        pi_t2_c = np.zeros(n_fp, dtype=np.float32)
        raw_t2_nz = clf_t2.predict_proba(
            np.hstack([np.asarray(X_sub[nz_cell][:, sharp_cols_exp2], dtype=np.float32), X_vis_cell_dir[nz_cell]])
        )[:, 1].astype(np.float32)
        sharp_t2_nz = _sigmoid(_logit(raw_t2_nz) + 0.40 * lid_resid_oof_fp[nz_cell])
        pi_t2_c[nz_cell] = np.clip(0.028 * sharp_t2_nz * tip_env_cell_fp[nz_cell], 0.0, 0.036)

        if do_live and nz_live is not None:
            raw_t2_lv = clf_t2.predict_proba(
                np.hstack([np.asarray(X_sub[nz_live][:, sharp_cols_exp2], dtype=np.float32), X_vis_full_dir[nz_live]])
            )[:, 1].astype(np.float32)
            sharp_t2_lv = _sigmoid(_logit(raw_t2_lv) + 0.40 * lid_resid_full_fp[nz_live])
            p_tip_exp2_live_fp[nz_live] += 0.25 * np.clip(0.028 * sharp_t2_lv * tip_env_full_fp[nz_live], 0.0, 0.036)
        del clf_t2, raw_t2_nz, sharp_t2_nz, X_vis_cell_dir, tip_env_cell_fp

        pi_e2_fp = 1.0 - (1.0 - pi_t2_c) * (1.0 - pi_blind_exp2_oof)
        del pi_t2_c

        # Emit EXP-2 cropped OOF mask
        pi_e2_2d = _to_2d(pi_e2_fp)
        em2_full = htcads.emit_submodular_celf(pi_e2_2d, elig_b2_c, max_dots=37654, marginal_bar=0.0)
        cell_em_by_exp["EXP-2"][cell.key] = em2_full[cell.bbox].copy()
        del elig_b2_c, em2_full

        # Emit EXP-3 cropped OOF mask (axial ridge continuity + anisotropic tip-preserving/flank-depleting collar)
        pi_e3_2d = _axial_enhance_2d(pi_e2_2d, foot)
        em3_full = htcads.emit_submodular_celf(pi_e3_2d, elig_aniso_c, max_dots=37654, marginal_bar=0.0020)
        cell_em_by_exp["EXP-3"][cell.key] = em3_full[cell.bbox].copy()
        del pi_e2_fp, pi_e2_2d, pi_e3_2d, em3_full, elig_aniso_c
        gc.collect()
        print(f"[HTCADS] Cell {cell.key} trained + OOF CELF emitted for EXP-1/2/3 in {time.time()-t0:.1f}s")

    del X_vis_full_dir, tip_env_full_fp, lid_resid_oof_fp, lid_resid_full_fp, labels_dil3, fp_idx_2d
    gc.collect()

    print("[HTCADS] Loading GEMSDOE raster registry for Protocol Rule 1 uniqueness verification...")
    t_reg = time.time()
    registry_rasters, reg_sample_idx, all_registry_shas = _collect_registry_rasters(foot)
    print(f"[HTCADS] Loaded {len(registry_rasters)} unique footprint-distinct GEMSDOE registry rasters in {time.time()-t_reg:.1f}s.")

    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        lidar_valid_2d = (s_lid.read(12) > 0) & foot

    experiments_spec = [
        {
            "id": "EXP-1",
            "name": "HTCADS-SubsurfGeo",
            "description": "LiDAR-blind scale-separated Subsurface/Geothermal/Scarp-Conduit + purely directional Tip/Relay Noisy-OR + 300 m CELF (isotropic B=2.0 collar, 37,654 dots).",
            "mode": "exp1",
            "aniso": False,
            "axial_smooth": False,
            "max_dots": 37654,
            "marginal_bar": 0.0,
        },
        {
            "id": "EXP-2",
            "name": "HTCADS-DualRegime",
            "description": "Adds H-K2 FFT Updip Dip-Projected Gravity Migration + coverage-neutral zero-mean 1 m LiDAR Contour-Orthogonal Scarp Specialist + 300 m CELF (isotropic B=2.0 collar, 37,654 dots).",
            "mode": "exp2",
            "aniso": False,
            "axial_smooth": False,
            "max_dots": 37654,
            "marginal_bar": 0.0,
        },
        {
            "id": "EXP-3",
            "name": "HTCADS-DinkelbachAniso",
            "description": "Dual-Regime multi-physics surface + strike-continuity filter + Anisotropic Flank-Depleting (d>2.25 px) / Tip-Preserving (d>1.35 px) collar + Dinkelbach marginal-DTI CELF stopping.",
            "mode": "exp2",
            "aniso": True,
            "axial_smooth": True,
            "max_dots": 37654,
            "marginal_bar": 0.0020,
        },
    ]

    exp_results = []
    for spec in experiments_spec:
        t0 = time.time()
        is_e1 = spec["mode"] == "exp1"
        pi_b_live = pi_blind_exp1_full if is_e1 else pi_blind_exp2_full
        pi_t_live = p_tip_exp1_live_fp if is_e1 else p_tip_exp2_live_fp

        pi_live_fp = 1.0 - (1.0 - pi_t_live) * (1.0 - pi_b_live)
        pi_live_2d = _to_2d(pi_live_fp)
        if spec["axial_smooth"]:
            pi_live_2d = _axial_enhance_2d(pi_live_2d, foot)
        elig_live = elig_aniso_live if spec["aniso"] else elig_b2_live
        dots_live_2d = htcads.emit_submodular_celf(
            pi_live_2d,
            elig_live,
            max_dots=spec["max_dots"],
            marginal_bar=spec["marginal_bar"],
        )

        cell_emissions = cell_em_by_exp[spec["id"]]
        ev_hr = holdout.evaluate_hide_and_recover(cell_emissions, ctx, b_visible_px=0.0, n_boot=1000, seed=20261026, name=spec["id"])
        delta_hr = holdout.paired_bootstrap_delta(ev_hr, ref_hr, boot_key="_boots")

        ev_sg = holdout.evaluate_sgmc_with_ci(dots_live_2d, ctx, n_boot=1000, seed=20261026, name=spec["id"])
        delta_sg = holdout.paired_bootstrap_delta(ev_sg, ref_sg, boot_key="_cal_boots")

        uniq = _check_uniqueness(pi_live_2d, dots_live_2d, foot, registry_rasters, reg_sample_idx)
        dk = d_full_2d[dots_live_2d]

        rec_out = {
            "experiment_id": spec["id"],
            "name": spec["name"],
            "description": spec["description"],
            "elapsed_seconds": round(time.time() - t0, 2),
            "emitted_dots": int(dots_live_2d.sum()),
            "structural_invariants": {
                "median_d_known_px": round(float(np.median(dk)), 2),
                "pct_le_2px_known": round(100.0 * float((dk <= 2.0).mean()), 2),
                "pct_le_10px_known": round(100.0 * float((dk <= 10.0).mean()), 2),
                "pct_in_lidar": round(100.0 * float(lidar_valid_2d[dots_live_2d].mean()), 2),
            },
            "holdout_hide_recover": {
                "pooled_dti": round(ev_hr["pooled_dti"], 6),
                "ci95": [round(ev_hr["ci95_cluster_bootstrap"][0], 6), round(ev_hr["ci95_cluster_bootstrap"][1], 6)],
                "champion_02778_same_evaluator": round(ref_hr["pooled_dti"], 6),
                "per_quadrant_dti": {k: round(v, 6) for k, v in ev_hr["per_quadrant_dti"].items()},
                "paired_delta_vs_0p2778_ref": round(delta_hr["delta"], 6),
                "paired_delta_ci95": [round(delta_hr["ci95"][0], 6), round(delta_hr["ci95"][1], 6)],
                "win_prob_vs_ref": round(delta_hr["win_prob"], 4),
                "ci95_strictly_positive": delta_hr["ci95_strictly_positive"],
                "label": (
                    f"HOLDOUT-DTI ({ev_hr['evaluator_version']}, N={ev_hr['n_withheld_positives']} withheld positives, "
                    f"95% CI [{ev_hr['ci95_cluster_bootstrap'][0]:.4f}, {ev_hr['ci95_cluster_bootstrap'][1]:.4f}])"
                ),
            },
            "holdout_sgmc_offcat": {
                "raw_dti": round(ev_sg["sgmc_raw_pooled_dti"], 6),
                "sgmc_prevalence_calibrated_dti": round(ev_sg["sgmc_prevalence_calibrated_dti"], 6),
                "ci95": [round(ev_sg["sgmc_calibrated_ci95"][0], 6), round(ev_sg["sgmc_calibrated_ci95"][1], 6)],
                "champion_02778_same_evaluator": round(ref_sg["sgmc_prevalence_calibrated_dti"], 6),
                "paired_delta_vs_0p2778_ref": round(delta_sg["delta"], 6),
                "paired_delta_ci95": [round(delta_sg["ci95"][0], 6), round(delta_sg["ci95"][1], 6)],
                "ci95_strictly_positive": delta_sg["ci95_strictly_positive"],
                "label": (
                    f"HOLDOUT-DTI ({ev_sg['evaluator_version']}, N={ev_sg['n_withheld_positives']} off-catalogue SGMC positives, "
                    f"95% CI [{ev_sg['sgmc_calibrated_ci95'][0]:.4f}, {ev_sg['sgmc_calibrated_ci95'][1]:.4f}])"
                ),
            },
            "uniqueness_audit": uniq,
            "_dots_live_2d": dots_live_2d,
            "_pi_live_2d": pi_live_2d,
            "_cell_emissions": cell_emissions,
        }
        exp_results.append(rec_out)
        print(
            f"[HTCADS] {spec['id']} ({spec['name']}): "
            f"Hide-Rec={ev_hr['pooled_dti']:.6f} (delta={delta_hr['delta']:+.6f}, CI=[{delta_hr['ci95'][0]:+.5f}, {delta_hr['ci95'][1]:+.5f}]), "
            f"SGMC-CAL={ev_sg['sgmc_prevalence_calibrated_dti']:.6f} (delta={delta_sg['delta']:+.6f}), "
            f"dots={int(dots_live_2d.sum())}, med_d={np.median(dk):.1f}px, <=10px={100*(dk<=10).mean():.1f}%, LiDAR={100*lidar_valid_2d[dots_live_2d].mean():.1f}%, "
            f"max_3px_ov={uniq['final_dots_max_detector_3px_overlap']:.4f}, uniq_pass={uniq['passed']}"
        )

    passing_exps = [e for e in exp_results if e["uniqueness_audit"]["passed"]]
    best_exp = max(passing_exps if passing_exps else exp_results, key=lambda e: e["holdout_hide_recover"]["pooled_dti"])

    oof_npz_path = wdir / "best_htcads_oof_cells.npz"
    np.savez_compressed(
        oof_npz_path,
        **{k: v.astype(np.uint8) for k, v in best_exp["_cell_emissions"].items()},
        full_dots=best_exp["_dots_live_2d"].astype(np.uint8),
    )
    np.save(wdir / "best_htcads_continuous_pi.npy", best_exp["_pi_live_2d"].astype(np.float32))

    ts_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = f"htcads-{best_exp['experiment_id'].lower()}-{best_exp['emitted_dots']}dots"
    note_140 = (
        f"HTCADS {best_exp['experiment_id']}; {best_exp['emitted_dots']:,} pixels; "
        f"HOLDOUT-DTI {best_exp['holdout_hide_recover']['evaluator_version']}; "
        f"N={best_exp['holdout_hide_recover']['n_withheld_positives']:,}"
    )[:140]

    dl_dir = downloads_dir()
    for old_f in dl_dir.glob("kanlergems2-*"):
        old_f.unlink()

    bundle = submission.write_submission_bundle(
        mask_or_probs=best_exp["_dots_live_2d"].astype(np.float32),
        foot=foot,
        labels=ctx.labels,
        template_tif=ddir / "sample_submission.tif",
        out_dir=dl_dir,
        slug=slug,
        timestamp_tag=ts_utc,
        candidate_meta={
            "candidate_id": best_exp["experiment_id"],
            "description": best_exp["description"],
            "submission_note": note_140,
        },
        prefix="kanlergems2",
    )
    tif_name = bundle["zeros_tif"]["filename"]
    tif_path = dl_dir / tif_name
    tif_sha = bundle["zeros_tif"]["sha256"]
    best_exp["uniqueness_audit"]["exact_sha256_unique"] = bool(tif_sha not in all_registry_shas)

    sharp_feature_names = [htcads.SUBSURF_FEATURE_NAMES[i] for i in sharp_cols_exp2]
    imp_rank = sorted(
        zip(sharp_feature_names, [round(float(x), 2) for x in blind_importances]),
        key=lambda t: t[1],
        reverse=True,
    )
    lid_imp_rank = sorted(
        zip(htcads.LIDAR_FEATURE_NAMES, [round(float(x), 2) for x in lidar_importances]),
        key=lambda t: t[1],
        reverse=True,
    )

    clean_exps = [{k: v for k, v in e.items() if not k.startswith("_")} for e in exp_results]
    experiments_summary = {
        "schema": "kanlergemsdoe2.htcads_experiments.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "total_wall_seconds": round(time.time() - t_start, 2),
        "within_protocol_budget": {
            "experiments_run": len(clean_exps),
            "max_experiments_allowed": 3,
            "wall_hours": round((time.time() - t_start) / 3600.0, 4),
            "max_wall_hours_allowed": 2.0,
        },
        "reference_0p2778_benchmark": {
            "name": "GEMSDOE32 historical 0.2778 user/owner-reported value (receipt not verified)",
            "score_provenance": "USER/OWNER-REPORTED UNVERIFIED; no organizer submission receipt stored",
            "holdout_hide_recover_uncensored_dti": round(ref_hr["pooled_dti"], 6),
            "holdout_hide_recover_ci95": [round(ref_hr["ci95_cluster_bootstrap"][0], 6), round(ref_hr["ci95_cluster_bootstrap"][1], 6)],
            "holdout_sgmc_calibrated_dti": round(ref_sg["sgmc_prevalence_calibrated_dti"], 6),
            "holdout_sgmc_ci95": [round(ref_sg["sgmc_calibrated_ci95"][0], 6), round(ref_sg["sgmc_calibrated_ci95"][1], 6)],
        },
        "experiments": clean_exps,
        "selected_experiment": best_exp["experiment_id"],
        "blind_subsurface_feature_gain_ranking": imp_rank,
        "lidar_specialist_feature_gain_ranking": lid_imp_rank,
    }
    (edir / "htcads_experiments.json").write_text(json.dumps(experiments_summary, indent=2) + "\n", encoding="utf-8")

    run_card_path = edir / "run_card.json"
    run_card = {
        "schema": "gems.parallel_run_card.v1",
        "site": "KANLERGEMSDOE2",
        "repo": "kanlerxz87-cyber/KANLERGEMSDOE2",
        "branch": "arena/1868484d-kanlergemsdoe2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": (
            f"H-K1 ({best_exp['experiment_id']}: {best_exp['name']}) — Hydrothermal-Tectonic Conduit & "
            "Anisotropic Dilational Step-Over Synthesis"
        ),
        "mechanism": (
            "Scale-separated Dual-Population Noisy-OR synthesis coupling (1) a strictly out-of-quadrant (>5 km buffer) "
            "27-channel Sharp Subsurface/Hydrothermal/Scarp-Conduit GBDT + first-principles Multi-Physics Conduit index "
            "(FFT 400 m upward-continued updip gravity crest migration, Gallardo-Meju gravity-magnetic cross-gradient, "
            "GeoDAWN short-wavelength hydrothermal demagnetization & K/Th metasomatism, MT clay-cap lateral edges, "
            "hydraulic-upgradient advected INGENIOUS 2 m F2mDAB thermal probes & geothermometers, siliceous sinter vents, "
            "and 100 m scarp-slope/toe-concavity) fused with a coverage-neutral zero-mean 1 m LiDAR contour-orthogonal "
            "scarp specialist, and (2) a purely directional Fault-Tip & Relay-Ramp Propagation GBDT strictly gated to "
            "forward tip cones and step-over bridges (identically zero on planar fault flanks), allocated via exact "
            "25-offset Euclidean 300 m submodular expected-DTI (CELF) with anisotropic flank depletion / tip preservation."
        ),
        "named_non_fault_mimic": (
            "Pleistocene Lake Lahontan wave-cut shorelines & lacustrine tufa mounds (suppressed via contour-orthogonality "
            "|sin(theta_scarp - theta_contour)| and Paleo_geothermal Deposit_type sinter>>tufa weighting), flat-lying "
            "unfaulted basaltic flows (suppressed via Gallardo-Meju gravity-magnetic cross-gradient & hydrothermal "
            "demagnetization residual), down-gradient alluvial thermal outflow plumes (corrected via 0.5-1.5 km "
            "up-gradient hydraulic back-projection), and Quaternary valley-floor mapping bias (immunized via scale-separated "
            "first-principles conduit coupling)."
        ),
        "leakage_canary": {
            "passed": canary["passed"],
            "max_single_feature_auc": canary["max_single_feature_auc"],
            "max_feature_name": canary["max_feature_name"],
            "total_features_tested": canary["total_features_tested"],
        },
        "holdout_dti": {
            "primary_hide_and_recover": best_exp["holdout_hide_recover"],
            "secondary_off_catalogue_sgmc": best_exp["holdout_sgmc_offcat"],
        },
        "structural_invariants": best_exp["structural_invariants"],
        "registry_comparison": best_exp["uniqueness_audit"],
        "correlation_overlap_vs_registry": best_exp["uniqueness_audit"],
        "raster_sha256": tif_sha,
        "zip_sha256": bundle["zeros_zip"]["sha256"],
        "submission_filename": tif_name,
        "zip_filename": bundle["zeros_zip"]["filename"],
        "submission_name": bundle["submission_name"],
        "submission_note": note_140,
        "note": note_140,
        "note_length": len(note_140),
    }
    run_card_path.write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")

    val_json_path = edir / "validator_receipt.json"
    subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "validate_submission.py"),
            "--tif",
            str(tif_path),
            "--run-card",
            str(run_card_path),
            "--out",
            str(val_json_path),
        ],
        check=False,
    )
    validator_output = json.loads(val_json_path.read_text(encoding="utf-8"))
    run_card["validator_output"] = validator_output
    run_card["status"] = validator_output["status"]
    run_card["verdict"] = validator_output["verdict"]
    run_card["verdict_scope"] = validator_output["verdict_scope"]
    run_card["ok_to_download"] = validator_output["status"]["download"] == "OK_TO_DOWNLOAD"
    run_card["authorized_to_submit"] = validator_output["status"]["submission_authorization"] == "AUTHORIZED"

    run_card_path.write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")
    (dl_dir / "run_card.json").write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")

    print("\n" + "=" * 78)
    print(
        f"[HTCADS] FINAL VERDICT: {run_card['verdict'].upper()} | "
        f"DOWNLOAD: {validator_output['status']['download']} | "
        f"SELECTOR: {validator_output['status']['selector_eligibility']} | "
        f"SUBMISSION: {validator_output['status']['submission_authorization']}"
    )
    print(f"[HTCADS] Selected: {best_exp['experiment_id']} ({best_exp['name']}) -> {tif_name}")
    print(f"[HTCADS] SHA-256 : {tif_sha}")
    print(f"[HTCADS] Note ({len(note_140)}/140 chars): {note_140}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
