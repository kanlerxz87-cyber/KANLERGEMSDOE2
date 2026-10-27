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
    assert len(downloaded) == 9 + 3 + sum(1 for r in recs if str(r.get("role", "")).startswith("portal-safe")), (
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


def test_format_audit_passes_for_all_focus_files_and_promoted() -> None:
    audit = _load("evidence/focus_site_audit_20261027.json")
    for f in audit["files"]:
        if f["label"].startswith("archive:"):
            continue
        assert f["all_checks_passed"], f"format checks failed for {f['label']}: {f['checks']}"
        assert f["nan_inside_footprint"] == 0
        assert f["dots_on_catalogue"] == 0


def test_promoted_file_hash_matches_run_card_and_is_unique_under_protocol() -> None:
    rc = _load("evidence/run_card.json")
    promoted = ROOT / "docs/downloads" / rc["submission_filename"]
    assert _sha256(promoted) == rc["raster_sha256"]
    audit = _load("evidence/focus_site_audit_20261027.json")
    # Protocol Rule 1: no focus-site file or non-lattice archive reference may exceed 70% 3-px overlap.
    for p in audit["promoted_vs_all"]:
        if "lattice" in p["against"]:
            continue
        assert p["overlap_3px_max_direction"] <= 0.70, p["against"]
        assert not p["exact_dot_identity"], p["against"]


def test_projection_is_labelled_and_arithmetically_consistent() -> None:
    d = _load("evidence/submission_table_20261027.json")
    pr = d["promoted"]["projection"]
    assert pr["label"].startswith("PROJECTION")
    expected = 0.2778 * pr["holdout_exp2"] / pr["holdout_champion"]
    assert abs(pr["point"] - round(expected, 4)) < 1e-9
    assert pr["range_low"] <= pr["point"] <= pr["range_high"]
    # the holdout inputs must equal the run card receipt
    rc = _load("evidence/run_card.json")["holdout_dti"]["primary_hide_and_recover"]
    assert abs(pr["holdout_exp2"] - rc["pooled_dti"]) < 1e-9
    assert abs(pr["holdout_champion"] - rc["champion_02778_same_evaluator"]) < 1e-9


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
