#!/usr/bin/env python3
"""KG2-ECPU-20261027 lane: effort-corrected PU propensity reweighting (preregistered).

Frozen design: registry/preregistration_ecpu_20261027.json (read it first).
Reuses shared template code only (Protocol Rule 2): gems32.htcads cached stack +
emit_submodular_celf, gems32.holdout evaluators, gems32.submission writer/auditor,
and the registry collector / uniqueness checker from scripts/run_htcads_experiments.py
(imported, not forked).

Outputs (never overwrites prior lanes' receipts):
  evidence/ecpu_experiments_20261027.json
  evidence/run_card_ecpu_20261027.json
  docs/downloads/kanlergems2-ecpu-<exp>-37654dots-20261027T<time>Z-<digest8>-zeros.tif (+ .zip + validation.json)
    - written for the selected experiment even when verdict=negative, in which case the
      run card / site must label it DO NOT SUBMIT (negative results are deliverables).

Selection rule (frozen pre-experiment): highest HIDE-RECOVER-v3.0 OOF pooled DTI among
EXP-1..3 passing uniqueness; tie-break SGMC-CAL. Twin C0 (unweighted) is a
non-promotable ablation control inside EXP-1.
"""
from __future__ import annotations

import gc
import hashlib
import importlib.util
import json
import shutil
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

from gems32 import holdout, htcads, submission  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402

# Reuse (do not fork) the HTCADS lane's registry collector + uniqueness checker.
_spec = importlib.util.spec_from_file_location(
    "run_htcads_experiments", ROOT / "scripts" / "run_htcads_experiments.py"
)
_ht = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_ht)  # defines functions/constants only; main() is __main__-guarded

SEED = 20261026  # identical bootstrap seed to prior lane for paired comparability
N_BOOT = 1000
MAX_DOTS = 37_654
REGIONAL_BLOB_COLS = {20, 21, 22, 24, 25, 26, 27, 33, 35}
SHARP_COLS = [i for i in range(len(htcads.SUBSURF_FEATURE_NAMES)) if i not in REGIONAL_BLOB_COLS]
STRATA_CAPS = {"high": 15_062, "mid": 13_179, "low": 9_413}  # 40/35/25% of 37,654


def _predict_chunked(model, X, cols=None, chunk=1_100_000):
    out = np.empty(X.shape[0], dtype=np.float32)
    for s in range(0, X.shape[0], chunk):
        blk = np.asarray(X[s : s + chunk], dtype=np.float32)
        if cols is not None:
            blk = blk[:, cols]
        out[s : s + chunk] = model.predict_proba(blk)[:, 1].astype(np.float32)
    return out


