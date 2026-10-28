"""Regressions for the literal-rule release stop and reproducible restore."""
from __future__ import annotations

import hashlib
import importlib
import json
import shutil
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_site  # noqa: E402
import restore_data  # noqa: E402
import validate_submission_kg2s2  # noqa: E402


def test_restore_stages_before_hash_and_preserves_previous_on_failure(tmp_path, monkeypatch):
    data = b"verified bytes"
    entry = {"id": "sample", "dest": "core/sample.bin", "group": "core",
             "repo": "owner/repo", "ref": "pinned", "path": "file.bin",
             "sha256": hashlib.sha256(data).hexdigest()}
    dest = tmp_path / entry["dest"]
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"old unverified bytes")

    def wrong_fetch(_repo, _ref, _path, dst):
        dst.write_bytes(b"wrong response")

    monkeypatch.setattr(restore_data, "fetch", wrong_fetch)
    with pytest.raises(ValueError, match="HASH MISMATCH"):
        restore_data.restore_entry(entry, tmp_path)
    assert dest.read_bytes() == b"old unverified bytes"
    assert not list(tmp_path.rglob("*.assembling"))

    def correct_fetch(_repo, _ref, _path, dst):
        dst.write_bytes(data)

    monkeypatch.setattr(restore_data, "fetch", correct_fetch)
    result = restore_data.restore_entry(entry, tmp_path)
    assert result["status"] == "restored" and dest.read_bytes() == data
    monkeypatch.setattr(restore_data, "fetch", lambda *_: pytest.fail("hash-pinned file should be reused"))
    assert restore_data.restore_entry(entry, tmp_path)["status"] == "present"


def test_restore_chunk_failure_leaves_no_partial_and_no_replacement(tmp_path, monkeypatch):
    data = b"part one part two"
    entry = {"id": "chunked", "dest": "core/chunked.bin", "group": "core",
             "repo": "owner/repo", "ref": "pinned", "parts": ["one", "two"],
             "sha256": hashlib.sha256(data).hexdigest()}
    dest = tmp_path / entry["dest"]
    dest.parent.mkdir(parents=True)
    dest.write_bytes(b"previous bytes")

    def interrupted(_repo, _ref, part, dst):
        dst.parent.mkdir(parents=True, exist_ok=True)
        if part == "two":
            dst.write_bytes(b"partial")
            raise subprocess.CalledProcessError(1, "gh")
        dst.write_bytes(b"part one ")

    monkeypatch.setattr(restore_data, "fetch", interrupted)
    with pytest.raises(subprocess.CalledProcessError):
        restore_data.restore_entry(entry, tmp_path)
    assert dest.read_bytes() == b"previous bytes"
    assert not list(tmp_path.rglob("*.assembling"))
    assert not list((tmp_path / "raw_parts").glob("*"))


