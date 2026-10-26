from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

class SiteParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.rows = 0
        self.in_body_table = False
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.add(a['id'])
        if tag == 'a' and a.get('href'):
            self.links.append(a['href'])
        if tag == 'tbody':
            self.in_body_table = True
        if tag == 'tr' and self.in_body_table:
            self.rows += 1
    def handle_endtag(self, tag):
        if tag == 'tbody':
            self.in_body_table = False


def test_static_site_has_real_sections_and_resolvable_local_links():
    parser = SiteParser(); parser.feed((ROOT / 'docs/h1-audit.html').read_text())
    assert parser.rows == 9
    assert {'top', 'decision', 'evidence', 'history', 'method', 'next'} <= parser.ids
    for link in parser.links:
        if link.startswith('#'):
            assert link[1:] in parser.ids
        elif link.startswith('./'):
            assert (ROOT / 'docs' / link[2:]).exists(), link


def test_run_card_fails_closed_and_no_submission_tiff_exists():
    card = json.loads((ROOT / 'docs/data/run-card.json').read_text())
    assert card['verdict'] == 'negative' and card['ok_to_submit'] is False
    assert card['stop_reason'] == 'DUPLICATE_LANE_SURFACE'
    assert card['holdout_dti'] is None and card['holdout_95_ci'] is None
    assert card['raster_sha256'] is None and card['validator_output'] is None
    assert card['slots_used'] == 0 and len(card['submission_note']) <= 140
    assert not list((ROOT / 'docs').rglob('*.tif'))


def test_stopped_lane_guard_exits_before_work():
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/probe_experiment.py')],
                            cwd=ROOT, capture_output=True, text=True, timeout=20)
    assert result.returncode != 0
    assert 'already hit a duplicate stop' in result.stderr


def test_nine_historical_links_and_claims_match_audit():
    text = (ROOT / 'docs/h1-audit.html').read_text()
    audit = json.loads((ROOT / 'docs/data/focus-audit.json').read_text())
    assert len(audit['sites']) == 9
    for entry in audit['sites']:
        assert entry['site'] in text
        assert f'{entry["owner_reported_unverified"]:.4f}' in text
        assert entry['research_only_url'].replace('&', '&amp;') in text
        assert not entry['unique_among_nine'] and not entry['ok_to_submit']
