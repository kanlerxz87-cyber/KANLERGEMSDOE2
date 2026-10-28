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
        headers = [cell.lower() for cell in table[0]] if table else []
        ranks = [i for i, cell in enumerate(headers) if cell.strip() == "rank"]
        public_scores = [i for i, cell in enumerate(headers) if "public" in cell and "tversky" in cell]
        if len(ranks) != 1 or len(public_scores) != 1 or ranks[0] == public_scores[0]:
            continue
        rank_col, score_col = ranks[0], public_scores[0]
        found = {}
        for row in table[1:]:
            if len(row) != len(headers):
                continue
            rank_match = re.fullmatch(r"#\s*(\d+)", row[rank_col].strip())
            score_text = row[score_col].strip()
            if not rank_match or not re.fullmatch(r"(?:0|1)\.\d{4,}", score_text):
                continue
            score = float(score_text)
            if not 0 <= score <= 1:
                continue
            rank = int(rank_match.group(1))
            if rank in found:
                raise ValueError("Duplicate leaderboard rank")
            found[rank] = score
        if all(i in found for i in range(1, 6)) and all(found[i] >= found[i + 1] for i in range(1, 5)):
            return found
    raise ValueError("Public leaderboard table/ranks not recognized; refusing to invent a score")


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
            request = Request(URL, headers={"User-Agent": "GEMS-evidence-feed/1.0 (+public leaderboard read only)"})
            with urlopen(request, timeout=25) as response:
                if response.geturl().split("?")[0].rstrip("/") != URL.rstrip("/"):
                    raise ValueError("Unexpected redirect, likely authentication or site change")
                text = response.read(5_000_001).decode("utf-8")
                if len(text) > 5_000_000:
                    raise ValueError("Unexpectedly large response")
        values = parse_leaderboard(text)
        data = {
            "status": "fixture_only" if args.input_html else "success",
            "source_url": URL,
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
