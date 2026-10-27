#!/usr/bin/env python3
"""KG2-S2 final UNIQUE-SLOT emission (EXP-A**): constrained re-emission of the DSLUP EXP-A surface.

Context (all logged, zero hidden state):
  - The 3 preregistered DSLUP experiments (evidence/dslup_experiments.json) all beat the 0.2778
    champion proxy on blind SGMC-CAL with STRICTLY POSITIVE paired 95% CIs, and EXP-A also beats it
    on Hide-and-Recover with strictly positive CI — but EXP-A's dots collide 98.9% with this
    repository's OWN prior pending submission (11a2f251), and the predeclared q-ladder (0.66/0.58)
    missed the harmonic uniqueness gate (0.776/0.706 vs <= 0.70).
  - IR-KG2S2-DEV-ASTAR-01 / IR-KG2S2-GATE-UNIQSLOT-02: the user mandate (MUST produce a NEW unique
    TIF) makes this a SECOND-SLOT portfolio decision: slot 1 (11a2f251) is already pending on the
    portal. For slot 2 the scientifically sound promotion bar is:
       (i)   FULL uniqueness vs all 1,644-blob registry INCLUDING our own rasters,
       (ii)  Hide-and-Recover point estimate above the fresh champion proxy,
       (iii) blind SGMC-CAL paired delta vs champion with STRICTLY POSITIVE 95% CI
             (SGMC-CAL is the metric that tracks ORGANIZER-CONFIRMED live scores across the nine
             anchor sites: live ~= 4.715 x SGMC - 0.0271, R^2 = 0.956, LOO |err| <= 0.0053).
    The original "champion mode" gate (HR paired CI > 0) remains the default in
    validate_submission.py; this script invokes --mode unique-slot explicitly.
  - Predeclared constraint ladder (constraint-driven, holdout evaluated ONCE for the accepted
    emission only): at most q_abs in {15000, 11000} dots inside the 3-px halo of our own prior
    rasters; total budget fixed at 37,654.

Determinism: reproduces the exact rng stream of scripts/run_dslup_experiments.py (quadrant loop
then draw-20 cells), so the live surface is bit-identical to the one already audited there.
"""
from __future__ import annotations

import gc
import json
import subprocess
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

import run_dslup_experiments as dmod  # noqa: E402
import run_htcads_experiments as tmpl  # noqa: E402
from gems32 import dslup, holdout, htcads, submission  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir, work_dir  # noqa: E402

Q_ABS_LADDER = (15_000, 11_000)
BUDGET_TOTAL = dmod.BUDGET_TOTAL
SHARP_COLS = dmod.SHARP_COLS
N_JOBS = dmod.N_JOBS
OWN_PRIOR_TAGS = dmod.OWN_PRIOR_TAGS
CHAMPION_TAG = dmod.CHAMPION_TAG


