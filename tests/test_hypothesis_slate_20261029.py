"""Regression checks for the 2026-10-29 research-only slate and fail-closed card."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_current_card_remains_negative_and_contains_no_score_or_artifact():
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    assert card["verdict"] == "negative"
    assert card["ok_to_submit"] is False
    assert card["holdout_dti"] is None
    assert card["holdout_ci95"] is None
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["experiments_run"] == 0
    assert card["weekly_slots_spent_this_session"] == 0
    assert len(card["note"]) <= 140
    assert card["correlation_overlap_vs_registry"]["full_registry_checked"] is False
    assert card["correlation_overlap_vs_registry"]["surface_pre_placement"] is None
    assert card["validator_output"]["new_candidate_no_nan_inside_footprint"] is None
    assert card["validator_output"]["new_candidate_values_in_0_1"] is None
    assert card["validator_output"]["new_candidate_crs_shape_transform_match"] is None
    prior = card["validator_output"]["historical_hptr_research_only"]
    assert prior["no_nan_inside_footprint"] and prior["values_in_0_1_inside_footprint"]
    assert prior["shape"] == [3730, 3292] and prior["crs"] == "EPSG:32611"
    assert prior["literal_witness_overlap_fraction"] > 0.70
    assert prior["usable_for_submission"] is False


def test_research_slate_has_three_falsifiable_candidates_and_official_sources():
    text = (ROOT / "research/2026-10-29_hypothesis_slate.md").read_text()
    assert "No experiment was run" in text
    assert "not an exhaustive forensic review" in text
    assert "graph-based centerline bend/termination" in text
    assert "Three-way blind-system interaction" in text
    assert "Background-corrected heat-flow residual" in text
    for label in ("Named non-fault mimic", "Distinction from local prior implementation", "Expected DTI priority / cost / data status"):
        assert label in text
    for url in (
        "https://www.usgs.gov/publications/influence-pre-existing-structures-geothermal-springs-inferences-potential-field",
        "https://www.usgs.gov/publications/discovering-blind-geothermal-systems-great-basin-region-integrated-geologic-and",
        "https://gdr.openei.org/submissions/1391",
        "https://pubs.usgs.gov/of/2005/1207/",
    ):
        assert url in text
    assert "no numerical gain forecast" in text
    assert "not viable until the exact inputs are obtained" in text


def test_generated_research_page_and_readme_point_to_current_slate():
    for page in ("research.html", "executive-summary.html"):
        html = (ROOT / "docs" / page).read_text()
        assert "2026-10-29_hypothesis_slate.md" in html
        assert "DO NOT SUBMIT" in html.upper()
    readme = (ROOT / "README.md").read_text()
    assert "Standing brief — read before every project session" in readme
    assert "2026-10-29_hypothesis_slate.md" in readme
    assert "PROMPT.md" in readme
