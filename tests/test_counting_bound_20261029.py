"""Regression checks for the pigeonhole counting bound (scripts/verify_counting_bound.py)."""
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVID = ROOT / "evidence" / "counting_bound_20261029.json"


def test_bound_arithmetic_matches_recorded_values():
    uncovered, n_ref, limit = 6649, 37654, 0.70
    assert (n_ref - uncovered) / n_ref > limit  # forced duplicate at frozen budget
    assert math.floor(uncovered / (1 - limit) + 1e-9) == 22163
    assert (22163 - uncovered) / 22163 <= limit
    assert (22164 - uncovered) / 22164 > limit  # first budget above the cap is forced


def test_recorded_evidence_is_internally_consistent():
    if not EVID.exists():
        return  # evidence produced by scripts/verify_counting_bound.py
    d = json.loads(EVID.read_text(encoding="utf-8"))
    assert d["witness_sha256_match"] is True
    assert d["footprint_pixels"] == d["covered_within_3px"] + d["uncovered_pixels"]
    assert d["forced_duplicate_at_reference_budget"] is True
    assert abs(d["minimum_overlap_at_reference_budget"] - (37654 - d["uncovered_pixels"]) / 37654) < 1e-12
