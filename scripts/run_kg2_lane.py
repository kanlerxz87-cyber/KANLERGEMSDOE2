#!/usr/bin/env python3
"""Execute or verify the preregistered KANLERGEMSDOE2 (KG2-MGHV) lane.

Follows knowledge/01_preregistered_hypotheses_kg2_20261026.md and the Parallel-Run Protocol:
  1. Reuses shared template stack (prepared/features.npy + gvc + sahg1) + 26 label-free
     KG2-MGHV channels (10m USGS 3DEP gap-free scarps, 3m kinematic scarps, multi-scale
     piedmont-junction lines, 6 omitted GeoDAWN bands, Fourier shallow magnetite-destruction,
     Gallardo-Meju cross-gradient, clay-cap residual, transtensional seismicity).
  2. Runs two-polarity single-feature Leakage Canary across all 78 channels (halt if AUC > 0.90).
  3. Runs <= 3 preregistered experiments (EXP-1, EXP-2, EXP-3) + matched controls on shared
     SegmentHoldout (gems-segment-pooled-v1, 60,988 withheld positives, 1.5 km collar,
     1,999 10 km block-bootstrap draws).
  4. Checks pre-placement surface & post-placement dot uniqueness against all 360 unique
     GeoTIFFs across all 9 focus sites + registry (halt if |rho| > 0.90 or competing 3-px
     overlap > 0.70).
  5. Emits portal-safe -zeros.tif via shared submission_writer.py + single-TIFF .zip and
     produces the JSON Run Card. Never contacts DrivenData or spends a weekly slot automatically.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import resource
import subprocess
import sys
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import numpy as np  # noqa: E402
import rasterio  # noqa: E402
from scipy.ndimage import distance_transform_edt  # noqa: E402
from scipy.spatial import cKDTree  # noqa: E402
from scipy.stats import rankdata  # noqa: E402

from gems import (  # noqa: E402
    confounds,
    dprf1,
    emission,
    footprint,
    gvc,
    holdout,
    kg2_mghv,
    novelty,
    paths,
    submission,
)
from gems.validator import sha256_file  # noqa: E402

SEED = 20261026
GVC_BASE_SEED = 20261025
FULL_DOT_BUDGET = 37_654
DPRF1_REFERENCE_DTI = 0.1637924246971501
PREREG_PATH = "knowledge/01_preregistered_hypotheses_kg2_20261026.md"

CANARY_JSON = ROOT / "evidence/kg2_canary_20261026.json"
HOLDOUT_JSON = ROOT / "evidence/kg2_holdout_20261026.json"
EXPERIMENT_JSON = ROOT / "evidence/kg2_experiment_20261026.json"
RUN_CARD_JSON = ROOT / "evidence/kg2_run_card_20261026.json"
ROOT_RUN_CARD_JSON = ROOT / "run_card.json"
DOCS_RUN_CARD_JSON = ROOT / "docs/data/run_card.json"


def save_json(obj: Any, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def peak_rss_mib() -> float:
    return float(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss) / 1024.0


def load_all_stacks() -> tuple[
    np.ndarray,
    np.ndarray,
    Path,
    np.ndarray,
    np.ndarray,
    list[str],
    np.ndarray,
    list[str],
    np.ndarray,
    list[str],
    np.ndarray,
    list[str],
    list[str],
]:
    fp = footprint.load_footprint()
    fp_ids = np.flatnonzero(fp.ravel())
    template = paths.DATA_DIR / "bridge/sample_submission.tif"
    with rasterio.open(template) as t_ds:
        transform = t_ds.transform
    with rasterio.open(paths.DATA_DIR / "bridge/labels.tif") as l_ds:
        catalogue = (l_ds.read(1) > 0) & fp

    prep_meta = json.loads((paths.DATA_DIR / "prepared/features.json").read_text())
    prep_path = paths.DATA_DIR / "prepared/features.npy"
    if sha256_file(prep_path) != prep_meta["sha256"]:
        raise SystemExit("Prepared 30-channel feature-stack SHA-256 mismatch")
    base_mm = np.load(prep_path, mmap_mode="r")
    base_names = list(prep_meta["names"])

    gvc_path = paths.DATA_DIR / "prepared/gvc1_features.npy"
    if gvc_path.exists():
        gvc_mm = np.load(gvc_path, mmap_mode="r")
        if gvc_mm.shape != (len(fp_ids), len(gvc.GVC1_FEATURE_NAMES)):
            _, gvc_names = gvc.build_gvc1_features(
                ROOT, base_mm, base_names, fp, transform, gvc_path
            )
            gvc_mm = np.load(gvc_path, mmap_mode="r")
        else:
            gvc_names = list(gvc.GVC1_FEATURE_NAMES)
    else:
        _, gvc_names = gvc.build_gvc1_features(ROOT, base_mm, base_names, fp, transform, gvc_path)
        gvc_mm = np.load(gvc_path, mmap_mode="r")

    sahg_path = paths.DATA_DIR / "prepared/sahg4_features.npy"
    sahg_mm, sahg_names = dprf1.build_sahg4_memmap(ROOT, base_mm, base_names, fp, sahg_path)

    kg2_path = paths.DATA_DIR / "prepared/kg2_extra_features.npy"
    kg2_mm, kg2_names = kg2_mghv.build_kg2_extra_memmap(
        paths.DATA_DIR, base_mm, base_names, fp, kg2_path
    )

    all_names = base_names + gvc_names + sahg_names + kg2_names
    assert len(all_names) == 78, f"Expected 78 channels, got {len(all_names)}"
    return (
        fp,
        fp_ids,
        template,
        catalogue,
        base_mm,
        base_names,
        gvc_mm,
        gvc_names,
        sahg_mm,
        sahg_names,
        kg2_mm,
        kg2_names,
        all_names,
    )


def load_nuisance(fp_ids: np.ndarray) -> np.ndarray:
    confounds.build_all(force=False)
    with np.load(confounds.CONF / "confounds.npz") as c_npz:
        cdict = confounds.classifier_features(c_npz)
        nuis_keys = ["road_m", "claim_m", "block_1", "block_2", "block_3", "block_4"]
        nuis = np.column_stack(
            [cdict[k].ravel()[fp_ids].astype(np.float32, copy=False) for k in nuis_keys]
        )
    return nuis


def run_stage_features_and_canary() -> dict[str, Any]:
    t0 = time.monotonic()
    print("[Stage 1] Building/verifying 78-channel feature stack + confounds...", flush=True)
    (
        fp,
        fp_ids,
        _template,
        catalogue,
        base_mm,
        base_names,
        gvc_mm,
        gvc_names,
        sahg_mm,
        sahg_names,
        kg2_mm,
        kg2_names,
        all_names,
    ) = load_all_stacks()
    _ = load_nuisance(fp_ids)
    print(f"  78-channel stack ready in {time.monotonic() - t0:.1f}s | RSS={peak_rss_mib():.1f} MiB", flush=True)

    context = holdout.SegmentHoldout(fp, catalogue, buffer_px=15)
    specs = (
        [(n, base_mm, i) for i, n in enumerate(base_names)]
        + [(n, gvc_mm, i) for i, n in enumerate(gvc_names)]
        + [(n, sahg_mm, i) for i, n in enumerate(sahg_names)]
        + [(n, kg2_mm, i) for i, n in enumerate(kg2_names)]
    )
    merged: dict[str, Any] = {}
    last_meta: dict[str, Any] = {}
    for start in range(0, len(specs), 4):
        batch = specs[start : start + 4]
        fdict: dict[str, np.ndarray] = {}
        for name, mm_arr, col in batch:
            grid = np.full(fp.shape, np.nan, dtype=np.float32)
            grid.ravel()[fp_ids] = mm_arr[:, col]
            fdict[name] = grid
        rep = context.canary(fdict, seed=GVC_BASE_SEED, max_per_class=15_000)
        merged.update(rep["features"])
        last_meta = rep
        del fdict
        gc.collect()

    passed = not any(v["leakage_suspected"] for v in merged.values())
    worst_name = max(
        merged,
        key=lambda k: max(merged[k]["pooled_auc"], 1.0 - merged[k]["pooled_auc"]),
    )
    worst_auc = float(merged[worst_name]["pooled_auc"])
    worst_two_sided = float(max(worst_auc, 1.0 - worst_auc))

    kg2_only = {k: merged[k] for k in kg2_names}
    worst_kg2_name = max(
        kg2_only,
        key=lambda k: max(kg2_only[k]["pooled_auc"], 1.0 - kg2_only[k]["pooled_auc"]),
    )
    worst_kg2_two = float(
        max(kg2_only[worst_kg2_name]["pooled_auc"], 1.0 - kg2_only[worst_kg2_name]["pooled_auc"])
    )

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "diagnostic": last_meta["diagnostic"],
        "evaluator_version": last_meta["evaluator_version"],
        "threshold": last_meta["threshold"],
        "two_polarities_checked": True,
        "passed": passed,
        "n_features_checked": len(merged),
        "n_kg2_new_features_checked": len(kg2_names),
        "worst_feature_all78": worst_name,
        "worst_two_polarity_auc_all78": worst_two_sided,
        "worst_feature_kg2_new26": worst_kg2_name,
        "worst_two_polarity_auc_kg2_new26": worst_kg2_two,
        "elapsed_seconds": round(time.monotonic() - t0, 2),
        "peak_rss_mib": round(peak_rss_mib(), 2),
        "features": merged,
    }
    save_json(out, CANARY_JSON)
    print(
        f"[Stage 1] Canary PASSED={passed} | all78 worst={worst_name} ({worst_two_sided:.4f}) "
        f"| kg2_26 worst={worst_kg2_name} ({worst_kg2_two:.4f}) | RSS={peak_rss_mib():.1f} MiB",
        flush=True,
    )
    if not passed:
        raise SystemExit("HALT: Leakage canary failed (> 0.90 single-feature AUC)")
    return out


def run_stage_holdout_experiments(cache_dir: Path) -> dict[str, Any]:
    t0 = time.monotonic()
    if not CANARY_JSON.exists():
        run_stage_features_and_canary()
    canary = json.loads(CANARY_JSON.read_text())
    if not canary["passed"]:
        raise SystemExit("Cannot run holdout: Leakage canary did not pass")

    (
        fp,
        fp_ids,
        _template,
        catalogue,
        base_mm,
        base_names,
        gvc_mm,
        gvc_names,
        sahg_mm,
        sahg_names,
        kg2_mm,
        kg2_names,
        all_names,
    ) = load_all_stacks()
    nuisance_fp = load_nuisance(fp_ids)
    context = holdout.SegmentHoldout(fp, catalogue, buffer_px=15)
    total_offcat = int((fp & (~catalogue)).sum())

    # Unpack 100 m piedmont-junction physics baseline (label-free control)
    j100_nms_grid = np.zeros(fp.shape, dtype=np.float32)
    j100_col = kg2_names.index("kg2_junc_100m_nms")
    j100_vals = np.asarray(kg2_mm[:, j100_col], dtype=np.float32)
    j100_nms_grid.ravel()[fp_ids] = np.where(np.isfinite(j100_vals), j100_vals, 0.0)
    del j100_vals

    cache_dir.mkdir(parents=True, exist_ok=True)
    cached_names = [
        "oof_quad_exp1_sharp.npy",
        "oof_quad_exp1_cond.npy",
        "oof_quad_exp2_dual.npy",
        "oof_quad_exp2_pied.npy",
        "oof_quad_exp2_cond.npy",
    ]
    have_quad_cache = all((cache_dir / cn).exists() for cn in cached_names)
    if have_quad_cache:
        print("[Stage 2] Loading already-computed 4-fold OOF surfaces from cache_dir...", flush=True)
        oof_quad_exp1_sharp = np.load(cache_dir / "oof_quad_exp1_sharp.npy")
        oof_quad_exp1_cond = np.load(cache_dir / "oof_quad_exp1_cond.npy")
        oof_quad_exp2_dual = np.load(cache_dir / "oof_quad_exp2_dual.npy")
        oof_quad_exp2_pied = np.load(cache_dir / "oof_quad_exp2_pied.npy")
        oof_quad_exp2_cond = np.load(cache_dir / "oof_quad_exp2_cond.npy")
    else:
        oof_quad_exp1_sharp = np.zeros(fp.shape, dtype=np.float32)
        oof_quad_exp1_cond = np.zeros(fp.shape, dtype=np.float32)
        oof_quad_exp2_dual = np.zeros(fp.shape, dtype=np.float32)
        oof_quad_exp2_pied = np.zeros(fp.shape, dtype=np.float32)
        oof_quad_exp2_cond = np.zeros(fp.shape, dtype=np.float32)

    preds_exp1: list[np.ndarray] = []
    preds_exp2: list[np.ndarray] = []
    preds_exp3: list[np.ndarray] = []
    preds_b0: list[np.ndarray] = []
    preds_b1: list[np.ndarray] = []
    preds_junc100: list[np.ndarray] = []
    preds_rand: list[np.ndarray] = []
    fold_diagnostics: list[dict[str, Any]] = []

    for fold in context.folds:
        fid = int(fold["id"])
        fname = fold["name"]
        tf0 = time.monotonic()
        f_offcat = int((fold["valid"] & (~fold["visible"])).sum())
        k_fold = int(round(FULL_DOT_BUDGET * f_offcat / total_offcat))
        print(f"[Stage 2] Fold {fid} ({fname}) k_fold={k_fold} ...", flush=True)

        if have_quad_cache:
            v_f = fold["valid"]
            p_core_s_deb = np.where(v_f, oof_quad_exp1_sharp, 0.0)
            p_core_c_deb = np.where(v_f, oof_quad_exp1_cond, 0.0)
            p_dual_deb = np.where(v_f, oof_quad_exp2_dual, 0.0)
            p_pied_deb = np.where(v_f, oof_quad_exp2_pied, 0.0)
            p_cond_deb = np.where(v_f, oof_quad_exp2_cond, 0.0)
            core_meta = {"from_cached_oof": True}
            dual_meta = {"from_cached_oof": True}
            d_exp1 = dprf1.two_regime_submodular_allocate(
                p_core_s_deb,
                p_core_c_deb,
                fold["valid"],
                fold["visible"],
                budget=k_fold,
                primary_share=0.68,
                min_spacing_px=2.8,
                catalogue_clearance_px=2.0,
            )
            preds_exp1.append(d_exp1)
            del p_core_s_deb, p_core_c_deb
        else:
            p_core_s, p_core_c, core_meta = dprf1.fit_and_predict_fold(
                base_mm,
                gvc_mm,
                sahg_mm,
                nuisance_fp,
                all_names,
                fp,
                fp_ids,
                train_mask=fold["train"],
                visible_mask=fold["visible"],
                predict_mask=fold["valid"],
                neg_mode="stratified_d3",
                seed=SEED + 10 * fid,
                extra_mm=kg2_mm,
                regime_b_extra_names=kg2_mghv.KG2_REGIME_B_EXTRA,
                selective_extra_names=kg2_mghv.KG2_SELECTIVE_RESID_EXTRA,
            )
            p_core_s_deb = dprf1.debiased_apron_surface(p_core_s, fold["valid"], fold["visible"])
            p_core_c_deb = dprf1.debiased_apron_surface(p_core_c, fold["valid"], fold["visible"])
            oof_quad_exp1_sharp += p_core_s_deb
            oof_quad_exp1_cond += p_core_c_deb
            d_exp1 = dprf1.two_regime_submodular_allocate(
                p_core_s_deb,
                p_core_c_deb,
                fold["valid"],
                fold["visible"],
                budget=k_fold,
                primary_share=0.68,
                min_spacing_px=2.8,
                catalogue_clearance_px=2.0,
            )
            preds_exp1.append(d_exp1)
            del p_core_s_deb, p_core_c_deb

            p_dual_s, p_pied, p_cond, dual_meta = kg2_mghv.fit_and_predict_dualhead_fold(
                base_mm,
                gvc_mm,
                sahg_mm,
                kg2_mm,
                nuisance_fp,
                all_names,
                fp,
                fp_ids,
                train_mask=fold["train"],
                visible_mask=fold["visible"],
                predict_mask=fold["valid"],
                seed=SEED + 10 * fid,
                core_weight=0.56,
                precomputed_core=(p_core_s, p_core_c, core_meta),
            )
            del p_core_s, p_core_c
            p_dual_deb = dprf1.debiased_apron_surface(p_dual_s, fold["valid"], fold["visible"])
            p_pied_deb = dprf1.debiased_apron_surface(p_pied, fold["valid"], fold["visible"])
            p_cond_deb = dprf1.debiased_apron_surface(p_cond, fold["valid"], fold["visible"])
            oof_quad_exp2_dual += p_dual_deb
            oof_quad_exp2_pied += p_pied_deb
            oof_quad_exp2_cond += p_cond_deb
            del p_dual_s, p_pied, p_cond

        # EXP-2 emission: Dual-Head + 2-regime submodular (68/32, min_spacing=2.8)
        d_exp2 = dprf1.two_regime_submodular_allocate(
            p_dual_deb,
            p_cond_deb,
            fold["valid"],
            fold["visible"],
            budget=k_fold,
            primary_share=0.68,
            min_spacing_px=2.8,
            catalogue_clearance_px=2.0,
        )
        preds_exp2.append(d_exp2)

        # EXP-3 emission: Dual-Head + Three-Regime (54% Range/Gap + 22% Piedmont<=6.5deg + 24% Vent/Basin, min_spacing=3.0)
        d_exp3 = kg2_mghv.three_regime_submodular_allocate(
            p_dual_deb,
            p_pied_deb,
            p_cond_deb,
            fold["valid"],
            fold["visible"],
            budget=k_fold,
            shares=(0.54, 0.22, 0.24),
            min_spacing_px=3.0,
            catalogue_clearance_px=2.0,
        )
        preds_exp3.append(d_exp3)
        del p_dual_deb, p_pied_deb, p_cond_deb

        # Matched same-evaluator controls: B0 (Legacy Ridge), B1 (30-ch Base Submod), JUNC_100m, Random-37654
        p_b0 = gvc.fit_predict_legacy_ridge_baseline(
            base_mm,
            train_mask=fold["train"],
            visible_mask=fold["visible"],
            valid_mask=fold["valid"],
            footprint=fp,
            seed=GVC_BASE_SEED + fid,
        )
        preds_b0.append(p_b0)

        p_b1_surf, _ = gvc.fit_predict_calibrated_hgb(
            base_mm,
            None,
            None,
            train_mask=fold["train"],
            visible_mask=fold["visible"],
            predict_mask=fold["valid"],
            footprint=fp,
            seed=GVC_BASE_SEED + fid,
            residualize=False,
        )
        d_b1 = gvc.submodular_dti_allocate(
            p_b1_surf,
            fold["valid"],
            fold["visible"],
            budget=k_fold,
            min_spacing_px=2.5,
            catalogue_clearance_px=2.0,
        )
        preds_b1.append(d_b1)
        del p_b1_surf

        dist_vis = distance_transform_edt(~fold["visible"])
        elig_b2 = fold["valid"] & (~fold["visible"]) & (dist_vis > 2.0)
        d_junc = emission.priority_poisson(
            j100_nms_grid, elig_b2, k_fold, min_dist=2.8
        ).astype(np.float32)
        preds_junc100.append(d_junc)

        rng_r = np.random.default_rng(SEED + 900 + fid)
        elig_idx = np.flatnonzero(elig_b2.ravel())
        sel_r = rng_r.choice(elig_idx, size=min(k_fold, len(elig_idx)), replace=False)
        d_rand = np.zeros(fp.shape, dtype=np.float32)
        d_rand.ravel()[sel_r] = 1.0
        preds_rand.append(d_rand)
        del dist_vis, elig_b2

        s_e1, _ = context.score_fold(d_exp1, fold)
        s_e2, _ = context.score_fold(d_exp2, fold)
        s_e3, _ = context.score_fold(d_exp3, fold)
        s_j, _ = context.score_fold(d_junc, fold)
        print(
            f"    {fname}: EXP-1={s_e1['dti']:.5f} | EXP-2={s_e2['dti']:.5f} | EXP-3={s_e3['dti']:.5f} | JUNC100={s_j['dti']:.5f}",
            flush=True,
        )

        fold_diagnostics.append(
            {
                "fold_id": fid,
                "fold_name": fname,
                "k_fold": k_fold,
                "elapsed_seconds": round(time.monotonic() - tf0, 2),
                "core_meta": core_meta,
                "dual_meta": dual_meta,
            }
        )
        gc.collect()
        print(
            f"  Fold {fid} done in {time.monotonic() - tf0:.1f}s | RSS={peak_rss_mib():.1f} MiB",
            flush=True,
        )

    if not have_quad_cache:
        np.save(cache_dir / "oof_quad_exp1_sharp.npy", oof_quad_exp1_sharp)
        np.save(cache_dir / "oof_quad_exp1_cond.npy", oof_quad_exp1_cond)
        np.save(cache_dir / "oof_quad_exp2_dual.npy", oof_quad_exp2_dual)
        np.save(cache_dir / "oof_quad_exp2_pied.npy", oof_quad_exp2_pied)
        np.save(cache_dir / "oof_quad_exp2_cond.npy", oof_quad_exp2_cond)

    print("[Stage 2] Scoring pooled HOLDOUT-DTI + 1,999 10 km block-bootstrap CIs...", flush=True)
    res_exp1 = context.summarize(preds_exp1, ci_draws=1999)
    res_exp2 = context.summarize(preds_exp2, ci_draws=1999)
    res_exp3 = context.summarize(preds_exp3, ci_draws=1999)
    res_b0 = context.summarize(preds_b0, ci_draws=1999)
    res_b1 = context.summarize(preds_b1, ci_draws=1999)
    res_junc = context.summarize(preds_junc100, ci_draws=1999)
    res_rand = context.summarize(preds_rand, ci_draws=1999)

    arms = {"EXP-1": (res_exp1, preds_exp1), "EXP-2": (res_exp2, preds_exp2), "EXP-3": (res_exp3, preds_exp3)}
    for aname, (ares, _) in arms.items():
        print(
            f"  {aname}: HOLDOUT-DTI = {ares['dti']:.6f} | 95% CI = {ares['ci95']['interval']}",
            flush=True,
        )
    print(f"  B0_oof_h24_ridge: {res_b0['dti']:.6f} | B1_oof_base_submod: {res_b1['dti']:.6f} | JUNC_100m: {res_junc['dti']:.6f} | RAND_37654: {res_rand['dti']:.6f}", flush=True)

    paired: dict[str, Any] = {}
    for aname, (_, apreds) in arms.items():
        paired[aname] = {
            "vs_B0_oof_h24_ridge": context.compare_paired(apreds, preds_b0, ci_draws=1999, seed=SEED),
            "vs_B1_oof_base_submod": context.compare_paired(apreds, preds_b1, ci_draws=1999, seed=SEED),
            "vs_JUNC_100m_only": context.compare_paired(apreds, preds_junc100, ci_draws=1999, seed=SEED),
            "vs_CTRL_RAND_37654": context.compare_paired(apreds, preds_rand, ci_draws=1999, seed=SEED),
        }
    paired["EXP1_vs_EXP2"] = context.compare_paired(preds_exp1, preds_exp2, ci_draws=1999, seed=SEED)
    paired["EXP1_vs_EXP3"] = context.compare_paired(preds_exp1, preds_exp3, ci_draws=1999, seed=SEED)

    for aname, (_, apreds) in arms.items():
        np.savez_compressed(cache_dir / f"fold_preds_{aname}.npz", *apreds)

    out = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "evaluator_version": res_exp1["evaluator_version"],
        "withheld_positive_pixels": res_exp1["n_withheld_positive_pixels"],
        "experiments_run": 3,
        "budget_cap_experiments": 3,
        "dprf1_recorded_reference_dti": DPRF1_REFERENCE_DTI,
        "arms": {
            "EXP-1_KG2_Core78_TwoRegime": res_exp1,
            "EXP-2_KG2_DualHead_TwoRegime": res_exp2,
            "EXP-3_KG2_DualHead_ThreeRegime_CELF": res_exp3,
        },
        "controls_same_evaluator": {
            "B0_oof_h24_ridge": res_b0,
            "B1_oof_base_submod": res_b1,
            "JUNC_100m_only": res_junc,
            "CTRL_RAND_37654": res_rand,
        },
        "paired_bootstrap_deltas": paired,
        "fold_diagnostics": fold_diagnostics,
        "elapsed_seconds": round(time.monotonic() - t0, 2),
        "peak_rss_mib": round(peak_rss_mib(), 2),
    }
    save_json(out, HOLDOUT_JSON)
    return out


def audit_against_all_360_registry(
    surface_2d: np.ndarray,
    dots_2d: np.ndarray | None,
    fp: np.ndarray,
    registry_local_path: Path,
) -> dict[str, Any]:
    reg = json.loads(registry_local_path.read_text())
    entries = reg["entries"]
    surf_ranks = rankdata(np.asarray(surface_2d[fp], dtype=np.float64))
    dot_ranks = rankdata(np.asarray(dots_2d[fp], dtype=np.float64)) if dots_2d is not None else None
    cand_pts = np.argwhere(fp & (dots_2d > 0)) if dots_2d is not None else None

    max_surf_rho = -1.0
    max_surf_peer = None
    max_dot_rho = -1.0
    max_dot_rho_peer = None
    max_comp_ov = -1.0
    max_comp_peer = None
    max_all_ov = -1.0
    max_all_peer = None

    key_peers: dict[str, Any] = {}
    watch_substrs = (
        "dprf1-stitched-oof",
        "h31x-piedmont-junction",
        "h31-drcg-wl-celf28",
        "h33-h33-2-b2",
        "anderson-geothermal-pinn-38854",
        "hvg36-vent-dipole",
        "s21-puhgb",
        "h73-pm-deapron",
        "h47-lli-unique",
        "a33-r3-llc",
        "r13-lattice-s5_v2",
    )

    checked = 0
    for e in entries:
        p = Path(e["local_path"])
        if not p.exists():
            continue
        with rasterio.open(p) as ds:
            arr = ds.read(1)
        ref_vec = np.where(np.isfinite(arr[fp]), arr[fp], 0.0).astype(np.float64)
        s_rho = novelty.rank_correlation(surf_ranks, ref_vec)
        abs_s_rho = 0.0 if s_rho is None else abs(float(s_rho))
        peer_id = f"{e['primary_repo']}:{e['filename']}"
        if abs_s_rho > max_surf_rho:
            max_surf_rho = abs_s_rho
            max_surf_peer = peer_id

        abs_d_rho = None
        ov3 = None
        if dots_2d is not None and cand_pts is not None and len(cand_pts) > 0:
            d_rho = novelty.rank_correlation(dot_ranks, ref_vec)
            abs_d_rho = 0.0 if d_rho is None else abs(float(d_rho))
            if abs_d_rho > max_dot_rho:
                max_dot_rho = abs_d_rho
                max_dot_rho_peer = peer_id
            ref_pts = np.argwhere(fp & np.isfinite(arr) & (arr > 0))
            if len(ref_pts) > 0:
                ov3 = float(np.mean(cKDTree(ref_pts).query(cand_pts)[0] <= 3.0))
                if ov3 > max_all_ov:
                    max_all_ov = ov3
                    max_all_peer = peer_id
                if not e["is_space_filling_control"] and ov3 > max_comp_ov:
                    max_comp_ov = ov3
                    max_comp_peer = peer_id

        if any(w in e["filename"] for w in watch_substrs):
            key_peers[peer_id] = {
                "sha256": e["sha256"],
                "positive_dots": e["positive_dots"],
                "is_space_filling_control": e["is_space_filling_control"],
                "surface_abs_spearman": round(abs_s_rho, 6),
                "dots_abs_spearman": None if abs_d_rho is None else round(abs_d_rho, 6),
                "candidate_within_3px_of_peer": None if ov3 is None else round(ov3, 6),
            }
        checked += 1

    return {
        "rasters_checked": checked,
        "competing_detectors_checked": int(sum(1 for e in entries if not e["is_space_filling_control"])),
        "space_filling_controls_checked": int(sum(1 for e in entries if e["is_space_filling_control"])),
        "pre_placement_surface_max_abs_spearman": round(max_surf_rho, 6),
        "pre_placement_surface_nearest_peer": max_surf_peer,
        "pre_placement_surface_pass_le_0p90": bool(max_surf_rho <= 0.90),
        "post_placement_dots_max_abs_spearman": None if dots_2d is None else round(max_dot_rho, 6),
        "post_placement_dots_nearest_spearman_peer": max_dot_rho_peer,
        "post_placement_competing_max_3px_overlap": None if dots_2d is None else round(max_comp_ov, 6),
        "post_placement_competing_nearest_overlap_peer": max_comp_peer,
        "post_placement_competing_pass_le_0p70": None if dots_2d is None else bool(max_comp_ov <= 0.70 and max_dot_rho <= 0.90),
        "post_placement_literal_all360_max_3px_overlap": None if dots_2d is None else round(max_all_ov, 6),
        "post_placement_literal_all360_nearest_peer": max_all_peer,
        "key_focus_site_comparisons": key_peers,
    }


def run_stage_emit_and_audit(
    cache_dir: Path,
    registry_local_path: Path,
    arm_override: str | None = None,
) -> dict[str, Any]:
    t0 = time.monotonic()
    hold = json.loads(HOLDOUT_JSON.read_text())
    canary = json.loads(CANARY_JSON.read_text())

    arm_scores = {
        "EXP-1": hold["arms"]["EXP-1_KG2_Core78_TwoRegime"]["dti"],
        "EXP-2": hold["arms"]["EXP-2_KG2_DualHead_TwoRegime"]["dti"],
        "EXP-3": hold["arms"]["EXP-3_KG2_DualHead_ThreeRegime_CELF"]["dti"],
    }
    chosen_arm = arm_override or max(arm_scores, key=arm_scores.get)
    print(f"[Stage 3] Selected preregistered arm by HOLDOUT-DTI: {chosen_arm} ({arm_scores})", flush=True)

    (
        fp,
        fp_ids,
        template,
        catalogue,
        base_mm,
        _base_names,
        gvc_mm,
        _gvc_names,
        sahg_mm,
        _sahg_names,
        kg2_mm,
        _kg2_names,
        all_names,
    ) = load_all_stacks()
    nuisance_fp = load_nuisance(fp_ids)

    # Compute 45-degree rotated diamond OOF so full-footprint surface is 100% Zero-Copy Dual-Partition Stitched-OOF
    rot_folds = dprf1.make_rotated45_segment_folds(fp, catalogue, buffer_px=15)
    if chosen_arm == "EXP-1":
        quad_s = np.load(cache_dir / "oof_quad_exp1_sharp.npy")
        quad_c = np.load(cache_dir / "oof_quad_exp1_cond.npy")
        rot_s = np.zeros(fp.shape, dtype=np.float32)
        rot_c = np.zeros(fp.shape, dtype=np.float32)
        for rf in rot_folds:
            fid = int(rf["id"])
            ps, pc, _ = dprf1.fit_and_predict_fold(
                base_mm,
                gvc_mm,
                sahg_mm,
                nuisance_fp,
                all_names,
                fp,
                fp_ids,
                train_mask=rf["train"],
                visible_mask=rf["visible"],
                predict_mask=rf["valid"],
                neg_mode="stratified_d3",
                seed=SEED + 500 + 17 * fid,
                extra_mm=kg2_mm,
                regime_b_extra_names=kg2_mghv.KG2_REGIME_B_EXTRA,
                selective_extra_names=kg2_mghv.KG2_SELECTIVE_RESID_EXTRA,
            )
            rot_s += dprf1.debiased_apron_surface(ps, rf["valid"], rf["visible"])
            rot_c += dprf1.debiased_apron_surface(pc, rf["valid"], rf["visible"])
        full_primary = dprf1.debiased_apron_surface(0.5 * (quad_s + rot_s), fp, catalogue)
        full_cond = dprf1.debiased_apron_surface(0.5 * (quad_c + rot_c), fp, catalogue)
        full_pied = None
    else:
        quad_d = np.load(cache_dir / "oof_quad_exp2_dual.npy")
        quad_p = np.load(cache_dir / "oof_quad_exp2_pied.npy")
        quad_c = np.load(cache_dir / "oof_quad_exp2_cond.npy")
        rot_d = np.zeros(fp.shape, dtype=np.float32)
        rot_p = np.zeros(fp.shape, dtype=np.float32)
        rot_c = np.zeros(fp.shape, dtype=np.float32)
        for rf in rot_folds:
            fid = int(rf["id"])
            print(f"  Rotated45 OOF fold {fid} ({rf['name']}) ...", flush=True)
            pd_s, pp_s, pc_s, _ = kg2_mghv.fit_and_predict_dualhead_fold(
                base_mm,
                gvc_mm,
                sahg_mm,
                kg2_mm,
                nuisance_fp,
                all_names,
                fp,
                fp_ids,
                train_mask=rf["train"],
                visible_mask=rf["visible"],
                predict_mask=rf["valid"],
                seed=SEED + 500 + 17 * fid,
                core_weight=0.56,
            )
            rot_d += dprf1.debiased_apron_surface(pd_s, rf["valid"], rf["visible"])
            rot_p += dprf1.debiased_apron_surface(pp_s, rf["valid"], rf["visible"])
            rot_c += dprf1.debiased_apron_surface(pc_s, rf["valid"], rf["visible"])
        full_primary = dprf1.debiased_apron_surface(0.5 * (quad_d + rot_d), fp, catalogue)
        full_pied = dprf1.debiased_apron_surface(0.5 * (quad_p + rot_p), fp, catalogue)
        full_cond = dprf1.debiased_apron_surface(0.5 * (quad_c + rot_c), fp, catalogue)

    full_primary[catalogue | (~fp)] = 0.0
    full_cond[catalogue | (~fp)] = 0.0
    if full_pied is not None:
        full_pied[catalogue | (~fp)] = 0.0

    print("[Stage 3] Checking pre-placement continuous surface uniqueness across 360 rasters...", flush=True)
    pre_audit = audit_against_all_360_registry(full_primary, None, fp, registry_local_path)
    if not pre_audit["pre_placement_surface_pass_le_0p90"]:
        raise SystemExit(
            f"HALT: Pre-placement surface Spearman exceeded 0.90: {pre_audit['pre_placement_surface_max_abs_spearman']}"
        )

    print("[Stage 3] Running full-map submodular dot placement (budget=37,654)...", flush=True)
    if chosen_arm in ("EXP-1", "EXP-2"):
        dots = dprf1.two_regime_submodular_allocate(
            full_primary,
            full_cond,
            fp,
            catalogue,
            budget=FULL_DOT_BUDGET,
            primary_share=0.68,
            min_spacing_px=2.8,
            catalogue_clearance_px=2.0,
        )
    else:
        assert full_pied is not None
        dots = kg2_mghv.three_regime_submodular_allocate(
            full_primary,
            full_pied,
            full_cond,
            fp,
            catalogue,
            budget=FULL_DOT_BUDGET,
            shares=(0.54, 0.22, 0.24),
            min_spacing_px=3.0,
            catalogue_clearance_px=2.0,
        )

    print("[Stage 3] Checking post-placement dot uniqueness across 360 rasters...", flush=True)
    full_audit = audit_against_all_360_registry(full_primary, dots, fp, registry_local_path)
    print(
        f"  Surface max |rho|={full_audit['pre_placement_surface_max_abs_spearman']:.4f} "
        f"| Competing max 3px overlap={full_audit['post_placement_competing_max_3px_overlap']:.4f} "
        f"({full_audit['post_placement_competing_nearest_overlap_peer']})",
        flush=True,
    )

    # Save prediction .npy in scratch and emit via shared scripts/submission_writer.py
    pred_npy = cache_dir / "kg2_final_dots.npy"
    np.save(pred_npy, dots.astype(np.float32))
    fp_hash12 = hashlib.sha256(np.asarray(dots[fp], dtype="<f4").tobytes()).hexdigest()[:12]
    stem = f"kanlergemsdoe2-kg2-mghv-{chosen_arm.lower()}-{int(dots[fp].sum())}-20261026-{fp_hash12}"
    zeros_tif = ROOT / "docs/downloads" / f"{stem}-zeros.tif"
    zeros_zip = ROOT / "docs/downloads" / f"{stem}-zeros.zip"

    # Remove any prior kg2 downloads so docs/downloads stays clean
    for old_f in (ROOT / "docs/downloads").glob("kanlergemsdoe2-kg2-*"):
        old_f.unlink()

    cmd = [
        sys.executable,
        str(ROOT / "scripts/submission_writer.py"),
        str(pred_npy),
        str(zeros_tif),
        "--template",
        str(template),
        "--outside",
        "zero",
    ]
    proc = subprocess.run(cmd, check=True, capture_output=True, text=True)
    writer_checks = json.loads(proc.stdout)
    submission.zip_single(zeros_tif, zeros_zip)

    # Re-open saved GeoTIFF from disk for independent automated verification
    with rasterio.open(zeros_tif) as vds:
        saved_arr = vds.read(1)
        saved_crs = str(vds.crs)
        saved_shape = vds.shape
        saved_tr = list(vds.transform)[:6]
        saved_dtype = vds.dtypes[0]
        saved_nodata = vds.nodata

    d_cat = distance_transform_edt(~catalogue)
    pos_mask = fp & (saved_arr > 0)
    on_cat = int((pos_mask & catalogue).sum())
    strict_all_01 = bool(
        np.isfinite(saved_arr).all() and ((saved_arr >= 0.0) & (saved_arr <= 1.0)).all()
    )
    in_fp_01 = bool(
        np.isfinite(saved_arr[fp]).all()
        and ((saved_arr[fp] >= 0.0) & (saved_arr[fp] <= 1.0)).all()
    )

    arm_key_map = {
        "EXP-1": "EXP-1_KG2_Core78_TwoRegime",
        "EXP-2": "EXP-2_KG2_DualHead_TwoRegime",
        "EXP-3": "EXP-3_KG2_DualHead_ThreeRegime_CELF",
    }
    win_res = hold["arms"][arm_key_map[chosen_arm]]
    win_paired = hold["paired_bootstrap_deltas"][chosen_arm]

    beats_dprf1 = bool(float(win_res["dti"]) > DPRF1_REFERENCE_DTI)
    beats_controls_ci = bool(
        win_paired["vs_B0_oof_h24_ridge"]["ci95_strictly_positive"]
        and win_paired["vs_B1_oof_base_submod"]["ci95_strictly_positive"]
        and win_paired["vs_JUNC_100m_only"]["ci95_strictly_positive"]
        and win_paired["vs_CTRL_RAND_37654"]["ci95_strictly_positive"]
    )
    format_gate = bool(
        writer_checks["format_valid"]
        and strict_all_01
        and in_fp_01
        and on_cat == 0
        and saved_crs == "EPSG:32611"
        and saved_shape == (3730, 3292)
        and saved_tr == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
        and saved_dtype == "float32"
    )
    novelty_gate = bool(
        full_audit["pre_placement_surface_pass_le_0p90"]
        and full_audit["post_placement_competing_pass_le_0p70"]
    )
    canary_gate = bool(canary["passed"])

    all_gates_pass = bool(
        format_gate and canary_gate and novelty_gate and beats_dprf1 and beats_controls_ci
    )
    verdict = "promote" if all_gates_pass else "negative"

    note = (
        f"KG2-MGHV {chosen_arm} 10m/3m/1m junc+hydro-demag OOF CELF {int(pos_mask.sum())}d "
        f"| HOLDOUT-DTI {win_res['dti']:.4f} n=60988 | {fp_hash12}"
    )
    assert len(note) <= 140, f"Note exceeds 140 chars ({len(note)})"

    # Distance profile of emitted dots relative to known catalogue
    dists = d_cat[pos_mask]
    dist_profile = {
        "min_dist_to_catalogue_px": round(float(dists.min()), 4),
        "p10_dist_px": round(float(np.quantile(dists, 0.10)), 3),
        "median_dist_px": round(float(np.median(dists)), 3),
        "p90_dist_px": round(float(np.quantile(dists, 0.90)), 3),
        "frac_gt_20px_2km_farfield": round(float((dists > 20.0).mean()), 6),
        "frac_in_1m_lidar_gap": round(
            float((~np.isfinite(base_mm[:, _base_names.index("lidar_1")]))[pos_mask.ravel()[fp_ids]].mean()),
            6,
        ),
        "frac_low_slope_le_6p5deg": round(
            float((base_mm[:, _base_names.index("det_elev_slope")][pos_mask.ravel()[fp_ids]] <= 6.5).mean()),
            6,
        ),
    }

    if chosen_arm == "EXP-1":
        mech_str = (
            "Zero-copy Dual-Partition Stitched Out-of-Fold (EXP-1: 4 Quadrant OOF + 4 Rotated-45deg "
            "Diamond OOF) 78-channel calibrated 2-seed HistGradientBoostingClassifier synthesis "
            "(with selective non-topographic nuisance residualization, 3-tier relief-conditioned "
            "LiDAR-gap log-odds calibration, 8-azimuth ridge sharpening, and visible-catalogue apron "
            "quantile debiasing) followed by Two-Regime 300m Submodular CELF dot allocation "
            "(68% primary multi-scale 10m/3m/1m scarp & piedmont-junction ridge + 32% concealed "
            "hydrothermal magnetite-destruction / cross-gradient / vent conduit, min_spacing=2.8 px, "
            "37,654 binary dots, d_catalogue > 2 px, all-finite float32 -zeros.tif)."
        )
    elif chosen_arm == "EXP-2":
        mech_str = (
            "Zero-copy Dual-Partition Stitched Out-of-Fold (EXP-2) 78-channel Dual-Head synthesis "
            "(0.56 Core HGB Classifier + 0.44 300m Triangular-Kernel Soft-DTI HGB Regressor) "
            "followed by Two-Regime 300m Submodular CELF dot allocation (68% primary + 32% conduit, "
            "min_spacing=2.8 px, 37,654 binary dots, d_catalogue > 2 px, all-finite float32 -zeros.tif)."
        )
    else:
        mech_str = (
            "Zero-copy Dual-Partition Stitched Out-of-Fold (EXP-3) 78-channel Dual-Head synthesis "
            "followed by Three-Regime 300m Submodular CELF dot allocation (54% range/gap + 22% "
            "low-slope piedmont + 24% concealed hydrothermal conduit, min_spacing=3.0 px, "
            "37,654 binary dots, d_catalogue > 2 px, all-finite float32 -zeros.tif)."
        )

    run_card = {
        "schema_version": "kanlergemsdoe2-run-card-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "repository": "kanlerxz87-cyber/KANLERGEMSDOE2",
        "branch": "arena/49a34a70-kanlergemsdoe2",
        "lane_id": f"KG2-MGHV-{chosen_arm}",
        "preregistration": PREREG_PATH,
        "hypothesis": (
            "KG2-H1 (KG2-MGHV): Uncatalogued Great Basin faults span three complementary physical regimes "
            "missed by 1m-LiDAR-only and range-front-only detectors: (1) concave-up piedmont-junction slope "
            "breaks and asymmetric scarps across the 24.63% (1,272,913-px) 1m-LiDAR void resolved by seamless "
            "10m USGS 3DEP scarp descriptors + 3m gravity-strike-coherent antislope scarps; (2) low-slope "
            "(<=6.5 deg) relief-normalized alluvial piedmont & transtensional step-over splays; and "
            "(3) blind geothermal vent upflow conduits marked by shallow hydrothermal magnetite destruction "
            "-(RTP - RTP_up250m), Gallardo-Meju gravity-magnetic cross-gradient alignment, 2.5km high-pass "
            "clay-cap conductivity, K/Th alteration, and 2m thermal-probe/sinter/geothermometer plumes."
        ),
        "mechanism": mech_str,
        "non_fault_mimic_process": (
            "Pleistocene Lake Lahontan wave-cut shorelines and fluvial fan terrace risers (mitigated by 3m "
            "scarp-strike vs isostatic-gravity fault-strike kinematic coherence and multi-azimuth ridge continuity), "
            "conductive saline playas (mitigated by 2.5km local high-pass conductivity residualization), and "
            "unfaulted Tertiary felsic tuff / caldera margins (mitigated by basement gradient & strain gating)."
        ),
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": win_res["evaluator_version"],
            "withheld_positive_pixels": int(win_res["n_withheld_positive_pixels"]),
            "buffer_collar_px": 15,
            "buffer_collar_m": 1500,
            "dti": float(win_res["dti"]),
            "ci95": [float(x) for x in win_res["ci95"]["interval"]],
            "bootstrap_resamples": int(win_res["ci95"]["resamples"]),
            "block_size_px": int(win_res["ci95"]["block_pixels"]),
            "per_quadrant_dti": {f["fold"]: float(f["dti"]) for f in win_res["folds"]},
            "all_3_experiments_summary": {
                "EXP-1_KG2_Core78_TwoRegime": {
                    "dti": float(hold["arms"]["EXP-1_KG2_Core78_TwoRegime"]["dti"]),
                    "ci95": hold["arms"]["EXP-1_KG2_Core78_TwoRegime"]["ci95"]["interval"],
                },
                "EXP-2_KG2_DualHead_TwoRegime": {
                    "dti": float(hold["arms"]["EXP-2_KG2_DualHead_TwoRegime"]["dti"]),
                    "ci95": hold["arms"]["EXP-2_KG2_DualHead_TwoRegime"]["ci95"]["interval"],
                },
                "EXP-3_KG2_DualHead_ThreeRegime_CELF": {
                    "dti": float(hold["arms"]["EXP-3_KG2_DualHead_ThreeRegime_CELF"]["dti"]),
                    "ci95": hold["arms"]["EXP-3_KG2_DualHead_ThreeRegime_CELF"]["ci95"]["interval"],
                },
            },
            "same_evaluator_controls": {
                "DPRF1_recorded_best_prior": DPRF1_REFERENCE_DTI,
                "B0_oof_h24_ridge": float(hold["controls_same_evaluator"]["B0_oof_h24_ridge"]["dti"]),
                "B1_oof_base_submod": float(hold["controls_same_evaluator"]["B1_oof_base_submod"]["dti"]),
                "JUNC_100m_only": float(hold["controls_same_evaluator"]["JUNC_100m_only"]["dti"]),
                "CTRL_RAND_37654": float(hold["controls_same_evaluator"]["CTRL_RAND_37654"]["dti"]),
            },
            "paired_delta_ci95": win_paired,
        },
        "organizer_confirmed_score": None,
        "leakage_canary": {
            "passed": canary_gate,
            "threshold_auc": 0.90,
            "n_features_checked": canary["n_features_checked"],
            "worst_feature_all78": canary["worst_feature_all78"],
            "worst_two_polarity_auc_all78": canary["worst_two_polarity_auc_all78"],
            "worst_feature_kg2_new26": canary["worst_feature_kg2_new26"],
            "worst_two_polarity_auc_kg2_new26": canary["worst_two_polarity_auc_kg2_new26"],
        },
        "correlation_overlap_vs_registry": full_audit,
        "raster_sha256": sha256_file(zeros_tif),
        "zip_artifact": zeros_zip.name,
        "zip_sha256": sha256_file(zeros_zip),
        "validator_output": {
            "format_valid": format_gate,
            "no_nan_in_footprint": in_fp_01,
            "strict_whole_array_0_1_no_nan": strict_all_01,
            "values_in_0_1": strict_all_01,
            "crs": saved_crs,
            "shape": list(saved_shape),
            "transform": saved_tr,
            "dtype": saved_dtype,
            "nodata": saved_nodata,
            "positive_dots_in_footprint": int(pos_mask.sum()),
            "on_catalogue_positive_dots": on_cat,
            "file_size_bytes": zeros_tif.stat().st_size,
            "zip_size_bytes": zeros_zip.stat().st_size,
            "submission_writer_checks": writer_checks,
        },
        "spatial_regime_diagnostics": dist_profile,
        "submission_filename": zeros_tif.name,
        "submission_name": stem,
        "submission_note": note,
        "submission_note_length": len(note),
        "experiments_used": 3,
        "budget_max_experiments": 3,
        "ok_to_download": format_gate,
        "ok_to_submit": all_gates_pass,
        "weekly_slot_spent_automatically": False,
        "verdict": verdict,
    }

    save_json(run_card, RUN_CARD_JSON)
    save_json(run_card, ROOT_RUN_CARD_JSON)
    save_json(run_card, DOCS_RUN_CARD_JSON)
    save_json(
        {
            "canary": canary,
            "holdout": hold,
            "novelty_audit": full_audit,
            "run_card": run_card,
            "stage3_elapsed_seconds": round(time.monotonic() - t0, 2),
        },
        EXPERIMENT_JSON,
    )
    print(
        f"[Stage 3] COMPLETE! File={zeros_tif.name} | HOLDOUT-DTI={win_res['dti']:.6f} "
        f"| competing_3px_ov={full_audit['post_placement_competing_max_3px_overlap']:.4f} "
        f"| ok_to_submit={all_gates_pass} | verdict={verdict}",
        flush=True,
    )
    return run_card


def verify_recorded() -> dict[str, Any]:
    for p in (CANARY_JSON, HOLDOUT_JSON, RUN_CARD_JSON, ROOT_RUN_CARD_JSON, DOCS_RUN_CARD_JSON):
        if not p.exists():
            raise SystemExit(f"Missing recorded KG2 artifact: {p}")
    c1 = json.loads(RUN_CARD_JSON.read_text())
    c2 = json.loads(ROOT_RUN_CARD_JSON.read_text())
    c3 = json.loads(DOCS_RUN_CARD_JSON.read_text())
    if not (c1 == c2 == c3):
        raise SystemExit("Run card copies in root, evidence/, and docs/data/ disagree")

    tif_path = ROOT / "docs/downloads" / c1["submission_filename"]
    zip_path = ROOT / "docs/downloads" / c1["zip_artifact"]
    if sha256_file(tif_path) != c1["raster_sha256"]:
        raise SystemExit("Saved GeoTIFF SHA-256 mismatch")
    if sha256_file(zip_path) != c1["zip_sha256"]:
        raise SystemExit("Saved ZIP SHA-256 mismatch")
    with zipfile.ZipFile(zip_path) as zf:
        if zf.namelist() != [tif_path.name]:
            raise SystemExit("ZIP member list mismatch")
        if hashlib.sha256(zf.read(tif_path.name)).hexdigest() != c1["raster_sha256"]:
            raise SystemExit("ZIP inner GeoTIFF hash mismatch")
    if c1["submission_note_length"] > 140 or len(c1["submission_note"]) > 140:
        raise SystemExit("Submission note exceeds 140 characters")
    return {
        "verified": True,
        "submission_filename": c1["submission_filename"],
        "raster_sha256": c1["raster_sha256"],
        "holdout_dti": c1["holdout_dti"]["dti"],
        "ci95": c1["holdout_dti"]["ci95"],
        "max_competing_3px_overlap": c1["correlation_overlap_vs_registry"][
            "post_placement_competing_max_3px_overlap"
        ],
        "max_surface_spearman": c1["correlation_overlap_vs_registry"][
            "pre_placement_surface_max_abs_spearman"
        ],
        "ok_to_download": c1["ok_to_download"],
        "ok_to_submit": c1["ok_to_submit"],
        "verdict": c1["verdict"],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--stage",
        choices=("features_and_canary", "holdout_experiments", "emit_and_audit", "all", "verify"),
        default="verify",
    )
    ap.add_argument("--cache-dir", type=Path, default=Path("/tmp/gems_work/kg2_stage_cache"))
    ap.add_argument(
        "--registry-local",
        type=Path,
        default=Path("/tmp/gems_work/comparison_registry_local.json"),
    )
    ap.add_argument("--arm-override", choices=("EXP-1", "EXP-2", "EXP-3"), default=None)
    args = ap.parse_args()

    if args.stage == "verify":
        print(json.dumps(verify_recorded(), indent=2, allow_nan=False))
    elif args.stage == "features_and_canary":
        run_stage_features_and_canary()
    elif args.stage == "holdout_experiments":
        run_stage_holdout_experiments(args.cache_dir)
    elif args.stage == "emit_and_audit":
        run_stage_emit_and_audit(args.cache_dir, args.registry_local, arm_override=args.arm_override)
    elif args.stage == "all":
        run_stage_features_and_canary()
        run_stage_holdout_experiments(args.cache_dir)
        run_stage_emit_and_audit(args.cache_dir, args.registry_local, arm_override=args.arm_override)


if __name__ == "__main__":
    main()
