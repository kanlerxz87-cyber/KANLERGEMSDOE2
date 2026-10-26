from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PAGES = [ROOT / 'index.html', ROOT / 'docs/k2-executive-summary.html',
         ROOT / 'docs/k2-how-to-submit.html', ROOT / 'docs/k2-research.html']


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs:
                self.links.append(attrs[key])


def test_all_local_links_exist_and_fragments_resolve():
    missing = []
    for page in PAGES:
        parser = Links(); parser.feed(page.read_text())
        for value in parser.links:
            url = urlsplit(value)
            if url.scheme or url.netloc:
                continue
            path = (page.parent / unquote(url.path)).resolve() if url.path else page
            if not path.is_file():
                missing.append((page.name, value))
            elif url.fragment and path.suffix == '.html':
                target = Links(); target.feed(path.read_text())
                if unquote(url.fragment) not in target.ids:
                    missing.append((page.name, value))
    assert not missing, missing


def test_status_and_reference_scope_are_visible():
    for path in PAGES[:2]:
        text = path.read_text()
        assert text.count('Reference download only') == 9
        assert 'Not estimable' in text
        assert text.count('DO NOT SUBMIT') >= 9
    assert 'No candidate is cleared' in PAGES[0].read_text()
    assert 'no new candidate' in PAGES[1].read_text().lower()
    assert 'no approved TIFF' in PAGES[2].read_text()
