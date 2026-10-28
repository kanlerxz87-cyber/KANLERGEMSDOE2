"""Session-3 TRBVC, 22-Sister-Repo Fleet Uniqueness, and Manifest Regression Tests."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_manifest_ir09_urls_and_hashes_clean() -> None:
    manifest = _load("registry/data_manifest.json")
    files = manifest["files"]
    assert len(files) == 46
    for entry in files:
        parts = entry.get("parts") or [entry["path"]]
        assert entry["repo"] and entry["ref"] and parts
        assert len(entry["sha256"]) == 64
        for p in parts:
            assert "data/external/dem10/" not in p
            assert "usgs_great_basin_heat_flow_points.csv" not in p


def test_preregistration_and_focus9_phd_synthesis_present() -> None:
    prereg = _load("registry/preregistration_trbvc_20261027.json")
    assert prereg["lane_id"] == "TRBVC-20261027"
    assert prereg["frozen_before_training"] is True
    assert len(prereg["ranked_hypotheses"]) == 5
    assert prereg["budget"]["max_experiments"] == 3

    hyp_doc = (ROOT / "knowledge/02_preregistered_hypotheses_kg2_s3_20261027.md").read_text(encoding="utf-8")
    for hid in ("H-KG2S3-1", "H-KG2S3-2", "H-KG2S3-3", "H-KG2S3-4", "H-KG2S3-5"):
        assert hid in hyp_doc

    phd_doc = (ROOT / "knowledge/01_focus9_gemsdoe32_phd_synthesis_20261027.md").read_text(encoding="utf-8")
    for site in (
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    ):
        assert site in phd_doc
    assert "0.2778" in phd_doc and "USER/OWNER-REPORTED" in phd_doc and "HOLDOUT-DTI" in phd_doc


def test_trbvc_80_channel_leakage_canary() -> None:
    canary = _load("evidence/leakage_canary_trbvc_20261027.json")
    assert canary["total_features_tested"] == 80
    assert canary["passed"] is True
    assert canary["max_single_feature_auc"] <= 0.90
    feats = canary["features"]
    assert len(feats) == 80
    trbvc_feats = [f for f in feats if f["feature"].startswith("trbvc_")]
    assert len(trbvc_feats) == 12
    assert all(f["oriented_auc"] <= 0.90 for f in trbvc_feats)


def test_trbvc_run_card_geotiff_and_automated_5_gate_validator() -> None:
    rc_bytes = (ROOT / "evidence/trbvc_run_card_20261027.json").read_bytes()
    dl_bytes = (ROOT / "docs/downloads/trbvc_run_card.json").read_bytes()
    assert rc_bytes == dl_bytes
    rc = json.loads(rc_bytes.decode("utf-8"))

    for req_key in (
        "hypothesis", "mechanism", "named_non_fault_mimic", "holdout_dti",
        "registry_comparison", "raster_sha256", "validator_output",
        "submission_name", "submission_note", "verdict", "budget",
    ):
        assert req_key in rc

    assert rc["verdict"] == "negative"
    assert rc["budget"]["experiments_executed"] == 3
    assert rc["budget"]["within_budget"] is True
    assert len(rc["submission_note"]) <= 140

    # Strict score labeling & holdout checks
    hr = rc["holdout_dti"]["primary_hide_and_recover"]
    sg = rc["holdout_dti"]["secondary_off_catalogue_sgmc"]
    cp = rc["holdout_dti"]["piedmont_off_catalogue_c_pied"]
    assert hr["score_label"] == "HOLDOUT-DTI" and hr["n_withheld_positives"] == 22232
    assert hr["pooled_dti"] > hr["champion_02778_same_evaluator"]
    assert hr["paired_delta_ci95"][0] > 0.0
    assert cp["score_label"] == "HOLDOUT-DTI" and cp["pooled_dti"] > 0.11
    assert cp["paired_delta_vs_dslup_ci95"][0] > 0.0
    assert sg["score_label"] == "HOLDOUT-DTI"
    assert sg["prevalence_calibrated_dti"] < sg["champion_02778_same_evaluator"]

    # Uniqueness checks across 281 distinct fleet rasters
    reg = rc["registry_comparison"]
    assert reg["n_footprint_distinct_rasters"] >= 280
    assert reg["pre_placement_surface_max_abs_spearman"] <= 0.90
    assert reg["final_dots_max_detector_3px_overlap"] <= 0.70

    # GeoTIFF, ZIP & DO-NOT-SUBMIT guard verification
    tif_path = ROOT / "docs/downloads" / rc["submission_name"]
    zip_path = ROOT / "docs/downloads" / rc["submission_zip"]
    guard_path = ROOT / "docs/downloads" / rc["submission_name"].replace("-zeros.tif", "-DO-NOT-SUBMIT.txt")
    assert tif_path.is_file() and zip_path.is_file() and guard_path.is_file()
    assert "DO NOT SUBMIT" in guard_path.read_text(encoding="utf-8")
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == rc["raster_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [rc["submission_name"]]

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.crs) == "EPSG:32611"
        assert ds.dtypes[0] == "float32"
        assert ds.nodata is None
        arr = ds.read(1)
    assert int(np.isnan(arr).sum()) == 0
    assert int(np.isinf(arr).sum()) == 0
    assert float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
    assert int((arr >= 0.5).sum()) == 37654

    # Verify pinned literal validation receipt (computed with restored cache)
    lit_rec = _load("evidence/trbvc_literal_validation_20261027.json")
    assert lit_rec["ok_to_submit"] is False and lit_rec["verdict"] == "negative"
    assert lit_rec["raster_sha256"] == rc["raster_sha256"]
    assert lit_rec["gates"]["exact_file_identity"] is True
    assert lit_rec["gates"]["local_grid_dtype_inside_range"] is True
    assert lit_rec["gates"]["literal_witness_not_duplicate"] is False
    assert lit_rec["format_audit"]["strict_whole_array_finite_0_1"] is True
    assert lit_rec["format_audit"]["inside_positive_pixels"] == 37654
    assert lit_rec["format_audit"]["on_catalogue_positive_pixels"] == 0

    # Live validator subprocess must fail closed both with and without restored cache (CI-safe)
    proc_lit = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts/validate_submission.py"),
            "--tif", str(tif_path),
            "--run-card", str(ROOT / "evidence/trbvc_run_card_20261027.json"),
        ],
        capture_output=True, text=True, check=False,
    )
    assert proc_lit.returncode == 1
    v_lit = json.loads(proc_lit.stdout)
    assert v_lit["ok_to_submit"] is False and v_lit["verdict"] == "negative"
    if v_lit["gates"].get("local_grid_dtype_inside_range"):
        assert v_lit["gates"]["exact_file_identity"] is True
        assert v_lit["gates"]["literal_witness_not_duplicate"] is False

    proc_s2 = subprocess.run(
        [
            sys.executable, str(ROOT / "scripts/validate_submission_kg2s2.py"),
            "--tif", str(tif_path), "--mode", "unique-slot",
            "--run-card", str(ROOT / "evidence/trbvc_run_card_20261027.json"),
        ],
        capture_output=True, text=True, check=False,
    )
    assert proc_s2.returncode == 1
    v_s2 = json.loads(proc_s2.stdout)
    assert v_s2["validated_ok_to_download_and_submit"] is False
    assert v_s2["verdict"] == "negative"


def test_sister_fleet_22_repos_uniqueness_receipt_and_site_sync() -> None:
    s22 = _load("evidence/sister_fleet_uniqueness_20261027.json")
    assert s22["total_sister_repos_audited"] == 22
    assert s22["total_sister_tifs_staged"] == 368
    assert s22["all_candidates_clear_70pct_across_all_22_sister_repos"] is True
    max_ov = s22["max_overlap_across_all_22_sister_repos"]
    assert max_ov["DSLUP_c71122d5_CHAMPION_UNIQUE"] <= 0.70
    assert max_ov["HTCADS_11a2f251_CHAMPION_S1"] <= 0.70
    assert max_ov["DARP_4ad35e71_RESEARCH_NEG"] <= 0.70
    assert max_ov["TRBVC_decad771_RESEARCH_NEG"] <= 0.70

    feed = _load("docs/data/status_feed.json")
    assert "kg2s3_trbvc_lane" in feed
    assert feed["kg2s3_trbvc_lane"]["verdict"] == "negative"
    assert feed["kg2s3_trbvc_lane"]["ok_to_submit"] is False
    assert feed["kg2s3_trbvc_lane"]["validated_ok_to_download_and_submit"] is False
