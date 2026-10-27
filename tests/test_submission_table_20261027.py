"""Cross-check concurrently restored historical files without authorizing them."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_restored_files_match_checksums_and_independent_pinned_audit() -> None:
    records = load("evidence/focus_site_files.json")["records"]
    downloaded = [r for r in records if r.get("status") == "downloaded"]
    assert len(downloaded) == 17
    for row in downloaded:
        path = ROOT / row["local_path"]
        assert path.is_file() and path.stat().st_size == row["bytes"]
        assert sha256(path) == row["sha256"]
    independently_pinned = load("evidence/focus_reaudit_20261027.json")["focus_sites"]
    for row in independently_pinned:
        match = [r for r in downloaded if r["site"] == row["site"] and r["role"] == "listed"]
        assert len(match) == 1
        assert Path(match[0]["local_path"]).name == row["file"]
        assert match[0]["sha256"] == row["file_audit"]["sha256"]
        assert not row["organizer_receipt_verified"]


def test_nine_user_reported_values_and_format_evidence() -> None:
    records = load("evidence/focus_site_files.json")["records"]
    top = {r["site"]: r["user_reported_score"] for r in records if r["role"] == "listed"}
    assert top == {"GEMSDOE24": .2477, "GEMSDOE25": .2600, "GEMSDOE27": .2449,
                   "GEMSDOE28": .2710, "GEMSDOE30": .2600, "GEMSDOE31": .2708,
                   "GEMSDOE32": .2778, "GEMSDOE33": .2632, "GEMSDOE36": .2750}
    audit = load("evidence/focus_site_audit_20261027.json")
    assert "Superseded" in audit["superseded_notice"]
    for row in audit["files"]:
        if not row["label"].startswith("archive:"):
            assert row["nan_inside_footprint"] == 0 and row["dots_on_catalogue"] == 0
    lattice = [r for r in audit["promoted_vs_all"] if "lattice" in r["against"]]
    assert len(lattice) == 1 and lattice[0]["promoted_dots_within_3px_of_against"] > .70
    assert lattice[0]["duplicate_by_protocol_overlap_gt_0p70"]


def test_old_projection_and_promotion_are_quarantined() -> None:
    data = load("evidence/submission_table_20261027.json")
    assert "promoted" not in data
    candidate = data["historical_candidate"]
    assert candidate["verdict"] == "negative" and candidate["ok_to_submit"] is False
    assert "not a score" in candidate["historical_quarantined_projection"]["status"]
    assert "literal" in candidate["lattice_overlap_note"]
    for page in ("docs/submission-table.html", "docs/audit-review.html"):
        text = (ROOT / page).read_text()
        assert "DO NOT SUBMIT" in text
        assert "VALIDATED: PROMOTE" not in text and "0.3146" not in text


def test_all_historical_site_download_links_resolve() -> None:
    text = (ROOT / "docs/submission-table.html").read_text()
    hrefs = re.findall(r'href="(downloads/[^"]+\.tif)"', text)
    assert len(hrefs) >= 10  # nine historical files plus the current research artifact
    for href in hrefs:
        assert (ROOT / "docs" / href).is_file()
    for page in list((ROOT / "docs").glob("*.html")) + [ROOT / "README.md", ROOT / "EXECUTIVE_SUMMARY.md"]:
        for name in set(re.findall(r"downloads/([A-Za-z0-9._-]+\.tif)", page.read_text())):
            assert (ROOT / "docs/downloads" / name).is_file(), (page, name)


def test_unsafe_concurrent_entrypoints_are_retired() -> None:
    for name in ("build_submission_table.py", "audit_focus_files.py", "fetch_focus_submissions.py"):
        proc = subprocess.run([sys.executable, str(ROOT / "scripts" / name)], capture_output=True, text=True)
        assert proc.returncode != 0
        assert "retired" in proc.stderr


def test_official_source_register_is_dated_and_linked() -> None:
    src = load("registry/official_sources_20261027.json")
    assert src["verified_on_utc"] == "2026-10-27"
    ids = [s["id"] for s in src["sources"]]
    assert len(ids) == len(set(ids))
    assert all(s["url"].startswith("https://") for s in src["sources"])
    leaderboard = next(s for s in src["sources"] if s["id"] == "OS-3")
    assert leaderboard["snapshot_values_used"]["rank_1"] == .4544
    assert leaderboard["snapshot_values_used"]["rank_25"] == .3195
