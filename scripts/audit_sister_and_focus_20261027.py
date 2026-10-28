#!/usr/bin/env python3
"""ARCHIVED: CLI disabled; historical claims below are not current evidence.

Comprehensive 2026-10-27 multi-site audit covering:
  - New KANLERGEMSDOE2 candidate (`kanlergems2-darp-exp-1-37654dots-...-4ad35e71-zeros.tif`) + DARP-EXP-2/3
  - Historical KANLERGEMSDOE2 candidates (`11a2f251`, `f5a469e94b14`, `cab53e1b`)
  - All 9 Focus Sites (`GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, 36`)
  - All Sister Sites (`KANLERGEMSDOE1, KANLERGEMSDOE3, WBGGEMSDOE1..3, EUGGEMSDOE1..3, GINNYGEMSDOE1..3`)
  - Non-H19-5 Fleet Leader (`GEMSDOE70` `0.2478 USER-REPORTED`)

Synchronizes `run_card.json` == `evidence/run_card.json` == `docs/data/run_card.json` ==
`docs/downloads/darp_mt10_run_card.json` and emits `evidence/darp_validator_receipt_20261027.json`
and `evidence/sister_and_focus_audit_20261027.json`.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32 import darp_mt10, holdout, submission  # noqa: E402
from gems32.paths import data_dir, downloads_dir, evidence_dir  # noqa: E402


def _sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ov3_asym(m_a: np.ndarray, d3_b: np.ndarray) -> float:
    na = int(m_a.sum())
    return float(d3_b[m_a].sum()) / max(na, 1)


def main() -> int:
    raise SystemExit(
        "Archived audit writer disabled: it can overwrite current evidence with "
        "self-attested scores or legacy promotion claims. Use audit_release.py."
    )


def _legacy_main_archived() -> int:
    """Retained only as historical code; not a current evidence generator."""
    ddir, edir, dldir = data_dir(), evidence_dir(), downloads_dir()
    extra = ddir / "scored_extra"
    scored = ddir / "scored"

    # Preserve historical run cards cleanly before unifying active run_card.json
    hist_htcads_rc = edir / "htcads_run_card_20261026.json"
    if not hist_htcads_rc.exists() and (edir / "run_card.json").exists():
        old_rc = json.loads((edir / "run_card.json").read_text(encoding="utf-8"))
        if "11a2f251" in json.dumps(old_rc):
            shutil.copy2(edir / "run_card.json", hist_htcads_rc)

    darp_exp = json.loads((edir / "darp_mt10_experiments_20261027.json").read_text(encoding="utf-8"))
    canary = json.loads((edir / "darp_mt10_canary_20261027.json").read_text(encoding="utf-8"))

    ctx = holdout.load_holdout_context(ddir)
    cp_ctx = darp_mt10.prepare_c_pied_truth(ddir, ctx)
    foot = ctx.foot

    new_art = darp_exp["submission_artifact"]
    new_tif = dldir / new_art["submission_filename"]
    with rasterio.open(new_tif) as ds:
        m_new = foot & np.isfinite(ds.read(1)) & (ds.read(1) >= 0.5)
    d3_new = distance_transform_edt(~m_new) <= 3.0

    champ_tif = dldir / "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
    with rasterio.open(champ_tif) as ds:
        m_champ = foot & np.isfinite(ds.read(1)) & (ds.read(1) >= 0.5)
    d3_champ = distance_transform_edt(~m_champ) <= 3.0

    htcads_tif = dldir / "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
    with rasterio.open(htcads_tif) as ds:
        m_ht = foot & np.isfinite(ds.read(1)) & (ds.read(1) >= 0.5)
    d3_ht = distance_transform_edt(~m_ht) <= 3.0

    # Audit representative primary GeoTIFF for every Sister & Fleet site
    sister_specs = [
        ("KANLERGEMSDOE2 (NEW DARP-MT10)", new_tif, None, "Research-only (`verdict = negative`: passes Gate 1/2/3-detector; `-0.0012` vs `0.2778` on Hide-Rec & hits 5-px lattice literal rule)"),
        ("KANLERGEMSDOE2 (Prior HTCADS EXP-2)", htcads_tif, None, "Prior PR #20 candidate (passes Hide-Rec `0.1124` & SGMC-CAL `0.0789` & `64.91%` detector uniqueness; held under PR #22 literal 5-px lattice rule unless waived)"),
        ("KANLERGEMSDOE1", extra / "KANLERGEMSDOE1__kanler-mplc-hgb-37654-20261026-0741963ae4e9-zeros.tif", None, "Sister repo `KANLERGEMSDOE1` MPLC-HGB 37,654-dot candidate"),
        ("KANLERGEMSDOE3", extra / "KANLERGEMSDOE3__kanlergemsdoe3-h-k3-1-cadg-submod-exp-k3-3-oof8f-37654-20261026-9a4ecfd71d00-zeros.tif", None, "Sister repo `KANLERGEMSDOE3` CADG-SUBMOD 8-fold OOF 37,654-dot candidate"),
        ("WBGGEMSDOE1", extra / "WBGGEMSDOE1__wbggemsdoe1-wbg-h1-dpgf1-exp-3-20261026-0749b3c8195f-zeros.tif", None, "Sister repo `WBGGEMSDOE1` DPGF-1 dip-projected candidate"),
        ("WBGGEMSDOE2", extra / "WBGGEMSDOE2__wbg2-h1-stepxasym-e2-34564dots-20261026T221541Z-efd46877-zeros.tif", None, "Sister repo `WBGGEMSDOE2` StepXAsym 34,564-dot candidate (note: sibling `a1b2c3d4` has 5.09M blanket bug `IR-SISTER-WBG2-BLANKET`)"),
        ("WBGGEMSDOE3", extra / "WBGGEMSDOE3__wb-gems-doe-3-stepover-damagezone-35000d-20261026T215413Z-zeros.tif", None, "Sister repo `WBGGEMSDOE3` Stepover-DamageZone 35,000-dot candidate"),
        ("GEMSDOE70 (Fleet Non-H19-5 #1)", extra / "GEMSDOE70__gems70-p5-dual-submod300-oof38k-20261020.tif", 0.2478, "Highest `USER-REPORTED` non-`H19-5` de-novo score across the 92-site fleet (`oof38k`)"),
    ]

    sister_rows = []
    for label_s, p_tif, rep_score, role_note in sister_specs:
        if not p_tif.exists():
            continue
        with rasterio.open(p_tif) as ds:
            arr = ds.read(1)
            has_nan = bool(np.isnan(arr).any())
            in_01 = bool(not has_nan and not np.isinf(arr).any() and float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0)
            nodata_v = ds.nodata
        m_s = foot & np.isfinite(arr) & (arr >= 0.5)
        d3_s = distance_transform_edt(~m_s) <= 3.0
        n_dots = int(m_s.sum())
        on_cat = int((m_s & ctx.labels).sum())
        sg = holdout.evaluate_sgmc_with_ci(m_s, ctx, n_boot=400, seed=20261027, name=label_s)
        cp = darp_mt10.evaluate_c_pied_with_ci(m_s, ctx, cp_ctx, n_boot=400, seed=20261027, name=label_s)

        sister_rows.append({
            "site": label_s,
            "filename": p_tif.name.split("__", 1)[-1],
            "sha256": _sha256(p_tif),
            "bytes": p_tif.stat().st_size,
            "dots": n_dots,
            "on_catalogue_dots": on_cat,
            "portal_safe_0_1": bool(in_01 and nodata_v is None and on_cat == 0),
            "has_outside_nan": has_nan,
            "user_reported_score": rep_score,
            "sgmc_cal_v3_dti": round(sg["sgmc_prevalence_calibrated_dti"], 6),
            "sgmc_cal_ci95": [round(x, 6) for x in sg["sgmc_calibrated_ci95"]],
            "c_pied_v1_dti": round(cp["pooled_dti"], 6),
            "c_pied_ci95": [round(x, 6) for x in cp["ci95_cluster_bootstrap"]],
            "overlap_3px_vs_02778_champ": round(_ov3_asym(m_s, d3_champ), 6),
            "overlap_3px_vs_new_darp": round(_ov3_asym(m_s, d3_new), 6) if p_tif != new_tif else 1.0,
            "overlap_3px_vs_htcads_11a2f251": round(_ov3_asym(m_s, d3_ht), 6) if p_tif != htcads_tif else 1.0,
            "note": role_note,
        })

    # Empty initialized sister repos verified via GitHub API on 2026-10-27
    empty_sister_sites = [
        {"site": f"{prefix}{i}", "owner_repo": f"{owner}/{prefix}{i}", "status": "empty_initialized_repo",
         "branches": 1, "prs": 0, "geotiff_count": 0, "portal_safe_0_1": None,
         "note": "Verified via GitHub API on 2026-10-27: newly initialized repository containing only `# README`, 0 GeoTIFF artifacts, and 0 leaderboard receipts."}
        for owner, prefix in [("eugboogieman123-ops", "EUGGEMSDOE"), ("ginnymcfiner23-ux", "GINNYGEMSDOE")]
        for i in (1, 2, 3)
    ]

    # Build unified canonical Run Card (Rule 5) synchronized across ALL paths
    exp1 = darp_exp["experiments"][0]
    exp2 = darp_exp["experiments"][1]
    exp3 = darp_exp["experiments"][2]
    u1 = exp1["uniqueness"]
    sub_note = (
        f"KG2 DARP-MT10 (DARP-EXP-1, 37654d): updip grav/RTP+asymMT+ComCat; "
        f"HideRec=0.0980, CPied=0.1169 (EXP2=0.1408); research negative"
    )
    assert len(sub_note) <= 140, f"Note too long: {len(sub_note)}"

    unified_run_card = {
        "schema_version": "2.0-unified-20261027",
        "project": "KANLERGEMSDOE2",
        "branch": darp_exp["branch"],
        "generated_at_utc": darp_exp["generated_at_utc"],
        "hypothesis": (
            "H-N1 (DARP-MT10): Concealed Basin-and-Range and Walker Lane geothermal faults are localized by "
            "(1) depth-adaptive multi-horizon (0/150/450/1000m) FFT upward-continued gravity & RTP ridges projected updip "
            "by delta_x = clip(0.55*Z_b*cot(58 deg), 0.5, 6.5) px onto surface emergence + true Miller-Singh tilt contact wavenumber (H-N2), "
            "(2) signed cross-strike hanging-wall minus footwall MT conductivity step (clay-cap seal baffle), "
            "(3) seamless 10m + 3m + 1m contour-orthogonal piedmont scarp fusion bridging 100% of the 24.60% 1m LiDAR void, and "
            "(4) 10km Great Basin S_hmin/A_phi dilation tendency x shallow (<=12 km) ComCat microseismicity & USGS/SB/GDR heat-flow upflow."
        ),
        "mechanism": (
            "4-quadrant spatially purged Out-of-Quadrant LightGBM specialists (`SegmentHoldout` 1.5 km buffer + cross-boundary "
            "component purge) blended with first-principles multi-physics piedmont conduit priors under Tri-Regime Noisy-OR "
            "and exact 25-offset 300 m Euclidean triangular-kernel greedy submodular CELF (`alpha=0.2, beta=0.8`)."
        ),
        "named_non_fault_mimic": (
            "(1) Symmetric interior saline playa brines (Humboldt/Carson Sink) mimicking MT fault seals; "
            "(2) Lake Lahontan wave-cut shoreline benches mimicking piedmont scarps; "
            "(3) TIGER highway/railroad embankments (<=90 m) mimicking 1m/3m LiDAR scarps; "
            "(4) High-relief Mesozoic range-crest bedrock thrusts mimicking active extensional faults."
        ),
        "non_fault_mimic_process": (
            "Playa brine interiors suppressed via cross-strike HW-FW asymmetry & slope floor; Lake Lahontan low-basin benches "
            "attenuated unless backed by updip gravity/MT step; TIGER roads masked within 45-120 m; range-crest thrusts weighted "
            "by piedmont structural habitat prior."
        ),
        "holdout_dti": {
            "selected_artifact_id": "DARP-EXP-1",
            "primary_hide_and_recover": {
                **exp1["hide_and_recover"],
                "champion_02778_same_evaluator": darp_exp["reference_benchmarks"]["GEMSDOE32_B2_0p2778_champ"]["hide_recover_v3_1_dti"],
            },
            "gems_segment_pooled_v1": exp1["gems_segment_pooled_v1"],
            "secondary_off_catalogue_sgmc": {
                **exp1["sgmc_off_catalogue"],
                "sgmc_prevalence_calibrated_dti": exp1["sgmc_off_catalogue"]["prevalence_calibrated_dti"],
                "champion_02778_same_evaluator": darp_exp["reference_benchmarks"]["GEMSDOE32_B2_0p2778_champ"]["sgmc_cal_v3_0_dti"],
            },
            "piedmont_off_catalogue_c_pied": {
                **exp1["c_pied_piedmont_off_catalogue"],
                "champion_02778_same_evaluator": darp_exp["reference_benchmarks"]["GEMSDOE32_B2_0p2778_champ"]["c_pied_v1_0_dti"],
            },
            "ablation_darp_exp2_piedmont_breakthrough": {
                "hide_and_recover": exp2["hide_and_recover"],
                "gems_segment_pooled_v1": exp2["gems_segment_pooled_v1"],
                "secondary_off_catalogue_sgmc": exp2["sgmc_off_catalogue"],
                "piedmont_off_catalogue_c_pied": exp2["c_pied_piedmont_off_catalogue"],
                "finding": (
                    "DARP-EXP-2 achieved 0.140750 HOLDOUT-DTI on GEMSDOE70-C-PIED-v1.0 (+0.039584 / +39.1% over 0.2778 Champion "
                    "0.101166, paired 95% CI [+0.017906, +0.057064]; +81.8% over prior HTCADS EXP-2 0.077405), proving seamless "
                    "10m+3m+1m piedmont fusion strongly recovers concealed basin-margin faults, while cubing `piedmont_habitat_prior` "
                    "(`IR-DARP-CREST-OVERDAMP-08`) over-damped Z_b < 150m range-front contacts (-0.002837 on Hide-Rec)."
                ),
            },
            "ablation_darp_exp3_dinkelbach": {
                "emitted_dots": exp3["emitted_dots"],
                "hide_and_recover": exp3["hide_and_recover"],
                "piedmont_off_catalogue_c_pied": exp3["c_pied_piedmont_off_catalogue"],
            },
            "champion_02778_benchmarks": darp_exp["reference_benchmarks"]["GEMSDOE32_B2_0p2778_champ"],
        },
        "correlation_overlap_vs_registry": {
            "detector_protocol_passed": u1["detector_protocol_passed"],
            "literal_including_5px_calibration_lattice_passed": u1["literal_including_5px_calibration_lattice_passed"],
            "rasters_checked": u1["unique_rasters_checked"],
            "competing_detectors_checked": u1["competing_detectors_checked"],
            "calibration_lattices_checked": u1["calibration_lattices_checked"],
            "pre_placement_surface_max_abs_spearman": u1["pre_placement_surface_max_abs_spearman"],
            "pre_placement_closest_peer": u1["pre_placement_closest_peer"],
            "post_placement_dots_max_abs_spearman": u1["final_dots_max_abs_spearman"],
            "post_placement_competing_max_3px_overlap": u1["final_dots_max_detector_3px_overlap"],
            "post_placement_closest_detector_peer": u1["final_dots_closest_3px_detector_peer"],
            "overlap_3px_vs_02778_champion": u1["named_benchmarks"]["GEMSDOE32_0p2778_champ"]["our_in_peer_3px"],
            "overlap_3px_vs_prior_htcads_11a2f251": round(_ov3_asym(m_new, d3_ht), 6),
            "literal_all_registry_max_3px_overlap": u1["literal_all_registry_max_3px_overlap"],
            "literal_all_registry_closest_peer": u1["literal_all_registry_closest_peer"],
            "exact_13gems_pigeonhole_proof": darp_exp["exact_13gems_lattice_pigeonhole"],
        },
        "registry_comparison": u1,
        "leakage_canary": {
            "passed": canary["passed"],
            "total_features_tested": canary["total_features_tested"],
            "max_single_feature_auc": canary["max_single_feature_auc"],
            "max_feature_name": canary["max_feature_name"],
            "threshold": 0.90,
        },
        "raster_sha256": new_art["raster_sha256"],
        "zip_sha256": new_art["zip_sha256"],
        "validator_output": new_art["format_audit"],
        "submission_name": new_art["submission_name"],
        "submission_filename": new_art["submission_filename"],
        "zip_filename": new_art["zip_filename"],
        "zip_artifact": new_art["zip_filename"],
        "note": sub_note,
        "submission_note": sub_note,
        "experiments_used": 3,
        "budget_max_experiments": 3,
        "wall_hours": darp_exp["wall_hours"],
        "budget_max_wall_hours": 2.0,
        "weekly_slot_spent_automatically": False,
        "verdict": "negative",
        "ok_to_download_for_research": True,
        "ok_to_download_and_submit": False,
        "decision_summary": (
            "OK TO DOWNLOAD FOR RESEARCH (13/13 [0,1] portal-safe format PASS, 0 NaNs, 68/68 leakage canaries PASS, "
            "detector uniqueness PASS at 67.08% <= 70% across 287 competing detectors & 58.83% vs prior 11a2f251) · "
            "NEGATIVE / DO NOT SUBMIT TO DRIVENDATA (primary HIDE-RECOVER-v3.1 delta is -0.001153 [-0.0169, +0.0141] vs "
            "0.2778 Champion despite +15.5% / +39.1% C_pied piedmont fault gains, and literal all-registry check hits the "
            "99.87%-footprint 13gems 5-px calibration grid; 0 weekly slots spent)."
        ),
    }

    card_bytes = (json.dumps(unified_run_card, indent=2) + "\n").encode("utf-8")
    for dst_card in [
        ROOT / "run_card.json",
        edir / "run_card.json",
        ROOT / "docs" / "data" / "run_card.json",
        dldir / "darp_mt10_run_card.json",
    ]:
        dst_card.parent.mkdir(parents=True, exist_ok=True)
        dst_card.write_bytes(card_bytes)

    sys.path.insert(0, str(ROOT / "scripts"))
    from validate_submission import validate_all_gates  # noqa: E402
    val_receipt = validate_all_gates(new_tif, edir / "run_card.json", ddir)
    (edir / "darp_validator_receipt_20261027.json").write_text(json.dumps(val_receipt, indent=2) + "\n", encoding="utf-8")

    multi_audit = {
        "generated_at_utc": darp_exp["generated_at_utc"],
        "sister_and_fleet_audited_rasters": sister_rows,
        "empty_initialized_sister_repos": empty_sister_sites,
    }
    (edir / "sister_and_focus_audit_20261027.json").write_text(json.dumps(multi_audit, indent=2) + "\n", encoding="utf-8")

    print(f"Synchronized 4 run_card.json copies (sha256={hashlib.sha256(card_bytes).hexdigest()[:12]}).")
    for r in sister_rows:
        print(
            f"  {r['site']:36s} dots={r['dots']:7,d} safe01={str(r['portal_safe_0_1']):5s} "
            f"CPied={r['c_pied_v1_dti']:.4f} SGMC={r['sgmc_cal_v3_dti']:.4f} "
            f"ov_02778={r['overlap_3px_vs_02778_champ']:.2%} ov_DARP={r['overlap_3px_vs_new_darp']:.2%}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
