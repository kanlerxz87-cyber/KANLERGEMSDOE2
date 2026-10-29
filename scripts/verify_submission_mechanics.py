#!/usr/bin/env python3
"""Verification pass 3: submission mechanics.

Checks:
  * the submission note file exists, is <=140 chars, and matches the run card;
  * every docs page / README link to the submission TIFF resolves and its
    SHA-256 matches the run card;
  * fail-closed gates are stated consistently everywhere: OK to download,
    NOT cleared to submit; no page promotes submission.
Exit nonzero on any failure.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    name = card["submission_name"]
    expected_sha = card["raster_sha256"]
    note = card["note"]
    failures = []

    # 1. Note file.
    note_path = ROOT / "docs/downloads" / f"note-{name[:-4]}.txt"
    if not note_path.is_file():
        failures.append(f"missing note file {note_path.name}")
    else:
        note_text = note_path.read_text(encoding="utf-8").strip()
        if len(note_text) > 140:
            failures.append(f"note too long: {len(note_text)} chars")
        if note_text != note:
            failures.append("note file text differs from run card note")

    # 2. TIFF exists and hashes match the card.
    tif = ROOT / "docs/downloads" / name
    if not tif.is_file():
        failures.append(f"missing {name}")
    elif sha256(tif) != expected_sha:
        failures.append(f"sha256 mismatch for {name}")

    # 3. Every page/readme that links the download resolves and matches the card.
    pages = list((ROOT / "docs").glob("*.html")) + [ROOT / "README.md", ROOT / "EXECUTIVE_SUMMARY.md"]
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for link_name in set(re.findall(r"downloads/([A-Za-z0-9._-]+\.tif)", text)):
            p = ROOT / "docs" / "downloads" / link_name
            if not p.is_file():
                failures.append(f"{page.name}: broken link downloads/{link_name}")
            elif link_name == name and sha256(p) != expected_sha:
                failures.append(f"{page.name}: linked {name} hash mismatch")
        upper = text.upper()
        if "PROMOTE" in upper and "OK TO SUBMIT" in upper:
            failures.append(f"{page.name}: contains promotion language")
        if "TWO VERDICTS" in upper:
            failures.append(f"{page.name}: contains contradictory two-verdicts language")

    # 4. Fail-closed verdict stated on the public pages.
    for page in (ROOT / "docs" / "index.html", ROOT / "docs" / "executive-summary.html",
                 ROOT / "docs" / "submission-table.html", ROOT / "README.md"):
        text = page.read_text(encoding="utf-8").lower()
        if "not cleared to submit" not in text:
            failures.append(f"{page.name}: missing 'not cleared to submit'")
        if card["ok_to_download"] and "ok to download" not in text and page.suffix == ".md":
            failures.append(f"{page.name}: missing 'ok to download'")

    # 5. Run-card fail-closed fields.
    if card["verdict"] != "negative" or card["ok_to_submit"] is not False:
        failures.append("run card is not fail-closed negative")
    if card.get("ok_to_download") is not True:
        failures.append("run card ok_to_download is not true")

    for f in failures:
        print("FAIL:", f)
    if not failures:
        print("PASS - submission mechanics: note <=140 chars and matches card; TIFF hash matches; all download links resolve; fail-closed gates consistent on pages and README")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
