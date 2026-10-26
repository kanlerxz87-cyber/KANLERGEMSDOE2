"""The quarantined historical TIFF is evidence only, never a current submission."""
import json
from pathlib import Path
import unittest

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


class HistoricalSubmissionTests(unittest.TestCase):
    def test_quarantined_tif_format_does_not_authorize_upload(self):
        tif = ROOT / 'research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif'
        self.assertTrue(tif.exists())
        with rasterio.open(tif) as dataset:
            a = dataset.read(1)
            self.assertEqual(dataset.count, 1)
            self.assertEqual(dataset.dtypes[0], 'float32')
            self.assertEqual(str(dataset.crs), 'EPSG:32611')
            self.assertEqual(dataset.shape, (3730, 3292))
        self.assertTrue(np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1)
        self.assertEqual(int((a > 0).sum()), 37654)
        old_receipt = json.loads(Path(str(tif) + '.receipt.json').read_text())
        self.assertTrue(old_receipt['all_pass'])  # format-only historical assertion
        self.assertLessEqual(old_receipt['note_chars'], 140)
        current = json.loads((ROOT / 'research/run_card.json').read_text())
        self.assertFalse(current['ok_to_download_and_submit'])
        self.assertEqual(current['prior_e1_review']['authorization'], 'withdrawn')

    def test_only_current_card_is_negative(self):
        current = json.loads((ROOT / 'research/run_card.json').read_text())
        self.assertEqual(current['verdict'], 'negative')
        self.assertIsNone(current['raster_sha256'])
        self.assertIsNone(current['holdout']['dti'])
        self.assertLessEqual(len(current['note']), 140)
