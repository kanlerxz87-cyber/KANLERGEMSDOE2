"""Regression tests for the 2026-10-27 per-site submission table and focus-site file restore.

These tests do not need the competition data (data/ is git-ignored). They check committed
evidence against committed files, so a silently broken link or hash fails CI.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_focus_site_files_match_recorded_sha256() -> None:
    recs = _load("evidence/focus_site_files.json")["records"]
    downloaded = [r for r in recs if r.get("status") == "downloaded"]
    assert len(downloaded) == 9 + 3 + sum(1 for r in recs if str(r.get("role", "")).startswith("all-finite")), (
        "expected 9 listed focus files + 3 alternates + siblings all downloaded")
    for r in downloaded:
        p = ROOT / r["local_path"]
        assert p.exists(), f"missing {r['local_path']}"
        assert _sha256(p) == r["sha256"], f"sha256 drift for {r['local_path']}"
        assert p.stat().st_size == r["bytes"]


def test_listed_top_scores_match_prompt_listing() -> None:
    """The 9 listed top-scoring submissions (USER-REPORTED) that the table must cover."""
    recs = _load("evidence/focus_site_files.json")["records"]
    tops = {r["site"]: r["user_reported_score"] for r in recs
            if r.get("role", "listed") == "listed" and r.get("user_reported_score") is not None}
    expected = {"GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449, "GEMSDOE28": 0.2710,
                "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708, "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632,
                "GEMSDOE36": 0.2750}
    assert set(tops) == set(expected), sorted(set(tops) ^ set(expected))
    for site, score in expected.items():
        assert abs(tops[site] - score) < 1e-9, (site, tops[site])
    assert max(tops, key=tops.get) == "GEMSDOE32"


def test_historical_local_format_audit_is_not_upload_authorization() -> None:
    audit = _load("evidence/focus_site_audit_20261027.json")
    assert "does not establish" in audit["status"]
    for f in audit["files"]:
        assert f["organizer_acceptance_verified"] is False
        if f["label"].startswith("archive:"):
            continue
        assert f["all_checks_passed"], f"format checks failed for {f['label']}: {f['checks']}"
        assert f["nan_inside_footprint"] == 0
        assert f["dots_on_catalogue"] == 0


def test_prior_file_hash_matches_run_card_but_fails_literal_protocol() -> None:
    rc = _load("evidence/run_card.json")
    prior = ROOT / "docs/downloads" / rc["submission_filename"]
    assert _sha256(prior) == rc["raster_sha256"]
    assert rc["verdict"] == "negative" and rc["ok_to_download_and_submit"] is False
    current = _load("evidence/release_audit_20261027.json")
    assert current["prior_candidate"]["witness_overlap_fraction"] > 0.70
    assert current["prior_candidate"]["duplicate_under_literal_rule"] is True


def test_current_comparison_has_no_unsupported_projection() -> None:
    d = _load("evidence/submission_table_20261027.json")
    assert d["verdict"] == "negative" and d["ok_to_submit"] is False
    assert d["new_raster"] is None and d["leaderboard_estimate"] is None
    assert len(d["focus_nine"]) == 9
    assert all(r["score_evidence_class"].startswith("USER/OWNER-REPORTED") for r in d["focus_nine"])

def test_submission_table_html_links_resolve() -> None:
    html_text = (ROOT / "docs/submission-table.html").read_text(encoding="utf-8")
    hrefs = re.findall(r'href="(downloads/[^"]+)"', html_text)
    assert hrefs, "table must link historical research files"
    for h in hrefs:
        assert (ROOT / "docs" / h).exists(), f"broken download link: {h}"
    assert "Local format / portal status" in html_text
    assert "USER/OWNER-REPORTED" in html_text
    assert "Not estimated" in html_text
    assert "Do not submit" in html_text


def test_public_pages_remove_stale_positive_promotion_sections() -> None:
    pages = ["index.html", "executive-summary.html", "research.html", "irregularities.html", "submission-table.html"]
    all_html = "\n".join((ROOT / "docs" / name).read_text(encoding="utf-8") for name in pages)
    for stale in ("PROMOTE — OK TO SUBMIT", "DARP-EXP-2", "SESSION-2 CANDIDATE", "verdict_control_separated_policy"):
        assert stale not in all_html
    home = (ROOT / "docs/index.html").read_text(encoding="utf-8")
    assert "NEGATIVE · DO NOT SUBMIT" in home
    assert "There is no approved file to download or submit" in home
    assert "href=\"downloads/kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif\"" not in home
    issues = (ROOT / "docs/irregularities.html").read_text(encoding="utf-8")
    assert "Archived “promote” verdicts are not current authorization" in issues
    assert "supersession_manifest_20261027.json" in issues
    supersession = _load("evidence/supersession_manifest_20261027.json")
    assert supersession["current_decision"]["verdict"] == "negative"
    assert supersession["current_decision"]["ok_to_submit"] is False
    assert all(row["current_interpretation"] for row in supersession["superseded_records"])
    assert "not current download or submission authorization" in supersession["notice"]
    feed = _load("docs/data/status_feed.json")
    assert feed["ok_to_submit"] is False and feed["file_to_submit"] is None
    assert "session2_candidate" not in feed and "darp_mt10_lane" not in feed


def test_all_pages_download_links_resolve() -> None:
    """Every docs/downloads/*.tif referenced by a page or the README exists (fixes the 12 broken links)."""
    pages = list((ROOT / "docs").glob("*.html")) + [ROOT / "README.md", ROOT / "EXECUTIVE_SUMMARY.md"]
    missing = []
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for name in set(re.findall(r"downloads/([A-Za-z0-9._-]+\.tif)", text)):
            if not (ROOT / "docs" / "downloads" / name).exists():
                missing.append((page.name, name))
    assert not missing, f"broken download links: {missing}"


def test_official_sources_record_has_urls_and_quotes() -> None:
    src = _load("registry/official_sources_20261027.json")
    ids = [s["id"] for s in src["sources"]]
    assert len(ids) == len(set(ids))
    for s in src["sources"]:
        assert s["url"].startswith("https://"), s["id"]
    lb = next(s for s in src["sources"] if s["id"] == "OS-3")
    assert lb["snapshot_values_used"]["rank_1"] == 0.4544
    assert lb["snapshot_values_used"]["rank_25"] == 0.3195
    registry = _load("registry/sources.json")
    record = next(s for s in registry["official_competition_sources"] if s["id"] == "SRC-DD-LEADERBOARD")
    assert "#1 = 0.4544" in record["verified_facts"]
    assert "#5 = 0.3566" in record["verified_facts"]
    assert "not a live verification" in record["verified_facts"]
