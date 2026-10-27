"""Verification suite for 2026-10-27 H-LDAH (Listric-Updip, Void-Bridged 10m DEM / 3m Scarp, & Borehole-Hydrothermal Tri-Regime) lane."""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

from gems32 import htcads

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_ldah_62_feature_leakage_canary_and_manifest() -> None:
    """Verify 62-feature Leakage Canary (50 baseline + 12 EXT27 discovery channels) and 41-entry data manifest."""
    canary = json.loads((ROOT / "evidence" / "leakage_canary.json").read_text(encoding="utf-8"))
    assert canary["passed"] is True
    assert canary["total_features_tested"] == 62
    assert canary["max_single_feature_auc"] <= 0.90
    ext_groups = [f for f in canary["features"] if f["group"] == "ext27_multi_scale_discovery"]
    assert len(ext_groups) == len(htcads.EXT27_FEATURE_NAMES) == 12
    assert all(f["oriented_auc"] <= 0.90 for f in ext_groups)

    man = json.loads((ROOT / "registry" / "data_manifest.json").read_text(encoding="utf-8"))
    assert len(man["files"]) == 41
    ids = {e["id"] for e in man["files"]}
    for req_id in [
        "ext_h52_scarp3m",
        "ext_usgs_comcat_geodawn",
        "ext_usgs_heat_flow_wells",
        "ext_acquisition_block_id",
        "ext_blm_closed_claim_distance",
        "ext_dem10_onesided3",
        "ext_dem10_hgm20_max",
    ]:
        assert req_id in ids


def test_ldah_promoted_exp2_beats_champion_and_prior_htcads_on_both_evaluators() -> None:
    """Verify LDAH-EXP2 beats both GEMSDOE32 B=2 (0.2778) and prior HTCADS-EXP2 (11a2f251) on both holdout evaluators."""
    exps_doc = json.loads((ROOT / "evidence" / "ldah_experiments_20261027.json").read_text(encoding="utf-8"))
    assert len(exps_doc["experiments"]) == 3
    assert exps_doc["within_protocol_budget"]["experiments_run"] == 3
    assert exps_doc["within_protocol_budget"]["wall_hours"] <= 2.0
    assert exps_doc["selected_experiment"] == "EXP-2"

    exp1, exp2, exp3 = exps_doc["experiments"]
    # All 3 experiments pass Protocol Rule 1 uniqueness across all registry rasters
    for e in (exp1, exp2, exp3):
        u = e["uniqueness_audit"]
        assert u["passed"] is True
        assert u["pre_placement_surface_max_abs_spearman"] < 0.90
        assert u["final_dots_max_abs_spearman"] < 0.90
        assert u["final_dots_max_detector_3px_overlap"] <= 0.70
        assert u["final_dots_max_harmonic_3px_overlap_all"] <= 0.70

    # EXP-2 beats both 0.2778 champion (HR=0.099202, SGMC=0.064121) AND prior HTCADS-EXP2 11a2f251 (HR=0.112353, SGMC=0.078913)
    hr2 = exp2["holdout_hide_recover"]
    sg2 = exp2["holdout_sgmc_offcat"]
    assert hr2["pooled_dti"] > 0.112353 > hr2["champion_02778_same_evaluator"]
    assert hr2["paired_delta_ci95"][0] > 0.0
    assert sg2["sgmc_prevalence_calibrated_dti"] > 0.081431 > 0.078913 > sg2["champion_02778_same_evaluator"]
    assert sg2["paired_delta_ci95"][0] > 0.0


def test_ldah_geotiff_and_cross_lane_audit() -> None:
    """Verify promoted LDAH GeoTIFF, ZIP, run cards, and 4-lane cross-lane registry audit."""
    rc = json.loads((ROOT / "evidence" / "ldah_run_card_20261027.json").read_text(encoding="utf-8"))
    rc_main = json.loads((ROOT / "evidence" / "run_card.json").read_text(encoding="utf-8"))
    rc_dl = json.loads((ROOT / "docs" / "downloads" / "run_card.json").read_text(encoding="utf-8"))
    assert rc == rc_main == rc_dl
    assert rc["verdict"] == "promote"
    assert rc["ok_to_download_and_submit"] is True
    assert len(rc["note"]) <= 140

    tif_path = ROOT / "docs" / "downloads" / rc["submission_filename"]
    zip_path = ROOT / "docs" / "downloads" / rc["zip_filename"]
    assert tif_path.exists()
    assert zip_path.exists()
    assert _sha256(tif_path) == rc["raster_sha256"]
    assert _sha256(zip_path) == rc["zip_sha256"]

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert (ds.height, ds.width) == (3730, 3292)
        assert ds.dtypes == ("float32",)
        assert ds.crs is not None and ds.crs.to_epsg() == 32611
        assert ds.transform == Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None
        arr = ds.read(1)

    assert np.isfinite(arr).all()
    assert int(np.isnan(arr).sum()) == 0
    assert float(arr.min()) == 0.0
    assert float(arr.max()) == 1.0
    assert int((arr > 0.5).sum()) == 37_654

    with zipfile.ZipFile(zip_path, "r") as zf:
        assert zf.namelist() == [tif_path.name]
        assert hashlib.sha256(zf.read(tif_path.name)).hexdigest() == rc["raster_sha256"]

    cross = json.loads((ROOT / "evidence" / "cross_lane_72raster_audit.json").read_text(encoding="utf-8"))
    ldah_lane = cross["lanes"]["LDAH-TriRegime-Discovery-EXP-2"]
    assert ldah_lane["passes_72_detector_registry_70pct_gate"] is True
    assert ldah_lane["max_3px_detector_overlap"] <= 0.70
