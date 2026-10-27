#!/usr/bin/env python3
"""Refresh a public leaderboard observation; never fabricate a missing value.

Uses only the public organizer page. Errors replace the status with unavailable
and retain the old observation solely as a dated snapshot, not a fresh value.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request, urlopen

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"


class Tables(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[str]]] = []
        self.table: list[list[str]] | None = None
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "table" and self.table is None:
            self.table = []
        elif tag == "tr" and self.table is not None:
            self.row = []
        elif tag in {"td", "th"} and self.row is not None:
            self.cell = []
        elif tag == "br" and self.cell is not None:
            self.cell.append(" ")

    def handle_data(self, data: str) -> None:
        if self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None and self.table is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.table is not None:
            self.tables.append(self.table)
            self.table = None


def parse_public_leader(html: str) -> float:
    """Extract #1's DW-Tversky from a labeled leaderboard table, or fail."""
    parser = Tables()
    parser.feed(html)
    for table in parser.tables:
        if not table:
            continue
        header = " ".join(table[0]).lower()
        if "rank" not in header or "tversky" not in header:
            continue
        for row in table[1:]:
            if len(row) < 4 or not re.fullmatch(r"#?\s*1", row[0].strip()):
                continue
            # The official table places the public DW-Tversky in column 4.
            cell = row[3].strip()
            if not re.fullmatch(r"(?:0(?:\.\d+)?|1(?:\.0+)?)", cell):
                raise ValueError("leader score cell is not a single [0,1] number")
            value = float(cell)
            if not 0 <= value <= 1:
                raise ValueError("leader score is outside [0,1]")
            return value
    raise ValueError("labeled #1 DW-Tversky table not found")


def refresh(output: Path, *, timeout: float = 25.0) -> dict:
    old = {}
    if output.exists():
        try:
            old = json.loads(output.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            pass
    now = datetime.now(timezone.utc).isoformat()
    try:
        request = Request(URL, headers={"User-Agent": "KANLERGEMSDOE2 public leaderboard monitor/1.0"})
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise ValueError(f"unexpected HTTP status {response.status}")
            page = response.read(5_000_001)
        if len(page) > 5_000_000:
            raise ValueError("leaderboard response exceeded size limit")
        score = parse_public_leader(page.decode("utf-8"))
        return {
            "status": "fresh", "observed_utc": now, "source": URL,
            "observation": {"rank": 1, "score": score},
            "evidence_class": "ORGANIZER-PUBLISHED public leaderboard observation; not a submission-page receipt",
            "note": "Public leaderboard only; not a prediction for any candidate and subject to change.",
        }
    except Exception as exc:
        previous = old.get("observation") or old.get("previous_observation")
        return {
            "status": "unavailable", "checked_utc": now, "source": URL,
            "observation": None,
            "previous_observation": previous,
            "previous_observed_utc": old.get("observed_utc") or old.get("previous_observed_utc"),
            "reason": f"{type(exc).__name__}: {str(exc)[:180]}",
            "note": "Refresh failed; the old snapshot is not asserted to be current.",
        }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--output", type=Path, default=Path("docs/data/leaderboard.json"))
    ap.add_argument("--require-success", action="store_true")
    args = ap.parse_args()
    result = refresh(args.output)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 1 if args.require_success and result["status"] != "fresh" else 0


if __name__ == "__main__":
    raise SystemExit(main())
