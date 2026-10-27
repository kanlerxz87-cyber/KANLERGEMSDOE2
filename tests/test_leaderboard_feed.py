"""No stale score is silently relabeled as a fresh leaderboard observation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from urllib.error import URLError

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("refresh_leaderboard", ROOT / "scripts/refresh_leaderboard.py")
assert spec and spec.loader
feed = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feed)


HTML = '''<html><table><thead><tr><th>Rank</th><th>Team members</th><th>Participant</th>
<th>Best public DW-Tversky</th><th>Shared work</th></tr></thead><tbody>
<tr><td>#1</td><td><a>avatar</a></td><td>someone</td><td>0.4544</td><td></td></tr>
<tr><td>#2</td><td></td><td>other</td><td>0.3916</td><td></td></tr></tbody></table></html>'''


def test_parse_requires_labeled_first_row() -> None:
    assert feed.parse_public_leader(HTML) == 0.4544
    for bad in ("", HTML.replace("DW-Tversky", "some other metric"), HTML.replace("0.4544", "1.20"),
                HTML.replace("#1", "#2"), HTML.replace("0.4544", "0.4544 approx")):
        with pytest.raises(ValueError):
            feed.parse_public_leader(bad)


def test_success_and_failure_distinguish_fresh_from_previous(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "leaderboard.json"
    output.write_text(json.dumps({"status": "snapshot", "observed_utc": "2026-10-27", "observation": {"rank": 1, "score": 0.4544}}))

    class Response:
        status = 200
        def __enter__(self): return self
        def __exit__(self, *args): return None
        def read(self, size): return HTML.encode()

    monkeypatch.setattr(feed, "urlopen", lambda *args, **kwargs: Response())
    fresh = feed.refresh(output)
    assert fresh["status"] == "fresh" and fresh["observation"]["score"] == 0.4544
    assert "not a submission-page receipt" in fresh["evidence_class"]
    output.write_text(json.dumps(fresh))
    def fail(*args, **kwargs):
        raise URLError("offline")
    monkeypatch.setattr(feed, "urlopen", fail)
    unavailable = feed.refresh(output)
    assert unavailable["status"] == "unavailable" and unavailable["observation"] is None
    assert unavailable["previous_observation"]["score"] == 0.4544
    assert unavailable["previous_observed_utc"] == fresh["observed_utc"]
    assert "not asserted to be current" in unavailable["note"]
