"""Synthetic regression tests: geometry and tool contracts, not competition scores."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock

import numpy as np
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/template/src'))
from gems.metric import marginal_inclusion_threshold
from gems.novelty import compare_registry, compare_prospective_registry
from scripts.audit_registry_witness import measure
from scripts.registry_guard import require_candidate_generation_allowed
from scripts.validate_raster import validate


class WitnessGeometryTests(unittest.TestCase):
    def test_full_support_is_universal_for_sparse_dots(self):
        foot = np.ones((20, 20), bool)
        reference = np.linspace(.01, 1, 400).reshape(20, 20)
        for dots in [((0, 0),), ((19, 19),), ((0, 3), (10, 10), (15, 19))]:
            candidate = np.zeros((20, 20))
            for pos in dots:
                candidate[pos] = 1
            result = measure(foot, reference, candidate)
            self.assertTrue(result['universal_nonempty_candidate_blocker'])
            self.assertEqual(result['candidate_within_radius_fraction'], 1.0)
            self.assertTrue(result['candidate_fails_literal_rule'])

    def test_high_area_coverage_does_not_prove_universal_stop(self):
        # A concentrated set of dots in the uncovered tail can still pass overlap.
        foot = np.zeros((100, 100), bool)
        foot[:10, :10] = True
        foot[99, 99] = True
        ref = np.zeros(foot.shape)
        ref[:10, :10] = 1
        candidate = np.zeros(foot.shape)
        candidate[99, 99] = 1
        result = measure(foot, ref, candidate)
        self.assertGreater(result['footprint_within_radius_fraction'], .98)
        self.assertFalse(result['universal_nonempty_candidate_blocker'])
        self.assertEqual(result['candidate_within_radius_fraction'], 0)
        self.assertFalse(result['candidate_fails_literal_rule'])

    def test_euclidean_inclusive_radius(self):
        foot = np.ones((12, 12), bool)
        ref = np.zeros(foot.shape); ref[2, 2] = 1
        candidate = np.zeros(foot.shape); candidate[2, 5] = 1; candidate[5, 5] = 1
        self.assertEqual(measure(foot, ref, candidate)['candidate_within_radius_fraction'], .5)

    def test_empty_and_bad_values_fail_closed(self):
        foot = np.ones((8, 8), bool)
        one = np.ones((8, 8)); zero = np.zeros_like(one)
        for ref, cand in [(zero, one), (one, zero)]:
            with self.assertRaises(ValueError): measure(foot, ref, cand)
        bad = one.copy(); bad[2, 2] = np.nan
        with self.assertRaises(ValueError): measure(foot, bad, one)
        bad[2, 2] = 1.1
        with self.assertRaises(ValueError): measure(foot, bad, one)

    def test_saved_evidence_and_negative_card_agree(self):
        evidence = json.loads((ROOT / 'evidence/registry_witness.json').read_text())
        row = evidence['references']['continuous_gemsdoe48']
        self.assertTrue(row['universal_nonempty_candidate_blocker'])
        self.assertEqual(row['candidate_within_radius_fraction'], 1)
        self.assertEqual(row['footprint_pixels'], row['reference_positive_pixels'])
        self.assertFalse(evidence['candidate_generation_permitted_under_literal_rule'])
        self.assertIn('withdrawn', evidence['prior_e1_authorization'])

    def test_guard_missing_or_wrong_hash_never_opens(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaisesRegex(RuntimeError, 'fail closed'):
                require_candidate_generation_allowed(Path(tmp))


class ThresholdTests(unittest.TestCase):
    def test_algebra_on_both_sides_of_break_even(self):
        tp, fp, fn = 1., 3., 4.
        score = tp / (tp + .2 * fp + .8 * fn)
        threshold = marginal_inclusion_threshold(score, .2)
        self.assertAlmostEqual(threshold, .2 * score)
        def after(k):
            return (tp + k) / ((tp + k) + .2 * (fp + 1 - k) + .8 * (fn - k))
        self.assertLess(after(threshold - .01), score)
        self.assertAlmostEqual(after(threshold), score)
        self.assertGreater(after(threshold + .01), score)

    def test_threshold_bad_inputs(self):
        for x, a in [(float('nan'), .2), (-1, .2), (1.1, .2), (.5, -1), (.5, 1.1)]:
            with self.subTest(x=x, a=a), self.assertRaises(ValueError):
                marginal_inclusion_threshold(x, a)


class NoveltyTemplateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.root = Path(self.tmp.name)
        self.foot = np.ones((12, 12), bool)
        self.surface = np.linspace(0, 1, 144).reshape(12, 12)
        self.dots = np.zeros((12, 12), bool); self.dots[0, 0] = True
        self.template = self.write('template.tif', np.zeros((12, 12)))

    def tearDown(self): self.tmp.cleanup()

    def write(self, name, array, crs='EPSG:32611', dtype='float32'):
        path = self.root / name
        with rasterio.open(path, 'w', driver='GTiff', height=array.shape[0], width=array.shape[1], count=1,
                           dtype=dtype, crs=crs, transform=from_origin(100, 200, 100, 100)) as ds:
            ds.write(array.astype(dtype), 1)
        return path

    def row(self, name, a, *, crs='EPSG:32611', file='continuous.tif'):
        self.write(name, a, crs=crs)
        return {'id': name, 'file': file, 'cache_path': name,
                'footprint_sha256': hashlib.sha256(a[self.foot].astype('<f4').tobytes()).hexdigest()}

    def test_continuous_control_is_not_exempt(self):
        a = np.linspace(.1, 1, 144, dtype=np.float32).reshape(12, 12)
        row = self.row('continuous.tif', a)
        result = compare_registry(self.surface, self.foot, [row], self.root, dots=self.dots,
                                  separate_calibration_controls=True, template_path=self.template)
        self.assertFalse(result['passed'])
        self.assertFalse(result['literal_unseparated_passed'])
        self.assertEqual(result['rows'][0]['candidate_dot_overlap_within_3px'], 1.0)
        self.assertTrue(result['rows'][0]['duplicate'])

    def test_prospective_control_still_has_literal_verdict(self):
        a = np.zeros((12, 12), np.float32); a[::5, ::5] = 1
        row = self.row('lattice.tif', a, file='inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif')
        result = compare_prospective_registry(self.surface, self.foot, [row], self.root, dots=self.dots,
                                              template_path=self.template)
        self.assertFalse(result['passed'])
        self.assertFalse(result['literal_all_entries_passed'])
        self.assertEqual(result['calibration_control_rasters_count'], 1)

    def test_missing_template_and_wrong_grid_rejected(self):
        row = self.row('wrong.tif', np.ones((12, 12), np.float32), crs='EPSG:4326')
        with self.assertRaisesRegex(ValueError, 'template'):
            compare_registry(self.surface, self.foot, [row], self.root)
        with self.assertRaisesRegex(ValueError, 'grid'):
            compare_registry(self.surface, self.foot, [row], self.root, template_path=self.template)

    def test_constant_or_empty_reference_fail_closed(self):
        for value in (0, 1):
            with self.subTest(value=value):
                row = self.row('constant.tif', np.full((12, 12), value, np.float32))
                result = compare_registry(self.surface, self.foot, [row], self.root, dots=self.dots,
                                          template_path=self.template)
                self.assertFalse(result['passed'])
                self.assertTrue(result['rows'][0]['invalid_or_undefined'])

    def test_dtype_and_grid_validator(self):
        path = self.write('double.tif', np.zeros((12, 12)), dtype='float64')
        report = validate(path, self.template)
        self.assertFalse(report['format_valid'])
        self.assertFalse(report['checks']['dtype_float32'])
        self.assertFalse(report['ok_to_submit'])