def _read_band_fp(path: Path, band: int, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(band).astype(np.float64)
    v = a[foot]
    med = float(np.nanmedian(v[np.isfinite(v)])) if np.isfinite(v).any() else 0.0
    v = np.where(np.isfinite(v), v, med)
    return v.astype(np.float32)


def _to2d(vec_fp, foot):
    g = np.zeros(foot.shape, dtype=np.float32)
    g[foot] = vec_fp
    return g


def _emit_stratified(pi2d, elig2d, e2d, ridge2d=None):
    """EXP-2 (ridge2d None) / EXP-3 (ridge gate on low stratum) emission."""
    ev = e2d[elig2d]
    if ev.size == 0:
        return np.zeros(pi2d.shape, dtype=bool)
    t1, t2 = np.percentile(ev, [33.3333, 66.6667])
    strata = {
        "high": elig2d & (e2d > t2),
        "mid": elig2d & (e2d > t1) & (e2d <= t2),
        "low": elig2d & (e2d <= t1),
    }
    if ridge2d is not None and strata["low"].any():
        thr = float(np.percentile(ridge2d[strata["low"]], 70.0))
        strata["low"] = strata["low"] & (ridge2d >= thr)
    dots = np.zeros(pi2d.shape, dtype=bool)
    for name, cap in STRATA_CAPS.items():
        if strata[name].any():
            dots |= htcads.emit_submodular_celf(pi2d, strata[name], max_dots=cap, marginal_bar=0.0)
    return dots


def main() -> int:
    t_start = time.time()
    ddir, wdir, edir = data_dir(), work_dir(), evidence_dir()
    canary = json.loads((edir / "ecpu_leakage_canary_20261027.json").read_text())
    assert canary["passed"] and canary["max_single_feature_auc"] <= 0.90, "Gate 2 canary failed"
    print(f"[ECPU] Gate2 canary OK maxAUC={canary['max_single_feature_auc']:.6f}", flush=True)

    stack = htcads.build_static_feature_stack(ddir, wdir)
    foot, X_sub = stack["foot"], stack["X_sub"]
    lidar_valid_fp = stack["lidar_valid_fp"].astype(np.float32)
    n_fp = int(foot.sum())
    ctx = holdout.load_holdout_context(ddir)

    # --- effort covariates (label-free) -------------------------------------
    depth = _read_band_fp(ddir / "training_features.tif", 15, foot)
    slope = _read_band_fp(ddir / "training_features.tif", 19, foot)
    road = _read_band_fp(ddir / "external" / "tiger_road_distance_m.tif", 1, foot)
    E = np.column_stack([
        lidar_valid_fp,
        np.log1p(np.clip(depth - float(depth.min()), 0, None)),
        slope,
        np.log1p(np.clip(road, 0, None)),
    ]).astype(np.float32)
    del depth, slope, road
    ridge_fp = np.maximum.reduce([
        np.asarray(X_sub[:, 0]), np.asarray(X_sub[:, 5]), np.asarray(X_sub[:, 10])
    ]).astype(np.float32)
    ridge2d = _to2d(ridge_fp, foot)

    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(n_fp, dtype=np.int32)
    labels_dil3 = binary_dilation(ctx.labels, structure=np.ones((3, 3), bool), iterations=3)
    rng = np.random.default_rng(20261027)

    # --- references (benchmarks, not experiments) ----------------------------
    def _mask(p):
        with rasterio.open(p) as ds:
            a = ds.read(1)
        return foot & np.isfinite(a) & (a >= 0.5)

    d28_mask = _mask(ddir / "scored" / "gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    b2_mask = _mask(ddir / "focus9" / "GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif")
    ht_mask = _mask(ROOT / "docs" / "downloads" / "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif")
    ref_hr = holdout.evaluate_hide_and_recover(d28_mask, ctx, b_visible_px=2.0, n_boot=N_BOOT, seed=SEED, name="REF-B2-procedural")
    ref_sg_b2 = holdout.evaluate_sgmc_with_ci(b2_mask, ctx, n_boot=N_BOOT, seed=SEED, name="REF-B2-static")
    ref_sg_ht = holdout.evaluate_sgmc_with_ci(ht_mask, ctx, n_boot=N_BOOT, seed=SEED, name="REF-HTCADS-static")
    print(f"[ECPU] REF B2 HR-procedural={ref_hr['pooled_dti']:.6f} SGMC={ref_sg_b2['sgmc_prevalence_calibrated_dti']:.6f} "
          f"| HTCADS SGMC={ref_sg_ht['sgmc_prevalence_calibrated_dti']:.6f}", flush=True)
    del d28_mask, b2_mask, ht_mask

    # --- per-fold training: propensity + weighted detector + unweighted twin -
    oof_w = np.zeros(n_fp, np.float32); full_w = np.zeros(n_fp, np.float32)
    oof_u = np.zeros(n_fp, np.float32); full_u = np.zeros(n_fp, np.float32)
    oof_e = np.zeros(n_fp, np.float32); full_e = np.zeros(n_fp, np.float32)
    e_by_fold = {}
    w_stats = {}
    for fold in holdout.FOLDS:
        t0 = time.time()
        q_mask = (ctx.quad == fold) & foot
        q_fp = fp_idx_2d[q_mask]
        collar = binary_dilation(ctx.quad == fold, structure=np.ones((3, 3), bool),
                                  iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar
        pos_2d = binary_dilation(ctx.labels & tdom, structure=np.ones((3, 3), bool), iterations=1) & tdom
        neg_2d = tdom & ~labels_dil3
        pos_idx = fp_idx_2d[pos_2d]; neg_idx = fp_idx_2d[neg_2d]
        if pos_idx.size > 38_000:
            pos_idx = rng.choice(pos_idx, size=38_000, replace=False)
        neg_sub = rng.choice(neg_idx, size=min(neg_idx.size, pos_idx.size * 4), replace=False)
        tr = np.concatenate([pos_idx, neg_sub])
        y = np.concatenate([np.ones(pos_idx.size, np.int8), np.zeros(neg_sub.size, np.int8)])

        prop = lgb.LGBMClassifier(n_estimators=80, learning_rate=0.08, num_leaves=15,
                                  min_child_samples=200, subsample=0.8, subsample_freq=1,
                                  colsample_bytree=0.9, reg_alpha=1.0, reg_lambda=5.0,
                                  random_state=800 + fold, n_jobs=4, verbose=-1)
        prop.fit(E[tr], y)
        e_all = _predict_chunked(prop, E)
        e_by_fold[fold] = e_all
        oof_e[q_fp] = e_all[q_fp]; full_e += 0.25 * e_all
        e_ref = float(np.median(e_all[pos_idx]))
        w_pos = np.clip(e_ref / np.maximum(e_all[pos_idx], 1e-6), 0.5, 4.0)
        w_tr = np.concatenate([w_pos, np.ones(neg_sub.size)]).astype(np.float32)
        w_stats[f"fold{fold}"] = {
            "e_ref_median_positive": e_ref,
            "w_pos_mean": float(w_pos.mean()), "w_pos_p05": float(np.percentile(w_pos, 5)),
            "w_pos_p95": float(np.percentile(w_pos, 95)),
            "frac_pos_at_clip4": float((w_pos >= 4.0).mean()),
            "propensity_feature_gain": prop.booster_.feature_importance(importance_type="gain").tolist(),
            "effort_feature_names": ["lidar_valid", "log1p_depth_to_base_shifted", "det_elev_slope", "log1p_road_dist_m"],
        }
        del prop, e_all

        for tag, weights, seed0, oof_arr, full_arr in (
            ("weighted", w_tr, 700, oof_w, full_w),
            ("twin_unweighted", None, 600, oof_u, full_u),
        ):
            clf = lgb.LGBMClassifier(n_estimators=135, learning_rate=0.065, num_leaves=31,
                                     min_child_samples=100, subsample=0.80, subsample_freq=1,
                                     colsample_bytree=0.75, reg_alpha=2.0, reg_lambda=8.0,
                                     random_state=seed0 + fold, n_jobs=4, verbose=-1)
            clf.fit(np.asarray(X_sub[tr][:, SHARP_COLS], dtype=np.float32), y, sample_weight=weights)
            pred = _predict_chunked(clf, X_sub, cols=SHARP_COLS)
            oof_arr[q_fp] = pred[q_fp]; full_arr += 0.25 * pred
            del clf, pred
        gc.collect()
        print(f"[ECPU] fold {fold} trained ({time.time()-t0:.1f}s) e_ref={e_ref:.4f}", flush=True)

    surfaces = {  # (oof_fp, live_fp)
        "EXP-1": (oof_w, full_w), "EXP-2": (oof_w, full_w), "EXP-3": (oof_w, full_w),
        "C0-twin": (oof_u, full_u),
    }

    # --- emissions ------------------------------------------------------------
    d_full = distance_transform_edt(~ctx.labels).astype(np.float32)
    elig_live = foot & (d_full > 2.0)
    results = {}
    live_dots = {}
    for exp_id, (oof_fp, live_fp) in surfaces.items():
        t0 = time.time()
        pi_oof2d = _to2d(oof_fp, foot); pi_live2d = _to2d(live_fp, foot)
        cell_em = {}
        for cell in ctx.cells:
            d_vis = distance_transform_edt(~cell.visible_full).astype(np.float32)
            elig = foot & (d_vis > 2.0)
            if exp_id in ("EXP-1", "C0-twin"):
                dots = htcads.emit_submodular_celf(pi_oof2d, elig, max_dots=MAX_DOTS, marginal_bar=0.0)
            else:
                e2d = _to2d(e_by_fold[cell.fold], foot)
                dots = _emit_stratified(pi_oof2d, elig, e2d, ridge2d if exp_id == "EXP-3" else None)
            cell_em[cell.key] = dots[cell.bbox].copy()
            del dots, d_vis, elig
        if exp_id in ("EXP-1", "C0-twin"):
            ld = htcads.emit_submodular_celf(pi_live2d, elig_live, max_dots=MAX_DOTS, marginal_bar=0.0)
        else:
            ld = _emit_stratified(pi_live2d, elig_live, _to2d(full_e, foot),
                                  ridge2d if exp_id == "EXP-3" else None)
        live_dots[exp_id] = ld
        ev_hr = holdout.evaluate_hide_and_recover(cell_em, ctx, b_visible_px=0.0, n_boot=N_BOOT, seed=SEED, name=exp_id)
        d_hr = holdout.paired_bootstrap_delta(ev_hr, ref_hr, boot_key="_boots")
        ev_sg = holdout.evaluate_sgmc_with_ci(ld, ctx, n_boot=N_BOOT, seed=SEED, name=exp_id)
        d_sg_b2 = holdout.paired_bootstrap_delta(ev_sg, ref_sg_b2, boot_key="_cal_boots")
        d_sg_ht = holdout.paired_bootstrap_delta(ev_sg, ref_sg_ht, boot_key="_cal_boots")
        results[exp_id] = {
            "experiment_id": exp_id,
            "elapsed_seconds": round(time.time() - t0, 1),
            "live_dots": int(ld.sum()),
            "holdout_hide_recover_oof": {
                "pooled_dti": ev_hr["pooled_dti"], "ci95": ev_hr["ci95_cluster_bootstrap"],
                "per_quadrant_dti": ev_hr["per_quadrant_dti"],
                "paired_delta_vs_ref_b2_procedural": d_hr,
                "label": f"HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N={ev_hr['n_withheld_positives']} withheld positives, 95% CI [{ev_hr['ci95_cluster_bootstrap'][0]:.4f}, {ev_hr['ci95_cluster_bootstrap'][1]:.4f}])",
            },
            "holdout_sgmc_static_live": {
                "raw_dti": ev_sg["sgmc_raw_pooled_dti"],
                "sgmc_prevalence_calibrated_dti": ev_sg["sgmc_prevalence_calibrated_dti"],
                "ci95": ev_sg["sgmc_calibrated_ci95"],
                "paired_delta_vs_b2_static": d_sg_b2,
                "paired_delta_vs_htcads_static": d_sg_ht,
                "label": f"HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N={ev_sg['n_withheld_positives']} off-catalogue SGMC positives, 95% CI [{ev_sg['sgmc_calibrated_ci95'][0]:.4f}, {ev_sg['sgmc_calibrated_ci95'][1]:.4f}])",
            },
            "_ev_hr": ev_hr, "_ev_sg": ev_sg,
        }
        print(f"[ECPU] {exp_id}: HR-OOF={ev_hr['pooled_dti']:.6f} SGMCcal={ev_sg['sgmc_prevalence_calibrated_dti']:.6f} "
              f"dots={int(ld.sum())} ({time.time()-t0:.1f}s)", flush=True)
        del cell_em, pi_oof2d
        gc.collect()

    # twin ablation paired vs EXP-1 (same emission, weights only difference)
    abl_hr = holdout.paired_bootstrap_delta(results["EXP-1"]["_ev_hr"], results["C0-twin"]["_ev_hr"], boot_key="_boots")
    abl_sg = holdout.paired_bootstrap_delta(results["EXP-1"]["_ev_sg"], results["C0-twin"]["_ev_sg"], boot_key="_cal_boots")

    # --- uniqueness (registry incl. this repo's prior downloads) -------------
    extra = ddir / "scored_extra"; extra.mkdir(parents=True, exist_ok=True)
    for src in list((ROOT / "docs" / "downloads").glob("*.tif")) + list((ddir / "focus9").glob("*.tif")):
        dst = extra / ("REPO__" + src.name if "docs" in str(src) else src.name)
        if not dst.exists():
            shutil.copy2(src, dst)
    registry, sample_idx, all_shas = _ht._collect_registry_rasters(foot)
    print(f"[ECPU] registry unique rasters={len(registry)} files_sha_seen={len(all_shas)}", flush=True)
    for exp_id in ("EXP-1", "EXP-2", "EXP-3", "C0-twin"):
        u = _ht._check_uniqueness(_to2d(surfaces[exp_id][1], foot), live_dots[exp_id], foot, registry, sample_idx)
        # explicit 3-px overlap vs prior promoted HTCADS file (most relevant peer)
        results[exp_id]["uniqueness"] = u
        print(f"[ECPU] {exp_id} uniqueness passed={u['passed']} max3px={u['final_dots_max_detector_3px_overlap']:.4f} "
              f"surfRho={u['pre_placement_surface_max_abs_spearman']:.4f} dotsRho={u['final_dots_max_abs_spearman']:.4f}", flush=True)

    # --- selection (frozen rule) ---------------------------------------------
    cands = [e for e in ("EXP-1", "EXP-2", "EXP-3") if results[e]["uniqueness"]["passed"]]
    sel = max(cands, key=lambda e: (results[e]["holdout_hide_recover_oof"]["pooled_dti"],
                                    results[e]["holdout_sgmc_static_live"]["sgmc_prevalence_calibrated_dti"])) if cands else None

    # --- strict preregistered Gate 4 ------------------------------------------
    HTCADS_OOF = 0.112353
    gate4 = {"selected": sel, "passed": False}
    if sel:
        r = results[sel]
        gate4 = {
            "selected": sel,
            "hr_beats_b2_paired_ci_gt0": bool(r["holdout_hide_recover_oof"]["paired_delta_vs_ref_b2_procedural"]["ci95_strictly_positive"]),
            "hr_point_ge_prior_htcads_oof_0p112353": bool(r["holdout_hide_recover_oof"]["pooled_dti"] >= HTCADS_OOF),
            "sgmc_beats_htcads_paired_ci_gt0": bool(r["holdout_sgmc_static_live"]["paired_delta_vs_htcads_static"]["ci95_strictly_positive"]),
        }
        gate4["passed"] = all(gate4[k] for k in gate4 if k != "selected")
    verdict = "promote" if (sel and gate4["passed"]) else "negative"

    # --- ledger-inversion PROJECTION (never a score) ---------------------------
    Ns = np.array([44090.0, 40199.0, 37654.0]); Ds = np.array([0.2600, 0.2708, 0.2778])
    A = np.vstack([Ns, np.ones_like(Ns)]).T
    slope, intercept = np.linalg.lstsq(A, 1.0 / Ds, rcond=None)[0]
    pred_inv = slope * Ns + intercept
    ss_res = float(((1 / Ds - pred_inv) ** 2).sum()); ss_tot = float(((1 / Ds - (1 / Ds).mean()) ** 2).sum())
    tpw = 0.2 / slope; K = intercept * tpw / 0.8
    ledger = {"slope": float(slope), "intercept": float(intercept), "r_squared": 1 - ss_res / ss_tot,
              "inferred_TPw_px": float(tpw), "inferred_K_hidden_px": float(K),
              "identity": "DTI = TPw/(0.2*N + 0.8*K); 1/DTI linear in N across collar family (44090,0.2600),(40199,0.2708),(37654,0.2778) ORGANIZER-CONFIRMED"}

    def _projection(exp_id):
        r = results[exp_id]
        n = r["live_dots"]
        r_hr = r["holdout_hide_recover_oof"]["pooled_dti"] / ref_hr["pooled_dti"]
        r_sg = r["holdout_sgmc_static_live"]["raw_dti"] / ref_sg_b2["sgmc_raw_pooled_dti"]
        outs = {}
        for nm, ratio in (("via_HR_OOF_ratio", r_hr), ("via_SGMC_raw_ratio", r_sg)):
            outs[nm] = float((tpw * ratio) / (0.2 * n + 0.8 * K))
        return {"label": "PROJECTION (ledger inversion; assumes candidate live TPw = champion TPw x holdout ratio; NOT a score)",
                "ratios": {"hr_oof_vs_b2procedural": float(r_hr), "sgmc_raw_vs_b2": float(r_sg)}, **outs}

    for e in results:
        results[e]["projection"] = _projection(e)

    # --- write selected GeoTIFF bundle ----------------------------------------
    bundle = None
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    note = None
    if sel:
        dots = live_dots[sel]
        hr_v = results[sel]["holdout_hide_recover_oof"]["pooled_dti"]
        note = f"KANLERGEMS2 ECPU {sel}: effort-propensity PU 27ch+CELF ({int(dots.sum())} dots, HR-OOF={hr_v:.4f})"[:140]
        bundle = submission.write_submission_bundle(
            dots.astype(np.float32), foot, ctx.labels,
            template_tif=ddir / "sample_submission.tif",
            out_dir=downloads_dir(),
            slug=f"ecpu-{sel.lower()}-{int(dots.sum())}dots",
            timestamp_tag=f"20261027T{ts[9:]}",
            candidate_meta={"candidate_id": sel, "description": f"KG2-ECPU {sel} (verdict={verdict})",
                            "submission_note": note},
        )
        print(f"[ECPU] wrote {bundle['zeros_tif']['filename']} sha={bundle['zeros_tif']['sha256']}", flush=True)

    clean = {}
    for e, r in results.items():
        clean[e] = {k: v for k, v in r.items() if not k.startswith("_")}
    out = {
        "schema": "kanlergemsdoe2.ecpu_experiments.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane_id": "KG2-ECPU-20261027",
        "preregistration": "registry/preregistration_ecpu_20261027.json",
        "total_wall_seconds": round(time.time() - t_start, 1),
        "budget": {"promotable_experiments_run": 3, "ablation_control": "C0-twin (non-promotable)",
                   "max_promotable": 3, "max_wall_hours": 2.0},
        "references": {
            "REF-B2-HR-procedural": {"pooled_dti": ref_hr["pooled_dti"], "ci95": ref_hr["ci95_cluster_bootstrap"],
                                     "label": f"HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0, N={ref_hr['n_withheld_positives']}, 95% CI [{ref_hr['ci95_cluster_bootstrap'][0]:.4f}, {ref_hr['ci95_cluster_bootstrap'][1]:.4f}]); file score 0.2778 ORGANIZER-CONFIRMED"},
            "REF-B2-SGMC-static": {"sgmc_prevalence_calibrated_dti": ref_sg_b2["sgmc_prevalence_calibrated_dti"], "ci95": ref_sg_b2["sgmc_calibrated_ci95"], "raw_dti": ref_sg_b2["sgmc_raw_pooled_dti"]},
            "REF-HTCADS-SGMC-static": {"sgmc_prevalence_calibrated_dti": ref_sg_ht["sgmc_prevalence_calibrated_dti"], "ci95": ref_sg_ht["sgmc_calibrated_ci95"], "raw_dti": ref_sg_ht["sgmc_raw_pooled_dti"]},
            "REF-HTCADS-HR-OOF-recorded": {"pooled_dti": HTCADS_OOF, "ci95": [0.098995, 0.125743],
                                           "source": "evidence/htcads_experiments.json (2026-10-26); comparator point+CI only, no same-session paired bootstrap"},
        },
        "propensity_weight_stats_by_fold": w_stats,
        "ablation_weighted_minus_unweighted": {"hr_oof_paired": abl_hr, "sgmc_paired": abl_sg},
        "experiments": clean,
        "selected_experiment": sel,
        "gate4_strict_preregistered": gate4,
        "verdict": verdict,
        "ledger_inversion": ledger,
        "bundle": bundle,
        "submission_note": note,
        "sharp_cols": SHARP_COLS,
        "sharp_col_names": [htcads.SUBSURF_FEATURE_NAMES[i] for i in SHARP_COLS],
    }
    (edir / "ecpu_experiments_20261027.json").write_text(json.dumps(out, indent=2) + "\n")
    print(f"[ECPU] DONE selected={sel} verdict={verdict} wall={time.time()-t_start:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
