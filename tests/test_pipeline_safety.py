"""Synthetic safety contracts only; these tests are not geological evidence."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import rasterio
from rasterio.transform import from_origin
from scripts import submission_writer as writer
from scripts.promotion_gate import check

ROOT = Path(__file__).resolve().parents[1]


class PipelineSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.template = self.root / 'template.tif'
        with rasterio.open(self.template, 'w', driver='GTiff', width=8, height=8,
                           count=1, dtype='float32', crs='EPSG:32611',
                           transform=from_origin(243350, 4508550, 100, 100)) as dst:
            dst.write(np.zeros((8, 8), dtype=np.float32), 1)
        self.out = self.root / 'data/candidates/test.tif'
        self.patcher = patch.object(writer, 'ROOT', self.root)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)

    def stage(self, arr, **kwargs):
        return writer.stage(arr, self.template, kwargs.pop('out', self.out),
                            name=kwargs.pop('name', 'synthetic-test'),
                            note=kwargs.pop('note', 'Synthetic format contract only'), **kwargs)

    def test_probability_preserved_and_never_approved(self):
        arr = np.full((8, 8), .25, dtype=np.float32)
        result = self.stage(arr)
        self.assertTrue(result['format_valid'])
        self.assertFalse(result['ok_to_download_and_submit'])
        self.assertFalse(result['eligible_for_selector'])
        with rasterio.open(self.out) as src:
            np.testing.assert_array_equal(src.read(1), arr)
        self.assertEqual(json.loads(Path(str(self.out)+'.format.json').read_text())['verdict'], 'negative')

    def test_nonfinite_and_range_not_binarized(self):
        for bad in [float('nan'), float('inf'), -float('inf'), -1, 1.1]:
            with self.subTest(bad=bad):
                arr = np.zeros((8, 8)); arr[1, 1] = bad
                with self.assertRaises(ValueError): self.stage(arr)
                self.assertFalse(self.out.exists())

    def test_shape_and_note_rejected(self):
        for kwargs in [dict(note=''), dict(note='x'*141), dict(name='../unsafe')]:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError): self.stage(np.zeros((8, 8)), **kwargs)
        with self.assertRaises(ValueError): self.stage(np.zeros((4, 4)))

    def test_no_publishing_or_overwriting(self):
        with self.assertRaises(ValueError):
            self.stage(np.zeros((8, 8)), out=self.root/'docs/downloads/test.tif')
        self.stage(np.zeros((8, 8)))
        with self.assertRaises(FileExistsError): self.stage(np.ones((8, 8)))

    def test_symlink_escape_rejected(self):
        directory = self.root/'data/candidates';directory.mkdir(parents=True)
        (directory/'escape').symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.stage(np.zeros((8, 8)), out=directory/'escape/test.tif')

    def test_legacy_experiments_fail_before_reading_data(self):
        for script in ['run_experiments.py','evaluate_holdout.py','build_features.py']:
            with self.subTest(script=script):
                p=subprocess.run([sys.executable, str(ROOT/'scripts'/script)], capture_output=True,text=True,cwd=self.root)
                self.assertEqual(p.returncode,2)
                self.assertIn('BLOCKED',p.stderr)

    def test_malformed_cards_fail_closed(self):
        for card in [None, [], 'invalid', {'holdout':None}, {'surface':[]}, {'dots':False}, {'validator':None}]:
            with self.subTest(card=card):
                self.assertEqual(check(card)['verdict'],'negative')

    def test_only_shared_evaluator_is_importable_from_active_source(self):
        self.assertFalse((ROOT/'src/gems/holdout.py').exists())
        self.assertFalse((ROOT/'src/gems/metric.py').exists())

    def test_published_site_has_no_conflict_markers_or_retired_results(self):
        for p in (ROOT/'docs').glob('*'):
            if p.is_file():
                self.assertNotIn('<<<<<<< HEAD', p.read_text(), str(p))
        for name in ['canaries.json','experiments_oof.json','run_card_e1_xg_hgb.json','uniqueness_E1.json']:
            self.assertFalse((ROOT/'docs'/name).exists())
        self.assertIn('DO NOT SUBMIT', (ROOT/'docs/lane-e1-xg-hgb.html').read_text())
