#!/usr/bin/env python3
"""Refresh an explicitly sourced public leaderboard snapshot, or mark it stale.

No login, upload, account quota, file-score association or prediction is involved.
A changed/login page must never be interpreted as a score. This script can run
on GitHub Actions; this sandbox allows no direct DrivenData network access.
"""
from __future__ import annotations

import argparse
import json
import math
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
LIVE_SNAPSHOT_URL = "https://kanlerxz87-cyber.github.io/KANLERGEMSDOE2/docs/data/public_leaderboard.json"
ROOT = Path(__file__).resolve().parents[1]


class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table = None
        self.row = None
        self.cell = None
        self.in_head = False
        self.implicit_head_row = False

    def handle_starttag(self, tag, attrs):
        if tag == "table" and self.table is None:
            self.table = []
        elif self.table is not None and tag == "thead":
            self.in_head = True
        elif self.table is not None and tag == "tr":
            self.row = []
            self.implicit_head_row = False
        elif self.table is not None and tag == "th" and self.in_head and self.row is None:
            # DrivenData's partial currently places <th> directly in <thead>
            # without an enclosing <tr>. Preserve it as one implicit header row.
            self.row = []
            self.implicit_head_row = True
            self.cell = []
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
        elif tag == "thead" and self.table is not None:
            if self.implicit_head_row and self.row is not None:
                self.table.append(self.row)
                self.row = None
            self.in_head = self.implicit_head_row = False
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = self.row = self.cell = None
            self.in_head = self.implicit_head_row = False


def parse_leaderboard(text: str) -> dict[int, float]:
    parser = Tables()
    parser.feed(text)
    for table in parser.tables:
        if not table:
            continue
        headers = [h.lower() for h in table[0]]
        score_columns = [i for i, h in enumerate(headers) if "tversky" in h and "public" in h]
        if not headers or "rank" not in headers[0] or len(score_columns) != 1:
            continue
        score_column = score_columns[0]
        found = {}
        for row in table[1:]:
            if len(row) != len(headers):
                continue
            rank_match = re.fullmatch(r"#\s*(\d+)", row[0].strip())
            if not rank_match:
                continue
            # Only the uniquely identified public-score column is trusted; a
            # name, count, timestamp, or other numeric column is never a score.
            score_cell = row[score_column]
            if not re.fullmatch(r"(?:0|1)\.\d{4,}", score_cell):
                continue
            score = float(score_cell)
            if not 0 <= score <= 1:
                continue
            rank = int(rank_match.group(1))
            if rank in found:
                raise ValueError("Duplicate leaderboard rank")
            found[rank] = score
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


def verified_snapshot(data: object, now: datetime) -> tuple[datetime, dict] | None:
    """Validate a prior public observation before showing it as stale fallback."""
    if not isinstance(data, dict):
        return None
    if data.get("status") == "unavailable":
        data = data.get("last_verified_snapshot")
    if not isinstance(data, dict) or data.get("status") not in ("success", "verified_snapshot"):
        return None
    if data.get("source_url") != URL:
        return None
    first, fifth = data.get("top_public_dti"), data.get("fifth_public_dti")
    if (type(first) not in (int, float) or type(fifth) not in (int, float)
            or not math.isfinite(first) or not math.isfinite(fifth)
            or not 0 <= fifth <= first <= 1):
        return None
    try:
        observed = datetime.fromisoformat(data["observed_utc"].replace("Z", "+00:00"))
        if observed.tzinfo is None or observed > now:
            return None
    except (AttributeError, KeyError, TypeError, ValueError, OverflowError):
        return None
    return observed, data


def fetch_live_previous() -> object:
    """Best-effort read of our deployed prior snapshot, never an organizer login."""
    request = Request(LIVE_SNAPSHOT_URL, headers={"User-Agent": "GEMS-evidence-feed/1.1"})
    with urlopen(request, timeout=10) as response:
        if response.geturl() != LIVE_SNAPSHOT_URL:
            raise ValueError("Unexpected prior-snapshot redirect")
        body = response.read(100_001)
        if len(body) > 100_000:
            raise ValueError("Unexpectedly large prior snapshot")
    return json.loads(body.decode("utf-8"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "docs/data/public_leaderboard.json")
    ap.add_argument("--input-html", type=Path, help="Offline fixture for testing; never used by scheduled refresh")
    ap.add_argument("--fetch-live-previous", action="store_true", help="On failure, also consider the prior deployed public snapshot")
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
        now = datetime.now(timezone.utc)
        candidates = [verified_snapshot(previous, now)]
        if args.fetch_live_previous and not args.input_html:
            try:
                candidates.append(verified_snapshot(fetch_live_previous(), now))
            except Exception:
                # A broken old deployment must never hide the original failure.
                pass
        valid = [item for item in candidates if item is not None]
        snapshot = max(valid, key=lambda item: item[0])[1] if valid else None
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
