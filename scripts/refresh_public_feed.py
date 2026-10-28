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
# The public page loads this server-rendered table asynchronously (HTMX).
PARTIAL_URL = URL.replace("/leaderboard/", "/leaderboard_partial/")
ROOT = Path(__file__).resolve().parents[1]


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table_classes: list[set[str]] = []
        self.table = None
        self.classes: set[str] = set()
        self.row = None
        self.cell = None

    def handle_starttag(self, tag, attrs):
        if tag == "table" and self.table is None:
            self.table = []
            self.classes = set(dict(attrs).get("class", "").split())
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
            self.table_classes.append(self.classes)
            self.table = self.row = self.cell = None
            self.classes = set()


def parse_leaderboard(text: str, *, allow_official_headerless_fragment: bool = False) -> dict[int, float]:
    parser = Tables()
    parser.feed(text)
    for table, classes in zip(parser.tables, parser.table_classes):
        headers = " ".join(table[0]).lower() if table else ""
        headered = all(term in headers for term in ("rank", "tversky", "public"))
        # The public HTMX fragment observed 2026-10-28 contains a headerless
        # <table class="leaderTable ... scores-table"> with exactly five cells:
        # rank, avatars, participant, score, shared work. Only the fixed official
        # fragment URL can enable this fallback; never treat an arbitrary page as it.
        fragment = (allow_official_headerless_fragment and not headered
                    and {"leaderTable", "scores-table"}.issubset(classes))
        if not (headered or fragment):
            continue
        found = {}
        for row in (table[1:] if headered else table):
            if not row:
                continue
            rank_match = re.fullmatch(r"#\s*(\d+)", row[0].strip())
            if not rank_match:
                continue
            # For the headerless fragment, only column 4 is a score. Never
            # mistake a participant name, date or submission count for one.
            candidates = [row[3]] if fragment and len(row) == 5 else (row[1:] if headered else [])
            scores = [float(c) for c in candidates if re.fullmatch(r"(?:0|1)\.\d{4,}", c)]
            if len(scores) != 1 or not 0 <= scores[0] <= 1:
                continue
            rank = int(rank_match.group(1))
            if rank in found:
                raise ValueError("Duplicate leaderboard rank")
            found[rank] = scores[0]
        if all(i in found for i in range(1, 6)) and all(found[i] >= found[i + 1] for i in range(1, 5)):
            return found
    raise ValueError("Public leaderboard table/ranks not recognized; refusing to invent a score")


def fetch_public_html(url: str) -> str:
    """Fetch only the exact public page or its official table fragment."""
    if url not in (URL, PARTIAL_URL):
        raise ValueError("Unexpected public leaderboard endpoint")
    request = Request(url, headers={"User-Agent": "GEMS-evidence-feed/1.0 (+public leaderboard read only)"})
    with urlopen(request, timeout=25) as response:
        if response.geturl().split("?")[0].rstrip("/") != url.rstrip("/"):
            raise ValueError("Unexpected redirect, likely authentication or site change")
        text = response.read(5_000_001).decode("utf-8")
        if len(text) > 5_000_000:
            raise ValueError("Unexpectedly large response")
    return text


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
        fetch_url = None
        if args.input_html:
            values = parse_leaderboard(args.input_html.read_text(encoding="utf-8"))
        else:
            fetch_url = URL
            text = fetch_public_html(URL)
            try:
                values = parse_leaderboard(text)
            except ValueError:
                # The page shell currently loads its table asynchronously.
                # A fragment is accepted only if the exact URL is returned and
                # the same strict rank/header/score checks pass.
                fetch_url = PARTIAL_URL
                values = parse_leaderboard(fetch_public_html(PARTIAL_URL), allow_official_headerless_fragment=True)
        data = {
            "status": "fixture_only" if args.input_html else "success",
            "source_url": URL,
            "fetch_url": fetch_url,
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
