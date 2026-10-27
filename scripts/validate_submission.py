#!/usr/bin/env python3
"""Automated End-to-End Submission Gate Validator (Zero Human Intervention Required).

Validates a candidate GeoTIFF + run card across all 5 mandatory automated gates:
  Gate 1 (FORMAT & [0,1] RANGE): 13 GeoTIFF checks against sample_submission.tif, 0 NaNs across all
         12,279,160 cells, values strictly in [0.0, 1.0], 0 pixels on existing_faults.tif.
  Gate 2 (LEAKAGE CANARY): Every individual feature tested alone on spatially-blocked holdout has AUC <= 0.90.
  Gate 3 (LANE UNIQUENESS): Pre-placement surface & final dots satisfy |Spearman| < 0.90 and 3-px dot
         overlap <= 0.70 against all geological detector rasters across all 9 focus sites + scored archive
         (with space-filling uniform calibration grids evaluated via null-calibrated excess).
  Gate 4 (HOLDOUT PERFORMANCE): Beats the 0.2778 Champion benchmark on leak-free Hide-and-Recover v3.0
         (with strictly positive paired 95% CI) AND beats Champion on blind off-catalogue SGMC-CAL v3.0.
  Gate 5 (PORTAL METADATA): Non-empty unique submission name and note <= 140 characters.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir  # noqa: E402
from gems32.submission import audit_geotiff  # noqa: E402


def validate_all_gates(tif_path: Path, run_card_path: Path, ddir: Path | None = None) -> dict:
    ddir = ddir or data_dir()
    sample_tif = ddir / "sample_submission.tif"
    labels_tif = ddir / "labels.tif"
    with rasterio.open(sample_tif) as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(labels_tif) as ds:
        labels = (ds.read(1) > 0) & foot

    fmt = audit_geotiff(tif_path, foot, labels, mode="zeros", template_tif=sample_tif)
    card = json.loads(run_card_path.read_text(encoding="utf-8"))

    sha_matches = fmt["sha256"] == card["raster_sha256"]
    canary = card["leakage_canary"]
    canary_ok = bool(canary["passed"] and float(canary["max_single_feature_auc"]) <= 0.90)

    uniq = card["registry_comparison"]
    uniq_ok = bool(
        float(uniq["pre_placement_surface_max_abs_spearman"]) < 0.90
        and float(uniq["final_dots_max_abs_spearman"]) < 0.90
        and float(uniq["final_dots_max_detector_3px_overlap"]) <= 0.70
        and bool(uniq["exact_sha256_unique"])
    )

    hr = card["holdout_dti"]["primary_hide_and_recover"]
    sg = card["holdout_dti"]["secondary_off_catalogue_sgmc"]
    holdout_ok = bool(
        float(hr["pooled_dti"]) > float(hr["champion_02778_same_evaluator"])
        and float(hr["paired_delta_ci95"][0]) > 0.0
        and float(sg["sgmc_prevalence_calibrated_dti"]) > float(sg["champion_02778_same_evaluator"])
    )
    # IR-20261027-03 (shared-tool fix, 2026-10-27): when a run card declares a prior
    # same-repo holdout best, Gate 4 must ALSO beat it. Previously a candidate could
    # pass Gate 4 by beating only the 0.2778 champion while being worse than an
    # already-validated in-repo candidate. Backwards compatible: cards without
    # prior-best fields are judged exactly as before.
    prior_hr = hr.get("prior_best_htcads_oof_same_evaluator_recorded")
    if prior_hr is not None:
        holdout_ok = holdout_ok and bool(float(hr["pooled_dti"]) >= float(prior_hr))
    prior_sg = sg.get("prior_best_htcads_same_evaluator")
    if prior_sg is not None:
        paired_prior = sg.get("paired_delta_vs_prior_best") or {}
        paired_ci = paired_prior.get("ci95") if isinstance(paired_prior, dict) else None
        sg_beats_prior = float(sg["sgmc_prevalence_calibrated_dti"]) > float(prior_sg)
        if paired_ci is not None:
            sg_beats_prior = sg_beats_prior and bool(float(paired_ci[0]) > 0.0)
        holdout_ok = holdout_ok and bool(sg_beats_prior)

    note = str(card.get("submission_note", ""))
    meta_ok = bool(card.get("submission_name") and 0 < len(note) <= 140)

    gates = {
        "gate_1_format_and_range_0_1": bool(fmt["all_checks_passed"] and sha_matches),
        "gate_2_leakage_canary_le_090": canary_ok,
        "gate_3_registry_uniqueness": uniq_ok,
        "gate_4_holdout_beats_champion": holdout_ok,
        "gate_5_portal_metadata_le_140": meta_ok,
    }
    all_ok = all(gates.values())
    return {
        "validated_ok_to_download_and_submit": all_ok,
        "human_intervention_required": False,
        "verdict": "promote" if all_ok else "negative",
        "raster_filename": tif_path.name,
        "raster_sha256": fmt["sha256"],
        "gates": gates,
        "format_audit": fmt,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--run-card", type=Path, default=ROOT / "evidence" / "run_card.json")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    res = validate_all_gates(args.tif, args.run_card)
    txt = json.dumps(res, indent=2)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    print(txt)
    return 0 if res["validated_ok_to_download_and_submit"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
