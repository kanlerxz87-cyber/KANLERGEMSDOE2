#!/usr/bin/env python3
"""Report non-personal table structure of the public feed to GitHub Actions annotations.

This is a read-only diagnostic, not a score, an account check, or a submission.
It prints headers and numeric-only cells from two rows, never names or raw HTML.
"""
from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen

from refresh_public_feed import URL, Tables, parse_leaderboard


def notice(title: str, text: str) -> None:
    # Actions workflow-command escaping prevents remote text from injecting commands.
    safe = text.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::notice title={title}::{safe}")


class Scripts(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.items: list[list] = []
        self.current: list | None = None

    def handle_starttag(self, tag, attrs) -> None:
        if tag == "script":
            self.current = [dict(attrs), ""]
            self.items.append(self.current)

    def handle_data(self, data) -> None:
        if self.current is not None:
            self.current[1] += data

    def handle_endtag(self, tag) -> None:
        if tag == "script":
            self.current = None


def inspect_script(label: str, text: str) -> None:
    """Emit endpoint paths and counts only, never public team names or tokens."""
    count = len(re.findall(r"leaderboard|ranking", text, re.I))
    paths = set(re.findall(r"[\"']((?:/|https?://)[^\"'\s<>]{1,180}(?:leaderboard|ranking)[^\"'\s<>]*)[\"']", text, re.I))
    clean = []
    for path in sorted(paths):
        path = urlsplit(path)._replace(query="", fragment="").geturl()
        if not re.search(r"csrf|token|cookie|password|session", path, re.I):
            clean.append(path)
    if count or clean:
        notice("Script hints", f"{label}; matches={count}; endpoint_paths={clean[:8]!r}"[:900])


def main() -> None:
    try:
        req = Request(URL, headers={"User-Agent": "GEMS-evidence-feed/1.0 (+public leaderboard read only)"})
        with urlopen(req, timeout=25) as response:
            html = response.read(5_000_001).decode("utf-8")
            notice("Response", f"status={response.status}; url={response.geturl().split('?')[0]}; chars={len(html)}")
        scripts = Scripts()
        scripts.feed(html)
        js_fetched = 0
        for attrs, content in scripts.items:
            src = attrs.get("src", "")
            clean_src = urlsplit(src)._replace(query="", fragment="").geturl()
            notice("Script", f"src={clean_src}; id={attrs.get('id', '')}; type={attrs.get('type', '')}; inline_chars={len(content)}")
            inspect_script(f"inline {attrs.get('id', '')}", content)
            full = urljoin(URL, src)
            if src and urlsplit(full).hostname == urlsplit(URL).hostname and js_fetched < 8:
                js_fetched += 1
                try:
                    req_js = Request(full, headers={"User-Agent": "GEMS-public-feed-diagnostic/1.0"})
                    with urlopen(req_js, timeout=8) as response:
                        inspect_script(clean_src, response.read(1_000_000).decode("utf-8", errors="replace"))
                except Exception as exc:
                    notice("Script unavailable", f"{clean_src}: {type(exc).__name__}")
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
