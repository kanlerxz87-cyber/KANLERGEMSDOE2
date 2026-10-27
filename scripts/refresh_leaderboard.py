#!/usr/bin/env python3
"""Refresh an official *public* leaderboard snapshot, never a submission receipt.

On failure the existing snapshot is untouched. GitHub Actions may run this on
its unrestricted runner; the current sandbox's shell cannot reach DrivenData.
"""
from __future__ import annotations

import argparse
import json
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
ROOT = Path(__file__).resolve().parents[1]


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.row = None
        self.cell = None
        self.rows = []

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1
        elif self.depth and tag == "tr":
            self.row = []
        elif self.depth and self.row is not None and tag in {"td", "th"}:
            self.cell = []

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None
            self.cell = None
        elif tag == "table" and self.depth:
            self.depth -= 1


def parse_leaderboard(html: str) -> dict[int, float]:
    parser = TableParser()
    parser.feed(html)
    values = {}
    for cells in parser.rows:
        if not cells:
            continue
        match = re.fullmatch(r"#\s*(\d+)", cells[0])
        if not match:
            continue
        rank = int(match.group(1))
        if rank not in (1, 5):
            continue
        candidates = [float(cell.strip()) for cell in cells[1:]
                      if re.fullmatch(r"(?:0|1)\.\d{4,}", cell.strip())]
        if len(candidates) != 1 or rank in values or not 0 <= candidates[0] <= 1:
            raise ValueError("Ambiguous rank row; refusing to update snapshot")
        values[rank] = candidates[0]
    if set(values) != {1, 5} or values[1] < values[5]:
        raise ValueError("Could not locate valid ranks 1 and 5")
    return values


def refresh(output: Path) -> dict:
    request = urllib.request.Request(URL, headers={"User-Agent": "KANLERGEMSDOE2-public-snapshot/1.0"})
    with urllib.request.urlopen(request, timeout=20) as response:
        parsed = urlparse(response.geturl())
        if parsed.scheme != "https" or parsed.hostname not in {"www.drivendata.org", "drivendata.org"} or "leaderboard" not in parsed.path:
            raise ValueError("Unexpected leaderboard redirect")
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("Leaderboard response exceeds safe size")
    values = parse_leaderboard(raw.decode("utf-8"))
    snapshot = {
        "source_url": URL,
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "source_class": "official public leaderboard snapshot, not a submission-page receipt",
        "public_rank_1": values[1], "public_rank_5": values[5],
        "note": "Public leaderboard values may have changed since this snapshot; see the live source.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_suffix(output.suffix + ".partial")
    try:
        tmp.write_text(json.dumps(snapshot, indent=2, allow_nan=False) + "\n")
        tmp.replace(output)
    finally:
        tmp.unlink(missing_ok=True)
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/data/leaderboard_snapshot.json")
    args = parser.parse_args()
    print(json.dumps(refresh(args.output), indent=2))


if __name__ == "__main__":
    main()
