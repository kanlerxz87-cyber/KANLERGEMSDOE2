#!/usr/bin/env python3
"""Report non-personal table structure of the public feed to GitHub Actions annotations.

This is a read-only diagnostic, not a score, an account check, or a submission.
It prints headers and numeric-only cells from two rows, never names or raw HTML.
"""
from __future__ import annotations

import re
from urllib.request import Request, urlopen

from refresh_public_feed import URL, Tables, parse_leaderboard


def notice(title: str, text: str) -> None:
    # Actions workflow-command escaping prevents remote text from injecting commands.
    safe = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::notice title={title}::{safe}")


def main() -> None:
    try:
        req = Request(URL, headers={"User-Agent": "GEMS-evidence-feed/1.0 (+public leaderboard read only)"})
        with urlopen(req, timeout=25) as response:
            html = response.read(5_000_001).decode("utf-8")
            notice("Response", f"status={response.status}; url={response.geturl().split('?')[0]}; chars={len(html)}")
        parser = Tables()
        parser.feed(html)
        notice("Tables", f"count={len(parser.tables)}")
        for i, table in enumerate(parser.tables[:8]):
            headers = table[0] if table else []
            samples = []
            for row in table[1:3]:
                numeric = [c for c in row if re.fullmatch(r"[#\d.\s]+", c)]
                samples.append({"cells": len(row), "numeric_only": numeric[:8]})
            notice(f"Table {i}", f"headers={headers!r}; rows={len(table)}; sample={samples!r}"[:900])
        try:
            values = parse_leaderboard(html)
            notice("Parser", f"recognized={len(values)} ranks")
        except ValueError as exc:
            notice("Parser", f"not recognized: {exc}")
    except Exception as exc:
        notice("Feed diagnostic", f"unavailable: {type(exc).__name__}: {exc}")


if __name__ == "__main__":
    main()
