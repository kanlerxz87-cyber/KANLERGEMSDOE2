#!/usr/bin/env python3
"""Execute preregistered KG2-S3-GMV experiments (EXP-A, EXP-B, EXP-C) + Run Card.

Lane (frozen in registry/preregistration_gmv.json BEFORE any experiment ran):
  Range-front tectonic-Geomorphology + fossil-vent alignMent + dual-tranche allocation.

Strictly obeys Parallel-Run Protocol Rules 1-6 and REUSES the template's shared tools:
  - gems32.holdout     (leak-free Hide-and-Recover v3.0 + SGMC-CAL v3.0, seed 20261026)
  - gems32.htcads      (cached 46-ch feature stack, visible-catalogue features, CELF allocator)
  - gems32.submission  (DrivenData-compliant -zeros.tif + .zip bundle writer + 13-point audit)
  - run_htcads_experiments helpers (physics pillar, OOF pattern, uniqueness check, scaling)
Session-specific: gems32.gmv (H1 geomorph + H2 RANSAC vent corridors, label-free).
"""
from __future__ import annotations

import gc
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import lightgbm as lgb
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import run_htcads_experiments as tmpl  # noqa: E402
from gems32 import gmv, holdout, htcads, submission  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402

N_JOBS = 2
N_BOOT = 1000
SEED = 20261026
BUDGET_TOTAL = 37_654
BUDGET_VENT = 6_000
BUDGET_MAIN = BUDGET_TOTAL - BUDGET_VENT
SHARP_BASE = [i for i in range(len(htcads.SUBSURF_FEATURE_NAMES)) if i not in tmpl._REGIONAL_BLOB_COLS]
GMV_NAMES = ["gmv_front_sinuosity", "gmv_valley_vf", "gmv_tilt_coherence",
             "gmv_tpi_discord", "gmv_vent_corridor", "gmv_vent_density"]
OWN_PRIOR_TAGS = ("11a2f251", "f5a469e94b14", "cab53e1b", "c71122d5", "cecbdca7", "4ad35e71")
CHAMPION_TAG = "e5eb6e7e"
WALL_CAP_S = 2 * 3600


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for ch in iter(lambda: f.read(1 << 20), b""):
            h.update(ch)
    return h.hexdigest()


def _to_2d(vec_fp: np.ndarray, foot: np.ndarray) -> np.ndarray:
    g = np.zeros(foot.shape, dtype=np.float32)
    g[foot] = vec_fp
    return g


def _axial_enhance_2d(pi_2d: np.ndarray, foot_m: np.ndarray) -> np.ndarray:
    from scipy.ndimage import gaussian_filter

    sm = gaussian_filter(pi_2d, sigma=0.50, mode="nearest")
    out = (0.86 * pi_2d + 0.14 * sm).astype(np.float32)
    out[~foot_m] = 0.0
    return out


def _canary_new_channels(X_gmv: np.ndarray, ctx, foot: np.ndarray, fp_idx_2d: np.ndarray) -> dict:
    """Rule 4 for the 6 NEW GMV channels: same draw-20 sampling as the template canary."""
    from sklearn.metrics import roc_auc_score

    rng = np.random.default_rng(SEED)
    pos_list, neg_list = [], []
    for cell in ctx.cells:
        if cell.seed != 20:
            continue
        fp_sub = fp_idx_2d[cell.bbox]
        ty, tx = cell.truth_coords
        p = fp_sub[ty, tx]
        p = p[p >= 0]
        neg_mask = cell.active_sub & (cell.k_dg_sub == 0.0)
        ny, nx = np.nonzero(neg_mask)
        ng = fp_sub[ny, nx]
        ng = ng[ng >= 0]
        if ng.size > 60_000:
            ng = rng.choice(ng, size=60_000, replace=False)
        pos_list.append(p)
        neg_list.append(ng)
    pos_idx = np.concatenate(pos_list)
    neg_idx = np.concatenate(neg_list)
    y = np.concatenate([np.ones(pos_idx.size), np.zeros(neg_idx.size)])
    all_idx = np.concatenate([pos_idx, neg_idx])
    feats = []
    for j, name in enumerate(GMV_NAMES):
        vals = np.asarray(X_gmv[all_idx, j], dtype=np.float32)
        auc = float(roc_auc_score(y, vals))
        sym = max(auc, 1.0 - auc)
        feats.append({"feature": name, "group": "gmv_new",
                      "raw_auc": round(auc, 6), "oriented_auc": round(sym, 6)})
    feats.sort(key=lambda r: r["oriented_auc"], reverse=True)
    mx = float(feats[0]["oriented_auc"])
    return {"protocol_rule": "Rule 4 Leakage Canary (single-feature holdout AUC <= 0.90)",
            "evaluator": "GEMSDOE32-HIDE-RECOVER-v3.0 (draw20 spatially-blocked withheld segments)",
            "threshold": 0.90, "total_features_tested": len(feats),
            "n_withheld_positive_pixels_tested": int(pos_idx.size),
            "n_negative_pixels_tested": int(neg_idx.size),
            "max_single_feature_auc": round(mx, 6),
            "max_feature_name": feats[0]["feature"],
            "passed": bool(mx <= 0.90), "features": feats}


