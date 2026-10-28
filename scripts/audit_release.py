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
    dslup_archive = json.loads((ROOT / "evidence/dslup_unique_slot_run_card.json").read_text())
    dslup = next(r for r in candidates if r["sha256"] == dslup_archive["raster_sha256"]
                 and r["file"] == dslup_archive["submission_filename"])
    pr34 = next(r for r in candidates if r["file"] == "kanlergemsdoe2-unique-hypothesis1-binary-20261027.tif")
    pr36 = next(r for r in candidates if r["file"] == "36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros.tif")
    card = {
        "schema": "gems.parallel-run-card.v2",
        "generated_utc": record["generated_utc"],
        "hypothesis": "H-K1 HTCADS frozen lane; proposed height-persistent cross-gradient ablation is not yet registered or fitted",
        "mechanism": "Compare potential-field gradient orientation and displacement across continuation heights with separate hydrothermal evidence; proposed, not fitted.",
        "named_non_fault_mimic": "Unfaulted lithologic contacts and survey leveling seams",
        "holdout_dti": None,
        "holdout_ci95": None,
        "holdout_status": "Not measured in this session: stopped before fit. Prior results are historical, not replayed.",
        "correlation_overlap_vs_registry": {
            "surface_pre_placement": None,
            "surface_status": "No new surface was built or compared",
            "prior_final_dots_spearman_vs_witness": prior["witness_final_dots_spearman"],
            "prior_final_dots_overlap_vs_witness": prior["witness_overlap_fraction"],
            "prior_dslup_final_dots_spearman_vs_witness": dslup["witness_final_dots_spearman"],
            "prior_dslup_final_dots_overlap_vs_witness": dslup["witness_overlap_fraction"],
            "witness_sha256": WITNESS_SHA,
            "unavoidable_overlap_at_registered_budget": budget["minimum_directional_overlap"],
            "complete_registry_checked": False,
        },
        "raster_sha256": None,
        "validator_output": {
            "new_raster": "not produced",
            "prior_raster_exact_byte_audit": prior,
            "prior_dslup_exact_byte_audit": dslup,
            "parallel_pr34_exact_byte_audit": pr34,
            "parallel_pr36_exact_byte_audit": pr36,
            "parallel_pr36_policy_stop": "15,000-dot budget and intentional lattice-gap placement violate the frozen lane; no holdout or full-registry clearance.",
            "note": "All prior and parallel rasters are research artifacts only; range/grid checks are not portal acceptance.",
        },
        "submission_name": None,
        "note": "No new candidate; literal registry duplicate stop. Research only; do not submit.",
        "experiments_run": 0,
        "maximum_experiments": 3,
        "weekly_slots_spent_this_session": 0,
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
