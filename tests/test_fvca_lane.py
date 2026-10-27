"""Verification suite for parallel negative research lane KG2-H1: FVCA-SUBMOD & cross-lane 72-raster audit."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

from gems import submodular_celf

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_fvca_geotiff_and_zip_format_and_negative_verdict() -> None:
    card = json.loads((ROOT / "evidence" / "fvca_run_card.json").read_text(encoding="utf-8"))
    docs_card = json.loads((ROOT / "docs" / "downloads" / "fvca_run_card.json").read_text(encoding="utf-8"))
    assert card == docs_card
    assert card["verdict"] == "negative"
    assert card["ok_to_submit"] is False
    assert card["ok_to_download_and_submit"] is False
    assert len(card["note"]) <= 140

    tif_path = ROOT / card["raster_path"]
    zip_path = ROOT / card["zip_path"]
    assert tif_path.exists()
    assert zip_path.exists()
    assert _sha256(tif_path) == card["raster_sha256"]
    assert _sha256(zip_path) == card["zip_sha256"]

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert (ds.height, ds.width) == (3730, 3292)
        assert ds.dtypes == ("float32",)
        assert ds.crs is not None and ds.crs.to_epsg() == 32611
        assert ds.transform == Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None
        arr = ds.read(1)

    assert np.isfinite(arr).all()
    assert float(arr.min()) >= 0.0
    assert float(arr.max()) <= 1.0
    assert set(np.unique(arr).tolist()).issubset({0.0, 1.0})
    assert int((arr > 0.0).sum()) == 38_500

    with zipfile.ZipFile(zip_path, "r") as zf:
        assert zf.namelist() == [tif_path.name]
        assert hashlib.sha256(zf.read(tif_path.name)).hexdigest() == card["raster_sha256"]


def test_fvca_canaries_and_cross_lane_72raster_audit() -> None:
    canaries = json.loads((ROOT / "evidence" / "fvca_canaries.json").read_text(encoding="utf-8"))
    assert canaries["n_features"] == 60
    assert canaries["passed"] is True
    assert canaries["max_feature_alone_auc"] <= 0.90
    assert all(not v["leakage_suspected"] for v in canaries["features"].values())

    cross = json.loads((ROOT / "evidence" / "cross_lane_72raster_audit.json").read_text(encoding="utf-8"))
    assert cross["non_lattice_detector_rasters_checked"] == 71
    lanes = cross["lanes"]
    for lane in lanes.values():
        assert lane["verdict"] == "negative"
        assert lane["ok_to_submit"] is False
        assert lane["literal_lattice_overlap_3px"] > 0.995
        assert lane["passes_72_detector_registry_70pct_gate"] is False
    assert lanes["HTCADS-DualRegime-EXP-2"]["historical_non_lattice_detector_only_pass"] is True
    assert lanes["KG2-MGHV-EXP-1"]["historical_non_lattice_detector_only_pass"] is True
    assert lanes["KG2-FVCA-SUBMOD-EXP-2"]["max_3px_detector_overlap"] > 0.70


def test_submodular_celf_allocator_and_bayes_calibration() -> None:
    p = np.linspace(0.0, 1.0, 201, dtype=np.float32)
    q = submodular_celf.bayes_case_control_calibrate(p, pi_true=0.025, pi_sample=0.25)
    assert q.dtype == np.float32
    assert np.isfinite(q).all()
    assert float(q.min()) > 0.0
    assert float(q.max()) < 1.0
    assert np.all(np.diff(q) >= 0.0)

    allowed = np.ones((24, 24), dtype=bool)
    allowed[11:14, 11:14] = False
    prob = np.full((24, 24), 0.001, dtype=np.float32)
    prob[4, 4] = 0.95
    prob[4, 5] = 0.94
    prob[19, 19] = 0.90
    prob[12, 13] = 0.99
    emitted = submodular_celf.celf_submodular_allocate(prob, allowed, budget=2, min_marginal_gain=0.0)
    assert emitted.shape == (24, 24)
    assert np.isfinite(emitted).all()
    assert int((emitted > 0.0).sum()) == 2
    assert float(emitted[12, 13]) == 0.0
    assert float(emitted[4, 4]) == 1.0
    assert float(emitted[19, 19]) == 1.0
    assert float(emitted[4, 5]) == 0.0
