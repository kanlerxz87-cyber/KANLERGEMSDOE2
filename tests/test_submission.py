"""Submission-file tests as unittest.TestCase so `unittest discover` (CI)
actually runs them — the previous pytest-style plain functions were silently
skipped by the unittest runner (found 2026-10-26, EXT lane review)."""
import glob, json, pathlib, unittest
import numpy as np, rasterio

ROOT = pathlib.Path(__file__).resolve().parents[1]

class LaneSubmissionTests(unittest.TestCase):
    def test_e1_lane_tif_range_and_grid(self):
        tif = ROOT / "research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif"
        self.assertTrue(tif.exists())
        with rasterio.open(tif) as d:
            a = d.read(1)
            self.assertEqual(d.count, 1); self.assertEqual(d.dtypes[0], "float32")
            self.assertEqual(str(d.crs), "EPSG:32611"); self.assertEqual(d.shape, (3730, 3292))
        self.assertTrue(np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1)
        self.assertEqual(int((a > 0).sum()), 37654)
        r = json.loads(pathlib.Path(str(tif) + ".receipt.json").read_text())
        self.assertTrue(r["all_pass"]); self.assertLessEqual(r["note_chars"], 140)

    def test_e1_lane_run_card(self):
        r = json.loads((ROOT / "evidence/run_card_e1_xg_hgb.json").read_text())
        self.assertEqual(r["verdict"], "negative")
        self.assertLessEqual(len(r["submission_note"]), 140); self.assertTrue(r["raster_sha256"])

    def test_ext_lane_tif_range_grid_and_card(self):
        tifs = sorted(glob.glob(str(ROOT / "docs/downloads/kanler-ext-mcsup-*-allfinite.tif")))
        self.assertEqual(len(tifs), 1)
        tif = pathlib.Path(tifs[0])
        with rasterio.open(tif) as d:
            a = d.read(1)
            self.assertEqual(d.count, 1); self.assertEqual(d.dtypes[0], "float32")
            self.assertEqual(str(d.crs), "EPSG:32611"); self.assertEqual(d.shape, (3730, 3292))
            self.assertIsNone(d.nodata)
        self.assertTrue(np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1)
        self.assertEqual(set(np.unique(a)), {0.0, 1.0})
        r = json.loads(pathlib.Path(str(tif) + ".receipt.json").read_text())
        self.assertTrue(r["all_pass"]); self.assertEqual(r["dots"], int((a > 0).sum()))
        self.assertEqual(r["dots"], 44090); self.assertLessEqual(r["note_chars"], 140)
        card = json.loads((ROOT / "evidence/run_card_ext.json").read_text())
        self.assertEqual(card["verdict"], "negative")
        self.assertFalse(card["ok_to_download_and_submit"])
        self.assertEqual(card["raster_sha256"], r["sha256"])
        self.assertLessEqual(len(card["submission_note"]), 140)
        u = card["correlation_overlap_vs_registry"]
        self.assertLessEqual(u["max_abs_surface_spearman"], 0.90)
        self.assertLessEqual(u["max_dot_overlap_3px_frac"], 0.70)
        self.assertLessEqual(card["leakage_canary"]["max_single_feature_abs_AUC"], 0.90)

if __name__ == "__main__":
    unittest.main()
