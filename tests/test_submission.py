"""Pytest-style regressions for the RETIRED inherited TIFF, never a promotion test."""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
TIFF = ROOT / "research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif"


def test_quarantined_tif_bytes_and_whole_grid_diagnostics():
    card = json.loads((ROOT / "research/run_card.json").read_text())
    assert hashlib.sha256(TIFF.read_bytes()).hexdigest() == card["raster_sha256"]
    with rasterio.open(TIFF) as dataset:
        array = dataset.read(1)
        assert dataset.count == 1 and dataset.dtypes[0] == "float32"
        assert str(dataset.crs) == "EPSG:32611" and dataset.shape == (3730, 3292)
    assert np.isfinite(array).all() and 0 <= array.min() <= array.max() <= 1
    assert (array > 0).sum() == 37654
    assert card["validator_output"]["outside_footprint_null_or_nan_conservative_check"] is False
    # A file with correct grid/range remains ineligible due to scientific and novelty stops.
    assert not card["ok_to_download_and_submit"]


def test_current_run_card_is_negative_and_has_no_new_file():
    card = json.loads((ROOT / "research/run_card.json").read_text())
    assert card["verdict"] == "negative" and len(card["note"]) <= 140
    assert card["new_raster_sha256"] is None and not card["registry_complete"]
    assert card["registry"]["candidate_fraction_within_3px"] > .70
    assert card["holdout"]["value"] is None
