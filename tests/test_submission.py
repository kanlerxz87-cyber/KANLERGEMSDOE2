from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import re
import sys
import tempfile
import unittest
import zipfile

import numpy as np
import rasterio
from rasterio.transform import Affine

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from promotion_gate import check as gate_check  # noqa: E402
from select_submission import evaluate_card as select_evaluate  # noqa: E402
from validate_raster import validate  # noqa: E402


def _load_celf_module():
    spec = importlib.util.spec_from_file_location(
        "kg2_submodular_celf",
        ROOT / "src" / "gems" / "submodular_celf.py",
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["kg2_submodular_celf"] = mod
    spec.loader.exec_module(mod)
    return mod


CELF_MOD = _load_celf_module()

EXPECTED_HEIGHT = 3730
EXPECTED_WIDTH = 3292
EXPECTED_TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_CRS = "EPSG:32611"


class CanonicalSubmissionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.card = json.loads((ROOT / "research" / "run_card.json").read_text())
        self.tif_path = ROOT / self.card["raster_path"]
        self.zip_path = ROOT / self.card["zip_path"]

    def test_canonical_geotiff_exists_and_matches_competition_grid(self) -> None:
        self.assertTrue(self.tif_path.exists())
        self.assertEqual(
            hashlib.sha256(self.tif_path.read_bytes()).hexdigest(),
            self.card["raster_sha256"],
        )
        with rasterio.open(self.tif_path) as src:
            self.assertEqual(src.count, 1)
            self.assertEqual(src.dtypes[0], "float32")
            self.assertEqual(src.height, EXPECTED_HEIGHT)
            self.assertEqual(src.width, EXPECTED_WIDTH)
            self.assertEqual(src.crs.to_epsg(), 32611)
            self.assertEqual(src.transform, EXPECTED_TRANSFORM)
            self.assertIsNone(src.nodata)
            arr = src.read(1)

        self.assertTrue(np.isfinite(arr).all(), "Whole-grid finite required (no NaN/Inf)")
        self.assertGreaterEqual(float(arr.min()), 0.0)
        self.assertLessEqual(float(arr.max()), 1.0)
        uniq = np.unique(arr)
        self.assertTrue(np.all(np.isin(uniq, [0.0, 1.0])))
        self.assertEqual(int((arr > 0.0).sum()), 38500)

    def test_validate_raster_passes_against_reference_grid(self) -> None:
        sample = ROOT / "data" / "sample_submission.tif"
        if sample.exists():
            res = validate(self.tif_path, sample)
            self.assertTrue(res["format_valid"])
            self.assertFalse(res["ok_to_submit"])
        else:
            with tempfile.TemporaryDirectory() as tmpdir:
                ref_path = pathlib.Path(tmpdir) / "ref.tif"
                profile = {
                    "driver": "GTiff",
                    "height": EXPECTED_HEIGHT,
                    "width": EXPECTED_WIDTH,
                    "count": 1,
                    "dtype": "float32",
                    "crs": EXPECTED_CRS,
                    "transform": EXPECTED_TRANSFORM,
                }
                with rasterio.open(ref_path, "w", **profile) as dst:
                    dst.write(np.zeros((EXPECTED_HEIGHT, EXPECTED_WIDTH), dtype=np.float32), 1)
                res = validate(self.tif_path, ref_path)
                self.assertTrue(res["format_valid"])
                self.assertFalse(res["ok_to_submit"])

    def test_single_tiff_zip_matches_geotiff_bytes(self) -> None:
        self.assertTrue(self.zip_path.exists())
        self.assertEqual(
            hashlib.sha256(self.zip_path.read_bytes()).hexdigest(),
            self.card["zip_sha256"],
        )
        with zipfile.ZipFile(self.zip_path, "r") as zf:
            names = zf.namelist()
            self.assertEqual(names, [self.tif_path.name])
            inner_sha = hashlib.sha256(zf.read(names[0])).hexdigest()
            self.assertEqual(inner_sha, self.card["raster_sha256"])

    def test_canaries_and_focus_sites_evidence_integrity(self) -> None:
        canaries = json.loads((ROOT / "evidence" / "canaries.json").read_text())
        self.assertEqual(canaries["n_features"], 60)
        self.assertTrue(canaries["passed"])
        self.assertLessEqual(canaries["max_feature_alone_auc"], 0.90)
        self.assertEqual(len(canaries["features"]), 60)
        self.assertTrue(all(not r["leakage_suspected"] for r in canaries["features"].values()))

        focus = json.loads((ROOT / "evidence" / "focus_sites.json").read_text())
        expected_sites = {
            "GEMSDOE24",
            "GEMSDOE25",
            "GEMSDOE27",
            "GEMSDOE28",
            "GEMSDOE30",
            "GEMSDOE31",
            "GEMSDOE32",
            "GEMSDOE33",
            "GEMSDOE36",
        }
        self.assertEqual({s["site"] for s in focus["focus_sites"]}, expected_sites)
        readme_text = (ROOT / "README.md").read_text()
        index_html = (ROOT / "docs" / "index.html").read_text()
        for s in focus["focus_sites"]:
            self.assertIn("OWNER-REPORTED", s["live_score"]["label"])
            self.assertIn("PROJECTION", s["lli_s3_projection"]["label"])
            u = s["uniqueness_vs_other_gemsdoe"]
            self.assertFalse(u["passes_70pct_rule_among_focus9"])
            self.assertLess(u["overlap_with_kanlergemsdoe2_kg2h1_3px"], 0.70)
            self.assertLess(abs(u["kernel_spearman_with_kg2h1"]), 0.90)
            self.assertIn(s["sha256"][:8], readme_text)
            self.assertIn(s["sha256"][:8], index_html)

    def test_promotion_gate_and_selector_enforce_negative_verdict(self) -> None:
        gate_res = gate_check(self.card)
        self.assertEqual(gate_res["verdict"], "negative")
        self.assertFalse(gate_res["eligible_for_selector"])
        self.assertFalse(gate_res["authorized_to_submit"])

        sel = select_evaluate(self.card)
        self.assertEqual(sel["verdict"], "negative")
        self.assertFalse(sel["ok_to_submit"])
        self.assertFalse(sel["slot_approved"])

    def test_docs_html_links_resolve_inside_docs(self) -> None:
        docs_root = (ROOT / "docs").resolve()
        html_files = sorted(docs_root.glob("*.html"))
        self.assertGreaterEqual(len(html_files), 4)
        for html_path in html_files:
            txt = html_path.read_text()
            for href in re.findall(r'href=["\']([^"\'#]+)["\']', txt):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                target = (html_path.parent / href).resolve()
                self.assertTrue(
                    str(target).startswith(str(docs_root)),
                    f"Link escapes docs/ root in {html_path.name}: {href}",
                )
                self.assertTrue(
                    target.exists(),
                    f"Broken link in {html_path.name}: {href}",
                )


class SubmodularCelfTests(unittest.TestCase):
    def test_bayes_calibration_strictly_monotone_and_bounded(self) -> None:
        p = np.linspace(0.0, 1.0, 201, dtype=np.float32)
        q = CELF_MOD.bayes_case_control_calibrate(p, pi_true=0.025, pi_sample=0.25)
        self.assertEqual(q.dtype, np.float32)
        self.assertTrue(np.isfinite(q).all())
        self.assertGreater(float(q.min()), 0.0)
        self.assertLess(float(q.max()), 1.0)
        self.assertTrue(np.all(np.diff(q) >= 0.0))

    def test_celf_allocator_respects_budget_allowed_mask_and_submodularity(self) -> None:
        h, w = 24, 24
        allowed = np.ones((h, w), dtype=bool)
        allowed[11:14, 11:14] = False  # masked visible-fault collar
        prob = np.full((h, w), 0.001, dtype=np.float32)
        prob[4, 4] = 0.95
        prob[4, 5] = 0.94  # adjacent neighbor whose marginal gain collapses once (4, 4) is picked
        prob[19, 19] = 0.90
        prob[12, 13] = 0.99  # inside excluded collar

        emitted = CELF_MOD.celf_submodular_allocate(
            prob,
            allowed,
            budget=2,
            min_marginal_gain=0.0,
        )
        self.assertEqual(emitted.shape, (h, w))
        self.assertTrue(np.isfinite(emitted).all())
        self.assertGreaterEqual(float(emitted.min()), 0.0)
        self.assertLessEqual(float(emitted.max()), 1.0)
        self.assertEqual(int((emitted > 0.0).sum()), 2)
        self.assertEqual(float(emitted[12, 13]), 0.0)
        self.assertEqual(float(emitted[4, 4]), 1.0)
        self.assertEqual(float(emitted[19, 19]), 1.0)
        self.assertEqual(float(emitted[4, 5]), 0.0)


if __name__ == "__main__":
    unittest.main()
