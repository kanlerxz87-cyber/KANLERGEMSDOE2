#!/usr/bin/env python3
"""Refresh an explicitly sourced public leaderboard snapshot, or mark it stale.

No login, upload, account quota, file-score association or prediction is involved.
A changed/login page must never be interpreted as a score. This script can run
on GitHub Actions; this sandbox allows no direct DrivenData network access.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
# The public page loads its first table asynchronously via this same-origin
# HTMX partial. Fetching the shell alone yields no <table> in ordinary HTTP.
PARTIAL_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard_partial/?page=1"
ROOT = Path(__file__).resolve().parents[1]


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table = None
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table" and self.table is None:
            self.table = []
        elif self.table is not None and tag == "tr":
            self.row = []
        elif self.row is not None and tag in ("td", "th"):
            self.cell = []
        elif self.cell is not None and tag in ("br", "p", "div"):
            self.cell.append(" ")

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = self.row = self.cell = None


def parse_leaderboard(text: str) -> dict[int, float]:
    parser = Tables()
    parser.feed(text)
    for table in parser.tables:
        headers = " ".join(table[0]).lower() if table else ""
        if "rank" not in headers or "tversky" not in headers or "public" not in headers:
            continue
        found = {}
        for row in table[1:]:
            if not row:
                continue
            rank_match = re.fullmatch(r"#\s*(\d+)", row[0].strip())
            if not rank_match:
                continue
            # Values live in their own score cell. Do not parse a date, name,
            # avatar URL or submission-count field as a leaderboard score.
            scores = [float(c) for c in row[1:] if re.fullmatch(r"(?:0|1)\.\d{4,}", c)]
            if len(scores) != 1 or not 0 <= scores[0] <= 1:
                continue
            rank = int(rank_match.group(1))
            if rank in found:
                raise ValueError("Duplicate leaderboard rank")
            found[rank] = scores[0]
        if all(i in found for i in range(1, 6)) and all(found[i] >= found[i + 1] for i in range(1, 5)):
            return found
    raise ValueError("Public leaderboard table/ranks not recognized; refusing to invent a score")


def fetch_public_partial() -> str:
    """Read the first-page public table referenced by the leaderboard shell."""
    request = Request(PARTIAL_URL, headers={"User-Agent": "GEMS-evidence-feed/1.1 (+public leaderboard read only)"})
    with urlopen(request, timeout=25) as response:
        # A login/challenge redirect must fail, not become a leaderboard snapshot.
        if response.geturl() != PARTIAL_URL:
            raise ValueError("Unexpected redirect, likely authentication or site change")
        body = response.read(5_000_001)
        if len(body) > 5_000_000:
            raise ValueError("Unexpectedly large response")
        return body.decode("utf-8")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/data/public_leaderboard.json")
    ap.add_argument("--input-html", type=Path, help="Offline fixture for testing; never used by scheduled refresh")
    ap.add_argument("--strict", action="store_true", help="Return nonzero on refresh failure")
    args = ap.parse_args(argv)
    previous = {}
    if args.out.is_file():
        try:
            previous = json.loads(args.out.read_text())
        except (OSError, ValueError):
            pass
    observed = datetime.now(timezone.utc).isoformat()
    try:
        if args.input_html:
            text = args.input_html.read_text(encoding="utf-8")
        else:
            text = fetch_public_partial()
        values = parse_leaderboard(text)
        data = {
            "status": "fixture_only" if args.input_html else "success",
            "source_url": URL,
            "retrieved_url": None if args.input_html else PARTIAL_URL,
            "observed_utc": observed,
            "top_public_dti": values[1],
            "fifth_public_dti": values[5],
            "evidence_class": "ORGANIZER PUBLIC LEADERBOARD OBSERVATION; not a submission-page receipt" if not args.input_html else "TEST FIXTURE; not an organizer observation",
            "warning": "Public leaderboard snapshot only; scores and account quota can change.",
        }
        failed = False
    except Exception as exc:
        snapshot = previous if previous.get("status") in ("success", "verified_snapshot") else previous.get("last_verified_snapshot")
        data = {
            "status": "unavailable",
            "source_url": URL,
            "attempted_utc": observed,
            "error": f"{type(exc).__name__}: {exc}",
            "top_public_dti": None,
            "fifth_public_dti": None,
            "last_verified_snapshot": snapshot,
            "warning": "Refresh failed. Any last snapshot is stale and no account quota was checked.",
        }
        failed = True
    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(args.out.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    tmp.replace(args.out)
    print(json.dumps(data, indent=2))
    return 1 if failed and args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