def test_restore_aggregates_errors_writes_partial_receipt_and_exits_nonzero(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    entries = [{"id": str(i), "dest": f"external/{i}", "group": "external",
                "repo": "owner/repo", "ref": "pinned"} for i in range(3)]
    manifest.write_text(json.dumps({"files": entries}))
    attempted = []

    def restore(entry, _root):
        attempted.append(entry["id"])
        if entry["id"] == "1":
            raise subprocess.CalledProcessError(1, "gh")
        return {"id": entry["id"], "dest": entry["dest"], "status": "restored", "sha256": "a" * 64}

    monkeypatch.setattr(restore_data, "ROOT", tmp_path)
    monkeypatch.setattr(restore_data, "restore_entry", restore)
    result = restore_data.main(["--group", "external", "--manifest", str(manifest),
                                "--target-dir", str(tmp_path / "cache")])
    receipt = json.loads((tmp_path / "data/restore_receipt_external.json").read_text())
    assert result == 1 and attempted == ["0", "1", "2"]
    assert receipt["status"] == "partial"
    assert receipt["verified_files_count"] == 2 and receipt["failed_files_count"] == 1
    assert [x["status"] for x in receipt["files"]] == ["restored", "failed", "restored"]
    assert "not organizer origin" in receipt["provenance"]


def test_legacy_validator_modes_cannot_authorize_self_asserted_card(tmp_path):
    card = tmp_path / "positive.json"
    card.write_text(json.dumps({"verdict": "promote", "raster_sha256": "0" * 64,
                                "ok_to_download_and_submit": True}))
    for mode in ("champion", "unique-slot"):
        result = validate_submission_kg2s2.validate_all_gates(tmp_path / "missing.tif", card, tmp_path, mode)
        assert result["legacy_requested_mode"] == mode and result["legacy_mode_ignored"] is True
        assert result["verdict"] == "negative" and result["ok_to_submit"] is False
        assert result["validated_ok_to_download_and_submit"] is False


@pytest.mark.parametrize("script", ["run_dslup_experiments.py", "run_dslup_unique_slot.py",
                                    "run_ecpu_experiments.py", "run_darp_mt10_experiments.py",
                                    "run_cpr_experiments.py", "generate_unique_submission.py"])
def test_archived_parallel_lane_entry_points_stop_before_fitting(script):
    module = importlib.import_module(script[:-3])
    with pytest.raises(SystemExit, match="Archived parallel lane disabled"):
        module.main()


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("href", "src") and value:
                self.urls.append(value)


def test_rendered_pages_and_feeds_are_fail_closed_and_local_links_resolve(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence"
    docs = tmp_path / "docs"
    downloads = docs / "downloads"
    evidence.mkdir()
    downloads.mkdir(parents=True)
    for filename in ("release_recheck_20261027.json", "current_run_card.json",
                     "dslup_literal_revalidation_20261027.json", "dslup_unique_slot_run_card.json",
                     "data_restore_recheck_20261027.json", "independent_witness_20261027.json",
                     "off36_literal_revalidation_20261027.json", "verification_passes_20261027.json"):
        shutil.copy2(ROOT / "evidence" / filename, evidence / filename)
    shutil.copy2(ROOT / "docs/style.css", docs / "style.css")
    (tmp_path / "research").mkdir()
    shutil.copy2(ROOT / "research/2026-10-27_htcads_hypotheses.md", tmp_path / "research")
    audit = json.loads((evidence / "release_recheck_20261027.json").read_text())
    filenames = {Path(row["path"]).name for row in audit["focus_nine"]}
    filenames.add(audit["prior_candidate"]["file"])
    filenames.add(json.loads((evidence / "dslup_literal_revalidation_20261027.json").read_text())["raster_filename"])
    filenames.add(json.loads((evidence / "off36_literal_revalidation_20261027.json").read_text())["raster_filename"])
    filenames.add(next(row["file"] for row in audit["all_local_candidate_artifacts"] if "unique-hypothesis1-binary" in row["file"]))
    for filename in filenames:
        shutil.copy2(ROOT / "docs/downloads" / filename, downloads / filename)
    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    monkeypatch.setattr(build_site, "DOCS", docs)
    build_site.main()

    feed = json.loads((docs / "data/status_feed.json").read_text())
    assert feed["submission"]["ok_to_submit"] is False
    assert feed["submission"]["current_candidate"] is None
    assert feed["archived_dslup"]["ok_to_submit"] is False
    assert feed["archived_dslup"]["literal_witness_overlap"] > 0.70
    assert json.loads((docs / "data/run_card.json").read_text()) == json.loads((evidence / "current_run_card.json").read_text())
    for page in docs.glob("*.html"):
        content = page.read_text()
        assert "PROMOTE — OK TO SUBMIT" not in content
        if page.name in ("executive-summary.html", "submission-table.html"):
            assert "USER/OWNER-REPORTED" in content
        parser = Links()
        parser.feed(content)
        for url in parser.urls:
            parsed = urlsplit(url)
            if not parsed.scheme and not parsed.netloc and parsed.path:
                assert (page.parent / unquote(parsed.path)).is_file(), (page, url)


def test_superseded_session2_cards_and_receipts_are_negative():
    for path in ("evidence/dslup_unique_slot_run_card.json", "docs/downloads/dslup_run_card.json",
                 "evidence/dslup_unique_slot_validator_receipt.json", "evidence/dslup_champion_mode_receipt.json"):
        receipt = json.loads((ROOT / path).read_text())
        assert receipt["verdict"] == "negative" and receipt["ok_to_submit"] is False
        assert "SUPERSEDED" in receipt["supersession_notice"]
        assert receipt["historical_verdict_at_creation"] == "promote"  # recorded, not endorsed


def test_independent_distance_transform_receipt_agrees_with_release_audit():
    check = json.loads((ROOT / "evidence/independent_witness_20261027.json").read_text())
    audit = json.loads((ROOT / "evidence/release_recheck_20261027.json").read_text())
    assert "distance transform" in check["method"].lower()
    assert check["matches_release_recheck"] is True
    assert check["ok_to_submit"] is False and check["verdict"] == "negative"
    assert check["complete_registry_replayed"] is False and check["holdout_or_leakage_replayed"] is False
    for key, value in check["independent_preflight"].items():
        assert audit["preflight"][key] == value
    rows = {row["file"]: row for row in check["candidates"]}
    reduced = next(row for name, row in rows.items() if name.startswith("36GEMSDOE-"))
    assert reduced["duplicate_vs_witness"] is False and reduced["overlap_fraction"] == 0.66
    assert reduced["dots"] == 15000 and reduced["matches_assigned_budget"] is False
    assert reduced["on_catalogue_positive_pixels"] == 107
    hyp1 = next(row for name, row in rows.items() if "unique-hypothesis1" in name)
    assert hyp1["duplicate_vs_witness"] is True and hyp1["on_catalogue_positive_pixels"] == 184


@pytest.mark.parametrize("flag,method", [("--verify-tnr1", "TNR1"), ("--verify-gvc1", "GVC1"),
                                         ("--verify-recorded", "MTR1")])
def test_missing_historical_verifiers_fail_with_explicit_scope(flag, method):
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_holdout.py"), flag],
                          capture_output=True, text=True, check=False)
    assert proc.returncode != 0
    assert f"Archived {method} verifier is missing" in proc.stderr
    assert "no verification or replay was performed" in proc.stderr


def test_restore_no_gh_uses_stdlib_github_api_and_cleans_temp(tmp_path, monkeypatch):
    import io
    calls = []
    monkeypatch.setattr(restore_data.shutil, "which", lambda *_: None)

    def open_url(request, timeout):
        calls.append((request.full_url, request.get_header("Accept"), timeout))
        return io.BytesIO(b"public mirror content")

    monkeypatch.setattr(restore_data, "urlopen", open_url)
    dest = tmp_path / "data" / "file.bin"
    restore_data.fetch("owner/repo", "ref/with space", "path/a file.bin", dest)
    assert dest.read_bytes() == b"public mirror content"
    assert calls == [("https://api.github.com/repos/owner/repo/contents/path/a%20file.bin?ref=ref%2Fwith%20space",
                      "application/vnd.github.raw", 120)]
    assert not list(tmp_path.rglob("*.partial"))


def test_restore_empty_group_is_not_success(tmp_path, monkeypatch):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": []}))
    monkeypatch.setattr(restore_data, "ROOT", tmp_path)
    result = restore_data.main(["--group", "core", "--manifest", str(manifest),
                                "--target-dir", str(tmp_path / "cache")])
    receipt = json.loads((tmp_path / "data/restore_receipt_core.json").read_text())
    assert result == 1 and receipt["status"] == "failed"
    assert receipt["verified_files_count"] == 0


def test_reduced_budget_file_fails_the_assigned_budget_even_though_one_witness_passes():
    receipt = json.loads((ROOT / "evidence/off36_literal_revalidation_20261027.json").read_text())
    assert receipt["ok_to_submit"] is False and receipt["verdict"] == "negative"
    assert receipt["gates"]["exact_file_identity"] is True
    assert receipt["gates"]["literal_witness_not_duplicate"] is True  # one witness is not a clearance
    assert receipt["gates"]["assigned_37654_dot_budget_matches"] is False
    assert receipt["gates"]["complete_current_registry_replayed"] is False
    assert receipt["gates"]["independent_canary_and_holdout_replay"] is False
    assert receipt["format_audit"]["on_catalogue_positive_pixels"] == 107


def test_pr36_superseded_cards_cannot_authorize_submission():
    for name in ("evidence/superseded/current_run_card_pr36_promote_20261027.json",
                 "docs/downloads/36GEMSDOE-off-catalogue-blind-geothermal-targeting-20261027T234345Z-2ecaae7a056e-zeros-validation.json"):
        data = json.loads((ROOT / name).read_text())
        assert data["verdict"] == "negative" and data["ok_to_submit"] is False
        assert data["historical_verdict_at_creation"] == "promote"
        assert "SUPERSEDED" in data["supersession_notice"]
