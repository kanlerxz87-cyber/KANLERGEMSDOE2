#!/usr/bin/env python3
"""Fetch and validate the official public leaderboard; preserve a stale snapshot on failure."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
from urllib.parse import urlparse
from urllib.request import Request, urlopen

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"

class Tables(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.table = self.row = self.cell = None
        self.depth = 0

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.depth += 1
            if self.depth == 1:
                self.table = []
        elif self.depth == 1 and tag == "tr":
            self.row = []
        elif self.depth == 1 and tag in ("td", "th") and self.row is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, text):
        if self.cell is not None:
            self.cell.append(text)

    def handle_endtag(self, tag):
        if self.depth == 1 and tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join(" ".join(self.cell).split()))
            self.cell = None
        elif self.depth == 1 and tag == "tr" and self.row is not None:
            if self.row:
                self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.depth:
            if self.depth == 1 and self.table is not None:
                self.tables.append(self.table)
                self.table = None
            self.depth -= 1


def parse(html: str) -> dict:
    p = Tables(); p.feed(html)
    for table in p.tables:
        for hi, headers in enumerate(table):
            normalized = [" ".join(x.lower().split()) for x in headers]
            rank_index = next((i for i, x in enumerate(normalized) if x == "rank"), None)
            participant_index = next((i for i, x in enumerate(normalized) if "participant" in x), None)
            score_index = next((i for i, x in enumerate(normalized) if "tversky" in x and "public" in x), None)
            if None in (rank_index, participant_index, score_index):
                continue
            top = []
            for cells in table[hi+1:]:
                if len(cells) <= max(rank_index, participant_index, score_index):
                    continue
                match = re.fullmatch(r"#?\s*(\d+)", cells[rank_index].strip())
                if not match or int(match.group(1)) != 1:
                    continue
                token = cells[score_index].strip()
                if not re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", token):
                    raise ValueError("Invalid rank-one public score")
                name = re.split(r"\s+\d+\s*(?:min|h|d|w|mo|y)\b|\s+[·⸱]", cells[participant_index], maxsplit=1)[0].strip()
                if not name or len(name) > 100:
                    raise ValueError("Invalid rank-one participant")
                top.append({"rank": 1, "participant": name, "score": float(token)})
            if len(top) != 1:
                raise ValueError("Leaderboard must have exactly one valid rank-one row")
            return top[0]
    raise ValueError("Official public DW-Tversky leaderboard table not found")


def refresh(out: Path) -> dict:
    req = Request(URL, headers={"User-Agent": "KANLERGEMSDOE2-public-feed/1.0"})
    with urlopen(req, timeout=30) as response:
        final = urlparse(response.geturl())
        if final.scheme != "https" or final.netloc != "www.drivendata.org" or final.path != urlparse(URL).path:
            raise ValueError("Leaderboard redirected to a different page, possibly login")
        if response.status != 200:
            raise ValueError("Leaderboard HTTP status is not 200")
        content_type = response.headers.get_content_type()
        if content_type != "text/html":
            raise ValueError("Leaderboard response is not HTML")
        body = response.read(3_000_001)
        if len(body) > 3_000_000:
            raise ValueError("Leaderboard response is too large")
    top = parse(body.decode("utf-8", "replace"))
    result = {"source": URL, "observed_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "method": "Direct public leaderboard fetch", "evidence_class": "ORGANIZER-PUBLISHED PUBLIC LEADERBOARD; not a submission-page receipt for this project", **top}
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    tmp.replace(out)
    return result


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=Path(__file__).resolve().parents[1] / "docs/data/leaderboard.json")
    ap.add_argument("--allow-stale", action="store_true", help="Keep existing timestamped snapshot and exit zero on fetch/parse failure")
    a = ap.parse_args()
    try:
        print(json.dumps(refresh(a.out)))
    except Exception as e:
        print(f"Leaderboard refresh failed; existing timestamped snapshot unchanged: {type(e).__name__}: {e}", file=sys.stderr)
        if not a.allow_stale or not a.out.is_file():
            return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
