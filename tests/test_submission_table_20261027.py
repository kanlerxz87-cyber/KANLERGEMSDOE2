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

def test_executive_summary_has_nine_sites_and_no_fabricated_leaderboard_estimate() -> None:
    html_text = (ROOT / "docs/executive-summary.html").read_text(encoding="utf-8")
    # New state: a unique candidate was generated this session — OK to download,
    # not cleared to submit. The fail-closed verdict is preserved.
    assert "kanlergemsdoe2-geothermal-blind-conduit-20261029T024633Z-60a6b7f6ca71-zeros.tif" in html_text
    assert "58967b215cf5351d2fd66861b51c23ab3c0d8b854864331d0ed988b6d544ad7a" in html_text
    assert "OK to DOWNLOAD" in html_text
    assert "not cleared to submit" in html_text.lower()
    assert "HOLDOUT-DTI 0.009154" in html_text
    assert "no organizer receipt" in html_text
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30", "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert site in html_text
    assert "0.2778" in html_text and "USER-REPORTED" in html_text
    assert "97.58%" in html_text
    assert "Do not submit" in html_text


def test_hypothesis_agenda_is_ranked_but_does_not_claim_unmeasured_gain() -> None:
    research = (ROOT / "research/2026-10-28_focus-nine-hypotheses.md").read_text(encoding="utf-8")
    html_text = (ROOT / "docs/research.html").read_text(encoding="utf-8")
    for phrase in ("potential-field crest migration", "Thermal transport-direction uncertainty", "Alteration-edge", "Seasonal deformation"):
        assert phrase.casefold() in research.casefold()
    assert "not fitted" in research and "no gain forecast" in research
    assert "NASA OPERA" in research and "not viable" in research
    assert "Four testable geological hypotheses" in html_text
    assert "not a numerical DTI forecast" in html_text
    assert "0.2778" in html_text


def test_current_run_card_is_negative_and_no_submission_authorized() -> None:
    card = _load("evidence/current_run_card.json")
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["ok_to_download"] is True and card["ok_to_download_and_submit"] is False
    assert card.get("experiments_run") == 1
    assert card.get("weekly_slots_spent_this_session") == 0
    assert card["raster_sha256"] and card["submission_name"]
    tif = ROOT / "docs/downloads" / card["submission_name"]
    assert tif.is_file() and _sha256(tif) == card["raster_sha256"]
    assert card["holdout_dti"] == 0.009154
    assert card["holdout_ci95"] == [0.006528, 0.012243]
    assert len(card["note"]) <= 140
    assert card["leakage_canary_auc"] <= 0.90


def test_submission_table_html_links_resolve() -> None:
    html_text = (ROOT / "docs/submission-table.html").read_text(encoding="utf-8")
    hrefs = re.findall(r'href="(downloads/[^"]+)"', html_text)
    assert hrefs, "table must link downloadable files"
    for h in hrefs:
        assert (ROOT / "docs" / h).exists(), f"broken download link: {h}"


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
