"""Offline tests for the pinned restoration and Pages integrity."""
from html.parser import HTMLParser
import hashlib
import json
from pathlib import Path

import pytest

import restore_inputs

ROOT = Path(__file__).resolve().parents[1]


def test_restoration_concatenates_pinned_parts_and_never_overwrites(tmp_path, monkeypatch):
    parts = {"first": b"verified-", "second": b"bytes"}
    expected = b"verified-bytes"
    record = {"id": "synthetic", "repository": "buffedlizard55-lab/GEMSDOE24", "commit": "a" * 40,
              "paths": list(parts), "destination": "data/restored.tif", "bytes": len(expected),
              "sha256": hashlib.sha256(expected).hexdigest()}
    def fake_git(*args, **kwargs):
        if "show" in args:
            part = args[-1].split(":", 1)[1]
            kwargs["stdout"].write(parts[part])
    monkeypatch.setattr(restore_inputs, "git", fake_git)
    assert restore_inputs.restore(record, root=tmp_path) == "restored-and-verified"
    dest = tmp_path / record["destination"]
    assert dest.read_bytes() == expected
    assert restore_inputs.restore(record, root=tmp_path, verify_only=True) == "verified-existing"
    dest.write_bytes(b"different")
    with pytest.raises(ValueError, match="not overwritten"):
        restore_inputs.restore(record, root=tmp_path)
    assert dest.read_bytes() == b"different"


def test_restore_rejects_path_escape_and_bad_parts(tmp_path, monkeypatch):
    record = {"id": "bad", "repository": "buffedlizard55-lab/GEMSDOE24", "commit": "a" * 40,
              "paths": ["../bad"], "destination": "../escape", "bytes": 1, "sha256": "0" * 64}
    with pytest.raises(ValueError, match="under data"):
        restore_inputs.restore(record, root=tmp_path)
    record["destination"] = "data/file.tif"
    monkeypatch.setattr(restore_inputs, "git", lambda *args, **kwargs: None)
    with pytest.raises(ValueError, match="Invalid pinned Git path"):
        restore_inputs.restore(record, root=tmp_path)
    assert not (tmp_path / "data/file.tif").exists()
    assert not list((tmp_path / "data").glob("*.partial"))


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.local = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ("href", "src") and value and not value.startswith(("https://", "http://", "#", "mailto:")):
                self.local.append(value.split("#", 1)[0].split("?", 1)[0])


def test_pages_links_resolve_and_no_old_uploads_are_published():
    docs = ROOT / "docs"
    for html in docs.glob("*.html"):
        parser = Links()
        parser.feed(html.read_text())
        for link in parser.local:
            assert (docs / link).is_file(), f"Broken local link {html.name}: {link}"
    assert not list(docs.rglob("*.tif")) and not list(docs.rglob("*.zip"))
    assert "DO NOT SUBMIT" in (docs / "index.html").read_text()
    assert "static observation" in (docs / "index.html").read_text()


def test_active_source_has_no_merge_conflict_markers():
    roots = [ROOT / "scripts", ROOT / "tests", ROOT / ".github/workflows", ROOT / "docs"]
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix in (".py", ".html", ".js", ".yml", ".json"):
                for line in path.read_text().splitlines():
                    assert not line.startswith(("<<<<<<< ", "=======", ">>>>>>> ")), f"Conflict marker in {path}"
