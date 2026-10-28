"""Session-3 receipt and status-feed invariants (no bulk data required).

These guard the fail-closed decision: no candidate may be marked OK to submit while the
literal all-registry rule (PR #25) is in force, and the 0.2778 lineage arithmetic must hold.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECEIPT = ROOT / "evidence" / "session3_independent_recheck_20261027.json"
FEED = ROOT / "docs" / "data" / "status_feed.json"


def _receipt() -> dict:
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def test_lineage_arithmetic_and_subset() -> None:
    lin = _receipt()["lineage_gemsdoe32_from_gemsdoe25"]
    assert lin["gemsdoe32_subset_of_gemsdoe25"] is True
    assert lin["removed_dots_from_gemsdoe25"] == 44090 - 37654 == 6436
    assert lin["removed_dots_all_within_2px_of_known_fault"] is True
    assert lin["removed_dots_on_known_fault_pixels"] == 0
    assert lin["gemsdoe25_minus_gemsdoe32_equals_within_2px_count"] is True


def test_focus_files_are_binary_and_do_not_sit_on_known_faults() -> None:
    mech = _receipt()["mechanism_near_known_fault"]
    assert set(mech) == {"GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                         "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"}
    for site, m in mech.items():
        assert m["on_known_fault_pixels_masked_by_organizer"] == 0, site
        assert m["value_stats"]["inside_distinct_values"] == 2, site
        assert m["value_stats"]["inside_min"] == 0.0 and m["value_stats"]["inside_max"] == 1.0, site


def test_candidates_are_format_valid_but_literal_duplicates() -> None:
    cands = _receipt()["candidates_format_and_witness"]
    assert cands, "no candidates recorded"
    for name, c in cands.items():
        assert c["crs"] == "EPSG:32611", name
        assert c["shape"] == [3730, 3292], name
        assert c["dtype"] == "float32", name
        assert c["inside_range_0_1"] is True and c["no_nan_inside_footprint"] is True, name
        assert c["grid_matches_pinned_owner_template"] is True, name
        # Fail-closed: the literal lattice test (>70%) must still flag every candidate.
        assert c["witness_overlap_fraction"] > 0.70, name
        assert c["duplicate_under_literal_rule"] is True, name


def test_status_feed_never_marks_a_candidate_ok() -> None:
    feed = json.loads(FEED.read_text(encoding="utf-8"))
    assert feed["ok_to_submit"] is False
    assert feed["validated_ok_to_download_and_submit"] is False
    s2 = feed["session2_candidate"]
    assert s2["ok_to_download_and_submit"] is False
    assert s2["verdict"] == "negative"
    assert "verdict_control_separated_policy" not in s2  # no unapproved exemption
    for candidate in feed["parallel_research_files"].values():
        assert candidate["ok_to_submit"] is False and candidate["verdict"] == "negative"


def test_pr34_candidate_irregularities_are_recorded() -> None:
    """PR #34 claims 0 on-catalogue dots and <2% focus overlap; the verified recheck must say otherwise."""
    c = _receipt()["candidates_format_and_witness"]["KG2-HYP1-binary-PR34"]
    assert c["on_catalogue_positive_pixels"] == 184
    assert c["witness_overlap_fraction"] > 0.70 and c["duplicate_under_literal_rule"] is True
    pw = _receipt()["pairwise_directional_3px_overlap_focus_and_candidates"]["KG2-HYP1-binary-PR34"]
    assert max(pw[k] for k in ["GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                               "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"]) > 0.02
