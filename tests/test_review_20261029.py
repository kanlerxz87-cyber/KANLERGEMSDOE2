"""Current-session negative preflight must remain fail-closed and auditable."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_card_is_negative_and_holdout_reported_honestly() -> None:
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    assert card["generated_utc"].startswith("2026-10-29T")
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["experiments_run"] == 1 and card["weekly_slots_spent_this_session"] == 0
    assert card["holdout_dti"] == 0.009154
    assert card["holdout_ci95"] == [0.006528, 0.012243]
    assert card["raster_sha256"] and card["submission_name"]
    tif = ROOT / "docs/downloads" / card["submission_name"]
    assert tif.is_file()
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card["raster_sha256"]
    assert len(card["note"]) <= 140
    # Leakage gate stays closed.
    assert card["leakage_canary_auc"] <= 0.90
    # Novelty gates stay within limits.
    reg = card["correlation_overlap_vs_registry"]
    assert reg["max_dot_overlap_within_3px_vs_local_rasters"] <= 0.70
    assert reg["max_abs_surface_rank_correlation"] <= 0.90
    assert reg["lattice_dot_overlap_within_3px"] <= 0.70


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
        assert "not cleared to submit" in page.lower()
    summary = (ROOT / "docs" / "executive-summary.html").read_text()
    assert "Candidate-hypothesis screen" in summary
    assert "USER/OWNER-REPORTED" in summary
    assert "Leaderboard-score estimate" in summary
    readme = (ROOT / "README.md").read_text()
    assert "current three-pass audit" in readme.casefold()
    assert "unique tiff was generated this session" in readme.casefold()
    assert "not cleared to submit" in readme.casefold()
    prompt = (ROOT / "PROMPT.md").read_text()
    assert "2026-10-29 three-pass review" in prompt
    assert "read it every time" in readme.casefold() or "at the start of every session" in readme.casefold()
