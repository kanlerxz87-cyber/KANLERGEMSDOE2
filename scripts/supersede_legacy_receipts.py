#!/usr/bin/env python3
"""Mark historical, detector-only approvals as superseded, preserving their measurements."""
from __future__ import annotations

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REASON = ("Superseded on 2026-10-27: the literal 3-px rule includes the registry lattice; "
          "see evidence/focus_reaudit_20261027.json. Historical flags were not a valid slot authorization.")


def load(rel):
    return json.loads((ROOT / rel).read_text())


def _json_safe(obj):
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, dict):
        return {k: _json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_json_safe(v) for v in obj]
    return obj


def write(rel, obj):
    (ROOT / rel).write_text(json.dumps(_json_safe(obj), indent=2, allow_nan=False) + "\n")


def main() -> None:
    h = load("evidence/run_card.json")
    h.setdefault("historical_detector_only_verdict", h["verdict"])
    h.update(verdict="negative", ok_to_download_and_submit=False, superseded_notice=REASON)
    h["registry_comparison"].setdefault("historical_detector_only_passed", h["registry_comparison"]["passed"])
    h["registry_comparison"]["passed"] = False
    h["registry_comparison"]["literal_lattice_overlap_3px"] = 0.9996813087586977
    if isinstance(h.get("validator_output"), dict):
        h["validator_output"]["validated_ok_to_download_and_submit"] = False
        h["validator_output"]["verdict"] = "negative"
        if "gates" in h["validator_output"]:
            h["validator_output"]["gates"]["gate_3_registry_uniqueness"] = False
        h["validator_output"]["superseded_notice"] = REASON
    write("evidence/run_card.json", h)

    k = load("evidence/kg2_run_card_20261026.json")
    k.setdefault("historical_detector_only_verdict", k["verdict"])
    k.update(verdict="negative", ok_to_submit=False, superseded_notice=REASON)
    k.setdefault("historical_submission_note", k.get("submission_note"))
    k["submission_note"] = "DO NOT SUBMIT. HOLDOUT-DTI 0.1771, 95% CI [0.1637,0.1908]; gems-segment-pooled-v1 N=60988; not replayed."
    k["submission_note_length"] = len(k["submission_note"])
    k["correlation_overlap_vs_registry"]["literal_all_entries_passed"] = False
    write("evidence/kg2_run_card_20261026.json", k)
    embedded = load("evidence/kg2_experiment_20261026.json")
    embedded["run_card"] = k
    embedded["superseded_notice"] = REASON
    write("evidence/kg2_experiment_20261026.json", embedded)

    experiments = load("evidence/htcads_experiments.json")
    experiments["reference_0p2778_benchmark"]["name"] = experiments["reference_0p2778_benchmark"]["name"].replace(
        "ORGANIZER-CONFIRMED", "UNVERIFIED USER/OWNER REPORT"
    )
    experiments["superseded_notice"] = REASON
    write("evidence/htcads_experiments.json", experiments)

    cross = load("evidence/cross_lane_72raster_audit.json")
    cross["superseded_notice"] = REASON
    lattice_by_lane = {
        "HTCADS-DualRegime-EXP-2": 0.9996813087586977,
        "KG2-MGHV-EXP-1": 0.9957507834493016,
        "KG2-FVCA-SUBMOD-EXP-2": 0.9966493506493507,
    }
    for name, frac in lattice_by_lane.items():
        row = cross["lanes"][name]
        row.setdefault("historical_detector_only_verdict", row["verdict"])
        row["verdict"] = "negative"
        row["ok_to_submit"] = False
        if "passes_72_detector_registry_70pct_gate" in row:
            row.setdefault("historical_non_lattice_detector_only_pass", row["passes_72_detector_registry_70pct_gate"])
            row["passes_72_detector_registry_70pct_gate"] = False
        row["literal_lattice_overlap_3px"] = frac
    write("evidence/cross_lane_72raster_audit.json", cross)

    legacy = load("evidence/nine_site_audit.json")
    legacy["superseded_notice"] = (
        "Historical owner/user reports, not organizer receipts. The old reciprocal fit cannot "
        "identify hidden truth or prove removed points were false positives. See focus_reaudit_20261027.json."
    )
    for row in legacy["focus_9_sites"] + legacy.get("independent_fleet_benchmarks", []):
        row["live_score_label"] = "UNVERIFIED USER/OWNER REPORT; no submission-page receipt linked to raster hash"
    legacy["forensic_02778_inversion"]["collar_zero_tp_proof"] = (
        "Not proven: dot counts and reported scores alone do not identify distance-weighted TP, FP, or hidden prevalence."
    )
    legacy["forensic_02778_inversion"]["status"] = "quarantined assumption-dependent model, not a measurement"
    write("evidence/nine_site_audit.json", legacy)

    old = load("evidence/nine_site_forensic_20261026.json")
    old["superseded_notice"] = legacy["superseded_notice"]
    write("evidence/nine_site_forensic_20261026.json", old)

    current = load("run_card.json")
    write("docs/downloads/htcads_run_card.json", current)
    report = load("docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-validation.json")
    write("evidence/validator_receipt.json", report)
    print("Historical promotion flags marked negative; measurements preserved and supersession recorded.")


if __name__ == "__main__":
    main()
