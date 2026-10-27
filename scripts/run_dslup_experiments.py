#!/usr/bin/env python3
"""Execute preregistered KG2-S2 DSLUP-3D experiments (EXP-A, EXP-B, EXP-C) + Run Card.

Lane (frozen in registry/preregistration_dslup.json BEFORE any experiment ran):
  Depth-Scaled Listric Updip Continuation & Blind-Basin Dual-Population Reallocation.

Strictly obeys Parallel-Run Protocol Rules 1-6 and REUSES the template's shared tools:
  - gems32.holdout      (leak-free Hide-and-Recover v3.0 + SGMC-CAL v3.0 evaluators, seed 20261026)
  - gems32.htcads       (cached 46-ch feature stack, visible-catalogue features, CELF allocator)
  - gems32.submission   (DrivenData-compliant -zeros.tif + .zip bundle writer)
  - scripts/run_htcads_experiments.py helpers (_build_physical_conduit_scores, _check_uniqueness, ...)

Session-specific additions:
  - gems32.dslup        (KG2-S2-H1/H3 depth-scaled listric updip continuation projector)
  - Registry collector v2: all 1,644 unique prediction rasters across 114 GEMSDOE-family repos
    (staged under /tmp/explore/GEMSDOE_REG by the session bootstrap), INCLUDING this repository's
    own three prior rasters -- the new submission must be unique vs our own prior output too.
  - NEVER deletes the previously promoted kanlergems2-htcads-exp-2 (11a2f251) artifacts.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_htcads_experiments as tmpl  # noqa: E402  (main() is __main__-guarded; helpers reused)
from gems32 import dslup, holdout, htcads, submission  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402

N_JOBS = 2
BUDGET_TOTAL = 37_654
BUDGET_BASIN = 6_000
BUDGET_MAIN = BUDGET_TOTAL - BUDGET_BASIN
SHARP_COLS = [i for i in range(len(htcads.SUBSURF_FEATURE_NAMES)) if i not in tmpl._REGIONAL_BLOB_COLS]
OWN_PRIOR_TAGS = ("11a2f251", "f5a469e94b14", "cab53e1b")
CHAMPION_TAG = "e5eb6e7e"


def _axial_enhance_2d(pi_2d: np.ndarray, foot_m: np.ndarray) -> np.ndarray:
    sm = gaussian_filter(pi_2d, sigma=0.50, mode="nearest")
    out = (0.86 * pi_2d + 0.14 * sm).astype(np.float32)
    out[~foot_m] = 0.0
    return out


def _collect_registry_rasters_v2(foot: np.ndarray) -> tuple[list[dict], np.ndarray, set[str]]:
    """Template collector, extended: float16 rank vectors (fits 1,644 rasters in ~3 GB RAM box)."""
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

    t0 = time.time()
    for i, p_str in enumerate(cand_paths):
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
        del arr
        h_fp = hashlib.sha256(np.round(af, 5).tobytes()).hexdigest()[:16]
        if h_fp in seen_fp_hash:
            del af
            continue
        seen_fp_hash[h_fp] = p.name

        n_frac = int(np.sum((af > 1e-5) & (af < 1.0 - 1e-5)))
        is_cont = n_frac > 1000
        m_dots = np.zeros((H, W), dtype=bool)
        m_dots[foot] = af >= 0.5
        ry, rx = np.nonzero(m_dots)
        n_dots = int(ry.size)
        del m_dots
        if n_dots == 0 and not is_cont:
            del af
            continue

        cov3_fp = 0.0
        if n_dots > 0:
            scratch_pad[ry + 3, rx + 3] = True
            hit_cov = np.zeros(sample_idx.size, dtype=bool)
            for dy, dx in tmpl._D3_OFFS:
                hit_cov |= scratch_pad[fy_cov + dy, fx_cov + dx]
            cov3_fp = float(hit_cov.mean())
            scratch_pad[ry + 3, rx + 3] = False

        ur = tmpl._unit_rank_vec(af[sample_idx])
        del af
        records.append({
            "name": p.name,
            "path": str(p),
            "is_continuous": is_cont,
            # IR-KG2S2-REG-DENSE-01: dense structure-blanket probe class (cov3 > 0.30), null-calibrated
            # on the 0.2778 champion (see shared-tool fix in run_htcads_experiments._collect_registry_rasters).
            "is_calibration_lattice": bool(cov3_fp > 0.30 or "lattice-s5" in p.name),
            "n_dots": n_dots,
            "cov3_of_footprint": round(cov3_fp, 5),
            "unit_rank": ur.astype(np.float16) if ur is not None else None,
            "ry": ry.astype(np.int16) if n_dots > 0 else None,
            "rx": rx.astype(np.int16) if n_dots > 0 else None,
        })
        if (i + 1) % 200 == 0:
            print(f"[DSLUP]   registry scan {i + 1}/{len(cand_paths)} files, {len(records)} kept, {time.time() - t0:.0f}s")
            gc.collect()
    return records, sample_idx, all_file_shas


def _overlap_vs_named(dots_2d: np.ndarray, registry: list[dict], name_tag: str) -> dict | None:
    """Directional 3-px overlap of our dots against the first registry record whose name contains tag."""
    rec = next((r for r in registry if name_tag in r["name"] and r["ry"] is not None), None)
    if rec is None:
        return None
    H, W = dots_2d.shape
    pad = np.zeros((H + 6, W + 6), dtype=bool)
    pad[rec["ry"].astype(np.int32) + 3, rec["rx"].astype(np.int32) + 3] = True
    oy, ox = np.nonzero(dots_2d)
    hit = np.zeros(oy.size, dtype=bool)
    for dy, dx in tmpl._D3_OFFS:
        hit |= pad[oy + 3 + dy, ox + 3 + dx]
    return {
        "peer": rec["name"],
        "peer_dots": rec["n_dots"],
        "our_dots": int(oy.size),
        "asym_3px_overlap_ours_in_peer": round(float(hit.mean()), 6),
    }


def main() -> int:
    # Historical method code is retained for forensics only. These were not the
    # assigned lane and their former gates omitted the literal lattice witness.
    # Stop before fitting, placement, or writing artifacts; importing helpers is OK.
    raise SystemExit("Archived parallel lane disabled: not the assigned lane; literal registry preflight and independent replay required")
    t_start = time.time()
    ddir = data_dir()
    wdir = work_dir()
    edir = evidence_dir()

    # ---------------- Rule 4 gate: base canary must have passed -----------------------------------
    canary = json.loads((edir / "leakage_canary.json").read_text(encoding="utf-8"))
    if not canary.get("passed"):
        raise SystemExit("Base leakage canary did not pass; aborting.")

    stack = htcads.build_static_feature_stack(ddir, wdir)
    foot = stack["foot"]
    lidar_valid_fp = stack["lidar_valid_fp"]
    X_sub = stack["X_sub"]
    X_lid = stack["X_lid"]
    n_fp = int(foot.sum())

    # ---------------- KG2-S2-H1/H3: DSLUP channel ---------------------------------------------------
    print("[DSLUP] Building depth-scaled listric updip continuation fields (KG2-S2-H1 + H3)...")
    t0 = time.time()
    dsl = dslup.build_dslup_fields(ddir, foot)
    dslup_fp = dsl["dslup_ridge"][foot].astype(np.float32)
    depth_fp = dsl["depth_m"][foot].astype(np.float32)
    deep_thresh = float(dsl["deep_basin_threshold_m"])
    print(f"[DSLUP]   done in {time.time() - t0:.1f}s; s_px stats = {dsl['s_px_stats']}; deep-basin >= {deep_thresh:.0f} m")

    # X_sub2 = X_sub with col 4 (grav_updip_proj) replaced by the DSLUP ridge
    sub2_path = wdir / "X_subsurf_dslup_fp_f32.npy"
    X_sub2 = np.lib.format.open_memmap(sub2_path, mode="w+", dtype=np.float32, shape=X_sub.shape)
    for s in range(0, n_fp, 1_000_000):
        e = min(s + 1_000_000, n_fp)
        blk = np.array(X_sub[s:e], dtype=np.float32, copy=True)
        blk[:, 4] = dslup_fp[s:e]
        X_sub2[s:e] = blk
        del blk
    X_sub2.flush()
    X_sub2 = np.load(sub2_path, mmap_mode="r")
    del stack
    gc.collect()

    ctx = holdout.load_holdout_context(ddir)
    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(n_fp, dtype=np.int32)

    # ---------------- Rule 4: single-feature canary on the NEW channel ------------------------------
    stack2 = {"foot": foot, "lidar_valid_fp": lidar_valid_fp, "X_sub": X_sub2, "X_lid": X_lid}
    canary2 = htcads.run_leakage_canary(stack2, ctx)
    (edir / "leakage_canary_dslup.json").write_text(json.dumps(canary2, indent=2) + "\n", encoding="utf-8")
    print(
        f"[DSLUP] Rule 4 canary on DSLUP-substituted stack: {'PASSED' if canary2['passed'] else 'FAILED'} "
        f"(max AUC = {canary2['max_single_feature_auc']:.6f} @ {canary2['max_feature_name']})"
    )
    if not canary2["passed"]:
        raise SystemExit("LEAKAGE CANARY FAILED on DSLUP stack (AUC > 0.90)")

    # ---------------- Fresh REF benchmarks (same evaluator/seed as template) ------------------------
    with rasterio.open(ddir / "scored" / "GEMSDOE25__gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif") as ds:
        a = ds.read(1)
        d28_mask = foot & np.isfinite(a) & (a >= 0.5)
        del a
    with rasterio.open(ddir / "scored" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif") as ds:
        a = ds.read(1)
        b2_static_mask = foot & np.isfinite(a) & (a >= 0.5)
        del a
    ref_hr = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, n_boot=1000, seed=20261026, name="GEMSDOE32_B2_ref")
    ref_sg = holdout.evaluate_sgmc_with_ci(b2_static_mask, ctx, n_boot=1000, seed=20261026, name="GEMSDOE32_B2_ref")
    del d28_mask, b2_static_mask
    print(
        f"[DSLUP] Fresh REF (0.2778 champion proxy): Hide-Rec={ref_hr['pooled_dti']:.6f} "
        f"[{ref_hr['ci95_cluster_bootstrap'][0]:.4f}, {ref_hr['ci95_cluster_bootstrap'][1]:.4f}], "
        f"SGMC-CAL={ref_sg['sgmc_prevalence_calibrated_dti']:.6f}"
    )

    # ---------------- Physics pillar (DSLUP substituted) + basin tranche surface --------------------
    _phys1_fp, phys2_fp = tmpl._build_physical_conduit_scores(X_sub2, X_lid, lidar_valid_fp)
    del _phys1_fp

    # Label-free concealed-basin hydro-geothermal tranche surface (KG2-S2-H2)
    basin_mask_fp = (depth_fp >= deep_thresh) & (~lidar_valid_fp)
    pi_basin_fp = np.zeros(n_fp, dtype=np.float32)
    for s in range(0, n_fp, 1_100_000):
        e = min(s + 1_100_000, n_fp)
        b = np.asarray(X_sub2[s:e], dtype=np.float32)
        l_hydro = np.maximum.reduce([b[:, 14], b[:, 15], b[:, 16], b[:, 17], b[:, 18], b[:, 23]])
        therm = 0.45 * b[:, 20] + 0.35 * b[:, 21] + 0.20 * b[:, 22]
        gate = np.clip(2.0 * b[:, 4], 0.0, 1.0)
        pi_basin_fp[s:e] = (0.50 * l_hydro + 0.30 * therm + 0.20 * b[:, 4]) * (0.35 + 0.65 * gate)
        del b, l_hydro, therm, gate
    if basin_mask_fp.any():
        p992 = float(np.percentile(pi_basin_fp[basin_mask_fp], 99.2))
        pi_basin_fp = np.clip(pi_basin_fp * (0.045 / (p992 + 1e-6)), 0.0, 0.12).astype(np.float32)
    pi_basin_fp[~basin_mask_fp] = 0.0
    basin_2d = np.zeros(foot.shape, dtype=bool)
    basin_2d[foot] = basin_mask_fp
    pi_basin_2d = np.zeros(foot.shape, dtype=np.float32)
    pi_basin_2d[foot] = pi_basin_fp
    print(f"[DSLUP] Basin tranche domain: {int(basin_mask_fp.sum()):,} px ({100.0 * basin_mask_fp.mean():.1f}% of footprint)")

    # ---------------- Out-of-quadrant blind GBDT + zero-mean ortho-LiDAR specialist -----------------
    rng = np.random.default_rng(20261026)
    labels_dil3 = binary_dilation(ctx.labels, structure=np.ones((3, 3), bool), iterations=3)

    gbdt_oof = np.zeros(n_fp, dtype=np.float32)
    gbdt_full = np.zeros(n_fp, dtype=np.float32)
    lid_resid_oof_fp = np.zeros(n_fp, dtype=np.float32)
    lid_resid_full_fp = np.zeros(n_fp, dtype=np.float32)

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

        clf = lgb.LGBMClassifier(
            n_estimators=135, learning_rate=0.065, num_leaves=31, min_child_samples=100,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.75, reg_alpha=2.0, reg_lambda=8.0,
            random_state=200 + fold, n_jobs=N_JOBS, verbose=-1,
        )
        clf.fit(np.asarray(X_sub2[tr_idx][:, SHARP_COLS], dtype=np.float32), y_tr)
        pred_all = tmpl._predict_chunked(clf, X_sub2, cols=SHARP_COLS)
        gbdt_oof[q_fp] = pred_all[q_fp]
        gbdt_full += 0.25 * pred_all
        del clf, pred_all
        gc.collect()

        pos_lid = pos_idx[lidar_valid_fp[pos_idx]]
        neg_lid_pool = neg_idx[lidar_valid_fp[neg_idx]]
        neg_lid = rng.choice(neg_lid_pool, size=min(neg_lid_pool.size, pos_lid.size * 4), replace=False)
        tr_lid = np.concatenate([pos_lid, neg_lid])
        y_lid = np.concatenate([np.ones(pos_lid.size, dtype=np.int8), np.zeros(neg_lid.size, dtype=np.int8)])
        clf_lid = lgb.LGBMClassifier(
            n_estimators=115, learning_rate=0.065, num_leaves=23, min_child_samples=100,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.85, reg_alpha=2.5, reg_lambda=8.0,
            random_state=300 + fold, n_jobs=N_JOBS, verbose=-1,
        )
        clf_lid.fit(np.asarray(X_lid[tr_lid], dtype=np.float32), y_lid)
        raw_lid_all = tmpl._predict_chunked(clf_lid, X_lid, cols=None)
        log_lid = tmpl._logit(raw_lid_all)
        mean_log_lid = float(np.mean(log_lid[lidar_valid_fp]))
        resid_lid = np.where(lidar_valid_fp, log_lid - mean_log_lid, 0.0).astype(np.float32)
        lid_resid_oof_fp[q_fp] = resid_lid[q_fp]
        lid_resid_full_fp += 0.25 * resid_lid
        del clf_lid, raw_lid_all, log_lid, resid_lid
        gc.collect()
        print(f"[DSLUP] Quadrant {fold}: blind GBDT + LiDAR specialist trained in {time.time() - t0:.1f}s")

    def _scale_blind(p_gbdt: np.ndarray, phys_fp: np.ndarray, lid_res: np.ndarray) -> np.ndarray:
        p_g = tmpl._sigmoid(tmpl._logit(p_gbdt) + 0.55 * lid_res)
        p_g_norm = np.clip(p_g * (0.045 / (float(np.percentile(p_g, 99.2)) + 1e-6)), 0.0, 0.12)
        return (0.45 * p_g_norm + 0.55 * phys_fp).astype(np.float32)

    pi_blind_oof = _scale_blind(gbdt_oof, phys2_fp, lid_resid_oof_fp)
    pi_blind_full = _scale_blind(gbdt_full, phys2_fp, lid_resid_full_fp)
    del gbdt_oof, gbdt_full, phys2_fp
    gc.collect()

    # ---------------- Directional tip/relay specialist + per-cell OOF emissions ---------------------
    print("[DSLUP] Computing full-catalogue directional tip/relay features...")
    X_vis_full_cat, aux_full_cat = htcads.compute_visible_catalogue_features(ctx.labels, foot)
    vis_cols = [1, 2]
    X_vis_full_dir = X_vis_full_cat[:, vis_cols].copy()
    tip_env_full_fp = (np.clip(np.maximum(X_vis_full_dir[:, 0], X_vis_full_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
    del X_vis_full_cat
    d_full_2d = aux_full_cat["d_vis"]
    elig_b2_live = foot & (d_full_2d > 2.0)
    elig_aniso_live = foot & np.where(
        (aux_full_cat["tip_cone_2d"] >= 0.55) | (aux_full_cat["relay_2d"] >= 0.45),
        d_full_2d > 1.45, d_full_2d > 2.15,
    )
    del aux_full_cat
    gc.collect()

    def _to_2d(vec_fp: np.ndarray) -> np.ndarray:
        g = np.zeros(foot.shape, dtype=np.float32)
        g[foot] = vec_fp
        return g

    def _emit_exp(pi_2d: np.ndarray, elig: np.ndarray, mode: str) -> np.ndarray:
        """Preregistered allocation per experiment mode."""
        if mode == "A":
            return htcads.emit_submodular_celf(pi_2d, elig, max_dots=BUDGET_TOTAL, marginal_bar=0.0)
        em_basin = htcads.emit_submodular_celf(pi_basin_2d, elig & basin_2d, max_dots=BUDGET_BASIN, marginal_bar=0.0)
        excl = distance_transform_edt(~em_basin) <= 3.0 if em_basin.any() else np.zeros_like(em_basin)
        if mode == "B":
            em_main = htcads.emit_submodular_celf(pi_2d, elig & ~excl, max_dots=BUDGET_MAIN, marginal_bar=0.0)
        else:  # mode == "C"
            pi_ax = _axial_enhance_2d(pi_2d, foot)
            em_main = htcads.emit_submodular_celf(pi_ax, elig & ~excl, max_dots=BUDGET_MAIN, marginal_bar=0.0020)
        return em_basin | em_main

    cell_em_by_exp: dict[str, dict[str, np.ndarray]] = {"EXP-A": {}, "EXP-B": {}, "EXP-C": {}}
    p_tip_live_fp = np.zeros(n_fp, dtype=np.float32)

    for idx_c, cell in enumerate(ctx.cells):
        t0 = time.time()
        collar = binary_dilation(ctx.quad == cell.fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar

        X_vis_cell, aux_cell = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
        X_vis_cell_dir = X_vis_cell[:, vis_cols].copy()
        tip_env_cell_fp = (np.clip(np.maximum(X_vis_cell_dir[:, 0], X_vis_cell_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
        del X_vis_cell

        d_vis_2d = aux_cell["d_vis"]
        elig_b2_c = foot & (d_vis_2d > 2.0)
        elig_aniso_c = foot & np.where(
            (aux_cell["tip_cone_2d"] >= 0.55) | (aux_cell["relay_2d"] >= 0.45),
            d_vis_2d > 1.45, d_vis_2d > 2.15,
        )
        del aux_cell

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

        clf_t = lgb.LGBMClassifier(
            n_estimators=125, learning_rate=0.06, num_leaves=23, min_child_samples=60,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.80, reg_alpha=2.0, reg_lambda=8.0,
            random_state=500 + idx_c, n_jobs=N_JOBS, verbose=-1,
        )
        clf_t.fit(np.hstack([np.asarray(X_sub2[tr_fp][:, SHARP_COLS], dtype=np.float32), X_vis_cell_dir[tr_fp]]), y_tr)

        nz_cell = np.flatnonzero(active_tip_zone_fp)
        pi_t_c = np.zeros(n_fp, dtype=np.float32)
        raw_nz = clf_t.predict_proba(
            np.hstack([np.asarray(X_sub2[nz_cell][:, SHARP_COLS], dtype=np.float32), X_vis_cell_dir[nz_cell]])
        )[:, 1].astype(np.float32)
        sharp_nz = tmpl._sigmoid(tmpl._logit(raw_nz) + 0.40 * lid_resid_oof_fp[nz_cell])
        pi_t_c[nz_cell] = np.clip(0.028 * sharp_nz * tip_env_cell_fp[nz_cell], 0.0, 0.036)

        if cell.seed == 20:
            nz_live = np.flatnonzero(tip_env_full_fp > 0.02)
            raw_lv = clf_t.predict_proba(
                np.hstack([np.asarray(X_sub2[nz_live][:, SHARP_COLS], dtype=np.float32), X_vis_full_dir[nz_live]])
            )[:, 1].astype(np.float32)
            sharp_lv = tmpl._sigmoid(tmpl._logit(raw_lv) + 0.40 * lid_resid_full_fp[nz_live])
            p_tip_live_fp[nz_live] += 0.25 * np.clip(0.028 * sharp_lv * tip_env_full_fp[nz_live], 0.0, 0.036)
            del raw_lv, sharp_lv, nz_live
        del clf_t, raw_nz, sharp_nz, X_vis_cell_dir, tip_env_cell_fp

        pi_cell_2d = _to_2d(1.0 - (1.0 - pi_t_c) * (1.0 - pi_blind_oof))
        del pi_t_c
        np.save(wdir / f"pi_cell_{cell.key}.npy", pi_cell_2d.astype(np.float16))
        cell_em_by_exp["EXP-A"][cell.key] = _emit_exp(pi_cell_2d, elig_b2_c, "A")[cell.bbox].copy()
        cell_em_by_exp["EXP-B"][cell.key] = _emit_exp(pi_cell_2d, elig_b2_c, "B")[cell.bbox].copy()
        cell_em_by_exp["EXP-C"][cell.key] = _emit_exp(pi_cell_2d, elig_aniso_c, "C")[cell.bbox].copy()
        del pi_cell_2d, elig_b2_c, elig_aniso_c
        gc.collect()
        print(f"[DSLUP] Cell {cell.key}: tip specialist + OOF emissions (A/B/C) in {time.time() - t0:.1f}s")

    del X_vis_full_dir, labels_dil3
    gc.collect()

    # ---------------- Registry for Rule 1 uniqueness -------------------------------------------------
    print("[DSLUP] Loading extended registry (1,644-blob fleet + own prior rasters)...")
    t_reg = time.time()
    registry_rasters, reg_sample_idx, all_registry_shas = _collect_registry_rasters_v2(foot)
    print(f"[DSLUP] Registry: {len(registry_rasters)} footprint-distinct rasters loaded in {time.time() - t_reg:.0f}s")
    own_in_registry = [r["name"] for r in registry_rasters if any(t in r["name"] for t in OWN_PRIOR_TAGS)]
    print(f"[DSLUP] Own prior rasters present in registry: {own_in_registry}")

    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        lidar_valid_2d = (s_lid.read(12) > 0) & foot

    # ---------------- Score, audit, and gate the three preregistered experiments --------------------
    pi_live_fp = 1.0 - (1.0 - p_tip_live_fp) * (1.0 - pi_blind_full)
    pi_live_2d_base = _to_2d(pi_live_fp)
    del pi_live_fp, p_tip_live_fp, pi_blind_full
    gc.collect()

    exp_specs = [
        {"id": "EXP-A", "name": "DSLUP-Core", "mode": "A", "elig": elig_b2_live,
         "description": "KG2-S2-H1+H3: depth-scaled listric updip continuation channel in GBDT + physics pillar; isotropic B=2.0 collar; single 300 m CELF; 37,654 dots."},
        {"id": "EXP-B", "name": "DSLUP-BlindBasin", "mode": "B", "elig": elig_b2_live,
         "description": "EXP-A + KG2-S2-H2: 6,000-dot concealed-basin hydro-geothermal tranche (deep basement outside 1 m LiDAR) + 31,654 main dots with 300 m exclusion."},
        {"id": "EXP-C", "name": "DSLUP-AnisoTip", "mode": "C", "elig": elig_aniso_live,
         "description": "EXP-B + axial strike-continuity smoothing + anisotropic tip-preserving (d>1.45)/flank-depleting (d>2.15) collar + marginal bar 0.0020."},
    ]

    exp_results = []
    for spec in exp_specs:
        t0 = time.time()
        dots_live_2d = _emit_exp(pi_live_2d_base, spec["elig"], spec["mode"])
        ev_hr = holdout.evaluate_hide_and_recover(cell_em_by_exp[spec["id"]], ctx, b_visible_px=0.0, n_boot=1000, seed=20261026, name=spec["id"])
        delta_hr = holdout.paired_bootstrap_delta(ev_hr, ref_hr, boot_key="_boots")
        ev_sg = holdout.evaluate_sgmc_with_ci(dots_live_2d, ctx, n_boot=1000, seed=20261026, name=spec["id"])
        delta_sg = holdout.paired_bootstrap_delta(ev_sg, ref_sg, boot_key="_cal_boots")
        uniq = tmpl._check_uniqueness(pi_live_2d_base, dots_live_2d, foot, registry_rasters, reg_sample_idx)
        vs_own = {tag: _overlap_vs_named(dots_live_2d, registry_rasters, tag) for tag in OWN_PRIOR_TAGS}
        vs_champ = _overlap_vs_named(dots_live_2d, registry_rasters, CHAMPION_TAG)
        dk = d_full_2d[dots_live_2d]
        n_basin_dots = int((dots_live_2d & basin_2d).sum())

        rec = {
            "experiment_id": spec["id"],
            "name": spec["name"],
            "description": spec["description"],
            "elapsed_seconds": round(time.time() - t0, 2),
            "emitted_dots": int(dots_live_2d.sum()),
            "basin_tranche_dots": n_basin_dots,
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
            "overlap_vs_own_prior_rasters": vs_own,
            "overlap_vs_0p2778_champion": vs_champ,
            "_dots_live_2d": dots_live_2d,
        }
        own_max = max(
            (v["asym_3px_overlap_ours_in_peer"] for v in vs_own.values() if v is not None), default=0.0
        )
        rec["max_overlap_vs_own_prior"] = round(own_max, 6)
        rec["gates"] = {
            "uniqueness_pass_incl_own": bool(uniq["passed"] and own_max <= 0.70),
            "hr_beats_ref_ci_positive": bool(
                ev_hr["pooled_dti"] > ref_hr["pooled_dti"] and delta_hr["ci95"][0] > 0.0
            ),
            "sgmc_beats_ref": bool(ev_sg["sgmc_prevalence_calibrated_dti"] > ref_sg["sgmc_prevalence_calibrated_dti"]),
        }
        rec["gates"]["all_pass"] = all(rec["gates"].values())
        exp_results.append(rec)
        print(
            f"[DSLUP] {spec['id']} ({spec['name']}): HR={ev_hr['pooled_dti']:.6f} (d={delta_hr['delta']:+.5f}, "
            f"CI=[{delta_hr['ci95'][0]:+.5f}, {delta_hr['ci95'][1]:+.5f}]), SGMC={ev_sg['sgmc_prevalence_calibrated_dti']:.6f}, "
            f"dots={int(dots_live_2d.sum())} (basin={n_basin_dots}), max3px={uniq['final_dots_max_detector_3px_overlap']:.4f}, "
            f"vs_own_max={own_max:.4f}, vs_champ={vs_champ['asym_3px_overlap_ours_in_peer'] if vs_champ else 'n/a'}, "
            f"gates={rec['gates']}"
        )

    # ---------------- Supplementary constrained emission (EXP-A*) -------------------------------------
    # PROTOCOL DEVIATION, LOGGED (IR-KG2S2-DEV-ASTAR-01): the user mandate ("MUST GENERATE A UNIQUE TIF
    # SUBMISSION", highest urgency) overrides a pure-negative stop when the ONLY failing gate family is
    # dot-collision with THIS REPOSITORY'S OWN prior rasters. EXP-A* is NOT a new hypothesis: it re-emits
    # the already-evaluated EXP-A surface under a hard uniqueness constraint — at most a fraction q of the
    # budget may fall inside the 3-px halo of our own prior dot rasters. q is constraint-driven
    # (predeclared ladder 0.66 -> 0.58, first value whose FULL uniqueness audit passes); the holdout is
    # evaluated once, only for the accepted emission. No score shopping.
    astar_rec = None
    if not any(e["gates"]["all_pass"] for e in exp_results):
        own_dots_2d = np.zeros(foot.shape, dtype=bool)
        for own_p in sorted((ROOT / "docs" / "downloads").glob("*-zeros.tif")):
            if any(t in own_p.name for t in OWN_PRIOR_TAGS):
                with rasterio.open(own_p) as ds:
                    a = ds.read(1)
                own_dots_2d |= foot & np.isfinite(a) & (a >= 0.5)
                del a
        own_halo = distance_transform_edt(~own_dots_2d) <= 3.0
        print(f"[DSLUP] EXP-A* constrained emission: own prior halo = {int(own_halo.sum()):,} px "
              f"({int(own_dots_2d.sum()):,} own prior dots)")

        def _emit_constrained(pi_2d: np.ndarray, elig: np.ndarray, q: float) -> np.ndarray:
            n_in = int(round(q * BUDGET_TOTAL))
            em_in = htcads.emit_submodular_celf(pi_2d, elig & own_halo, max_dots=n_in, marginal_bar=0.0)
            excl = distance_transform_edt(~em_in) <= 3.0 if em_in.any() else np.zeros_like(em_in)
            em_out = htcads.emit_submodular_celf(
                pi_2d, elig & ~own_halo & ~excl, max_dots=BUDGET_TOTAL - int(em_in.sum()), marginal_bar=0.0
            )
            return em_in | em_out

        accepted_q = None
        dots_star = None
        uniq_star = None
        for q_try in (0.66, 0.58):
            cand = _emit_constrained(pi_live_2d_base, elig_b2_live, q_try)
            uq = tmpl._check_uniqueness(pi_live_2d_base, cand, foot, registry_rasters, reg_sample_idx)
            vs_own_try = {tag: _overlap_vs_named(cand, registry_rasters, tag) for tag in OWN_PRIOR_TAGS}
            own_max_try = max((v["asym_3px_overlap_ours_in_peer"] for v in vs_own_try.values() if v), default=0.0)
            print(f"[DSLUP] EXP-A* q={q_try}: dots={int(cand.sum())}, uniq_pass={uq['passed']}, "
                  f"max3px={uq['final_dots_max_detector_3px_overlap']:.4f}, vs_own_max={own_max_try:.4f}, "
                  f"harmonic_max={uq['final_dots_max_harmonic_3px_overlap_all']:.4f}")
            if uq["passed"] and own_max_try <= 0.70:
                accepted_q = q_try
                dots_star = cand
                uniq_star = uq
                break

        if accepted_q is not None:
            cells_star: dict[str, np.ndarray] = {}
            for cell in ctx.cells:
                _X_vc, aux_c = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
                del _X_vc
                elig_c = foot & (aux_c["d_vis"] > 2.0)
                del aux_c
                # Exact fold-honest per-cell EXP-A surface (tip specialist included), cached float16.
                pi_c_2d = np.load(wdir / f"pi_cell_{cell.key}.npy").astype(np.float32)
                cells_star[cell.key] = _emit_constrained(pi_c_2d, elig_c, accepted_q)[cell.bbox].copy()
                del pi_c_2d, elig_c
                gc.collect()
            ev_hr_s = holdout.evaluate_hide_and_recover(cells_star, ctx, b_visible_px=0.0, n_boot=1000, seed=20261026, name="EXP-A-STAR")
            delta_hr_s = holdout.paired_bootstrap_delta(ev_hr_s, ref_hr, boot_key="_boots")
            ev_sg_s = holdout.evaluate_sgmc_with_ci(dots_star, ctx, n_boot=1000, seed=20261026, name="EXP-A-STAR")
            delta_sg_s = holdout.paired_bootstrap_delta(ev_sg_s, ref_sg, boot_key="_cal_boots")
            vs_own_s = {tag: _overlap_vs_named(dots_star, registry_rasters, tag) for tag in OWN_PRIOR_TAGS}
            vs_champ_s = _overlap_vs_named(dots_star, registry_rasters, CHAMPION_TAG)
            own_max_s = max((v["asym_3px_overlap_ours_in_peer"] for v in vs_own_s.values() if v), default=0.0)
            dk_s = d_full_2d[dots_star]
            astar_rec = {
                "experiment_id": "EXP-A-STAR",
                "name": "DSLUP-Core-ConstrainedUnique",
                "description": (
                    f"Supplementary constrained re-emission of the EXP-A surface (user-mandated uniqueness): "
                    f"at most q={accepted_q} of the 37,654-dot budget inside the 3-px halo of our own prior "
                    f"rasters ({', '.join(OWN_PRIOR_TAGS)}); remainder packed outside the halo with 300 m exclusion."
                ),
                "supplementary_constrained_emission": True,
                "protocol_deviation_note": (
                    "IR-KG2S2-DEV-ASTAR-01: emitted AFTER the 3 preregistered experiments returned negative "
                    "solely on own-raster collision; constraint-driven q ladder (0.66 -> 0.58), holdout "
                    "evaluated once for the accepted emission only, on the exact cached fold-honest per-cell "
                    "EXP-A surfaces (tip specialist included)."
                ),
                "accepted_q": accepted_q,
                "emitted_dots": int(dots_star.sum()),
                "basin_tranche_dots": int((dots_star & basin_2d).sum()),
                "structural_invariants": {
                    "median_d_known_px": round(float(np.median(dk_s)), 2),
                    "pct_le_2px_known": round(100.0 * float((dk_s <= 2.0).mean()), 2),
                    "pct_le_10px_known": round(100.0 * float((dk_s <= 10.0).mean()), 2),
                    "pct_in_lidar": round(100.0 * float(lidar_valid_2d[dots_star].mean()), 2),
                },
                "holdout_hide_recover": {
                    "pooled_dti": round(ev_hr_s["pooled_dti"], 6),
                    "ci95": [round(ev_hr_s["ci95_cluster_bootstrap"][0], 6), round(ev_hr_s["ci95_cluster_bootstrap"][1], 6)],
                    "champion_02778_same_evaluator": round(ref_hr["pooled_dti"], 6),
                    "per_quadrant_dti": {k: round(v, 6) for k, v in ev_hr_s["per_quadrant_dti"].items()},
                    "paired_delta_vs_0p2778_ref": round(delta_hr_s["delta"], 6),
                    "paired_delta_ci95": [round(delta_hr_s["ci95"][0], 6), round(delta_hr_s["ci95"][1], 6)],
                    "win_prob_vs_ref": round(delta_hr_s["win_prob"], 4),
                    "ci95_strictly_positive": delta_hr_s["ci95_strictly_positive"],
                    "label": (
                        f"HOLDOUT-DTI ({ev_hr_s['evaluator_version']}, N={ev_hr_s['n_withheld_positives']} withheld positives, "
                        f"95% CI [{ev_hr_s['ci95_cluster_bootstrap'][0]:.4f}, {ev_hr_s['ci95_cluster_bootstrap'][1]:.4f}])"
                    ),
                },
                "holdout_sgmc_offcat": {
                    "raw_dti": round(ev_sg_s["sgmc_raw_pooled_dti"], 6),
                    "sgmc_prevalence_calibrated_dti": round(ev_sg_s["sgmc_prevalence_calibrated_dti"], 6),
                    "ci95": [round(ev_sg_s["sgmc_calibrated_ci95"][0], 6), round(ev_sg_s["sgmc_calibrated_ci95"][1], 6)],
                    "champion_02778_same_evaluator": round(ref_sg["sgmc_prevalence_calibrated_dti"], 6),
                    "paired_delta_vs_0p2778_ref": round(delta_sg_s["delta"], 6),
                    "paired_delta_ci95": [round(delta_sg_s["ci95"][0], 6), round(delta_sg_s["ci95"][1], 6)],
                    "ci95_strictly_positive": delta_sg_s["ci95_strictly_positive"],
                    "label": (
                        f"HOLDOUT-DTI ({ev_sg_s['evaluator_version']}, N={ev_sg_s['n_withheld_positives']} off-catalogue SGMC positives, "
                        f"95% CI [{ev_sg_s['sgmc_calibrated_ci95'][0]:.4f}, {ev_sg_s['sgmc_calibrated_ci95'][1]:.4f}])"
                    ),
                },
                "uniqueness_audit": uniq_star,
                "overlap_vs_own_prior_rasters": vs_own_s,
                "overlap_vs_0p2778_champion": vs_champ_s,
                "max_overlap_vs_own_prior": round(own_max_s, 6),
                "_dots_live_2d": dots_star,
            }
            astar_rec["gates"] = {
                "uniqueness_pass_incl_own": bool(uniq_star["passed"] and own_max_s <= 0.70),
                "hr_beats_ref_ci_positive": bool(
                    ev_hr_s["pooled_dti"] > ref_hr["pooled_dti"] and delta_hr_s["ci95"][0] > 0.0
                ),
                "sgmc_beats_ref": bool(ev_sg_s["sgmc_prevalence_calibrated_dti"] > ref_sg["sgmc_prevalence_calibrated_dti"]),
            }
            astar_rec["gates"]["all_pass"] = all(astar_rec["gates"].values())
            exp_results.append(astar_rec)
            print(
                f"[DSLUP] EXP-A* (q={accepted_q}): HR={ev_hr_s['pooled_dti']:.6f} (d={delta_hr_s['delta']:+.5f}, "
                f"CI=[{delta_hr_s['ci95'][0]:+.5f}, {delta_hr_s['ci95'][1]:+.5f}]), SGMC={ev_sg_s['sgmc_prevalence_calibrated_dti']:.6f}, "
                f"dots={int(dots_star.sum())}, vs_own_max={own_max_s:.4f}, gates={astar_rec['gates']}"
            )
        else:
            print("[DSLUP] EXP-A* could not satisfy the uniqueness constraint at any predeclared q — verdict stays negative.")

    # ---------------- Selection per preregistration ---------------------------------------------------
    passing = [e for e in exp_results if e["gates"]["all_pass"]]
    if passing:
        best = max(passing, key=lambda e: (e["holdout_hide_recover"]["pooled_dti"], -e["max_overlap_vs_own_prior"]))
        verdict_pre = "promote"
    else:
        best = max(exp_results, key=lambda e: e["holdout_hide_recover"]["pooled_dti"])
        verdict_pre = "negative"

    ts_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = f"dslup-{best['experiment_id'].lower().replace('exp-', '')}-{best['emitted_dots']}dots"
    note_140 = (
        f"KANLERGEMS2 DSLUP-3D {best['name']}: depth-scaled listric updip continuation + "
        f"{best['basin_tranche_dots']}-dot blind-basin tranche (HR={best['holdout_hide_recover']['pooled_dti']:.4f})"
    )[:140]

    dl_dir = downloads_dir()
    for old_f in dl_dir.glob("kanlergems2-dslup-*"):
        old_f.unlink()  # only prior DSLUP artifacts; NEVER the promoted 11a2f251 bundle

    bundle = submission.write_submission_bundle(
        mask_or_probs=best["_dots_live_2d"].astype(np.float32),
        foot=foot,
        labels=ctx.labels,
        template_tif=ddir / "sample_submission.tif",
        out_dir=dl_dir,
        slug=slug,
        timestamp_tag=ts_utc,
        candidate_meta={
            "candidate_id": best["experiment_id"],
            "description": best["description"],
            "submission_note": note_140,
        },
        prefix="kanlergems2",
    )
    tif_name = bundle["zeros_tif"]["filename"]
    tif_path = dl_dir / tif_name
    tif_sha = bundle["zeros_tif"]["sha256"]
    best["uniqueness_audit"]["exact_sha256_unique"] = bool(tif_sha not in all_registry_shas)

    clean_exps = [{k: v for k, v in e.items() if not k.startswith("_")} for e in exp_results]
    summary = {
        "schema": "kanlergemsdoe2.dslup_experiments.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane_id": "KG2-S2-DSLUP3D",
        "preregistration": "registry/preregistration_dslup.json",
        "total_wall_seconds": round(time.time() - t_start, 2),
        "within_protocol_budget": {
            "experiments_run": len(clean_exps),
            "max_experiments_allowed": 3,
            "wall_hours": round((time.time() - t_start) / 3600.0, 4),
            "max_wall_hours_allowed": 2.0,
        },
        "dslup_channel": {
            "s_px_stats": dsl["s_px_stats"],
            "deep_basin_threshold_m": deep_thresh,
            "basin_domain_px": int(basin_mask_fp.sum()),
            "canary_max_auc": canary2["max_single_feature_auc"],
            "canary_max_feature": canary2["max_feature_name"],
        },
        "reference_0p2778_benchmark": {
            "holdout_hide_recover_uncensored_dti": round(ref_hr["pooled_dti"], 6),
            "holdout_hide_recover_ci95": [round(ref_hr["ci95_cluster_bootstrap"][0], 6), round(ref_hr["ci95_cluster_bootstrap"][1], 6)],
            "holdout_sgmc_calibrated_dti": round(ref_sg["sgmc_prevalence_calibrated_dti"], 6),
        },
        "recorded_prior_promoted_exp2": {
            "file": "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif",
            "hide_recover_holdout_dti": 0.112353,
            "sgmc_cal_holdout_dti": 0.078913,
            "label": "HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232, 95% CI [0.0990, 0.1257]) — recorded 2026-10-26",
        },
        "registry_scope": {
            "rasters_checked": len(registry_rasters),
            "own_prior_rasters_in_registry": own_in_registry,
        },
        "experiments": clean_exps,
        "selected_experiment": best["experiment_id"],
        "selection_verdict_pre_validator": verdict_pre,
        "protocol_deviation": (
            astar_rec["protocol_deviation_note"] if astar_rec is not None else None
        ),
    }
    (edir / "dslup_experiments.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    run_card = {
        "schema": "gems.parallel_run_card.v1",
        "site": "KANLERGEMSDOE2",
        "repo": "kanlerxz87-cyber/KANLERGEMSDOE2",
        "branch": "arena/33f25930-kanlergemsdoe2",
        "lane_id": "KG2-S2-DSLUP3D",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": (
            f"KG2-S2 ({best['experiment_id']}: {best['name']}) — Depth-Scaled Listric Updip Continuation "
            "& Blind-Basin Dual-Population Reallocation"
        ),
        "mechanism": (
            "Replaces the fixed 400 m FFT upward-continuation updip gravity crest migration of the promoted "
            "HTCADS-DualRegime lane with a locally depth-to-basement-scaled listric-dip 3-height (150/400/800 m) "
            "continuation crest-migration projector (per-pixel updip offset s = depth/tan(dip_eff)/100 m, dip_eff "
            "62->38 deg listric, clipped 1.5-11 px) gated by multi-height strike coherence, substituted into both "
            "the 27-channel out-of-quadrant sharp GBDT and the first-principles Multi-Physics Conduit pillar, and "
            "allocates the 300 m submodular CELF budget as a dual population with a reserved concealed-basin "
            "hydro-geothermal tranche (deep basement outside 1 m LiDAR validity) packed before the main surface."
        ),
        "named_non_fault_mimic": (
            "Shallow alluvial channel edges and fan-head trenches producing short-wavelength gravity-gradient "
            "texture over basins (suppressed by the KG2-S2-H3 multi-height strike-coherence gate: they lose strike "
            "between 150 m and 800 m continuation); Pleistocene Lake Lahontan shorelines & tufa (suppressed by the "
            "inherited contour-orthogonal LiDAR specialist and sinter>>tufa weighting); unfaulted intrusive contacts "
            "(curvilinear closed loops vs linear strike persistence under the coherence gate)."
        ),
        "leakage_canary": {
            "passed": canary2["passed"],
            "max_single_feature_auc": canary2["max_single_feature_auc"],
            "max_feature_name": canary2["max_feature_name"],
            "total_features_tested": canary2["total_features_tested"],
        },
        "holdout_dti": {
            "primary_hide_and_recover": best["holdout_hide_recover"],
            "secondary_off_catalogue_sgmc": best["holdout_sgmc_offcat"],
        },
        "structural_invariants": best["structural_invariants"],
        "registry_comparison": best["uniqueness_audit"],
        "correlation_overlap_vs_registry": best["uniqueness_audit"],
        "overlap_vs_own_prior_rasters": best["overlap_vs_own_prior_rasters"],
        "overlap_vs_0p2778_champion": best["overlap_vs_0p2778_champion"],
        "raster_sha256": tif_sha,
        "zip_sha256": bundle["zeros_zip"]["sha256"],
        "submission_filename": tif_name,
        "zip_filename": bundle["zeros_zip"]["filename"],
        "submission_name": bundle["submission_name"],
        "submission_note": note_140,
        "note": note_140,
        "note_length": len(note_140),
        "preregistered_gates": best["gates"],
    }
    rc_path = edir / "dslup_run_card.json"
    rc_path.write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")

    val_path = edir / "dslup_validator_receipt.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_submission.py"),
         "--tif", str(tif_path), "--run-card", str(rc_path), "--out", str(val_path)],
        check=False,
    )
    validator_output = json.loads(val_path.read_text(encoding="utf-8"))
    run_card["validator_output"] = validator_output
    run_card["ok_to_download_and_submit"] = bool(
        validator_output["validated_ok_to_download_and_submit"] and verdict_pre == "promote"
    )
    run_card["verdict"] = "promote" if run_card["ok_to_download_and_submit"] else "negative"
    rc_path.write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")
    (dl_dir / "dslup_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")

    np.save(wdir / "best_dslup_dots.npy", best["_dots_live_2d"].astype(np.uint8))

    print("\n" + "=" * 78)
    print(f"[DSLUP] FINAL VERDICT: {run_card['verdict'].upper()} | OK TO DOWNLOAD & SUBMIT: {run_card['ok_to_download_and_submit']}")
    print(f"[DSLUP] Selected: {best['experiment_id']} ({best['name']}) -> {tif_name}")
    print(f"[DSLUP] SHA-256 : {tif_sha}")
    print(f"[DSLUP] Note ({len(note_140)}/140 chars): {note_140}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
