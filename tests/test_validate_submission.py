import tempfile
import unittest
from pathlib import Path

import numpy as np
import rasterio
from rasterio.transform import from_origin

from scripts.validate_submission import validate


class ValidateSubmissionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        self.template = self.root / "template.tif"
        self.candidate = self.root / "candidate.tif"
        self.transform = from_origin(500000, 4100000, 100, 100)
        self.template_data = np.ones((4, 5), dtype="float32")
        self.template_data[0, 0] = -9999.0
        self._write(self.template, self.template_data, nodata=-9999.0)
        candidate_data = np.full((4, 5), 0.5, dtype="float32")
        candidate_data[0, 0] = -9999.0
        self._write(self.candidate, candidate_data, nodata=-9999.0)

    def tearDown(self):
        self.tempdir.cleanup()

    def _write(self, path, data, *, nodata, transform=None):
        with rasterio.open(
            path,
            "w",
            driver="GTiff",
            height=data.shape[0],
            width=data.shape[1],
            count=1,
            dtype="float32",
            crs="EPSG:32611",
            transform=transform or self.transform,
            nodata=nodata,
        ) as dst:
            dst.write(data.astype("float32"), 1)

    def test_valid_candidate_passes(self):
        report = validate(self.template, self.candidate)
        self.assertTrue(report["format_valid"], report["errors"])
        self.assertTrue(report["checks"]["crs_shape_transform_match"])
        self.assertTrue(report["checks"]["inside_values_inclusive_0_1"])

    def test_out_of_range_candidate_fails(self):
        values = np.full((4, 5), 0.5, dtype="float32")
        values[1, 1] = 1.01
        values[0, 0] = -9999.0
        self._write(self.candidate, values, nodata=-9999.0)
        report = validate(self.template, self.candidate)
        self.assertFalse(report["format_valid"])
        self.assertFalse(report["checks"]["inside_values_inclusive_0_1"])

    def test_transform_mismatch_fails(self):
        self._write(
            self.candidate,
            np.full((4, 5), 0.5, dtype="float32"),
            nodata=-9999.0,
            transform=from_origin(500100, 4100000, 100, 100),
        )
        report = validate(self.template, self.candidate)
        self.assertFalse(report["format_valid"])
        self.assertFalse(report["checks"]["crs_shape_transform_match"])

    def test_nonfinite_inside_footprint_fails(self):
        values = np.full((4, 5), 0.5, dtype="float32")
        values[0, 0] = -9999.0
        values[1, 1] = np.inf
        self._write(self.candidate, values, nodata=-9999.0)
        report = validate(self.template, self.candidate)
        self.assertFalse(report["format_valid"])
        self.assertFalse(report["checks"]["no_nan_or_infinity_inside_footprint"])

    def test_footprint_mask_mismatch_fails(self):
        values = np.full((4, 5), 0.5, dtype="float32")
        # Mark a template-footprint pixel as nodata in the prediction.
        values[0, 0] = -9999.0
        values[2, 2] = -9999.0
        self._write(self.candidate, values, nodata=-9999.0)
        report = validate(self.template, self.candidate)
        self.assertFalse(report["format_valid"])
        self.assertFalse(report["checks"]["candidate_mask_matches_template_footprint"])


if __name__ == "__main__":
    unittest.main()
