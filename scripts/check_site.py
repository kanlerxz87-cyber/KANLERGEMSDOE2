#!/usr/bin/env python3
"""Validate local HTML links and prevent accidental TIFF/ZIP publication."""
from html.parser import HTMLParser
from pathlib import Path
import urllib.parse

ROOT = Path(__file__).resolve().parents[1] / 'docs'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        self.links.extend(v for k, v in attrs if k in ('href', 'src') and v)


def check():
    errors = []
    for path in ROOT.rglob('*.html'):
        parser = Links()
        parser.feed(path.read_text())
        for link in parser.links:
            url = urllib.parse.urlparse(link)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (path.parent / urllib.parse.unquote(url.path)).resolve()
            if not target.is_relative_to(ROOT.resolve()) or not target.exists():
                errors.append(f'{path.name}: unresolved local link {link}')
    # Current decision is negative: no accidental data publication is allowed.
    for suffix in ('*.tif', '*.tiff', '*.zip'):
        errors.extend('Unapproved download: ' + str(p) for p in ROOT.rglob(suffix))
    return errors


if __name__ == '__main__':
    errors = check()
    print('\n'.join(errors) if errors else 'PASS: local HTML links resolve; no unapproved raster downloads')
    raise SystemExit(bool(errors))
