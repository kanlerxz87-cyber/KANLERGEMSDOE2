"""Protect the current evidence boundary against stale promotional claims."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_replay_stop_and_focus_geometry():
    replay = json.loads((ROOT / "evidence/review_20261028_replay.json").read_text())
    pre = replay["preflight"]
    assert replay["verdict"] == "negative" and replay["ok_to_submit"] is False
    assert pre["forced_duplicate"] and pre["minimum_overlapping_dots"] == 31005
    assert pre["minimum_directional_overlap"] > pre["limit"]
    assert replay["hptr_exact_bytes"]["witness_overlap_dots"] == 37640
    assert replay["hptr_exact_bytes"]["duplicate_under_literal_rule"] is True
    assert replay["geometry"]["g32_b2_vs_g25_d28_filtered_by_distance_gt_2px_xor"] == 0
    assert len(replay["focus_nine"]) == 9
    assert all(r["duplicate_within_focus_nine"] for r in replay["focus_nine"])


def test_published_dashboard_does_not_call_proxies_leaderboard_wins():
    feed = json.loads((ROOT / "docs/data/status_feed.json").read_text())
    assert feed["ok_to_submit"] is False
    for lane in ("kg2s3_hptr_lane", "kg2s3_trbvc_lane"):
        assert feed[lane]["sgmc_cal_v3_dti"] is None
        assert feed[lane]["hide_recover_v3_dti"] is None
        assert feed[lane]["ok_to_submit"] is False
    for name in ("index.html", "executive-summary.html", "research.html", "irregularities.html"):
        text = (ROOT / "docs" / name).read_text()
        assert "DO NOT SUBMIT" in text.upper()
        assert "procedure proxies do not demonstrate a leaderboard win" in text
        assert "HOLDOUT-DTI SGMC-CAL" not in text
        assert "breakthrough" not in text.lower()
    assert "No credible leaderboard estimate" in (ROOT / "EXECUTIVE_SUMMARY.md").read_text()