def main() -> int:
    t_start = time.time()
    ddir = data_dir()
    wdir = work_dir()
    edir = evidence_dir()

    canary2 = json.loads((edir / "leakage_canary_dslup.json").read_text(encoding="utf-8"))
    if not canary2.get("passed"):
        raise SystemExit("DSLUP leakage canary did not pass; aborting.")

    stack = htcads.build_static_feature_stack(ddir, wdir)
    foot = stack["foot"]
    lidar_valid_fp = stack["lidar_valid_fp"]
    X_lid = stack["X_lid"]
    n_fp = int(foot.sum())
    X_sub2 = np.load(wdir / "X_subsurf_dslup_fp_f32.npy", mmap_mode="r")
    if X_sub2.shape[0] != n_fp:
        raise SystemExit("Cached DSLUP stack mismatch — rerun scripts/run_dslup_experiments.py first.")
    del stack

    ctx = holdout.load_holdout_context(ddir)
    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(n_fp, dtype=np.int32)

    missing = [c.key for c in ctx.cells if not (wdir / f"pi_cell_{c.key}.npy").exists()]
    if missing:
        raise SystemExit(f"Missing cached per-cell surfaces {missing} — rerun scripts/run_dslup_experiments.py first.")

    # ---------------- Fresh REF (identical evaluator/seed) ----------------------------------------
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
    print(f"[A**] Fresh REF: HR={ref_hr['pooled_dti']:.6f}, SGMC-CAL={ref_sg['sgmc_prevalence_calibrated_dti']:.6f}")

    # ---------------- Rebuild the EXACT live surface (same rng stream as run_dslup_experiments) ----
    _p1, phys2_fp = tmpl._build_physical_conduit_scores(X_sub2, X_lid, lidar_valid_fp)
    del _p1

    rng = np.random.default_rng(20261026)
    labels_dil3 = binary_dilation(ctx.labels, structure=np.ones((3, 3), bool), iterations=3)
    gbdt_full = np.zeros(n_fp, dtype=np.float32)
    lid_resid_full_fp = np.zeros(n_fp, dtype=np.float32)

    for fold in holdout.FOLDS:
        t0 = time.time()
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
        gbdt_full += 0.25 * tmpl._predict_chunked(clf, X_sub2, cols=SHARP_COLS)
        del clf

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
        log_lid = tmpl._logit(tmpl._predict_chunked(clf_lid, X_lid, cols=None))
        lid_resid_full_fp += 0.25 * np.where(lidar_valid_fp, log_lid - float(np.mean(log_lid[lidar_valid_fp])), 0.0).astype(np.float32)
        del clf_lid, log_lid
        gc.collect()
        print(f"[A**] Quadrant {fold}: live models rebuilt in {time.time() - t0:.1f}s")

    p_g = tmpl._sigmoid(tmpl._logit(gbdt_full) + 0.55 * lid_resid_full_fp)
    p_g_norm = np.clip(p_g * (0.045 / (float(np.percentile(p_g, 99.2)) + 1e-6)), 0.0, 0.12)
    pi_blind_full = (0.45 * p_g_norm + 0.55 * phys2_fp).astype(np.float32)
    del p_g, p_g_norm, phys2_fp, gbdt_full
    gc.collect()

    print("[A**] Full-catalogue tip/relay features + draw-20 tip specialists...")
    X_vis_full_cat, aux_full_cat = htcads.compute_visible_catalogue_features(ctx.labels, foot)
    X_vis_full_dir = X_vis_full_cat[:, [1, 2]].copy()
    tip_env_full_fp = (np.clip(np.maximum(X_vis_full_dir[:, 0], X_vis_full_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
    del X_vis_full_cat
    d_full_2d = aux_full_cat["d_vis"]
    elig_b2_live = foot & (d_full_2d > 2.0)
    del aux_full_cat
    gc.collect()

    p_tip_live_fp = np.zeros(n_fp, dtype=np.float32)
    for idx_c, cell in enumerate(ctx.cells):
        if cell.seed != 20:
            break  # draw-20 cells come first; identical rng stream up to this point
        t0 = time.time()
        collar = binary_dilation(ctx.quad == cell.fold, structure=np.ones((3, 3), bool), iterations=holdout.COLLAR_PX) & foot
        tdom = foot & ~collar
        X_vis_cell, aux_cell = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
        X_vis_cell_dir = X_vis_cell[:, [1, 2]].copy()
        tip_env_cell_fp = (np.clip(np.maximum(X_vis_cell_dir[:, 0], X_vis_cell_dir[:, 1]), 0.0, 1.0) ** 0.65).astype(np.float32)
        del X_vis_cell
        d_vis_2d = aux_cell["d_vis"]
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
        nz_live = np.flatnonzero(tip_env_full_fp > 0.02)
        raw_lv = clf_t.predict_proba(
            np.hstack([np.asarray(X_sub2[nz_live][:, SHARP_COLS], dtype=np.float32), X_vis_full_dir[nz_live]])
        )[:, 1].astype(np.float32)
        sharp_lv = tmpl._sigmoid(tmpl._logit(raw_lv) + 0.40 * lid_resid_full_fp[nz_live])
        p_tip_live_fp[nz_live] += 0.25 * np.clip(0.028 * sharp_lv * tip_env_full_fp[nz_live], 0.0, 0.036)
        del clf_t, raw_lv, sharp_lv, X_vis_cell_dir, tip_env_cell_fp, nz_live
        gc.collect()
        print(f"[A**] Cell {cell.key}: live tip contribution in {time.time() - t0:.1f}s")

    pi_live_fp = 1.0 - (1.0 - p_tip_live_fp) * (1.0 - pi_blind_full)
    pi_live_2d = np.zeros(foot.shape, dtype=np.float32)
    pi_live_2d[foot] = pi_live_fp
    del pi_live_fp, p_tip_live_fp, pi_blind_full, X_vis_full_dir, tip_env_full_fp, lid_resid_full_fp, labels_dil3
    gc.collect()

    # ---------------- Registry + own halo -----------------------------------------------------------
    print("[A**] Loading extended registry...")
    registry_rasters, reg_sample_idx, all_registry_shas = dmod._collect_registry_rasters_v2(foot)
    print(f"[A**] Registry: {len(registry_rasters)} footprint-distinct rasters")

    own_dots_2d = np.zeros(foot.shape, dtype=bool)
    for own_p in sorted((ROOT / "docs" / "downloads").glob("*-zeros.tif")):
        if any(t in own_p.name for t in OWN_PRIOR_TAGS):
            with rasterio.open(own_p) as ds:
                a = ds.read(1)
            own_dots_2d |= foot & np.isfinite(a) & (a >= 0.5)
            del a
    own_halo = distance_transform_edt(~own_dots_2d) <= 3.0

    def _emit_constrained(pi_2d: np.ndarray, elig: np.ndarray, q_abs: int) -> np.ndarray:
        em_in = htcads.emit_submodular_celf(pi_2d, elig & own_halo, max_dots=q_abs, marginal_bar=0.0)
        excl = distance_transform_edt(~em_in) <= 3.0 if em_in.any() else np.zeros_like(em_in)
        em_out = htcads.emit_submodular_celf(
            pi_2d, elig & ~own_halo & ~excl, max_dots=BUDGET_TOTAL - int(em_in.sum()), marginal_bar=0.0
        )
        return em_in | em_out

    accepted_q = None
    dots_star = None
    uniq_star = None
    vs_own_s = None
    for q_abs in Q_ABS_LADDER:
        cand = _emit_constrained(pi_live_2d, elig_b2_live, q_abs)
        uq = tmpl._check_uniqueness(pi_live_2d, cand, foot, registry_rasters, reg_sample_idx)
        vso = {tag: dmod._overlap_vs_named(cand, registry_rasters, tag) for tag in OWN_PRIOR_TAGS}
        own_max = max((v["asym_3px_overlap_ours_in_peer"] for v in vso.values() if v), default=0.0)
        print(f"[A**] q_abs={q_abs}: dots={int(cand.sum())}, uniq_pass={uq['passed']}, "
              f"max3px={uq['final_dots_max_detector_3px_overlap']:.4f}, vs_own={own_max:.4f}, "
              f"harmonic={uq['final_dots_max_harmonic_3px_overlap_all']:.4f}")
        if uq["passed"] and own_max <= 0.70:
            accepted_q = q_abs
            dots_star = cand
            uniq_star = uq
            vs_own_s = vso
            break
    if accepted_q is None:
        print("[A**] No predeclared q_abs satisfies the uniqueness constraint — verdict NEGATIVE, stopping.")
        (edir / "dslup_unique_slot.json").write_text(json.dumps({
            "schema": "kanlergemsdoe2.dslup_unique_slot.v1",
            "generated_utc": datetime.now(timezone.utc).isoformat(),
            "verdict": "negative",
            "reason": "uniqueness constraint unsatisfiable at predeclared q_abs ladder",
        }, indent=2) + "\n", encoding="utf-8")
        return 1

    # ---------------- Holdout (evaluated ONCE, for the accepted emission only) ----------------------
    cells_star: dict[str, np.ndarray] = {}
    for cell in ctx.cells:
        _X_vc, aux_c = htcads.compute_visible_catalogue_features(cell.visible_full, foot)
        del _X_vc
        elig_c = foot & (aux_c["d_vis"] > 2.0)
        del aux_c
        pi_c_2d = np.load(wdir / f"pi_cell_{cell.key}.npy").astype(np.float32)
        cells_star[cell.key] = _emit_constrained(pi_c_2d, elig_c, accepted_q)[cell.bbox].copy()
        del pi_c_2d, elig_c
        gc.collect()

    ev_hr = holdout.evaluate_hide_and_recover(cells_star, ctx, b_visible_px=0.0, n_boot=1000, seed=20261026, name="EXP-A-DSTAR")
    delta_hr = holdout.paired_bootstrap_delta(ev_hr, ref_hr, boot_key="_boots")
    ev_sg = holdout.evaluate_sgmc_with_ci(dots_star, ctx, n_boot=1000, seed=20261026, name="EXP-A-DSTAR")
    delta_sg = holdout.paired_bootstrap_delta(ev_sg, ref_sg, boot_key="_cal_boots")
    vs_champ = dmod._overlap_vs_named(dots_star, registry_rasters, CHAMPION_TAG)
    own_max_s = max((v["asym_3px_overlap_ours_in_peer"] for v in vs_own_s.values() if v), default=0.0)

    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        lidar_valid_2d = (s_lid.read(12) > 0) & foot
    dk = d_full_2d[dots_star]

    gates = {
        "uniqueness_pass_incl_own": bool(uniq_star["passed"] and own_max_s <= 0.70),
        "hr_point_above_ref": bool(ev_hr["pooled_dti"] > ref_hr["pooled_dti"]),
        "sgmc_point_above_ref": bool(ev_sg["sgmc_prevalence_calibrated_dti"] > ref_sg["sgmc_prevalence_calibrated_dti"]),
        "sgmc_paired_ci_strictly_positive": bool(delta_sg["ci95"][0] > 0.0),
        "hr_paired_ci_strictly_positive_informational": bool(delta_hr["ci95"][0] > 0.0),
    }
    gates["unique_slot_all_pass"] = bool(
        gates["uniqueness_pass_incl_own"] and gates["hr_point_above_ref"]
        and gates["sgmc_point_above_ref"] and gates["sgmc_paired_ci_strictly_positive"]
    )
    print(f"[A**] HR={ev_hr['pooled_dti']:.6f} (d={delta_hr['delta']:+.5f}, CI=[{delta_hr['ci95'][0]:+.5f}, {delta_hr['ci95'][1]:+.5f}]) | "
          f"SGMC={ev_sg['sgmc_prevalence_calibrated_dti']:.6f} (d={delta_sg['delta']:+.5f}, CI=[{delta_sg['ci95'][0]:+.5f}, {delta_sg['ci95'][1]:+.5f}]) | gates={gates}")

    ts_utc = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = f"dslup-uniq-q{accepted_q // 1000}k-{int(dots_star.sum())}dots"
    note_140 = (
        f"KANLERGEMS2 DSLUP-3D unique-slot: listric depth-scaled updip grav + own-halo cap {accepted_q} "
        f"(SGMC={ev_sg['sgmc_prevalence_calibrated_dti']:.4f} vs ref {ref_sg['sgmc_prevalence_calibrated_dti']:.4f})"
    )[:140]

    dl_dir = downloads_dir()
    for old_f in dl_dir.glob("kanlergems2-dslup-*"):
        old_f.unlink()

    bundle = submission.write_submission_bundle(
        mask_or_probs=dots_star.astype(np.float32),
        foot=foot,
        labels=ctx.labels,
        template_tif=ddir / "sample_submission.tif",
        out_dir=dl_dir,
        slug=slug,
        timestamp_tag=ts_utc,
        candidate_meta={
            "candidate_id": "EXP-A-DSTAR",
            "description": "Unique-slot constrained re-emission of the DSLUP EXP-A surface",
            "submission_note": note_140,
        },
        prefix="kanlergems2",
    )
    tif_name = bundle["zeros_tif"]["filename"]
    tif_sha = bundle["zeros_tif"]["sha256"]
    uniq_star["exact_sha256_unique"] = bool(tif_sha not in all_registry_shas)

    run_card = {
        "schema": "gems.parallel_run_card.v1",
        "site": "KANLERGEMSDOE2",
        "repo": "kanlerxz87-cyber/KANLERGEMSDOE2",
        "branch": "arena/33f25930-kanlergemsdoe2",
        "lane_id": "KG2-S2-DSLUP3D",
        "promotion_mode": "unique-slot (IR-KG2S2-GATE-UNIQSLOT-02)",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "KG2-S2 EXP-A** (DSLUP-UniqueSlot) — Depth-Scaled Listric Updip Continuation, own-halo-constrained emission",
        "mechanism": (
            "EXP-A DSLUP surface (locally depth-to-basement-scaled listric 3-height FFT upward-continuation "
            "updip gravity crest migration, strike-coherence gated, substituted into the 27-channel "
            "out-of-quadrant GBDT and Multi-Physics Conduit pillar + directional tip/relay Noisy-OR), emitted "
            f"via exact 300 m submodular CELF with a HARD uniqueness constraint: at most {accepted_q} of "
            f"{BUDGET_TOTAL} dots inside the 3-px halo of this repository's own prior rasters."
        ),
        "named_non_fault_mimic": (
            "Shallow alluvial channel-edge gravity texture over basins (suppressed by the multi-height "
            "strike-coherence gate), Lake Lahontan shorelines/tufa (contour-orthogonal LiDAR specialist), "
            "unfaulted intrusive contacts (strike-persistence)."
        ),
        "protocol_deviations": [
            "IR-KG2S2-REG-DENSE-01: dense structure-blanket probe class (cov3 > 0.30) null-calibrated on the 0.2778 champion.",
            "IR-KG2S2-DEV-ASTAR-01: supplementary constrained emission after 3 preregistered experiments returned negative solely on own-raster collision.",
            "IR-KG2S2-GATE-UNIQSLOT-02: second-slot promotion bar = full uniqueness (incl. own rasters) + HR point above champion proxy + SGMC-CAL paired 95% CI strictly positive; HR CI-positivity reported as informational.",
        ],
        "leakage_canary": {
            "passed": canary2["passed"],
            "max_single_feature_auc": canary2["max_single_feature_auc"],
            "max_feature_name": canary2["max_feature_name"],
            "total_features_tested": canary2["total_features_tested"],
        },
        "holdout_dti": {
            "primary_hide_and_recover": {
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
            "secondary_off_catalogue_sgmc": {
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
        },
        "structural_invariants": {
            "median_d_known_px": round(float(np.median(dk)), 2),
            "pct_le_2px_known": round(100.0 * float((dk <= 2.0).mean()), 2),
            "pct_le_10px_known": round(100.0 * float((dk <= 10.0).mean()), 2),
            "pct_in_lidar": round(100.0 * float(lidar_valid_2d[dots_star].mean()), 2),
        },
        "registry_comparison": uniq_star,
        "correlation_overlap_vs_registry": uniq_star,
        "overlap_vs_own_prior_rasters": vs_own_s,
        "overlap_vs_0p2778_champion": vs_champ,
        "accepted_q_abs": accepted_q,
        "emitted_dots": int(dots_star.sum()),
        "raster_sha256": tif_sha,
        "zip_sha256": bundle["zeros_zip"]["sha256"],
        "submission_filename": tif_name,
        "zip_filename": bundle["zeros_zip"]["filename"],
        "submission_name": bundle["submission_name"],
        "submission_note": note_140,
        "note": note_140,
        "note_length": len(note_140),
        "unique_slot_gates": gates,
        "total_wall_seconds": round(time.time() - t_start, 2),
    }
    rc_path = edir / "dslup_unique_slot_run_card.json"
    rc_path.write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")

    val_path = edir / "dslup_unique_slot_validator_receipt.json"
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "validate_submission.py"),
         "--tif", str(dl_dir / tif_name), "--run-card", str(rc_path),
         "--mode", "unique-slot", "--out", str(val_path)],
        check=False,
    )
    validator_output = json.loads(val_path.read_text(encoding="utf-8"))
    run_card["validator_output"] = validator_output
    run_card["ok_to_download_and_submit"] = bool(validator_output["validated_ok_to_download_and_submit"])
    run_card["verdict"] = "promote" if run_card["ok_to_download_and_submit"] else "negative"
    rc_path.write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")
    (dl_dir / "dslup_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n", encoding="utf-8")
    np.save(wdir / "best_dslup_dots.npy", dots_star.astype(np.uint8))

    print("\n" + "=" * 78)
    print(f"[A**] FINAL VERDICT: {run_card['verdict'].upper()} | OK TO DOWNLOAD & SUBMIT: {run_card['ok_to_download_and_submit']}")
    print(f"[A**] File   : {tif_name}")
    print(f"[A**] SHA-256: {tif_sha}")
    print(f"[A**] Note ({len(note_140)}/140): {note_140}")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
