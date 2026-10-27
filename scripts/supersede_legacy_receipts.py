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

    # These additional historical receipts can be present after concurrent main updates.
    table_path = ROOT / "evidence/submission_table_20261027.json"
    if table_path.exists():
        table = load("evidence/submission_table_20261027.json")
        table["superseded_notice"] = REASON
        old_candidate = table.pop("promoted", table.get("historical_candidate", {}))
        old_candidate["verdict"] = "negative"
        old_candidate["ok_to_submit"] = False
        old_candidate["historical_lattice_note"] = old_candidate.get("historical_lattice_note", old_candidate.get("lattice_overlap_note"))
        old_candidate["lattice_overlap_note"] = "99.968% overlap triggers the literal any-registry stop; no control exemption applies."
        if "projection" in old_candidate:
            old_candidate["historical_quarantined_projection"] = old_candidate.pop("projection")
        if "rank_context" in old_candidate:
            old_candidate["historical_quarantined_rank_context"] = old_candidate.pop("rank_context")
        if "historical_quarantined_projection" in old_candidate:
            old_candidate["historical_quarantined_projection"]["status"] = "unvalidated historical arithmetic; not a score or reliable forecast"
        table["historical_candidate"] = old_candidate
        for row in table.get("irregularities", []):
            if row["id"] == "IRR-2026-10-27-06":
                row["finding"] = "The lattice overlap triggers the literal rule even though a space-filling control is not geological copying."
            elif row["id"] == "IRR-2026-10-27-02":
                row["finding"] = "The historical GeoTIFF zero-fills outside the footprint; official bounds wording and portal acceptance are not independently resolved. DO NOT SUBMIT."
        write("evidence/submission_table_20261027.json", table)

    focus_path = ROOT / "evidence/focus_site_audit_20261027.json"
    if focus_path.exists():
        focus = load("evidence/focus_site_audit_20261027.json")
        focus["superseded_notice"] = REASON
        for row in focus.get("files", []):
            if row.get("label") == "KANLERGEMSDOE2 promoted EXP-2":
                row["label"] = "KANLERGEMSDOE2 historical EXP-2 (negative)"
        for row in focus.get("pairwise_overlap", []):
            for key in ("a", "b"):
                if row.get(key) == "KANLERGEMSDOE2 promoted EXP-2":
                    row[key] = "KANLERGEMSDOE2 historical EXP-2 (negative)"
        for row in focus.get("promoted_vs_all", []):
            if "lattice" in row.get("against", ""):
                row["note"] = "Space-filling lattice still triggers the literal all-entry duplicate rule."
        write("evidence/focus_site_audit_20261027.json", focus)

    records_path = ROOT / "evidence/focus_site_files.json"
    if records_path.exists():
        records = load("evidence/focus_site_files.json")
        records["superseded_notice"] = "Historical files only; no submission is authorized. All-finite encoding is not a portal-acceptance guarantee."
        for row in records.get("records", []):
            role = row.get("role", "")
            if "portal-safe" in role:
                row.setdefault("historical_role", role)
                row["role"] = role.replace("portal-safe", "all-finite")
        write("evidence/focus_site_files.json", records)

    current = load("run_card.json")
    write("docs/downloads/htcads_run_card.json", current)
    report = load("docs/downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-validation.json")
    write("evidence/validator_receipt.json", report)
    print("Historical promotion flags marked negative; measurements preserved and supersession recorded.")


if __name__ == "__main__":
    main()
