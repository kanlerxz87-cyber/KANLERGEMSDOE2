"""Workflow, selector, and published-site safety regressions."""
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

from scripts.promotion_gate import check

ROOT = Path(__file__).resolve().parents[1]


class GuardedCliTests(unittest.TestCase):
    def test_missing_witness_blocks_before_reading_or_writing_candidate(self):
        scripts = [
            ['submission_writer.py', 'does-not-exist.npy', '--slug', 'test', '--note', 'test'],
            ['evaluate_holdout.py', '--predictions', 'missing', '--baseline', 'missing',
             '--baseline-id', 'test', '--features', 'missing.json', '--out', 'blocked.json'],
            ['audit_uniqueness.py', '--stage', 'surface', '--surface', 'missing.npy',
             '--registry', 'missing.json', '--registry-root', 'missing', '--out', 'blocked.json'],
        ]
        with tempfile.TemporaryDirectory() as tmp:
            for args in scripts:
                with self.subTest(script=args[0]):
                    run = subprocess.run([sys.executable, str(ROOT / 'scripts' / args[0]), *args[1:], '--data-dir', tmp],
                                         cwd=tmp, text=True, capture_output=True)
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn('fail closed', run.stderr)
            self.assertFalse(list(Path(tmp).glob('*.json')))
            self.assertFalse(list(Path(tmp).rglob('*.tif')))

    def test_malformed_cards_are_negative_not_exceptions(self):
        for card in [{}, None, {'holdout': None, 'surface': 'bad', 'validator': None},
                     {'lane': 'x', 'holdout': {'evaluator_version': None}},
                     {'lane': 'x', 'holdout': {'evaluator_version': 'v', 'withheld_positives': True}}]:
            with self.subTest(card=card):
                self.assertEqual(check(card)['verdict'], 'negative')

    def test_selector_still_cannot_authorize(self):
        data = json.loads((ROOT / 'evidence/selector_decision.json').read_text())
        self.assertEqual(data['verdict'], 'negative')
        self.assertFalse(data['eligible_for_selector'])
        self.assertFalse(data['authorized_to_submit'])
        self.assertFalse(data['slot_approved'])


class LinkCollector(HTMLParser):
    def __init__(self): super().__init__(); self.links = []
    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value: self.links.append(value)


class PublishedSiteTests(unittest.TestCase):
    def test_local_html_links_and_conflict_markers(self):
        for path in (ROOT / 'docs').glob('*.html'):
            with self.subTest(page=path.name):
                text = path.read_text()
                self.assertNotIn('<<<<<<<', text)
                self.assertNotIn('>>>>>>>', text)
                parser = LinkCollector(); parser.feed(text)
                for link in parser.links:
                    url = urlsplit(link)
                    if url.scheme or url.netloc or not url.path: continue
                    self.assertTrue((path.parent / url.path).exists(), f'{path.name}: {link}')

    def test_no_public_tiff_or_unsupported_live_projection(self):
        self.assertFalse(list((ROOT / 'docs').rglob('*.tif')))
        index = (ROOT / 'docs/index.html').read_text()
        self.assertIn('No new TIFF is approved', index)
        self.assertIn('Owner-reported', index)
        self.assertIn('not a team', json.loads((ROOT / 'docs/leaderboard_snapshot.json').read_text())['scope'].lower())
        self.assertNotIn('est ~0.22', index)

    def test_run_card_replicas_are_identical(self):
        canonical = json.loads((ROOT / 'research/run_card.json').read_text())
        for path in ['evidence/run_card.json', 'docs/run-card.json', 'docs/run_card.json']:
            self.assertEqual(json.loads((ROOT / path).read_text()), canonical)
