#!/usr/bin/env python3
"""Build a single honest negative run card from the existing-file re-audit.

No new raster, model experiment, or organizer submission is created. The
historical holdout/canary are explicitly recorded, not independently replayed.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import footprint  # noqa: E402
from gems.validator import sha256_file  # noqa: E402


def main() -> None:
    prior = json.loads((ROOT / "evidence/run_card.json").read_text())
    audit = json.loads((ROOT / "evidence/focus_reaudit_20261027.json").read_text())
    filename = prior["submission_filename"]
    candidates = [r for r in audit["previous_local_candidates"] if r["file"] == filename]
    if len(candidates) != 1:
        raise SystemExit("Expected exactly one historical candidate in re-audit")
    candidate = candidates[0]
    path = ROOT / "docs/downloads" / filename
    actual_sha = sha256_file(path)
    if actual_sha != candidate["file_audit"]["sha256"] or actual_sha != prior["raster_sha256"]:
        raise SystemExit("Candidate bytes do not match historical and re-audit hashes")
    fp = footprint.load_footprint()
    with rasterio.open(path) as ds:
        arr = ds.read(1)
        shape_ok = ds.shape == (footprint.HEIGHT, footprint.WIDTH)
        crs_ok = ds.crs == rasterio.crs.CRS.from_string(footprint.CRS)
        transform_ok = ds.transform == footprint.TRANSFORM
        single_band, dtype = ds.count == 1, ds.dtypes[0]
    inside = arr[fp]
    labels_path = ROOT / "data/labels.tif"
    on_catalogue = None
    if labels_path.is_file():
        with rasterio.open(labels_path) as ds:
            if (ds.shape, ds.crs, ds.transform) != ((footprint.HEIGHT, footprint.WIDTH), rasterio.crs.CRS.from_string(footprint.CRS), footprint.TRANSFORM):
                raise SystemExit("Restored labels grid mismatch")
            labels = ds.read(1)
        on_catalogue = int((fp & np.isfinite(labels) & (labels > 0) & (arr > 0)).sum())
    h = prior["holdout_dti"]["primary_hide_and_recover"]
    note = "HTCADS EXP-2: existing research raster; literal registry duplicate. DO NOT SUBMIT."
    if len(note) > 140:
        raise SystemExit("Note exceeds 140 characters")
    overlap = candidate["lattice_overlap_fraction"]
    if overlap is None or overlap <= 0.70:
        raise SystemExit("Re-audit does not establish the expected hard stop")
    prior_rho = prior["registry_comparison"].get("pre_placement_surface_max_abs_spearman")
    card = {
        "schema": "kanlergems2.parallel-run-card.v3",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lane": "HTCADS-K2: registry/preregistration_htcads.json",
        "hypothesis": "Fault and geothermal conduit structure may be identified by corroborated potential-field, hydrothermal, and topographic signals near, but not copied from, known faults.",
        "mechanism": "Re-audit of the prior HTCADS-DualRegime EXP-2 artifact, combining subsurface, thermal, LiDAR and visible-fault context with sparse 300 m allocation. No new model was trained.",
        "named_non_fault_mimic": "Lake Lahontan shorelines and alluvial thermal outflow can mimic scarps and hydrothermal anomalies.",
        "holdout_dti": {
            "label": "HOLDOUT-DTI", "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0",
            "n_withheld_positive_pixels": 22232, "dti": h["pooled_dti"], "ci95": h["ci95"],
            "source": "evidence/run_card.json; prior-session result, not independently replayed",
            "replayed_this_session": False,
            "is_leaderboard_prediction": False,
        },
        "leakage_canary": {
            "source": "evidence/leakage_canary.json; prior-session result, not independently replayed",
            "replayed_this_session": False,
            "prior_reported_features": prior["leakage_canary"]["total_features_tested"],
            "prior_reported_worst_auc": prior["leakage_canary"]["max_single_feature_auc"],
        },
        "correlation_overlap_vs_registry": {
            "pre_placement_surface_max_abs_spearman_prior_report": prior_rho,
            "pre_placement_surface_replayed": False,
            "final_3px_lattice_overlap_fraction": overlap,
            "final_3px_lattice_overlap_pixels": candidate["lattice_overlap_pixels"],
            "lattice_positive_pixels": audit["registry_lattice"]["positive_pixels"],
            "candidate_positive_pixels": candidate["file_audit"]["positive_pixels_inside"],
            "focus_sites_compared": len(candidate["focus_comparisons"]),
            "max_focus_site_3px_overlap": max(x["fraction_candidate_dots_within_3px"] for x in candidate["focus_comparisons"]),
            "all_registry_entries_replayed": False,
            "duplicate_stop_triggered": True,
            "evidence": "evidence/focus_reaudit_20261027.json",
        },
        "raster_sha256": actual_sha,
        "validator_output": {
            "single_band": single_band, "dtype": dtype, "crs_match_pinned_mirror": crs_ok,
            "shape_match_pinned_mirror": shape_ok, "transform_match_pinned_mirror": transform_ok,
            "nan_inside_footprint": int(np.isnan(inside).sum()),
            "nonfinite_inside_footprint": int((~np.isfinite(inside)).sum()),
            "all_cells_finite": bool(np.isfinite(arr).all()),
            "all_cells_in_0_1": bool(np.isfinite(arr).all() and ((arr >= 0) & (arr <= 1)).all()),
            "minimum": float(arr.min()), "maximum": float(arr.max()),
            "positive_on_mirrored_catalogue_pixels": on_catalogue,
            "scope": "Local preflight only; official source identity and portal acceptance are not verified.",
        },
        "submission_name": filename,
        "note": note,
        "note_length": len(note),
        "new_experiments_this_session": 0,
        "budget_max_experiments": 3,
        "new_raster_generated_this_session": False,
        "submission_slots_used": 0,
        "estimated_organizer_score": None,
        "organizer_score_reason": "No organizer receipt or validated model linking this artifact to the private test score.",
        "quota_status": "unknown; account submissions page requires login",
        "ok_to_submit": False,
        "verdict": "negative",
    }
    for out in (ROOT / "run_card.json", ROOT / "docs/data/run_card.json"):
        out.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"run_card": "run_card.json", "raster_sha256": actual_sha,
                      "lattice_overlap": overlap, "verdict": card["verdict"]}, indent=2))


if __name__ == "__main__":
    main()
