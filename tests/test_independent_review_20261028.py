"""Regression tests for the independent negative review (no live submission)."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems import release_audit  # noqa: E402
import audit_data_inputs  # noqa: E402
import audit_release  # noqa: E402
import prepare_data  # noqa: E402
import refresh_public_feed  # noqa: E402


def test_unconditional_and_off_catalogue_counting_bounds():
    foot = np.ones((4, 5), dtype=bool)
    near = np.ones_like(foot)
    near.ravel()[:3] = False
    catalogue = np.zeros_like(foot)
    catalogue.ravel()[0] = True  # one of the three gaps cannot receive a dot
    ref = {"foot": foot, "near": near, "catalogue": catalogue,
           "reference": np.zeros_like(foot), "uncovered": 3}
    result = release_audit.forced_budget_result(ref, 10)
    assert result["minimum_overlapping_dots"] == 7
    assert result["minimum_directional_overlap"] == 0.70
    assert result["forced_duplicate"] is False  # strictly greater than 70%
    assert result["maximum_budget_not_forced_by_witness"] == 10
    assert result["off_catalogue_uncovered_pixels"] == 2
    assert result["minimum_overlap_off_catalogue"] == 0.8
    assert result["maximum_off_catalogue_budget_not_forced_by_witness"] == 6
    assert result["budget_fits_off_catalogue"] is True
    assert release_audit.forced_budget_result(ref, 20)["minimum_overlap_off_catalogue"] is None
    assert release_audit.forced_budget_result(ref, 11)["forced_duplicate"] is True
    ref["uncovered"] = 4
    with pytest.raises(ValueError, match="does not match"):
        release_audit.forced_budget_result(ref, 10)


def test_recorded_recheck_is_consistent_and_does_not_clear_full_registry():
    audit = json.loads((ROOT / "evidence/release_audit_20261028_independent.json").read_text())
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    b = audit["preflight"]
    assert (b["uncovered_pixels"], b["off_catalogue_uncovered_pixels"]) == (6649, 6514)
    assert b["minimum_overlap_off_catalogue"] == pytest.approx(31140 / 37654)
    assert b["maximum_off_catalogue_budget_not_forced_by_witness"] == 21713
    assert card["generated_utc"] == audit["generated_utc"]
    assert card["correlation_overlap_vs_registry"]["complete_registry_checked"] is False
    assert card["correlation_overlap_vs_registry"]["surface_pre_placement"] is None
    assert card["holdout_dti"] is None and card["raster_sha256"] is None
    assert card["ok_to_submit"] is False and card["verdict"] == "negative"


def _manifest(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "a.bin").write_bytes(b"abc")
    (data / "b.bin").write_bytes(b"def")
    entries = [
        {"id": "a", "group": "core", "dest": "a.bin", "sha256": hashlib.sha256(b"abc").hexdigest(), "bytes": 3},
        {"id": "b", "group": "external", "dest": "b.bin", "sha256": hashlib.sha256(b"def").hexdigest()},
    ]
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"files": entries}))
    return data, manifest, entries


def test_mirror_audit_detects_missing_hash_and_size_changes(tmp_path):
    data, manifest, entries = _manifest(tmp_path)
    good = audit_data_inputs.audit(manifest, data)
    assert good["complete"] is True
    assert good["groups"] == {"core": {"verified": 1, "total": 1}, "external": {"verified": 1, "total": 1}}
    assert "does not authenticate" in good["provenance"]
    (data / "a.bin").write_bytes(b"different")
    (data / "b.bin").unlink()
    bad = audit_data_inputs.audit(manifest, data)
    assert bad["complete"] is False
    assert [r["status"] for r in bad["files"]] == ["hash_mismatch", "missing"]
    out = tmp_path / "out.json"
    assert audit_data_inputs.main(["--manifest", str(manifest), "--data-dir", str(data), "--out", str(out)]) == 1
    assert json.loads(out.read_text())["complete"] is False
    (data / "a.bin").write_bytes(b"abc")
    entries[0]["bytes"] = 4
    manifest.write_text(json.dumps({"files": entries}))
    assert audit_data_inputs.audit(manifest, data, "core")["files"][0]["status"] == "size_mismatch"


def test_mirror_audit_rejects_path_escape_duplicates_and_destructive_receipts(tmp_path):
    data, manifest, entries = _manifest(tmp_path)
    with pytest.raises(ValueError, match="must not overwrite"):
        audit_data_inputs.main(["--manifest", str(manifest), "--data-dir", str(data), "--out", str(data / "a.bin")])
    assert (data / "a.bin").read_bytes() == b"abc"
    with pytest.raises(ValueError, match="must not overwrite"):
        audit_data_inputs.main(["--manifest", str(manifest), "--data-dir", str(data), "--group", "core", "--out", str(data / "b.bin")])
    assert (data / "b.bin").read_bytes() == b"def"
    with pytest.raises(ValueError, match="must not overwrite"):
        audit_data_inputs.main(["--manifest", str(manifest), "--data-dir", str(data), "--out", str(manifest)])
    entries[0]["dest"] = "../escape.bin"
    manifest.write_text(json.dumps({"files": entries}))
    with pytest.raises(ValueError, match="escapes data root"):
        audit_data_inputs.audit(manifest, data)
    entries[0]["dest"] = "a.bin"
    entries[1]["id"] = "a"
    manifest.write_text(json.dumps({"files": entries}))
    with pytest.raises(ValueError, match="duplicate"):
        audit_data_inputs.audit(manifest, data)


def test_feature_band_descriptions_and_receipt_overwrite_protection(tmp_path, monkeypatch):
    expected = ["magnetic", "gravity"]
    prepare_data.validate_band_order(["magnetic - nT", "gravity - mGal"], expected)
    with pytest.raises(ValueError, match="band order"):
        prepare_data.validate_band_order(["gravity - mGal", "magnetic - nT"], expected)
    with pytest.raises(ValueError, match="nonempty description"):
        prepare_data.validate_band_order(["magnetic", None], expected)
    monkeypatch.setattr(prepare_data.paths, "DATA_DIR", tmp_path)
    monkeypatch.setattr(prepare_data.footprint, "load_footprint", lambda: np.ones((2, 2), bool))
    monkeypatch.setattr(sys, "argv", ["prepare_data.py", "--receipt", str(tmp_path / "training_features.tif")])
    with pytest.raises(SystemExit, match="must not overwrite"):
        prepare_data.main()
    monkeypatch.setattr(sys, "argv", ["prepare_data.py", "--receipt", str(tmp_path / "labels.tif")])
    with pytest.raises(SystemExit, match="must not overwrite"):
        prepare_data.main()


def test_release_audit_output_cannot_overwrite_reference(tmp_path, monkeypatch):
    template = tmp_path / "sample_submission.tif"
    template.write_bytes(b"not a TIFF; should remain untouched")
    monkeypatch.setattr(sys, "argv", ["audit_release.py", "--data-dir", str(tmp_path), "--out", str(template)])
    with pytest.raises(ValueError, match="must not overwrite"):
        audit_release.main()
    assert template.read_bytes() == b"not a TIFF; should remain untouched"


def test_public_feed_uses_only_fixed_partial_and_rejects_redirects(monkeypatch):
    seen = []
    class Response:
        def __init__(self, url):
            self.url = url
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def geturl(self):
            return self.url
        def read(self, limit):
            assert limit == 5_000_001
            return b"<table></table>"
    def open_url(request, timeout):
        seen.append(request.full_url)
        assert timeout == 25
        return Response(request.full_url)
    monkeypatch.setattr(refresh_public_feed, "urlopen", open_url)
    assert refresh_public_feed.fetch_public_partial() == "<table></table>"
    assert seen == [refresh_public_feed.PARTIAL_URL]
    monkeypatch.setattr(refresh_public_feed, "urlopen", lambda *a, **k: Response("https://example.org/login"))
    with pytest.raises(ValueError, match="Unexpected redirect"):
        refresh_public_feed.fetch_public_partial()


def test_refresh_failure_keeps_newest_valid_deployed_snapshot(tmp_path, monkeypatch):
    old = {"status": "verified_snapshot", "source_url": refresh_public_feed.URL,
           "observed_utc": "2026-10-27T00:00:00Z", "top_public_dti": .45, "fifth_public_dti": .35}
    newer = {**old, "status": "success", "observed_utc": "2026-10-28T00:00:00Z",
             "top_public_dti": .4544, "fifth_public_dti": .3570}
    out = tmp_path / "feed.json"
    out.write_text(json.dumps(old))
    def fail():
        raise ValueError("offline")
    monkeypatch.setattr(refresh_public_feed, "fetch_public_partial", fail)
    monkeypatch.setattr(refresh_public_feed, "fetch_live_previous", lambda: newer)
    assert refresh_public_feed.main(["--out", str(out), "--fetch-live-previous", "--strict"]) == 1
    result = json.loads(out.read_text())
    assert result["status"] == "unavailable" and result["top_public_dti"] is None
    assert result["last_verified_snapshot"] == newer
    # A forged source or a future timestamp is not accepted as a prior observation.
    monkeypatch.setattr(refresh_public_feed, "fetch_live_previous", lambda: {**newer, "source_url": "https://example.org"})
    out.write_text(json.dumps(old))
    refresh_public_feed.main(["--out", str(out), "--fetch-live-previous"])
    assert json.loads(out.read_text())["last_verified_snapshot"] == old
    monkeypatch.setattr(refresh_public_feed, "fetch_live_previous", lambda: {**newer, "observed_utc": "2100-01-01T00:00:00Z"})
    out.write_text(json.dumps(old))
    refresh_public_feed.main(["--out", str(out), "--fetch-live-previous"])
    assert json.loads(out.read_text())["last_verified_snapshot"] == old


def test_public_partial_header_without_tr_and_only_designated_score_column():
    rows = ''.join(
        f'<tr><td>#{i}</td><td>avatar</td><td>Team {i}</td><td>{score:.4f}</td><td>1.0000</td></tr>'
        for i, score in enumerate([.4544, .3916, .3911, .3724, .3570], 1)
    )
    header = ('<thead><th>Rank</th><th>Team members</th><th>Participant</th>'
              '<th>Best<br>public<br>DW-Tversky (in descending order)</th><th>Shared work</th></thead>')
    html = '<table id="leaderTable">' + header + '<tbody>' + rows + '</tbody></table>'
    parsed = refresh_public_feed.parse_leaderboard(html)
    assert parsed[1] == .4544 and parsed[5] == .3570  # ignore numeric decoy in Shared work
    with pytest.raises(ValueError, match="not recognized"):
        refresh_public_feed.parse_leaderboard(html.replace('.3570', 'missing'))
    with pytest.raises(ValueError, match="not recognized"):
        refresh_public_feed.parse_leaderboard(html.replace('Shared work</th>', 'Another public Tversky</th>'))


def test_pages_foreground_nine_sites_and_do_not_publish_unreplayed_breakthroughs():
    for name in ("index.html", "executive-summary.html", "submission-table.html"):
        html = (ROOT / "docs" / name).read_text()
        assert html.index("GEMSDOE32") < html.index("Archived results, not verified breakthroughs")
        assert "USER/OWNER-REPORTED" in html
        assert "DO NOT SUBMIT" in html.upper()
        assert "first KANLERGEMSDOE2 candidate to beat" not in html
        assert "pure-false-positive" not in html.lower()
    feed = json.loads((ROOT / "docs/data/status_feed.json").read_text())
    assert feed["ok_to_submit"] is False
    for lane in ("kg2s3_hptr_lane", "kg2s3_trbvc_lane", "kg2s3_lope_lane"):
        assert feed[lane]["historical_holdouts_independently_replayed"] is False
        assert feed[lane]["full_registry_independently_checked"] is False
    for token in ("hptr", "trbvc"):
        note = next((ROOT / "docs/downloads").glob(f"kanlergems2-{token}-*DO-NOT-SUBMIT.txt")).read_text().lower()
        assert "do not submit" in note
        assert "not independently replayed" in note
        assert "if submitting" not in note
