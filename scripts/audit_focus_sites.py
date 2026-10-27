#!/usr/bin/env python3
"""Build a conservative, provenance-first audit of the nine focus-site rasters.

This replaces the former forensic script, which incorrectly labeled owner/mirror
scores organizer-confirmed and over-interpreted a three-point score/dot-count fit.
This entrypoint is deliberately not an experiment runner.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from audit_focus9_submission import REGISTRY, run as audit_candidate  # noqa: E402


def main() -> int:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    detailed_path = ROOT / "evidence" / "focus9_submission_audit_20261027.json"
    detailed = audit_candidate(
        ROOT / "docs" / "downloads" / "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif",
        REGISTRY,
        ROOT / ".cache" / "gems_data" / "focus9",
        detailed_path,
    )
    # File sizes are display metadata, not identifiers; the pinned SHA-256 is the
    # source identity. Make the reproducible size explicit in the compact summary.
    for site in detailed["focus_sites"]:
        cached = ROOT / ".cache" / "gems_data" / "focus9" / f"{site['site']}__{Path(site['source_file']).name}"
        site["source_file_bytes"] = cached.stat().st_size
    run_card = json.loads((ROOT / "evidence" / "run_card.json").read_text(encoding="utf-8"))
    primary = run_card["holdout_dti"]["primary_hide_and_recover"]
    summary = {
        "schema": "kanlergemsdoe2.nine_site_audit.v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "score_provenance": {
            "status": "USER_OR_OWNER_REPORTED_UNVERIFIED",
            "organizer_receipt_present": False,
            "definition": "The historical values below were supplied by the user and appear in owner-controlled mirrors. They are not verified by a DrivenData submission receipt or authenticated leaderboard snapshot.",
        },
        "source_scope": {
            "registry_file": "registry/focus9_site_registry.json",
            "pinned_owner_mirror_tifs": len(detailed["focus_sites"]),
            "byte_identity": "Each downloaded TIFF SHA-256 was verified against the tracked registry at its pinned Git commit.",
            "limitation": "A GitHub mirror is not an organizer-controlled score receipt or an authoritative current leaderboard feed.",
        },
        "candidate": {
            "file": detailed["candidate"]["filename"],
            "sha256": detailed["candidate"]["sha256"],
            "format": detailed["candidate"]["format"],
            "holdout_dti": {
                **primary,
                "label": primary["label"],
                "status": "RECORDED_IN_FROZEN_RUN_CARD; not rerun in this audit",
                "source_run_card_branch": run_card["branch"],
            },
            "uniqueness": detailed["candidate"]["focus9_final_dots_check"],
            "historical_full_registry_gate": {
                "preplacement_surface_max_abs_spearman": run_card["registry_comparison"]["pre_placement_surface_max_abs_spearman"],
                "final_dot_max_abs_spearman": run_card["registry_comparison"]["final_dots_max_abs_spearman"],
                "final_dot_max_3px_overlap": run_card["registry_comparison"]["final_dots_max_detector_3px_overlap"],
                "rasters_checked": run_card["registry_comparison"]["unique_rasters_checked"],
                "status": "RECORDED_IN_FROZEN_RUN_CARD; not independently recomputed here",
            },
            "authorization": {
                "format_safe": detailed["candidate"]["format"]["format_safe"],
                "eligible_for_selector": detailed["candidate"]["focus9_uniqueness_pass"],
                "authorized_to_submit": False,
                "live_slot_selected": False,
                "organizer_receipt_present": False,
            },
        },
        "focus_9_sites": detailed["focus_sites"],
        "exact_duplicate_pairs_among_focus_site_top_tifs": detailed["exact_duplicate_pairs_among_focus_site_top_tifs"],
        "gemSdoe32_analysis": {
            "reported_score": 0.2778,
            "score_label": "USER/OWNER-REPORTED UNVERIFIED; not organizer-confirmed",
            "source_file": "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
            "format_safe_as_stored": next(s["portal_range_0_1_safe_as_stored"] for s in detailed["focus_sites"] if s["site"] == "GEMSDOE32"),
            "positive_pixels_in_template_footprint": next(s["positive_dots_in_footprint"] for s in detailed["focus_sites"] if s["site"] == "GEMSDOE32"),
            "scientific_interpretation": "The value cannot be reconstructed from the TIFF or mirrored files. Given a 300 m neighborhood-overlap objective and the officially documented Tversky loss weights (alpha=0.2 for false positives, beta=0.8 for false negatives), spacing and pruning can improve a candidate by reducing redundant/false-positive mass while preserving covered fault neighborhoods. That is a plausible mechanism, not evidence that the removed collar dots were all false positives or that the hidden score is caused by one operation.",
            "limits": [
                "No organizer receipt was checked or stored.",
                "The old three-point linear inversion is retracted: dot count and score do not identify weighted TP, hidden-set size, or whether removed pixels hit true faults.",
                "Holdout results produced under static catalogue-distance masks can self-censor withheld faults; do not use those legacy per-site values as calibrated live-score proxies.",
            ],
        },
        "retractions_and_irregularities": [
            "The former file labeled historical site scores ORGANIZER-CONFIRMED without a verified organizer receipt; all such labels have been removed.",
            "The former 3-point R-squared fit was used to claim a hidden truth-set size and zero true positives among pruned catalogue-collar dots. Those are not identifiable from the available points; the inference is withdrawn.",
            "Prior claims of fleet totals, leaderboard rank, causal submission lineage, and projected DTI were not supported by a receipt or a reproducible official source and are not carried forward.",
            "The candidate TIFF and frozen holdout run card were produced on a prior Arena branch; this audit verifies the TIFF hash and format on the current branch but does not reproduce the model run or recover the missing pre-placement surface.",
        ],
        "detailed_receipt": "evidence/focus9_submission_audit_20261027.json",
    }
    out = ROOT / "evidence" / "nine_site_audit.json"
    out.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"[audit_focus_sites] Wrote {out}; no model experiment was run.")
    print(f"[audit_focus_sites] Historical scores are {summary['score_provenance']['status']}.")
    return 0 if detailed["candidate"]["focus9_uniqueness_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
