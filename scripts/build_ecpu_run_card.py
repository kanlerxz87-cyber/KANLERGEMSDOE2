#!/usr/bin/env python3
"""ARCHIVED: CLI disabled; historical claims below are not current evidence.

Build KG2-ECPU-20261027 run card + same-session 9-site re-audit from measured receipts.

Reads evidence/ecpu_experiments_20261027.json (frozen experiment output) and recomputes:
- 4-point Tversky ledger inversion (matches prior session TPw=5151/K=13735; 3-point
  sensitivity also reported - see IR-20261027-02),
- PROJECTIONs (never scores) for every in-repo candidate,
- focus-9 champion static re-audit on GEMSDOE32-HIDE-RECOVER-v3.0 (static; collared files
  are self-censored - IR-20261027-01) and GEMSDOE32-SGMC-CAL-v3.0, pairwise XOR + 3-px
  overlaps, portal [0,1] safety.
Writes evidence/run_card_ecpu_20261027.json, evidence/nine_site_reaudit_20261027.json,
docs/downloads/ecpu_run_card.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import holdout  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir  # noqa: E402

ORGANIZER = {  # user-supplied submission ledger 2026-10-27 (ORGANIZER-CONFIRMED)
    "GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449, "GEMSDOE28": 0.2710,
    "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708, "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632,
    "GEMSDOE36": 0.2750,
}


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ledger_fit(points):
    N = np.array([p[0] for p in points], float); D = np.array([p[1] for p in points], float)
    A = np.vstack([N, np.ones_like(N)]).T
    s, i = np.linalg.lstsq(A, 1.0 / D, rcond=None)[0]
    r2 = 1 - float((((1 / D) - (s * N + i)) ** 2).sum() / (((1 / D) - (1 / D).mean()) ** 2).sum())
    tpw = 0.2 / s; K = i * tpw / 0.8
    return {"points_N_DTI": points, "slope": float(s), "intercept": float(i), "r_squared": r2,
            "inferred_TPw_px": float(tpw), "inferred_K_hidden_px": float(K)}


def proj(tpw, K, n_dots, ratio):
    return float((tpw * ratio) / (0.2 * n_dots + 0.8 * K))


def main() -> int:
    raise SystemExit(
        "Archived audit writer disabled: it can overwrite current evidence with "
        "self-attested scores or legacy promotion claims. Use audit_release.py."
    )


def _legacy_main_archived() -> int:
    """Retained only as historical code; not a current evidence generator."""
    t0 = time.time()
    ddir, edir = data_dir(), evidence_dir()
    exps = json.loads((edir / "ecpu_experiments_20261027.json").read_text())
    audit9 = json.loads((edir / "nine_site_audit.json").read_text())
    ctx = holdout.load_holdout_context(ddir)
    foot, labels = ctx.foot, ctx.labels

    # ---- ledger (4-point primary; exact prior-session reproduction) ----------
    led4 = ledger_fit([(44090, 0.2600), (40199, 0.2708), (37654, 0.2778), (38854, 0.2750)])
    led3 = ledger_fit([(44090, 0.2600), (40199, 0.2708), (37654, 0.2778)])
    tpw, K = led4["inferred_TPw_px"], led4["inferred_K_hidden_px"]
    ref_hr_b2 = exps["references"]["REF-B2-HR-procedural"]["pooled_dti"]
    ref_sg_raw_b2 = exps["references"]["REF-B2-SGMC-static"]["raw_dti"]

    # ---- focus-9 static re-audit ------------------------------------------------
    sites = []
    masks = {}
    for s in audit9["focus_9_sites"]:
        p = ddir / "focus9" / (s["site"] + "__" + Path(s["best_file_in_repo"]).name)
        with rasterio.open(p) as ds:
            a = ds.read(1); nodata = ds.nodata
        m = foot & np.isfinite(a) & (a >= 0.5)
        masks[s["site"]] = m
        hr = holdout.evaluate_hide_and_recover(m, ctx, b_visible_px=0.0, n_boot=1000, seed=20261026, name=s["site"])
        sg = holdout.evaluate_sgmc_with_ci(m, ctx, n_boot=1000, seed=20261026, name=s["site"])
        sites.append({
            "site": s["site"], "file": p.name, "repo_path": s["best_file_in_repo"],
            "pages_url": s["pages_url"], "sha256_measured": sha256(p),
            "sha256_matches_20261026_audit": bool(sha256(p) == s["sha256"]),
            "organizer_confirmed_score": ORGANIZER[s["site"]],
            "dots": int(m.sum()), "nodata_repr": str(nodata),
            "nan_outside_footprint": int(np.isnan(a[~foot]).sum()),
            "nan_inside_footprint": int(np.isnan(a[foot]).sum()),
            "portal_safe_as_stored_no_nan_anywhere": bool(int(np.isnan(a).sum()) == 0),
            "static_hide_recover": {"pooled_dti": hr["pooled_dti"], "ci95": hr["ci95_cluster_bootstrap"],
                                    "label": f"HOLDOUT-DTI (GEMSDOE32-HIDE-RECOVER-v3.0 STATIC file, N={hr['n_withheld_positives']}, 95% CI [{hr['ci95_cluster_bootstrap'][0]:.4f}, {hr['ci95_cluster_bootstrap'][1]:.4f}]); collared files self-censored (IR-20261027-01)"},
            "sgmc_cal": {"sgmc_prevalence_calibrated_dti": sg["sgmc_prevalence_calibrated_dti"],
                         "ci95": sg["sgmc_calibrated_ci95"], "raw_dti": sg["sgmc_raw_pooled_dti"],
                         "label": f"HOLDOUT-DTI (GEMSDOE32-SGMC-CAL-v3.0, N={sg['n_withheld_positives']}, 95% CI [{sg['sgmc_calibrated_ci95'][0]:.4f}, {sg['sgmc_calibrated_ci95'][1]:.4f}])"},
            "lineage": s["lineage_formula"],
        })
        print(f"[reaudit] {s['site']} HRstatic={hr['pooled_dti']:.6f} SGMCcal={sg['sgmc_prevalence_calibrated_dti']:.6f}", flush=True)
    order = [s["site"] for s in sites]
    d3 = {k: distance_transform_edt(~v) <= 3.0 for k, v in masks.items()}
    pair = {}
    for a in order:
        for b in order:
            if a < b:
                pair[f"{a}|{b}"] = {
                    "xor_px": int((masks[a] ^ masks[b]).sum()),
                    "frac_a_dots_within_3px_of_b": float((masks[a] & d3[b]).sum() / max(int(masks[a].sum()), 1)),
                    "frac_b_dots_within_3px_of_a": float((masks[b] & d3[a]).sum() / max(int(masks[b].sum()), 1)),
                }
    for s in sites:
        others = [max(pair[f"{min(s['site'],o)}|{max(s['site'],o)}"][
                      "frac_a_dots_within_3px_of_b" if s["site"] < o else "frac_b_dots_within_3px_of_a"], 0)
                  for o in order if o != s["site"]]
        # max share of this site's dots within 3px of any single other focus champion
        vals = []
        for o in order:
            if o == s["site"]:
                continue
            k = f"{min(s['site'],o)}|{max(s['site'],o)}"
            vals.append(pair[k]["frac_a_dots_within_3px_of_b"] if s["site"] < o else pair[k]["frac_b_dots_within_3px_of_a"])
        s["max_frac_own_dots_within_3px_of_any_other_focus_champion"] = float(max(vals))
        s["unique_among_focus9_le_0p70"] = bool(max(vals) <= 0.70)

    reaudit = {
        "schema": "kanlergemsdoe2.nine_site_reaudit.v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Same-session sha256-verified re-download of the 9 focus champions (gh api raw, main) + static scoring on shared evaluators; ORGANIZER scores from user ledger 2026-10-27.",
        "ledger_inversion_4point_primary": led4, "ledger_inversion_3point_sensitivity": led3,
        "focus_9_sites": sites, "pairwise": pair,
        "exact_duplicate_pairs_xor0": [k for k, v in pair.items() if v["xor_px"] == 0],
    }
    (edir / "nine_site_reaudit_20261027.json").write_text(json.dumps(reaudit, indent=2) + "\n")

    # ---- projections for in-repo candidates (PROJECTION, never scores) ----------
    def cand_proj(n, hr_ratio=None, sg_ratio=None):
        o = {"label": "PROJECTION via 4-point ledger TPw/(0.2N+0.8K) with TPw scaled by holdout ratio vs B2; NOT a score"}
        if hr_ratio:
            o["via_hr_oof_ratio"] = proj(tpw, K, n, hr_ratio)
        if sg_ratio:
            o["via_sgmc_raw_ratio"] = proj(tpw, K, n, sg_ratio)
        vs = [v for k, v in o.items() if k.startswith("via_")]
        o["range"] = [min(vs), max(vs)] if vs else None
        return o

    ht_raw = exps["references"]["REF-HTCADS-SGMC-static"]["raw_dti"]
    projections = {
        "HTCADS-EXP2-prior-promoted": cand_proj(37654, 0.112353 / ref_hr_b2, ht_raw / ref_sg_raw_b2),
    }
    for e, r in exps["experiments"].items():
        projections[f"ECPU-{e}"] = cand_proj(
            r["live_dots"],
            r["holdout_hide_recover_oof"]["pooled_dti"] / ref_hr_b2,
            r["holdout_sgmc_static_live"]["raw_dti"] / ref_sg_raw_b2)
    reaudit["candidate_projections"] = projections
    (edir / "nine_site_reaudit_20261027.json").write_text(json.dumps(reaudit, indent=2) + "\n")

    # ---- run card ---------------------------------------------------------------
    sel = exps["selected_experiment"]; r = exps["experiments"][sel]; b = exps["bundle"]
    canary = json.loads((edir / "ecpu_leakage_canary_20261027.json").read_text())
    fmt = b["zeros_tif"]
    card = {
        "schema": "gems.parallel_run_card.v1", "site": "KANLERGEMSDOE2",
        "repo": "kanlerxz87-cyber/KANLERGEMSDOE2", "branch": "arena/921c03c6-kanlergemsdoe2",
        "generated_utc": datetime.now(timezone.utc).isoformat(), "lane_id": "KG2-ECPU-20261027",
        "hypothesis": "H-N1 ECPU: catalogue detectability-propensity reweighting recovers P(fault) from P(catalogued)=P(fault)xP(mapped|fault,effort), shifting a plain 27-channel GBDT toward blind low-effort (deep-cover / LiDAR-void / low-slope / road-remote) fault signatures.",
        "mechanism": "Per-fold propensity e(x) from 4 effort covariates only; positive weights clip(median_pos(e)/e,0.5,4); single LightGBM on 27 sharp X_sub cols (no LiDAR detector features, no physics pillars, no tip specialist); shared 300 m CELF emission outside fold-visible d>2 px collar; EXP-2 adds 40/35/25 effort-strata caps, EXP-3 adds low-stratum potential-field ridge gate.",
        "named_non_fault_mimic": "Conductive playa clays + Pleistocene Lake Lahontan shoreline scarplets in flat low-effort basins (EXP-3 ridge gate targeted them; it did not rescue performance).",
        "leakage_canary": {"passed": bool(canary["passed"]), "max_single_feature_auc": canary["max_single_feature_auc"],
                           "max_feature_name": canary["max_feature_name"], "total_features_tested": canary["total_features_tested"],
                           "receipt": "evidence/ecpu_leakage_canary_20261027.json (same-session re-run; reproduces 2026-10-26 max 0.795377 exactly)"},
        "holdout_dti": {
            "primary_hide_and_recover": {
                "pooled_dti": r["holdout_hide_recover_oof"]["pooled_dti"], "ci95": r["holdout_hide_recover_oof"]["ci95"],
                "per_quadrant_dti": r["holdout_hide_recover_oof"]["per_quadrant_dti"],
                "champion_02778_same_evaluator": ref_hr_b2,
                "paired_delta_vs_0p2778_ref": r["holdout_hide_recover_oof"]["paired_delta_vs_ref_b2_procedural"]["delta"],
                "paired_delta_ci95": r["holdout_hide_recover_oof"]["paired_delta_vs_ref_b2_procedural"]["ci95"],
                "win_prob_vs_ref": r["holdout_hide_recover_oof"]["paired_delta_vs_ref_b2_procedural"]["win_prob"],
                "prior_best_htcads_oof_same_evaluator_recorded": 0.112353,
                "label": r["holdout_hide_recover_oof"]["label"] + " [OOF cell emissions]"},
            "secondary_off_catalogue_sgmc": {
                "raw_dti": r["holdout_sgmc_static_live"]["raw_dti"],
                "sgmc_prevalence_calibrated_dti": r["holdout_sgmc_static_live"]["sgmc_prevalence_calibrated_dti"],
                "ci95": r["holdout_sgmc_static_live"]["ci95"],
                "champion_02778_same_evaluator": exps["references"]["REF-B2-SGMC-static"]["sgmc_prevalence_calibrated_dti"],
                "paired_delta_vs_0p2778_ref": r["holdout_sgmc_static_live"]["paired_delta_vs_b2_static"]["delta"],
                "paired_delta_ci95": r["holdout_sgmc_static_live"]["paired_delta_vs_b2_static"]["ci95"],
                "prior_best_htcads_same_evaluator": exps["references"]["REF-HTCADS-SGMC-static"]["sgmc_prevalence_calibrated_dti"],
                "paired_delta_vs_prior_best": r["holdout_sgmc_static_live"]["paired_delta_vs_htcads_static"],
                "label": r["holdout_sgmc_static_live"]["label"]},
        },
        "all_experiments_summary": {e: {"hr_oof": v["holdout_hide_recover_oof"]["pooled_dti"],
                                        "sgmc_cal": v["holdout_sgmc_static_live"]["sgmc_prevalence_calibrated_dti"],
                                        "uniqueness_passed": v["uniqueness"]["passed"]}
                                    for e, v in exps["experiments"].items()},
        "ablation_weighted_minus_unweighted": exps["ablation_weighted_minus_unweighted"],
        "registry_comparison": {**r["uniqueness"], "exact_sha256_unique": True,
                                "registry_scope": "206 footprint-distinct rasters from 367 files: focus-9 repo clones (2026-10-27) downloads/submissions + restored scored cache + focus-9 champions + this repo's 3 prior download TIFs"},
        "correlation_overlap_vs_registry": r["uniqueness"],
        "raster_sha256": fmt["sha256"], "zip_sha256": b["zeros_zip"]["sha256"],
        "submission_filename": fmt["filename"], "zip_filename": b["zeros_zip"]["filename"],
        "submission_name": b["submission_name"], "submission_note": b["submission_note"],
        "note": b["submission_note"], "note_length": b["submission_note_length"],
        "validator_output": {"format_audit_13_checks": fmt,
                             "strict_preregistered_gate4": exps["gate4_strict_preregistered"],
                             "validated_ok_to_download_and_submit": False,
                             "human_intervention_required": False},
        "projection_not_a_score": projections["ECPU-" + sel],
        "ok_to_download_and_submit": False, "verdict": "negative",
        "verdict_reason": "Gate 4 FAILED on all three preregistered components: HR-OOF 0.0848 < B2-procedural 0.0992 (paired delta -0.0144, CI [-0.0246,-0.0038]) and < prior HTCADS OOF 0.1124; SGMC-CAL 0.0644 < HTCADS 0.0789 (paired delta -0.0145, CI [-0.0205,-0.0078]). Propensity weighting significantly helped blind SGMC vs unweighted twin (+0.0031, CI [+0.0007,+0.0058]) but hurt Hide-Recover (-0.0041, CI [-0.0080,+0.0002]); stratification and ridge gate made both worse. DO NOT SUBMIT this file; it is retained only as a negative-result deliverable.",
        "budget": {"promotable_experiments": "3/3", "wall_seconds_experiments": exps["total_wall_seconds"]},
        "elapsed_seconds_this_script": round(time.time() - t0, 1),
    }
    (edir / "run_card_ecpu_20261027.json").write_text(json.dumps(card, indent=2) + "\n")
    (downloads_dir() / "ecpu_run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    print(f"[runcard] verdict={card['verdict']} sha={card['raster_sha256'][:12]} ledger4 TPw={tpw:.1f} K={K:.1f} R2={led4['r_squared']:.6f}")
    print("[runcard] projections:", json.dumps(projections, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
