#!/usr/bin/env python3
"""Read-only public leaderboard markup diagnostic; no account or submissions.

A single GitHub Actions notice reports numeric samples, structural classes,
and query-free public endpoint paths only. It never records participant names,
HTML, cookies, tokens, or full URLs with query strings.
"""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from refresh_public_feed import URL, Tables, parse_leaderboard

PARTIAL_URL = URL.replace("/leaderboard/", "/leaderboard_partial/")


class Structure(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, str]] = []
        self.scores: list[dict] = []
        self.paths: set[str] = set()
        self.title = ""
        self.visible_signin = False

    def handle_starttag(self, tag, attrs) -> None:
        attrs = dict(attrs)
        class_id = " ".join(attrs.get(k, "") for k in ("id", "class", "role"))[:120]
        # Classes/IDs are structure, but filter out unexpected characters.
        class_id = re.sub(r"[^A-Za-z0-9_:. -]", "", class_id)
        class_id = re.sub(r"leaderRow_\d+", "leaderRow", class_id)
        self.stack.append((tag, class_id.strip()))
        for key in ("href", "src", "hx-get", "hx-post", "data-url"):
            value = attrs.get(key, "")
            if re.search(r"leaderboard|ranking|/api/", value, re.I):
                path = urlsplit(value)._replace(query="", fragment="").geturl()
                if len(path) < 180 and not re.search(r"token|session|csrf|cookie|password", path, re.I):
                    self.paths.add(path)

    def handle_startendtag(self, tag, attrs) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag) -> None:
        # HTML is not always strictly nested; pop the matching tag and descendants.
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_data(self, data) -> None:
        text = data.strip()
        if not text:
            return
        if self.stack and self.stack[-1][0] == "title":
            self.title = text[:100]
        if re.search(r"sign in to (?:view|see) the leaderboard", text, re.I):
            self.visible_signin = True
        # Scores only; never capture free-text rows or participants.
        if re.fullmatch(r"0\.\d{4,6}", text) and len(self.scores) < 6:
            self.scores.append({"value": text, "ancestors": self.stack[-5:]})


def main() -> None:
    report: dict = {}
    try:
        req = Request(PARTIAL_URL, headers={"User-Agent": "GEMS-evidence-feed/1.0 (+public leaderboard read only)"})
        with urlopen(req, timeout=25) as response:
            html = response.read(5_000_001).decode("utf-8", errors="replace")
            report.update(status=response.status, chars=len(html),
                          url=response.geturl().split("?")[0])
        structure = Structure()
        structure.feed(html)
        parser = Tables()
        parser.feed(html)
        report.update(title=structure.title, table_count=len(parser.tables),
                      table_classes=[sorted(classes) for classes in parser.table_classes[:2]],
                      table_ids=parser.table_ids[:2],
                      numeric_score_samples=structure.scores,
                      query_free_endpoint_paths=sorted(structure.paths)[:20],
                      visible_signin_message=structure.visible_signin)
        try:
            values = parse_leaderboard(html, allow_official_headerless_fragment=True)
            report["parser_recognized_ranks"] = len(values)
            report["top_public_dti"] = values[1]
            report["fifth_public_dti"] = values[5]
        except ValueError as exc:
            report["parser_error"] = str(exc)
    except Exception as exc:
        report["unavailable"] = type(exc).__name__
    text = json.dumps(report, ensure_ascii=True, separators=(",", ":"))[:6000]
    safe = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::notice title=Public feed structure::{safe}")


if __name__ == "__main__":
    main()