def main() -> int:
    raise SystemExit(
        "Archived runner disabled: not the assigned HTCADS lane; the literal registry stop "
        "and preserved historical receipts prohibit this execution path."
    )


def _legacy_main_archived() -> int:
    """Historical implementation retained for audit; do not use as an active runner."""
    t_start = time.time()
    ddir = data_dir()
    wdir = work_dir()
    edir = evidence_dir()
    print(f"[GMV] data={ddir} work={wdir}", flush=True)

    # ---- Rule 4 gate: base template canary receipt must exist+pass; GMV canary runs below.
    base_canary = json.loads((edir / "leakage_canary.json").read_text(encoding="utf-8"))
    if not base_canary.get("passed"):
        raise SystemExit("Base leakage canary did not pass; aborting.")
    print(f"[GMV] base canary PASSED (max AUC {base_canary['max_single_feature_auc']}).", flush=True)

    # ---- Focus-mirror SHA verification (fail closed).
    focus = {s["site"]: s for s in json.loads(
        (ROOT / "registry" / "focus_sites_20261027.json").read_text())["sites"]}
    g25_name = Path(focus["GEMSDOE25"]["path"]).name
    g32_name = Path(focus["GEMSDOE32"]["path"]).name
    # local filenames drop the GEMSDOE{nn}__ prefix used in ddir/scored
    g25_local = ROOT / "docs" / "downloads" / Path(g25_name).name
    g32_local = ROOT / "docs" / "downloads" / Path(g32_name).name
    assert _sha256(g25_local) == focus["GEMSDOE25"]["sha256"], "GEMSDOE25 mirror SHA mismatch"
    assert _sha256(g32_local) == focus["GEMSDOE32"]["sha256"], "GEMSDOE32 mirror SHA mismatch"
    print("[GMV] focus mirrors SHA-verified (G25 + G32).", flush=True)

    # ---- Template stack (reused cache) + GMV features.
    stack = htcads.build_static_feature_stack(ddir, wdir / "htcads_cache")
    foot = stack["foot"]
    lidar_valid_fp = stack["lidar_valid_fp"]
    X_sub, X_lid = stack["X_sub"], stack["X_lid"]
    n_fp = int(foot.sum())
    with rasterio.open(ddir / "sample_submission.tif") as ds:
        transform, shape = ds.transform, (ds.height, ds.width)

    g_path = wdir / "X_gmv_fp_f32.npy"
    g_done = wdir / "X_gmv_fp.done"
    gmv_cache_reused = bool(g_done.exists() and g_path.exists())
    if gmv_cache_reused:
        # Deterministic builders; a completed cache is bit-identical to a rebuild.
        # (Resume path for wall-budget safety; recorded in the experiments receipt.)
        X_gmv = np.load(g_path, mmap_mode="r")
        assert X_gmv.shape == (n_fp, 6), f"stale GMV cache shape {X_gmv.shape}"
        print("[GMV] reusing completed GMV feature cache (deterministic rebuild skipped).", flush=True)
    else:
        print("[GMV] Building H1 geomorphology suite...", flush=True)
        t0 = time.time()
        h1 = gmv.build_h1_geomorph(ddir, foot)
        print(f"[GMV]   H1 done in {time.time()-t0:.0f}s", flush=True)
        hg_gate = np.maximum(np.asarray(X_sub[:, 0]), np.asarray(X_sub[:, 5]))
        hg_2d = _to_2d(hg_gate.astype(np.float32), foot)
        del hg_gate
        print("[GMV] Building H2 vent-alignment corridors...", flush=True)
        t0 = time.time()
        h2 = gmv.build_h2_corridors(ddir, foot, transform, shape, hg_2d)
        print(f"[GMV]   H2 done in {time.time()-t0:.0f}s "
              f"(points={h2['n_h2_points']}, lines={h2['n_h2_lines']})", flush=True)
        del hg_2d
        X_gmv = np.lib.format.open_memmap(g_path, mode="w+", dtype=np.float32, shape=(n_fp, 6))
        for j, nm in enumerate(GMV_NAMES):
            src = h1[nm] if nm in h1 else h2[nm]
            X_gmv[:, j] = src[foot]
            del src
        X_gmv.flush()
        X_gmv = np.load(g_path, mmap_mode="r")
        g_done.write_text(datetime.now(timezone.utc).isoformat() + "\n", encoding="utf-8")
        del h1, h2
        gc.collect()
    for j, nm in enumerate(GMV_NAMES):
        v = np.asarray(X_gmv[:, j])
        print(f"[GMV]   {nm}: mean={v.mean():.4f} p99={np.percentile(v, 99):.4f} "
              f"frac>0={np.mean(v > 0):.3f}", flush=True)

    ctx = holdout.load_holdout_context(ddir)
    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(n_fp, dtype=np.int32)

    # ---- Rule 4: canary on NEW channels.
    can_new = _canary_new_channels(X_gmv, ctx, foot, fp_idx_2d)
    (edir / "gmv_canary_20261027.json").write_text(json.dumps(can_new, indent=2) + "\n")
    print(f"[GMV] Rule 4 NEW-channel canary: {'PASSED' if can_new['passed'] else 'FAILED'} "
          f"(max AUC {can_new['max_single_feature_auc']} @ {can_new['max_feature_name']})", flush=True)
    if not can_new["passed"]:
        raise SystemExit("GMV LEAKAGE CANARY FAILED (AUC > 0.90)")

    # ---- Fresh REF benchmarks (template-identical calls).
    with rasterio.open(g25_local) as ds:
        a = ds.read(1)
        d28_mask = foot & np.isfinite(a) & (a >= 0.5)
    with rasterio.open(g32_local) as ds:
        a = ds.read(1)
        b2_mask = foot & np.isfinite(a) & (a >= 0.5)
    print(f"[GMV] REF masks: d28={int(d28_mask.sum())} b2={int(b2_mask.sum())}", flush=True)
    ref_hr = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0,
                                               n_boot=N_BOOT, seed=SEED, name="GEMSDOE32_B2_ref")
    ref_sg = holdout.evaluate_sgmc_with_ci(b2_mask, ctx, n_boot=N_BOOT, seed=SEED,
                                           name="GEMSDOE32_B2_ref")
    hr_b2_diag = holdout.evaluate_hide_and_recover(b2_mask, ctx, b_visible_px=2.0,
                                                   n_boot=N_BOOT, seed=SEED, name="G32mask_diag")
    print(f"[GMV] REF HR={ref_hr['pooled_dti']:.6f} "
          f"[{ref_hr['ci95_cluster_bootstrap'][0]:.4f},{ref_hr['ci95_cluster_bootstrap'][1]:.4f}] "
          f"SGMC-CAL={ref_sg['sgmc_prevalence_calibrated_dti']:.6f}; "
          f"diag HR(G32mask)={hr_b2_diag['pooled_dti']:.6f}", flush=True)

    # ---- Physics pillar: template phys2 + GMV scaled addition (weights fixed pre-results).
    _p1, phys2 = tmpl._build_physical_conduit_scores(X_sub, X_lid, lidar_valid_fp)
    del _p1
    l_geo = np.maximum.reduce([np.asarray(X_gmv[:, 0]), np.asarray(X_gmv[:, 1]),
                               np.asarray(X_gmv[:, 2]), np.asarray(X_gmv[:, 3])]).astype(np.float32)
    l_vent = np.asarray(X_gmv[:, 4]).astype(np.float32)
    gmv_raw = (0.60 * l_geo + 0.40 * l_vent).astype(np.float32)
    del l_geo, l_vent
    gmv_scaled = np.clip(gmv_raw * (0.045 / (float(np.percentile(gmv_raw, 99.2)) + 1e-6)),
                         0.0, 0.12).astype(np.float32)
    del gmv_raw
    phys_gmv = np.clip(0.62 * phys2 + 0.38 * gmv_scaled, 0.0, 0.12).astype(np.float32)
    del phys2, gmv_scaled

    # ---- Vent tranche domain/surface (static, label-free).
    vent_corr_fp = np.asarray(X_gmv[:, 4]).astype(np.float32)
    vthr = max(1e-6, float(np.percentile(vent_corr_fp, 92.0)))
    vent_mask_fp = vent_corr_fp > vthr
    print(f"[GMV] vent domain: {int(vent_mask_fp.sum()):,} px "
          f"({100*vent_mask_fp.mean():.1f}% footprint, thr={vthr:.4f})", flush=True)
    vent_2d = np.zeros(foot.shape, dtype=bool)
    vent_2d[foot] = vent_mask_fp
    pi_vent_2d = _to_2d(np.where(vent_mask_fp, vent_corr_fp, 0.0).astype(np.float32), foot)
    del vent_corr_fp, vent_mask_fp

    # ---- OOF blind GBDT (sharp template cols + 6 GMV cols) + LiDAR specialist.
    NAUG = X_sub.shape[1]
    SHARP_AUG = SHARP_BASE + [NAUG + j for j in range(6)]

    def _Xaug_block(idx: np.ndarray, cols: list[int]) -> np.ndarray:
        idx = np.asarray(idx)
        base_c = [c for c in cols if c < NAUG]
        gmv_c = [c - NAUG for c in cols if c >= NAUG]
        parts = []
        if base_c:
            parts.append(np.asarray(X_sub[idx][:, base_c], dtype=np.float32))
        if gmv_c:
            parts.append(np.asarray(X_gmv[idx][:, gmv_c], dtype=np.float32))
        return np.hstack(parts) if len(parts) == 2 else parts[0]

    def _predict_aug(clf, cols: list[int], chunk: int = 900_000) -> np.ndarray:
        out = np.empty(n_fp, dtype=np.float32)
        for s in range(0, n_fp, chunk):
            e = min(s + chunk, n_fp)
            out[s:e] = clf.predict_proba(
                _Xaug_block(np.arange(s, e), cols))[:, 1].astype(np.float32)
        return out

    rng = np.random.default_rng(SEED)
    labels_dil3 = binary_dilation(ctx.labels, structure=np.ones((3, 3), bool), iterations=3)
    gbdt_oof = np.zeros(n_fp, dtype=np.float32)
    gbdt_full = np.zeros(n_fp, dtype=np.float32)
    lid_oof = np.zeros(n_fp, dtype=np.float32)
    lid_full = np.zeros(n_fp, dtype=np.float32)
    for fold in holdout.FOLDS:
        t0 = time.time()
        q_fp = fp_idx_2d[(ctx.quad == fold) & foot]
        collar = binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool),
                                 iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar
        pos_2d = binary_dilation(ctx.labels & tdom, structure=np.ones((3, 3), bool),
                                 iterations=1) & tdom
        pos_idx = fp_idx_2d[pos_2d]
        neg_idx = fp_idx_2d[tdom & ~labels_dil3]
        if pos_idx.size > 38_000:
            pos_idx = rng.choice(pos_idx, size=38_000, replace=False)
        neg_sub = rng.choice(neg_idx, size=min(neg_idx.size, pos_idx.size * 4), replace=False)
        tr_idx = np.concatenate([pos_idx, neg_sub])
        y_tr = np.concatenate([np.ones(pos_idx.size, dtype=np.int8),
                               np.zeros(neg_sub.size, dtype=np.int8)])
        clf = lgb.LGBMClassifier(
            n_estimators=135, learning_rate=0.065, num_leaves=31, min_child_samples=100,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.75,
            reg_alpha=2.0, reg_lambda=8.0, random_state=400 + fold, n_jobs=N_JOBS, verbose=-1)
        clf.fit(_Xaug_block(tr_idx, SHARP_AUG), y_tr)
        pred = _predict_aug(clf, SHARP_AUG)
        gbdt_oof[q_fp] = pred[q_fp]
        gbdt_full += 0.25 * pred
        del clf, pred
        gc.collect()
        pos_lid = pos_idx[lidar_valid_fp[pos_idx]]
        pool_lid = neg_idx[lidar_valid_fp[neg_idx]]
        neg_lid = rng.choice(pool_lid, size=min(pool_lid.size, pos_lid.size * 4), replace=False)
        tr_lid = np.concatenate([pos_lid, neg_lid])
        y_lid = np.concatenate([np.ones(pos_lid.size, dtype=np.int8),
                                np.zeros(neg_lid.size, dtype=np.int8)])
        clf_l = lgb.LGBMClassifier(
            n_estimators=115, learning_rate=0.065, num_leaves=23, min_child_samples=100,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.85,
            reg_alpha=2.5, reg_lambda=8.0, random_state=600 + fold, n_jobs=N_JOBS, verbose=-1)
        clf_l.fit(np.asarray(X_lid[tr_lid], dtype=np.float32), y_lid)
        raw = tmpl._predict_chunked(clf_l, X_lid, cols=None)
        lg = tmpl._logit(raw)
        resid = np.where(lidar_valid_fp, lg - float(np.mean(lg[lidar_valid_fp])),
                         0.0).astype(np.float32)
        lid_oof[q_fp] = resid[q_fp]
        lid_full += 0.25 * resid
        del clf_l, raw, lg, resid
        gc.collect()
        print(f"[GMV] quadrant {fold} trained in {time.time()-t0:.0f}s "
              f"(elapsed {time.time()-t_start:.0f}s)", flush=True)

    def _scale_blind(p_gbdt, phys_fp, lid_res):
        p_g = tmpl._sigmoid(tmpl._logit(p_gbdt) + 0.55 * lid_res)
        p_gn = np.clip(p_g * (0.045 / (float(np.percentile(p_g, 99.2)) + 1e-6)), 0.0, 0.12)
        return (0.45 * p_gn + 0.55 * phys_fp).astype(np.float32)

    pi_oof = _scale_blind(gbdt_oof, phys_gmv, lid_oof)
    pi_full = _scale_blind(gbdt_full, phys_gmv, lid_full)
    del gbdt_oof, gbdt_full, phys_gmv, lid_oof
    gc.collect()

    # ---- Tip/relay specialist + per-cell OOF emissions.
    X_vis_full, aux_full = htcads.compute_visible_catalogue_features(ctx.labels, foot)
    X_vis_full_dir = X_vis_full[:, [1, 2]].copy()
    tip_full = (np.clip(np.maximum(X_vis_full_dir[:, 0], X_vis_full_dir[:, 1]),
                        0.0, 1.0) ** 0.65).astype(np.float32)
    del X_vis_full
    d_full = aux_full["d_vis"]
    elig_b2_live = foot & (d_full > 2.0)
    elig_aniso_live = foot & np.where(
        (aux_full["tip_cone_2d"] >= 0.55) | (aux_full["relay_2d"] >= 0.45),
        d_full > 1.45, d_full > 2.15)
    del aux_full
    gc.collect()

    def _emit(pi_2d, elig, mode):
        if mode == "A":
            return htcads.emit_submodular_celf(pi_2d, elig, max_dots=BUDGET_TOTAL,
                                               marginal_bar=0.0)
        em_v = htcads.emit_submodular_celf(pi_vent_2d, elig & vent_2d, max_dots=BUDGET_VENT,
                                           marginal_bar=0.0)
        excl = distance_transform_edt(~em_v) <= 3.0 if em_v.any() else np.zeros_like(em_v)
        if mode == "B":
            em_m = htcads.emit_submodular_celf(pi_2d, elig & ~excl, max_dots=BUDGET_MAIN,
                                               marginal_bar=0.0)
        else:
            em_m = htcads.emit_submodular_celf(_axial_enhance_2d(pi_2d, foot), elig & ~excl,
                                               max_dots=BUDGET_MAIN, marginal_bar=0.0020)
        return em_v | em_m

    cell_em = {"EXP-A": {}, "EXP-B": {}, "EXP-C": {}}
    p_tip_live = np.zeros(n_fp, dtype=np.float32)
    for ic, cell in enumerate(ctx.cells):
        t0 = time.time()
        collar = binary_dilation(ctx.quad == cell.fold, structure=np.ones((3, 3), bool),
                                 iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar
        Xv, aux = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
        Xv_dir = Xv[:, [1, 2]].copy()
        tip_c = (np.clip(np.maximum(Xv_dir[:, 0], Xv_dir[:, 1]), 0.0, 1.0) ** 0.65
                 ).astype(np.float32)
        del Xv
        dv = aux["d_vis"]
        e_b2 = foot & (dv > 2.0)
        e_an = foot & np.where((aux["tip_cone_2d"] >= 0.55) | (aux["relay_2d"] >= 0.45),
                               dv > 1.45, dv > 2.15)
        del aux
        act = np.zeros(foot.shape, dtype=bool)
        act[foot] = tip_c > 0.02
        hid = (ctx.labels & tdom) & ~cell.visible_full
        pos_fp = fp_idx_2d[binary_dilation(hid, structure=np.ones((3, 3), bool),
                                           iterations=1) & tdom & (dv > 1.4) & act]
        neg_pool = fp_idx_2d[tdom & ~labels_dil3 & (dv > 1.4) & act]
        del dv, hid, act
        neg_fp = rng.choice(neg_pool, size=min(neg_pool.size, pos_fp.size * 5), replace=False)
        tr = np.concatenate([pos_fp, neg_fp])
        y = np.concatenate([np.ones(pos_fp.size, dtype=np.int8),
                            np.zeros(neg_fp.size, dtype=np.int8)])
        clf_t = lgb.LGBMClassifier(
            n_estimators=125, learning_rate=0.06, num_leaves=23, min_child_samples=60,
            subsample=0.80, subsample_freq=1, colsample_bytree=0.80,
            reg_alpha=2.0, reg_lambda=8.0, random_state=700 + ic, n_jobs=N_JOBS, verbose=-1)
        clf_t.fit(np.hstack([_Xaug_block(tr, SHARP_AUG), Xv_dir[tr]]), y)
        nz = np.flatnonzero(tip_c > 0.02)
        raw_nz = clf_t.predict_proba(
            np.hstack([_Xaug_block(nz, SHARP_AUG), Xv_dir[nz]]))[:, 1].astype(np.float32)
        sharp = tmpl._sigmoid(tmpl._logit(raw_nz) + 0.40 * lid_full[nz])
        pi_t = np.zeros(n_fp, dtype=np.float32)
        pi_t[nz] = np.clip(0.028 * sharp * tip_c[nz], 0.0, 0.036)
        if cell.seed == 20:
            nzl = np.flatnonzero(tip_full > 0.02)
            raw_lv = clf_t.predict_proba(
                np.hstack([_Xaug_block(nzl, SHARP_AUG), X_vis_full_dir[nzl]])
            )[:, 1].astype(np.float32)
            sh_lv = tmpl._sigmoid(tmpl._logit(raw_lv) + 0.40 * lid_full[nzl])
            p_tip_live[nzl] += 0.25 * np.clip(0.028 * sh_lv * tip_full[nzl], 0.0, 0.036)
            del raw_lv, sh_lv, nzl
        del clf_t, raw_nz, sharp, Xv_dir, tip_c
        pi_cell = _to_2d(1.0 - (1.0 - pi_t) * (1.0 - pi_oof), foot)
        del pi_t
        cell_em["EXP-A"][cell.key] = _emit(pi_cell, e_b2, "A")[cell.bbox].copy()
        cell_em["EXP-B"][cell.key] = _emit(pi_cell, e_b2, "B")[cell.bbox].copy()
        cell_em["EXP-C"][cell.key] = _emit(pi_cell, e_an, "C")[cell.bbox].copy()
        del pi_cell, e_b2, e_an
        gc.collect()
        print(f"[GMV] cell {cell.key} done in {time.time()-t0:.0f}s "
              f"(elapsed {time.time()-t_start:.0f}s)", flush=True)
        if time.time() - t_start > WALL_CAP_S:
            raise SystemExit("GMV wall-clock budget exceeded")

    del X_vis_full_dir, labels_dil3
    gc.collect()

    # ---- Registry + live surfaces.
    print("[GMV] loading registry...", flush=True)
    t0 = time.time()
    registry, reg_idx, reg_shas = tmpl._collect_registry_rasters(foot)
    print(f"[GMV] registry: {len(registry)} footprint-distinct rasters "
          f"in {time.time()-t0:.0f}s", flush=True)
    own_hit = [r["name"] for r in registry if any(t in r["name"] for t in OWN_PRIOR_TAGS)]
    champ_hit = [r["name"] for r in registry if CHAMPION_TAG in r["name"]]
    print(f"[GMV] own priors in registry: {len(own_hit)}; champion files: {len(champ_hit)}",
          flush=True)
    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        lid_valid_2d = (s_lid.read(12) > 0) & foot

    pi_live = 1.0 - (1.0 - p_tip_live) * (1.0 - pi_full)
    pi_base = _to_2d(pi_live.astype(np.float32), foot)
    pi_ax = _axial_enhance_2d(pi_base, foot)
    del pi_live, p_tip_live, pi_full
    gc.collect()

    specs = [
        {"id": "EXP-A", "mode": "A", "elig": elig_b2_live,
         "surf": pi_base, "desc": "H1 geomorph suite in GBDT + physics pillar; B=2.0; single CELF 37654."},
        {"id": "EXP-B", "mode": "B", "elig": elig_b2_live,
         "surf": pi_base, "desc": "EXP-A + H2 RANSAC vent corridors; dual CELF (6000 vent + 31654 main)."},
        {"id": "EXP-C", "mode": "C", "elig": elig_aniso_live,
         "surf": pi_ax, "desc": "EXP-B + axial smoothing + aniso collar + bar 0.0020."},
    ]
    results = []
    for spec in specs:
        dots = _emit(spec["surf"] if spec["id"] != "EXP-C" else pi_base, spec["elig"], spec["mode"])
        # NOTE: EXP-C emission uses the axial surface inside _emit; uniqueness surface matches.
        ev_hr = holdout.evaluate_hide_and_recover(cell_em[spec["id"]], ctx, b_visible_px=0.0,
                                                  n_boot=N_BOOT, seed=SEED, name=spec["id"])
        d_hr = holdout.paired_bootstrap_delta(ev_hr, ref_hr, boot_key="_boots")
        ev_sg = holdout.evaluate_sgmc_with_ci(dots, ctx, n_boot=N_BOOT, seed=SEED, name=spec["id"])
        d_sg = holdout.paired_bootstrap_delta(ev_sg, ref_sg, boot_key="_cal_boots")
        uniq = tmpl._check_uniqueness(spec["surf"], dots, foot, registry, reg_idx)
        dk = distance_transform_edt(~ctx.labels)[dots]
        res = {"id": spec["id"], "description": spec["desc"],
               "n_dots": int(dots.sum()),
               "hr": {"pooled_dti": ev_hr["pooled_dti"], "ci95": ev_hr["ci95_cluster_bootstrap"],
                      "paired_delta": d_hr["delta"], "paired_ci95": d_hr["ci95"],
                      "win_prob": d_hr.get("win_prob")},
               "sgmc": {"raw": ev_sg["sgmc_raw_pooled_dti"], "raw_ci95": ev_sg["sgmc_raw_ci95"],
                        "cal": ev_sg["sgmc_prevalence_calibrated_dti"],
                        "cal_ci95": ev_sg["sgmc_calibrated_ci95"],
                        "paired_delta": d_sg["delta"], "paired_ci95": d_sg["ci95"],
                        "win_prob": d_sg.get("win_prob")},
               "uniq": uniq,
               "struct": {"median_d_known_px": float(np.median(dk)),
                          "pct_le_2px": float(np.mean(dk <= 2.0)),
                          "pct_le_10px": float(np.mean(dk <= 10.0)),
                          "pct_in_lidar": float(np.mean(lid_valid_2d[dots]))}}
        del dk
        results.append(res)
        print(f"[GMV] {spec['id']}: HR={res['hr']['pooled_dti']:.6f} "
              f"(d={res['hr']['paired_delta']:+.6f} CI[{res['hr']['paired_ci95'][0]:+.4f},"
              f"{res['hr']['paired_ci95'][1]:+.4f}]) SGMC={res['sgmc']['cal']:.6f} "
              f"(d={res['sgmc']['paired_delta']:+.6f} CI[{res['sgmc']['paired_ci95'][0]:+.4f},"
              f"{res['sgmc']['paired_ci95'][1]:+.4f}]) det3px={uniq['final_dots_max_detector_3px_overlap']:.4f} "
              f"all3px={uniq['final_dots_max_3px_overlap_all']:.4f} dots={res['n_dots']}",
              flush=True)
        np.save(wdir / f"gmv_dots_{spec['id']}.npy", dots)
        del dots
        gc.collect()

    exp_receipt = {
        "schema": "KANLERGEMSDOE2-GMV-EXPERIMENTS-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "KG2-S3-GMV", "budget_cap_experiments": 3,
        "experiments_executed": 3, "elapsed_seconds": round(time.time() - t_start, 1),
        "preregistration": "registry/preregistration_gmv.json",
        "gmv_cache_reused": bool(gmv_cache_reused),
        "reference": {
            "hr_pooled_dti": ref_hr["pooled_dti"], "hr_ci95": ref_hr["ci95_cluster_bootstrap"],
            "sgmc_cal": ref_sg["sgmc_prevalence_calibrated_dti"],
            "sgmc_cal_ci95": ref_sg["sgmc_calibrated_ci95"],
            "diag_hr_g32mask": hr_b2_diag["pooled_dti"],
            "n_hr_withheld": 22232, "n_sgmc": int(ctx.sgmc_n_truth)},
        "registry": {"unique_rasters": len(registry),
                     "own_priors_present": own_hit, "champion_present": champ_hit},
        "canary_new_channels": can_new,
        "experiments": results,
    }
    (edir / "gmv_experiments_20261027.json").write_text(
        json.dumps(exp_receipt, indent=2, default=float) + "\n", encoding="utf-8")

    # ---- Gate (champion-mode promotion bar from preregistration).
    def _passes(r):
        u = r["uniq"]
        return bool(
            r["hr"]["paired_ci95"][0] > 0.0 and r["sgmc"]["paired_ci95"][0] > 0.0
            and u["pre_placement_surface_max_abs_spearman"] <= 0.90
            and u["final_dots_max_abs_spearman"] <= 0.90
            and u["final_dots_max_detector_3px_overlap"] <= 0.70
            and r["struct"]["pct_le_2px"] == 0.0 and r["n_dots"] == BUDGET_TOTAL)

    passing = [r for r in results if _passes(r)]
    passing.sort(key=lambda r: r["sgmc"]["cal"], reverse=True)
    wall = time.time() - t_start
    card = {
        "schema": "gems.parallel_run_card.v1", "site": "KANLERGEMSDOE2",
        "repo": "kanlerxz87-cyber/KANLERGEMSDOE2", "branch": "arena/e896cd9a-kanlergemsdoe2",
        "lane_id": "KG2-S3-GMV",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "KG2-S3 GMV: range-front Smf/Vf/tilt/TPI-discordance + RANSAC fossil-vent alignment corridors",
        "mechanism": ("H1 4-ch geomorph suite + H2 2-ch vent corridors appended to sharp-column OOF LightGBM; "
                      "template physics pillar + GMV scaled addition (0.62/0.38); tip/relay Noisy-OR; exact 300m CELF"
                      + ("; 6000-dot vent tranche" if passing and passing[0]["id"] != "EXP-A" else "; single emission")),
        "named_non_fault_mimic": ("Lithologic fronts/faceted spurs (HG-step gate), Lahontan shorelines "
                                  "(contour-discordance), road-following springs (TIGER clearance), mine blasts "
                                  "(depth<=12km + HG coincidence)."),
        "leakage_canary": {"passed": bool(can_new["passed"]),
                           "max_single_feature_auc": can_new["max_single_feature_auc"],
                           "max_feature_name": can_new["max_feature_name"],
                           "total_features_tested": 6,
                           "base_template_canary": {"passed": True,
                                                    "max_single_feature_auc": base_canary["max_single_feature_auc"]}},
        "wall_seconds": round(wall, 1),
        "experiments_run": 3,
    }
    if passing:
        w = passing[0]
        dots = np.load(wdir / f"gmv_dots_{w['id']}.npy")
        tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        note = (f"KG2-S3 GMV {w['id']}: Smf/Vf/tilt+TPI x RANSAC vent corridors, dual CELF "
                f"(HR={w['hr']['pooled_dti']:.4f}, SGMC={w['sgmc']['cal']:.4f} vs ref)")
        if len(note) > 140:
            note = note[:140]
        bundle = submission.write_submission_bundle(
            dots, foot, ctx.labels, ddir / "sample_submission.tif", downloads_dir(),
            slug=f"gmv-{w['id'].lower()}-37654dots", timestamp_tag=tag,
            candidate_meta={"candidate_id": f"KG2-S3-GMV-{w['id']}",
                            "description": w["description"], "submission_note": note})
        tif_path = downloads_dir() / (bundle["submission_name"] + ".tif")
        card.update({
            "winning_experiment": w["id"], "verdict": "promote",
            "ok_to_download_and_submit": True,
            "holdout_dti": {
                "primary_hide_and_recover": {
                    "pooled_dti": w["hr"]["pooled_dti"], "ci95": w["hr"]["ci95"],
                    "champion_02778_same_evaluator": ref_hr["pooled_dti"],
                    "paired_delta_vs_0p2778_ref": w["hr"]["paired_delta"],
                    "paired_delta_ci95": w["hr"]["paired_ci95"],
                    "label": ("HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N=22232 withheld "
                              "positives, 95% CI)")},
                "secondary_off_catalogue_sgmc": {
                    "sgmc_prevalence_calibrated_dti": w["sgmc"]["cal"],
                    "ci95": w["sgmc"]["cal_ci95"],
                    "champion_02778_same_evaluator": ref_sg["sgmc_prevalence_calibrated_dti"],
                    "paired_delta_vs_0p2778_ref": w["sgmc"]["paired_delta"],
                    "paired_delta_ci95": w["sgmc"]["paired_ci95"],
                    "label": ("HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N=%d off-catalogue SGMC "
                              "positives, 95% CI)" % int(ctx.sgmc_n_truth))}},
            "structural_invariants": w["struct"],
            "registry_comparison": {**w["uniq"],
                                    "exact_sha256_unique": bundle["zeros_tif"]["sha256"] not in reg_shas},
            "raster_sha256": bundle["zeros_tif"]["sha256"],
            "submission_filename": tif_path.name,
            "zip_filename": bundle["submission_name"] + ".zip",
            "zip_sha256": bundle["zeros_zip"]["sha256"],
            "submission_name": bundle["submission_name"],
            "submission_note": note,
            "validator_output": bundle["zeros_tif"],
        })
        print(f"[GMV] PROMOTE {w['id']}: {tif_path.name}", flush=True)
    else:
        card.update({
            "winning_experiment": None, "verdict": "negative",
            "ok_to_download_and_submit": False,
            "holdout_dti": {"note": "No experiment passed the preregistered promotion bar; "
                                    "per-experiment numbers in evidence/gmv_experiments_20261027.json."},
            "registry_comparison": {"note": "Per-experiment uniqueness in experiments receipt."},
            "raster_sha256": None, "submission_filename": None,
            "submission_name": None, "submission_note": None,
            "validator_output": None,
        })
        print("[GMV] NEGATIVE: no experiment passed the promotion bar.", flush=True)
    (edir / "gmv_run_card_20261027.json").write_text(
        json.dumps(card, indent=2, default=float) + "\n", encoding="utf-8")
    if card["verdict"] == "promote":
        (downloads_dir() / "gmv_run_card.json").write_text(
            (edir / "gmv_run_card_20261027.json").read_text(encoding="utf-8"), encoding="utf-8")
    print(f"[GMV] done in {wall:.0f}s; verdict={card['verdict']}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
