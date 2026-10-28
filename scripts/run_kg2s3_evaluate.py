#!/usr/bin/env python3
"""KG2-S3 E2 evaluation on the shared instruments (no private metric, no hyper-parameter search).

* HIDE-RECOVER-v3.0 (src/gems32/holdout.evaluate_hide_and_recover): the LOPE emission is re-run inside
  every holdout cell with the catalogue-distance factor rebuilt from the cell's VISIBLE faults only
  (same fitted density, same two-phase quota emission, same inside keep fraction).  Paired cluster bootstrap vs
  the champion (G32) on identical draws.
* SGMC-CAL-v3.0 (evaluate_sgmc_with_ci) on the full-grid candidate, paired vs the champion.
* Leakage canary: single-feature AUC (orientation-free, max(AUC, 1-AUC)) of every input factor and of
  the fitted density itself at the withheld hide-and-recover truth vs cell background; > 0.90 = leak.
Output: evidence/kg2s3_lope_holdout.json.  Labels: HOLDOUT-DTI (evaluator, N withheld, 95 % CI).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import run_kg2s3_lli_cv as cv  # noqa: E402
import run_kg2s3_lope as runlope  # noqa: E402
from gems32 import holdout as ho  # noqa: E402
from gems32 import lope  # noqa: E402
from gems32.paths import data_dir, docs_dir, work_dir  # noqa: E402

CHAMPION = "focus_20261027/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
CHAMPION_PRECOLLAR = "focus_20261027/GEMSDOE25__gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif"
DSLUP_RECORDED = {"hr_pooled": 0.125925, "sgmc_cal": 0.098140, "champion_hr": 0.099202}


def strip(d: dict) -> dict:
    return {k: v for k, v in d.items() if not k.startswith("_") and k != "folds"}


def main() -> int:
    raise SystemExit(
        "Archived runner disabled: not the assigned HTCADS lane; the literal registry stop "
        "and preserved historical receipts prohibit this execution path."
    )


def _legacy_main_archived() -> int:
    """Historical implementation retained for audit; do not use as an active runner."""
    t0 = time.time()
    ddir, wdir = data_dir(), work_dir() / "kg2s3"
    emis = json.loads((ROOT / "evidence/kg2s3_lope_emission.json").read_text())
    mu = 0.0
    keep = float(emis["constrained"]["inside_keep_fraction"])
    lam_map, f, sp, fm, active, meta = runlope.fitted_lambda_map(emis["design"], emis["ridge"])
    lam_strata = f["lambda"]
    saved = np.load(wdir / "lope_dots.npz")
    cand_full = saved["constrained"]
    halo = saved["halo"]
    ctx = ho.load_holdout_context(ddir)
    print(f"[{time.time()-t0:.0f}s] holdout context ready; keep={keep}", flush=True)

    fac = cv.DESIGNS[emis["design"]]
    per_cell = {}
    canary_x = {k: [] for k in ("d_visible_catalogue", "d_H19-5", "phys_scarp", "geod_shear_level", "lope_density")}
    canary_y = []
    rng = np.random.default_rng(20261027)
    for cell in ctx.cells:
        sl = cell.bbox
        vis = cell.visible_full
        d_vis = distance_transform_edt(~vis).astype(np.float32)
        lv_dcat = lope.dcat_levels(d_vis)
        fm_c = dict(fm)
        fm_c["lv_dcat"] = lv_dcat
        act_c = ctx.foot & ~vis
        sp_c = cv.design_spec(fm_c, act_c, fac)
        lam_c = np.zeros(act_c.shape, np.float32)
        lam_c[act_c] = lam_strata[sp_c.stratum[act_c]].astype(np.float32)
        lam_sub = lam_c[sl]
        elig = act_c[sl]
        g_sub = float(lam_sub.sum())
        halo_sub = halo[sl]
        d_in, i_in = lope.emit_threshold_greedy(lam_sub, elig & halo_sub, g_sub)
        n_in = int(round(int(d_in.sum()) * keep))
        n_out = int(np.ceil(n_in * (1 - runlope.HALO_CAP) / runlope.HALO_CAP))
        q_max = int(np.ceil(int(d_in.sum()) * (1 - runlope.HALO_CAP) / runlope.HALO_CAP)) + 16
        d_out, i_out = lope.emit_threshold_greedy(lam_sub, elig & ~halo_sub, g_sub, force=True, max_dots=q_max,
                                                  kmax0=i_in["kmax"])
        dots_sub = lope.first_n(d_in, i_in, n_in) | lope.first_n(d_out, i_out, n_out)
        info = {"rounds": i_in["rounds"] + i_out["rounds"]}
        per_cell[cell.key] = dots_sub.astype(np.float32)
        # canary sample (truth vs background inside the cell's scored domain)
        ty, tx = cell.truth_coords
        bg = np.flatnonzero(cell.active_sub.ravel())
        bg = rng.choice(bg, size=min(bg.size, 20 * max(ty.size, 1), 60000), replace=False)
        by, bx = np.unravel_index(bg, cell.active_sub.shape)
        yy = np.concatenate([ty, by]); xx = np.concatenate([tx, bx])
        canary_y.append(np.concatenate([np.ones(ty.size), np.zeros(by.size)]))
        canary_x["d_visible_catalogue"].append(d_vis[sl][yy, xx])
        canary_x["d_H19-5"].append(fm["d_ref"][sl][yy, xx])
        canary_x["phys_scarp"].append(np.nan_to_num(fm["phys"][sl][yy, xx]))
        canary_x["geod_shear_level"].append(fm["lv_strain"][sl][yy, xx].astype(np.float32))
        canary_x["lope_density"].append(lam_sub[yy, xx])
        print(f"[{time.time()-t0:.0f}s] {cell.key}: emitted {int(dots_sub.sum())} (rounds {info['rounds']}), truth {cell.n_truth}", flush=True)

    y = np.concatenate(canary_y)
    canary = {}
    for k, parts in canary_x.items():
        v = np.concatenate(parts).astype(np.float64)
        a = roc_auc_score(y, v)
        canary[k] = float(max(a, 1 - a))
    max_feat = max(canary, key=canary.get)

    hr = ho.evaluate_hide_and_recover(per_cell, ctx, n_boot=1000, seed=20261026, name="kg2s3-lope")
    # Champion proxy exactly as recorded by KG2-S2 (scripts/run_dslup_unique_slot.py): the pre-collar G25
    # d2.8 mask with the champion's 2-px collar applied to VISIBLE faults only (b_visible_px=2.0).  The
    # fixed G32 raster is also reported, but it is reverse-leaky on this holdout (its collar used the FULL
    # catalogue, so it avoids the hidden segments by construction).
    with rasterio.open(ddir / CHAMPION_PRECOLLAR) as s:
        a = s.read(1)
        d28 = ctx.foot & np.isfinite(a) & (a >= 0.5)
    with rasterio.open(ddir / CHAMPION) as s:
        a = s.read(1)
        champ = ctx.foot & np.isfinite(a) & (a >= 0.5)
    hr_ch = ho.evaluate_hide_and_recover(d28, ctx, b_visible_px=2.0, n_boot=1000, seed=20261026, name="GEMSDOE32_B2_ref")
    hr_fixed = ho.evaluate_hide_and_recover(champ, ctx, n_boot=1000, seed=20261026, name="G32-fixed-raster")
    d_hr = ho.paired_bootstrap_delta(hr, hr_ch)
    sg = ho.evaluate_sgmc_with_ci(cand_full, ctx, n_boot=1000, seed=20261026, name="kg2s3-lope")
    sg_ch = ho.evaluate_sgmc_with_ci(champ, ctx, n_boot=1000, seed=20261026, name="GEMSDOE32_B2_ref")
    d_sg = ho.paired_bootstrap_delta(sg, sg_ch, boot_key="_cal_boots")
    gates = {
        "hr_beats_dslup": bool(hr["pooled_dti"] > DSLUP_RECORDED["hr_pooled"]),
        "hr_paired_ci_vs_champion_strictly_positive": bool(d_hr["ci95_strictly_positive"]),
        "sgmc_beats_dslup": bool(sg["sgmc_prevalence_calibrated_dti"] > DSLUP_RECORDED["sgmc_cal"]),
        "canary_max_auc_le_0_90": bool(canary[max_feat] <= 0.90),
    }
    out = {
        "schema": "kg2s3.lope_holdout.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate": "KG2-S3 LOPE (constrained)", "inside_keep_fraction": keep,
        "candidate_dots_sha256": hashlib.sha256(np.packbits(cand_full.astype(bool).ravel()).tobytes()).hexdigest(),
        "candidate_n_dots": int(cand_full.sum()), "design": emis["design"], "ridge": emis["ridge"],
        "hide_and_recover": strip(hr), "hide_and_recover_champion_same_evaluator": strip(hr_ch),
        "hide_and_recover_champion_fixed_raster_reverse_leaky": strip(hr_fixed),
        "hide_and_recover_paired_delta_vs_champion": d_hr,
        "sgmc_cal": strip(sg), "sgmc_cal_champion_same_evaluator": strip(sg_ch),
        "sgmc_cal_paired_delta_vs_champion": d_sg,
        "dslup_recorded_reference": DSLUP_RECORDED,
        "leakage_canary": {"auc_by_feature": canary, "max_feature": max_feat, "max_auc": canary[max_feat],
                           "n_truth_px": int(y.sum()), "n_background_px": int((1 - y).sum()),
                           "passed": bool(canary[max_feat] <= 0.90)},
        "per_cell_emitted": {k: int(v.sum()) for k, v in per_cell.items()},
        "protocol_gates": gates,
        "verdict": "promote" if all(gates.values()) else "negative",
    }
    (ROOT / "evidence/kg2s3_lope_holdout.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    print(json.dumps({k: out[k] for k in ("hide_and_recover_paired_delta_vs_champion", "sgmc_cal_paired_delta_vs_champion",
                                          "leakage_canary", "protocol_gates", "verdict")}, indent=1))
    print("HR", hr["pooled_dti"], hr["ci95_cluster_bootstrap"], "N", hr["n_withheld_positives"], "| champion", hr_ch["pooled_dti"])
    print("SGMC-CAL", sg["sgmc_prevalence_calibrated_dti"], sg["sgmc_calibrated_ci95"], "| champion", sg_ch["sgmc_prevalence_calibrated_dti"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
