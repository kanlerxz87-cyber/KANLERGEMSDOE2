#!/usr/bin/env python3
"""Publish the current negative run card from verified preflight evidence.

No model is fit and no candidate is generated. Historical results are explicitly
identified as unreplayed records, not new validation or leaderboard estimates.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from validate_submission import validate_all_gates  # noqa: E402


def save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def main() -> int:
    data = Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data"))
    pre = json.loads((ROOT / "evidence/registry_preflight_20261027.json").read_text())
    old = json.loads((ROOT / "evidence/archive/htcads_run_card_20261026.json").read_text())
    fname = old["submission_filename"]
    tif = ROOT / "docs/downloads" / fname
    val = validate_all_gates(tif, ROOT / "evidence/archive/htcads_run_card_20261026.json", data)
    if not pre.get("duplicate_forced") or val.get("ok_to_submit") is not False:
        raise SystemExit("Review requires the current verified duplicate-stop and negative selector")
    if val.get("raster_sha256") != old.get("raster_sha256"):
        raise SystemExit("Historical raster hash mismatch")
    witness = val.get("literal_lattice_witness") or {}
    if witness.get("literal_duplicate") is not True:
        raise SystemExit("Exact historical file did not reproduce the literal duplicate")
    fmt = val["format_audit"]["checks"]
    old_hr = old["holdout_dti"]["primary_hide_and_recover"]
    note = "Research only: HTC-Next stopped before placement; literal registry duplicate. DO NOT SUBMIT."
    assert len(note) <= 140
    card = {
        "schema": "gems.parallel_run_card.v2",
        "reviewed_utc": pre["generated_utc"],
        "repository": "kanlerxz87-cyber/KANLERGEMSDOE2",
        "hypothesis": "HTC-Next H1: thermal–alteration flank asymmetry in the HTCADS-K2 lane",
        "mechanism": "Compare ridge-normal K-on-Th and conductance flank contrasts with up-gradient INGENIOUS thermal indicators on gravity/magnetic structural ridges; no model fitted in this run.",
        "named_non_fault_mimic": "Alluvial-fan provenance or volcanic-contact boundaries; shallow groundwater/plumbing anomalies.",
        "holdout_dti": {
            "value": None, "evaluator_version": None, "withheld_positive_pixels": None, "ci95": None,
            "reason": "No candidate, feature canaries or holdout were run after the pre-placement duplicate proof.",
            "prior_artifact_record_not_replayed": {
                "label": "HOLDOUT-DTI",
                "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0",
                "withheld_positive_pixels": 22232,
                "value": old_hr["pooled_dti"],
                "ci95": old_hr["ci95"],
                "scope": "Historical HTC-EXP-2 report; not independently replayed here and not a leaderboard estimate.",
            },
        },
        "correlation_overlap_vs_registry": {
            "surface_rank_correlation": None,
            "surface_overlap": None,
            "reason": "No new surface was fitted; a counting proof forces the stop at the preregistered budget.",
            "witness_filename": pre["witness_filename"],
            "witness_sha256": pre["witness_sha256"],
            "witness_covered_pixels": pre["covered_pixels"],
            "witness_uncovered_pixels": pre["uncovered_pixels"],
            "budget": pre["candidate_budget"],
            "minimum_possible_overlap": pre["minimum_possible_directional_overlap"],
            "actual_historical_candidate_overlap": witness["directional_overlap"],
            "literal_duplicate": True,
            "scope": "A single pinned registry entry is a sufficient stop witness; the entire registry was not replayed.",
        },
        "raster_sha256": None,
        "new_raster_generated": False,
        "submission_name": None,
        "note": note,
        "existing_research_artifact": {
            "filename": fname,
            "path": f"docs/downloads/{fname}",
            "sha256": old["raster_sha256"],
            "new_this_session": False,
            "ok_to_download_for_research": True,
            "ok_to_submit": False,
        },
        "validator_output": {
            "new_raster": None,
            "historical_file_local_format_valid": val["local_format_valid"],
            "historical_file_no_nan_inside_footprint": fmt["footprint_all_finite"]["pass"],
            "historical_file_values_in_0_1": fmt["footprint_range_0_1"]["pass"],
            "historical_file_all_pixels_finite_in_0_1": fmt["variant_strict_whole_array_no_nan_allowed"]["pass"],
            "historical_file_crs_matches": fmt["crs_epsg_32611"]["pass"],
            "historical_file_shape_matches": fmt["shape_matches_template"]["pass"],
            "historical_file_transform_matches": fmt["geotransform_matches_template"]["pass"],
            "template_provenance": "hash-pinned owner mirror, not independently organizer-authenticated",
            "portal_acceptance": "unknown",
            "full_receipt": "evidence/validator_receipt.json",
        },
        "experiments_run": 0,
        "experiment_limit": 3,
        "weekly_slots_used": 0,
        "ok_to_submit": False,
        "verdict": "negative",
    }
    save(ROOT / "evidence/validator_receipt.json", val)
    sidecar_name = fname.removesuffix("-zeros.tif") + "-validation.json"
    save(ROOT / "docs/downloads" / sidecar_name, val)
    for src, target in (("focus9_audit_20261027.json", "focus9_audit.json"),
                        ("registry_preflight_20261027.json", "registry_preflight.json"),
                        ("input_diagnostics_20261027.json", "input_diagnostics.json")):
        save(ROOT / "docs/data" / target, json.loads((ROOT / "evidence" / src).read_text()))
    for path in (ROOT / "evidence/run_card.json", ROOT / "run_card.json", ROOT / "docs/data/run_card.json",
                 ROOT / "docs/downloads/htcads_run_card.json"):
        save(path, card)
    feed = {
        "schema": "gems.release-status.v2", "updated_utc": card["reviewed_utc"],
        "verdict": "negative", "ok_to_submit": False, "new_raster_generated": False,
        "reason": "Literal registered-lattice duplicate forced before fitting/placement; no selector approval.",
        "run_card": "run_card.json", "historical_research_file": "../downloads/" + fname,
    }
    save(ROOT / "docs/data/status_feed.json", feed)
    print(json.dumps({"verdict": card["verdict"], "ok_to_submit": False,
                      "new_raster_generated": False, "run_card": "evidence/run_card.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
