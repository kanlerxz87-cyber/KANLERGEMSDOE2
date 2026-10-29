"""Current-session negative preflight must remain fail-closed and auditable."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_card_is_negative_and_bound_matches_frozen_budget() -> None:
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    bounds = card["correlation_overlap_vs_registry"]
    assert card["generated_utc"].startswith("2026-10-29T")
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["experiments_run"] == 0 and card["weekly_slots_spent_this_session"] == 0
    assert card["holdout_dti"] is None and card["holdout_ci95"] is None
    assert card["raster_sha256"] is None and card["submission_name"] is None
    assert len(card["note"]) <= 140
    assert bounds["minimum_overlapping_dots"] == bounds["frozen_budget"] - bounds["witness_uncovered_footprint_pixels"]
    assert bounds["minimum_overlap_fraction"] > bounds["protocol_limit"]
    assert bounds["full_registry_checked"] is False
    assert card["validator_output"]["values_in_0_1"] is None


def test_hypothesis_screen_distinguishes_proposals_from_validation() -> None:
    text = (ROOT / "research/2026-10-29_candidate_hypothesis_screen.md").read_text()
    for required in (
        "Uncertainty-aware hydrothermal path-convergence stability",
        "Fold-local three-way tip–ridge–hydrothermal agreement",
        "Asymmetric scarp–basement-gradient corroboration",
        "Named non-fault mimic",
        "not a numeric DTI forecast",
        "No candidate is marked validated",
        "NASA OPERA",
        "DrivenData GEMS problem description",
    ):
        assert required.casefold() in text.casefold()


def test_pages_and_readme_show_current_fail_closed_decision() -> None:
    for name in ("index.html", "executive-summary.html", "research.html", "irregularities.html"):
        page = (ROOT / "docs" / name).read_text()
        assert "2026-10-29 review: DO NOT SUBMIT" in page
        assert "review_20261029.md" in page
        assert "No experiment or new holdout was run" in page
    summary = (ROOT / "docs" / "executive-summary.html").read_text()
    assert "Candidate-hypothesis screen" in summary
    assert "USER/OWNER-REPORTED" in summary
    assert "Leaderboard-score estimate" in summary
    readme = (ROOT / "README.md").read_text()
    assert "current three-pass audit" in readme.casefold() and "no unique tiff was generated" in readme.casefold()
    prompt = (ROOT / "PROMPT.md").read_text()
    assert "2026-10-29 three-pass review" in prompt
    assert "read it every time" in readme.casefold() or "at the start of every session" in readme.casefold()
