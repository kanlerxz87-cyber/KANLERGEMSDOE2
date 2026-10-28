#!/usr/bin/env python3
"""Recompute the literal registry stop and nine-site artifact comparison.

Reads hash-pinned owner mirrors from the ignored data cache. Does not fit a
model, change predictions, contact DrivenData, or authorize a submission.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.release_audit import (  # noqa: E402
    WITNESS_SHA, _circle3, _grid, assess_file, forced_budget_result, load_reference,
)
from gems.validator import sha256_file  # noqa: E402
from gems32.paths import data_dir  # noqa: E402


def audit_focus(ref: dict, data: Path) -> tuple[list[dict], dict]:
    manifest = json.loads((ROOT / "registry/focus_sites_20261027.json").read_text())
    entries, masks = [], []
    for row in manifest["sites"]:
        p = data / "focus_20261027" / (row["site"] + "__" + Path(row["path"]).name)
        if not p.is_file() or sha256_file(p) != row["sha256"]:
            raise ValueError(f"Missing or hash-mismatched nine-site file: {row['site']}")
        with rasterio.open(p) as ds:
            if _grid(ds) != ref["grid"] or ds.count != 1:
                raise ValueError(f"Grid/bands disagree for {row['site']}")
            a = ds.read(1)
        mask = ref["foot"] & np.isfinite(a) & (a > 0)
        if not mask.any():
            raise ValueError(f"Empty historical raster: {row['site']}")
        item = {
            **row,
            "score_evidence_class": "USER/OWNER-REPORTED; not an organizer receipt",
            "positive_pixels": int(mask.sum()),
            "finite_0_1_inside_footprint": bool(
                np.isfinite(a[ref["foot"]]).all()
                and ((a[ref["foot"]] >= 0) & (a[ref["foot"]] <= 1)).all()
            ),
            "strict_whole_array_finite_0_1": bool(
                np.isfinite(a).all() and ((a >= 0) & (a <= 1)).all()
            ),
            "outside_footprint_all_nan": bool(np.isnan(a[~ref["foot"]]).all()),
            "page_download_url": f"https://{row['repository'].split('/')[0]}.github.io/{row['site']}/{row['path']}",
            "pinned_download_url": f"https://github.com/{row['repository']}/raw/{row['ref']}/{row['path']}",
            "pinned_source_url": f"https://github.com/{row['repository']}/blob/{row['ref']}/{row['path']}",
        }
        entries.append(item)
        masks.append(mask)
    # A single dilated reference suffices for every candidate comparison.
    overlaps = [[None] * len(entries) for _ in entries]
    xors = [[None] * len(entries) for _ in entries]
    for j, reference_mask in enumerate(masks):
        covered = binary_dilation(reference_mask, structure=_circle3())
        for i, candidate in enumerate(masks):
            if i != j:
                overlaps[i][j] = float((candidate & covered).sum() / candidate.sum())
                xors[i][j] = int(np.logical_xor(candidate, reference_mask).sum())
    for i, row in enumerate(entries):
        closest = max((j for j in range(len(entries)) if j != i), key=lambda j: overlaps[i][j])
        row["nearest_focus_site"] = entries[closest]["site"]
        row["max_directional_focus_overlap_within_3px"] = overlaps[i][closest]
        row["duplicate_within_focus_nine"] = overlaps[i][closest] > 0.70
        row["exact_pixel_duplicate_sites"] = [entries[j]["site"] for j in range(len(entries)) if j != i and xors[i][j] == 0]
        row["all_directional_overlaps"] = {
            entries[j]["site"]: overlaps[i][j] for j in range(len(entries)) if j != i
        }
    by_site = {row["site"]: masks[i] for i, row in enumerate(entries)}
    dcat = distance_transform_edt(~ref["catalogue"])
    b2_from_25 = by_site["GEMSDOE25"] & (dcat > 2.0)
    forensic = {
        "g32_b2_vs_g25_d28_filtered_by_distance_gt_2px_xor": int(
            np.logical_xor(by_site["GEMSDOE32"], b2_from_25).sum()
        ),
        "g25_to_g32_removed_pixels": int((by_site["GEMSDOE25"] & ~by_site["GEMSDOE32"]).sum()),
        "g32_not_in_g36_pixels": int((by_site["GEMSDOE32"] & ~by_site["GEMSDOE36"]).sum()),
        "g36_extra_pixels_over_g32": int((by_site["GEMSDOE36"] & ~by_site["GEMSDOE32"]).sum()),
        "caveat": "Geometry and user-reported scores are observable; hidden-truth contributions and causal mechanisms are not.",
    }
    return entries, forensic


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/release_audit_20261027.json")
    ap.add_argument("--card-out", type=Path, default=ROOT / "evidence/current_run_card.json")
    ap.add_argument("--data-dir", type=Path, default=None)
    args = ap.parse_args()
    data = args.data_dir or data_dir()
    ref = load_reference(ROOT, data)
    budget = forced_budget_result(ref, 37654)
    old = json.loads((ROOT / "evidence/run_card.json").read_text())
    paths = sorted((ROOT / "docs/downloads").glob("*.tif"))
    candidates = [assess_file(p, ref) for p in paths]
    focus, forensic = audit_focus(ref, data)
    record = {
        "schema": "gems.release-integrity-audit.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Fresh exact-byte and focus-nine comparison. The complete live registry and prior surface were not replayed.",
        "source_authentication": "Pinned owner mirrors; hashes prove byte identity, not organizer origin.",
        "preflight": budget,
        "prior_candidate": next(r for r in candidates if r["sha256"] == old["raster_sha256"]),
        "all_local_candidate_artifacts": candidates,
        "focus_nine": focus,
        "focus_lineage_geometry": forensic,
        "historical_holdout_not_replayed": {
            "source": "evidence/run_card.json",
            "label": "HOLDOUT-DTI",
            "evaluator_version": "GEMSDOE32-HIDE-RECOVER-v3.0",
            "withheld_positive_occurrences": 22232,
            "dti": old["holdout_dti"]["primary_hide_and_recover"]["pooled_dti"],
            "ci95": old["holdout_dti"]["primary_hide_and_recover"]["ci95"],
            "warning": "Prior-session receipt only; unavailable OOF/cache replay and prior registry exception preclude promotion.",
        },
        "surface_before_placement": {"status": "not replayed", "value": None},
        "new_geological_experiments": 0,
        "new_submissions": 0,
        "new_geotiff_created": False,
        "verdict": "negative",
        "ok_to_submit": False,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(record, indent=2, allow_nan=False) + "\n")
    prior = record["prior_candidate"]
    top_focus = max(focus, key=lambda row: float(row["owner_reported_score"]))
    historical = record["historical_holdout_not_replayed"]
    card = {
        "schema": "gems.parallel-run-card.v3",
        "review_date_utc": record["generated_utc"][:10],
        "generated_utc": record["generated_utc"],
        "assigned_preregistered_lane": "HTCADS-K2",
        "hypothesis": "R1: thermal-path direction-uncertainty ensemble; research hypothesis only, not preregistered for this run and not evaluated.",
        "mechanism": "Propagate independent 2 m probe and well/spring thermal evidence along a fixed family of terrain-elevation-gradient perturbations, then require convergence on independent structural ridges. The terrain gradient is only a proxy; no measured groundwater hydraulic head is used.",
        "named_non_fault_mimic": "Shallow groundwater flow or irrigation can create terrain-following thermal anomalies without geothermal faults.",
        "code_review_corrections": [
            {
                "feature_index": 28,
                "previous_label_in_source_and_historical_receipts": "anderson_slip_tendency",
                "corrected_shared_feature_label": "strike_alignment_fixed_62deg",
                "actual_operation": "cos(dom_strike_fp - 62 degrees)^2; fixed-axis axial strike alignment only",
                "uses_stress_tensor_fault_normal_friction_or_slip_model": False,
                "feature_values_changed": False,
            },
            {
                "thermal_direction": "smoothed detrended terrain-elevation gradient proxy",
                "measured_groundwater_hydraulic_head_used": False,
                "interpretation": "Do not call this measured hydraulic gradient or groundwater-flow vector.",
            },
        ],
        "hard_stop": {
            "status": "STOP_BEFORE_FIT_OR_PLACEMENT",
            "basis": "Frozen literal any-registry 3-pixel overlap rule",
            "candidate_dot_budget": budget["candidate_dot_budget"],
            "minimum_overlapping_dots": budget["minimum_overlapping_dots"],
            "minimum_directional_overlap": budget["minimum_directional_overlap"],
            "maximum_allowed_overlap": budget["limit"],
            "witness_file": budget["witness_filename"],
            "witness_sha256": WITNESS_SHA,
            "scope": budget["scope"],
        },
        "current_holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator": None,
            "withheld_positive_n": None,
            "pooled_dti": None,
            "ci95": None,
            "status": "NOT MEASURED: hard stop preceded fitting and holdout evaluation.",
        },
        "prior_holdout_not_replayed": {
            "label": historical["label"],
            "evidence_class": "HISTORICAL PRIOR-SESSION RECEIPT; not replayed and not a current score",
            "evaluator": historical["evaluator_version"],
            "withheld_positive_n": historical["withheld_positive_occurrences"],
            "pooled_dti": historical["dti"],
            "ci95": historical["ci95"],
            "promotion_use": False,
        },
        "correlation_overlap_vs_registry": {
            "surface_pre_placement": None,
            "surface_status": "No new continuous surface was built or compared.",
            "prior_final_dots_spearman_vs_registered_witness": prior["witness_final_dots_spearman"],
            "prior_final_dots_directional_overlap_within_3px_vs_witness": prior["witness_overlap_fraction"],
            "prior_final_dot_count": prior["inside_positive_pixels"],
            "complete_current_registry_checked": False,
            "all_registry_rank_correlation_and_overlap_gate": "NOT RUN; only the registered witness and separately audited nine focus-site files are in the current committed comparison.",
        },
        "new_raster_created": False,
        "raster_sha256": None,
        "validator_output": {
            "new_raster": "NOT PRODUCED; no current candidate to validate.",
            "prior_raster_exact_byte_audit": prior,
            "interpretation": "The prior raster is a research artifact only; range/grid checks are not portal acceptance.",
        },
        "submission_name": None,
        "note": "No candidate; literal registry 3-px gate forces duplicate at 37,654 dots. Research only; do not submit.",
        "note_characters": len("No candidate; literal registry 3-px gate forces duplicate at 37,654 dots. Research only; do not submit."),
        "submission_note": "No candidate; literal registry 3-px gate forces duplicate at 37,654 dots. Research only; do not submit.",
        "submission_note_characters": len("No candidate; literal registry 3-px gate forces duplicate at 37,654 dots. Research only; do not submit."),
        "experiments_run_in_this_review": 0,
        "historical_registered_htcads_experiment_arms": 3,
        "additional_experiments_authorized": 0,
        "weekly_slots_spent_this_review": 0,
        "organizer_confirmed_score": None,
        "best_focus_site_score_in_dated_records": {
            "site": top_focus["site"],
            "value": top_focus["owner_reported_score"],
            "evidence_class": top_focus["score_evidence_class"],
            "not_a_new_score_or_projection": True,
        },
        "ok_to_submit": False,
        "verdict": "negative",
    }
    args.card_out.parent.mkdir(parents=True, exist_ok=True)
    args.card_out.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"output": str(args.out), "preflight": budget,
                      "prior_candidate_overlap": record["prior_candidate"]["witness_overlap_fraction"],
                      "focus_sites_audited": len(focus), "ok_to_submit": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
