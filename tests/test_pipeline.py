"""Synthetic software contract tests, never scientific experiment results."""
import ast
import hashlib
from io import BytesIO
import json
from pathlib import Path
import sys
import tarfile
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from submission_writer import write_candidate
from restore_core_data import restore_archive_group, safe_destination, valid_existing
from prepare_data import inspect
from promotion_gate import check


class PipelineTests(unittest.TestCase):
    def test_active_python_parses_and_has_no_conflict_markers(self):
        for folder in ('scripts', 'tests', 'vendor/template'):
            for path in (ROOT / folder).rglob('*.py'):
                ast.parse(path.read_text(), filename=str(path))
        for path in (ROOT / 'docs').rglob('*'):
            if path.suffix in ('.html', '.md', '.json'):
                for line in path.read_text().splitlines():
                    self.assertFalse(line.startswith(('<<<<<<< ', '>>>>>>> ')), str(path))

    def test_malformed_gate_inputs_fail_closed(self):
        for value in (None, [], 'yes', 1, {'holdout': None, 'validator': [], 'surface': False}):
            self.assertEqual(check(value)['verdict'], 'negative')

    def test_missing_data_does_not_synthesize(self):
        with tempfile.TemporaryDirectory() as temp:
            report = inspect(Path(temp))
            self.assertFalse(report['ready'])
            self.assertFalse(report['training_authorized'])
            self.assertEqual(len(list(Path(temp).iterdir())), 0)

    def test_destination_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): safe_destination(Path(temp), '../outside.tif')

    def test_archive_checksum_atomicity(self):
        payload = b'fixture bytes, NOT a competition raster'
        stream = BytesIO()
        with tarfile.open(fileobj=stream, mode='w:gz') as archive:
            info = tarfile.TarInfo('repository-commit/data/a')
            info.size = len(payload)
            archive.addfile(info, BytesIO(payload))
        entry = dict(id='fixture', repo='owner/repo', ref='pinned', path='data/a', dest='a',
                     bytes=len(payload), sha256=hashlib.sha256(payload).hexdigest())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch('restore_core_data.urllib.request.urlopen', return_value=BytesIO(stream.getvalue())):
                result = restore_archive_group([entry], root)
            self.assertEqual(result[0]['status'], 'restored-verified')
            self.assertTrue(valid_existing(root / 'a', entry))
            bad = dict(entry, sha256='0' * 64)
            with patch('restore_core_data.urllib.request.urlopen', return_value=BytesIO(stream.getvalue())):
                with self.assertRaises(ValueError): restore_archive_group([bad], root)
            self.assertEqual((root / 'a').read_bytes(), payload)
            self.assertEqual([p.name for p in root.iterdir()], ['a'])

    def test_legacy_format_only_writer_is_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            sample = root / 'sample.tif'
            with rasterio.open(sample, 'w', driver='GTiff', height=8, width=8, count=1,
                               dtype='float32', crs='EPSG:32611', transform=from_origin(1000, 2000, 100, 100)) as dst:
                dst.write(np.zeros((8, 8), np.float32), 1)
            values = np.full((8, 8), .27, np.float32)
            output = root / 'data/candidates/candidate.tif'
            with patch('submission_writer.ROOT', root):
                with self.assertRaisesRegex(ValueError, 'BLOCKED'):
                    write_candidate(values, sample, output, name='software-fixture', note='Synthetic unit test only')
            self.assertFalse(output.exists())
            # The pinned shared writer still preserves probabilities in an isolated synthetic test.
            from gems.submission import write_submission
            path = write_submission(values, sample, root / 'shared-fixture.tif', outside='nan')
            with rasterio.open(path) as src:
                np.testing.assert_array_equal(src.read(1), values)

    def test_current_published_links_resolve(self):
        from check_site import check as check_links
        self.assertEqual(check_links(), [])

    def test_build_does_not_change_authoritative_run_card(self):
        from build_site import build
        path = ROOT / 'research/run_card.json'
        before = path.read_bytes()
        build()
        self.assertEqual(path.read_bytes(), before)

    def test_shared_entrypoints_not_legacy_imports(self):
        self.assertFalse((ROOT / 'src/gems/holdout.py').exists())
        for name in ('submission_writer.py', 'evaluate_holdout.py', 'audit_feature_canaries.py'):
            self.assertIn('vendor/template/src', (ROOT / 'scripts' / name).read_text())
