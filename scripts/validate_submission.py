#!/usr/bin/env python3
"""Automated artifact, provenance, and selector-gate validator.

Important: this script can establish GeoTIFF/ZIP safety and whether a candidate is
eligible for a separate human-controlled slot selector. It cannot choose a live slot,
authorize an upload, log into DrivenData, or establish an organizer score.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems32.paths import data_dir  # noqa: E402
from gems32.submission import audit_geotiff, sha256_file  # noqa: E402

DEFAULT_UNIQUENESS_AUDIT = ROOT / "evidence" / "focus9_submission_audit_20261027.json"


def _audit_zip(zip_path: Path | None, tif_path: Path, expected_sha: str) -> dict:
    if zip_path is None:
        return {"present": False, "safe_single_tif_bundle": False, "reason": "No ZIP path supplied or recorded."}
    if not zip_path.is_file():
        return {"present": False, "safe_single_tif_bundle": False, "path": str(zip_path), "reason": "ZIP does not exist."}
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = zf.namelist()
            if len(names) != 1 or names[0] != tif_path.name:
                return {
                    "present": True,
                    "safe_single_tif_bundle": False,
                    "path": str(zip_path),
                    "members": names,
                    "reason": "ZIP must contain exactly the validated GeoTIFF by its basename.",
                }
            inner_sha = hashlib.sha256(zf.read(names[0])).hexdigest()
        zip_sha = sha256_file(zip_path)
        return {
            "present": True,
            "safe_single_tif_bundle": inner_sha == expected_sha,
            "path": str(zip_path),
            "filename": zip_path.name,
            "sha256": zip_sha,
            "inner_filename": names[0],
            "inner_sha256": inner_sha,
            "inner_hash_matches_tif": inner_sha == expected_sha,
            "members": names,
        }
    except (OSError, zipfile.BadZipFile) as exc:
        return {"present": True, "safe_single_tif_bundle": False, "path": str(zip_path), "reason": str(exc)}


def validate_all_gates(
    tif_path: Path,
    run_card_path: Path,
    ddir: Path | None = None,
    zip_path: Path | None = None,
    uniqueness_audit_path: Path | None = None,
) -> dict:
    ddir = ddir or data_dir()
    sample_tif = ddir / "sample_submission.tif"
    labels_tif = ddir / "labels.tif"
    if not sample_tif.is_file() or not labels_tif.is_file():
        raise FileNotFoundError("Restore core competition data first: python scripts/restore_data.py --group core")
    with rasterio.open(sample_tif) as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(labels_tif) as ds:
        labels = (ds.read(1) > 0) & foot

    fmt = audit_geotiff(tif_path, foot, labels, mode="zeros", template_tif=sample_tif)
    card = json.loads(run_card_path.read_text(encoding="utf-8"))
    if fmt["sha256"] != card.get("raster_sha256"):
        raise ValueError("Candidate TIFF SHA-256 does not match the frozen run card")

    if zip_path is None:
        zip_name = card.get("zip_filename") or card.get("zip_artifact")
        if zip_name:
            zip_path = tif_path.parent / zip_name
    zip_audit = _audit_zip(zip_path, tif_path, fmt["sha256"])
    if zip_audit.get("present") and card.get("zip_sha256"):
        zip_audit["zip_hash_matches_run_card"] = zip_audit.get("sha256") == card["zip_sha256"]

    canary = card.get("leakage_canary", {})
    canary_ok = bool(
        canary.get("passed") is True
        and canary.get("max_single_feature_auc") is not None
        and float(canary["max_single_feature_auc"]) <= 0.90
    )

    uniq = card.get("correlation_overlap_vs_registry") or card.get("registry_comparison", {})
    recorded_surface_ok = bool(
        float(uniq.get("pre_placement_surface_max_abs_spearman", 1.0)) <= 0.90
        and bool(uniq.get("exact_sha256_unique", False))
    )
    recorded_dots_ok = bool(
        float(uniq.get("final_dots_max_abs_spearman", 1.0)) <= 0.90
        and float(uniq.get("final_dots_max_detector_3px_overlap", 1.0)) <= 0.70
    )

    audit_path = uniqueness_audit_path or DEFAULT_UNIQUENESS_AUDIT
    focus9_audit = {}
    focus9_ok = False
    if audit_path.is_file():
        focus9_audit = json.loads(audit_path.read_text(encoding="utf-8"))
        candidate_audit = focus9_audit.get("candidate", {})
        focus9_ok = bool(
            candidate_audit.get("sha256") == fmt["sha256"]
            and candidate_audit.get("focus9_uniqueness_pass") is True
            and all(focus9_audit.get("gates", {}).values())
        )
    unique_ok = bool(recorded_surface_ok and recorded_dots_ok and focus9_ok)

    holdout_ok = False
    hr = card.get("holdout_dti", {}).get("primary_hide_and_recover", {})
    sg = card.get("holdout_dti", {}).get("secondary_off_catalogue_sgmc", {})
    if hr and sg:
        holdout_ok = bool(
            float(hr.get("pooled_dti", 0.0)) > float(hr.get("champion_02778_same_evaluator", float("inf")))
            and float(hr.get("paired_delta_ci95", [float("-inf")])[0]) > 0.0
            and float(sg.get("sgmc_prevalence_calibrated_dti", 0.0)) > float(sg.get("champion_02778_same_evaluator", float("inf")))
            and float(sg.get("paired_delta_ci95", [float("-inf")])[0]) > 0.0
        )

    note = str(card.get("submission_note", card.get("note", ""))).strip()
    metadata_ok = bool(card.get("submission_name") and 0 < len(note) <= 140)
    format_safe = bool(fmt["all_checks_passed"])
    bundle_ok = bool(zip_audit.get("safe_single_tif_bundle") and zip_audit.get("zip_hash_matches_run_card", True))
    download_ok = bool(format_safe and unique_ok and bundle_ok)
    selector_eligible = bool(download_ok and canary_ok and holdout_ok and metadata_ok)

    gates = {
        "format_grid_and_full_array_range_0_1": format_safe,
        "single_tif_zip_bundle_matches_tif": bundle_ok,
        "leakage_canary_recorded_auc_le_0_90": canary_ok,
        "registry_uniqueness_recorded_plus_focus9_recomputed": unique_ok,
        "holdout_dti_recorded_positive_paired_ci": holdout_ok,
        "submission_name_and_note_le_140_chars": metadata_ok,
    }
    verdict = "promote" if selector_eligible else "negative"
    return {
        "schema": "kanlergemsdoe2.submission_validation.v2",
        "candidate_filename": tif_path.name,
        "candidate_sha256": fmt["sha256"],
        "status": {
            "format_validation": "FORMAT_SAFE" if format_safe else "FORMAT_UNSAFE",
            "download": "OK_TO_DOWNLOAD" if download_ok else "DO_NOT_DOWNLOAD",
            "selector_eligibility": "ELIGIBLE" if selector_eligible else "NOT_ELIGIBLE",
            "submission_authorization": "NOT_AUTHORIZED",
            "live_slot_selected": False,
            "upload_performed": False,
            "organizer_receipt_present": False,
        },
        "offline_validation_automated": True,
        "live_submission_requires_separate_user_action": True,
        "model_run_reproduced_in_this_validation": False,
        "model_run_branch_recorded": card.get("branch"),
        "verdict": verdict,
        "verdict_scope": "Scientific promotion to a separate live-slot selector only; it is not upload authorization.",
        "gates": gates,
        "format_audit": fmt,
        "zip_audit": zip_audit,
        "uniqueness_evidence": {
            "historical_full_registry_recorded": {
                "preplacement_surface_max_abs_spearman": uniq.get("pre_placement_surface_max_abs_spearman"),
                "final_dots_max_abs_spearman": uniq.get("final_dots_max_abs_spearman"),
                "final_dots_max_detector_3px_overlap": uniq.get("final_dots_max_detector_3px_overlap"),
                "rasters_checked": uniq.get("unique_rasters_checked"),
                "status": "RECORDED_IN_FROZEN_RUN_CARD_NOT_RECOMPUTED_HERE",
            },
            "focus9_current_audit_path": str(audit_path.relative_to(ROOT)) if audit_path.is_relative_to(ROOT) else str(audit_path),
            "focus9_gate_pass": focus9_ok,
        },
        "holdout_evidence": {
            "hide_and_recover": hr,
            "sgmc_off_catalogue": sg,
            "status": "RECORDED_IN_FROZEN_RUN_CARD_NOT_RERUN_HERE",
        },
        "score_provenance": {
            "historical_0_2778": "USER/OWNER-REPORTED UNVERIFIED; no organizer receipt stored",
            "candidate_live_score": None,
            "note": "HOLDOUT-DTI is not a live leaderboard score or score projection.",
        },
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--run-card", type=Path, default=ROOT / "evidence" / "run_card.json")
    ap.add_argument("--zip", type=Path, default=None)
    ap.add_argument("--uniqueness-audit", type=Path, default=DEFAULT_UNIQUENESS_AUDIT)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()

    res = validate_all_gates(args.tif, args.run_card, zip_path=args.zip, uniqueness_audit_path=args.uniqueness_audit)
    txt = json.dumps(res, indent=2, allow_nan=False)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(txt + "\n", encoding="utf-8")
    print(txt)
    return 0 if all(res["gates"].values()) and res["status"]["selector_eligibility"] == "ELIGIBLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
