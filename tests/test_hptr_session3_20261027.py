"""Session-3 KG2-S3-HPTR, 3-Suite Holdout Dominance & 123-Repo Fleet Audit Tests."""
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
sys.path.insert(0, str(ROOT / "src"))

from gems32 import hptr  # noqa: E402


def _load(rel: str) -> dict:
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_hptr_module_synthetic_transforms_finite_and_fold_honest() -> None:
    assert len(hptr.HPTR_FEATURE_NAMES) == 12
    assert hptr.HPTR_REGIONAL_COLS == {4}
    rng = np.random.default_rng(20261027)
    foot = np.ones((48, 48), dtype=bool)
    foot[:3, :] = False

    field = rng.normal(size=(48, 48)).astype(np.float32)
    worm = hptr._steerable_worm_2d(field, foot, length_px=6.0, n_az=6)
    zb = np.full((48, 48), 350.0, dtype=np.float32)
    s_px, uy, ux = hptr._listric_shift_and_unit_down(zb, field, foot)
    assert worm.shape == (48, 48) and np.isfinite(worm[foot]).all()
    assert s_px.shape == (48, 48) and np.isfinite(s_px[foot]).all()
    assert np.isfinite(uy[foot]).all() and np.isfinite(ux[foot]).all()

    vis_a = np.zeros((48, 48), dtype=bool)
    vis_a[10:25, 20] = True  # N-S fault segment
    strike_fp = np.full((int(foot.sum()),), np.pi / 2.0, dtype=np.float32)

    tip_a, meta_a = hptr.compute_hptr_visible_tip_concord(vis_a, strike_fp, foot)
    assert tip_a.shape == (int(foot.sum()), 5) and np.isfinite(tip_a).all()
    assert float(tip_a.max()) > 0.0

    # Adding a separate withheld fault segment changes tip geometry; withholding it must NOT leak
    vis_b = vis_a.copy()
    vis_b[30:42, 34] = True
    tip_b, meta_b = hptr.compute_hptr_visible_tip_concord(vis_b, strike_fp, foot)
    assert tip_b.shape == (int(foot.sum()), 5)
    assert not np.allclose(tip_a, tip_b)


def test_hptr_preregistration_and_81_channel_canary() -> None:
    prereg = _load("registry/preregistration_hptr_20261027.json")
    assert prereg["lane_id"] == "KG2-S3-HPTR"
    assert len(prereg["hypotheses_ranked"]) == 4
    assert prereg["budget"]["max_experiments"] == 3

    hyp_md = (ROOT / "knowledge/03_preregistered_hypotheses_hptr_20261027.md").read_text(encoding="utf-8")
    for hid in ("H-S3-1", "H-S3-2", "H-S3-3", "H-S3-4"):
        assert hid in hyp_md

    canary = _load("evidence/hptr_leakage_canary_20261027.json")
    assert canary["total_features_tested"] == 81
    assert canary["passed"] is True
    assert canary["max_single_feature_auc"] <= 0.90
    hptr_feats = [f for f in canary["features"] if f["feature"].startswith("hptr_")]
    assert len(hptr_feats) == 12
    assert all(f["oriented_auc"] <= 0.90 for f in hptr_feats)


def test_hptr_run_card_geotiff_and_three_suite_dominance() -> None:
    rc_bytes = (ROOT / "evidence/session3_hptr_run_card_20261027.json").read_bytes()
    dl_bytes = (ROOT / "docs/downloads/hptr_run_card.json").read_bytes()
    assert rc_bytes == dl_bytes
    rc = json.loads(rc_bytes.decode("utf-8"))

    for req_key in (
        "hypothesis", "mechanism", "named_non_fault_mimic", "holdout_dti",
        "correlation_overlap_vs_registry", "registry_comparison", "raster_sha256",
        "validator_output", "submission_name", "submission_note", "verdict", "budget",
    ):
        assert req_key in rc

    assert rc["verdict"] == "negative"
    assert rc["ok_to_submit"] is False
    assert rc["validated_ok_to_download_and_submit"] is False
    assert rc["budget"]["experiments_executed"] == 3
    assert rc["budget"]["within_budget"] is True
    assert 0 < len(rc["submission_note"]) <= 140

    # Beats 0.2778 GEMSDOE32 champion across ALL THREE blind holdout benchmarks simultaneously
    hr = rc["holdout_dti"]["primary_hide_and_recover"]
    sg = rc["holdout_dti"]["secondary_off_catalogue_sgmc"]
    cp = rc["holdout_dti"]["tertiary_concealed_piedmont_c_pied"]
    assert hr["pooled_dti"] > hr["champion_02778_same_evaluator"]
    assert hr["paired_delta_ci95"][0] > 0.0 and hr["ci95_strictly_positive"] is True
    assert sg["sgmc_prevalence_calibrated_dti"] > sg["champion_02778_same_evaluator"]
    assert sg["paired_delta_ci95"][0] > 0.0 and sg["ci95_strictly_positive"] is True
    assert cp["pooled_dti"] > cp["champion_02778_same_evaluator"]

    # Binary (r>=0.5) non-blanket detector uniqueness & Spearman checks
    reg = rc["registry_comparison"]
    assert reg["pre_placement_surface_max_abs_spearman"] < 0.90
    assert reg["final_dots_max_abs_spearman"] < 0.90
    assert reg["final_dots_max_detector_3px_overlap"] <= 0.70
    assert rc["max_overlap_vs_all_kanlergemsdoe2_rasters"] <= 0.50

    # GeoTIFF, ZIP, sidecar & DO-NOT-SUBMIT guard verification
    tif_path = ROOT / "docs/downloads" / rc["raster_filename"]
    zip_path = ROOT / "docs/downloads" / rc["zip_filename"]
    val_path = ROOT / "docs/downloads" / rc["raster_filename"].replace("-zeros.tif", "-validation.json")
    guard_path = ROOT / "docs/downloads" / rc["raster_filename"].replace("-zeros.tif", "-DO-NOT-SUBMIT.txt")
    assert tif_path.is_file() and zip_path.is_file() and val_path.is_file() and guard_path.is_file()
    assert "DO NOT SUBMIT" in guard_path.read_text(encoding="utf-8")
    assert hashlib.sha256(tif_path.read_bytes()).hexdigest() == rc["raster_sha256"]

    with zipfile.ZipFile(zip_path) as zf:
        assert zf.namelist() == [rc["raster_filename"]]

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

    # Pinned validator receipts
    lit_rec = _load("evidence/hptr_validation_literal_witness_20261027.json")
    assert lit_rec["verdict"] == "negative" and lit_rec["ok_to_submit"] is False
    assert lit_rec["raster_sha256"] == rc["raster_sha256"]
    assert lit_rec["gates"]["exact_file_identity"] is True
    assert lit_rec["gates"]["local_grid_dtype_inside_range"] is True
    assert lit_rec["format_audit"]["strict_whole_array_finite_0_1"] is True
    assert lit_rec["format_audit"]["on_catalogue_positive_pixels"] == 0

    kg2s3_rec = _load("evidence/hptr_kg2s3_gate_receipt_20261027.json")
    assert kg2s3_rec["verdict"] == "NOT_OK_DO_NOT_SUBMIT"
    assert kg2s3_rec["gates"]["gate_1_format_0_1"]["passed"] is True
    assert kg2s3_rec["gates"]["gate_2_canary"]["passed"] is True
    assert kg2s3_rec["gates"]["gate_5_metadata"]["passed"] is True

    # Cache-independent live validator subprocesses
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/validate_submission.py"),
         "--tif", str(tif_path), "--run-card", str(ROOT / "evidence/session3_hptr_run_card_20261027.json")],
        capture_output=True, text=True, check=False,
    )
    assert proc.returncode == 1
    out = json.loads(proc.stdout)
    assert out["verdict"] == "negative" and out["ok_to_submit"] is False


def test_hptr_123_repo_fleet_audit_and_site_sync() -> None:
    fl = _load("evidence/hptr_full_fleet_audit_20261027.json")
    assert len(fl["focus_nine_audit"]) == 9
    assert len(fl["sister_24_audit"]) == 21
    for r in fl["focus_nine_audit"]:
        assert r["hptr_exp2_in_peer_3px_overlap"] <= 0.50
    for sr in fl["sister_24_audit"]:
        if sr["site"] != "KANLERGEMSDOE2" and sr["representative_raster"] is not None:
            assert sr["representative_raster"]["hptr_exp2_in_peer_3px_overlap"] <= 0.50

    expected_sisters = {
        "KANLERGEMSDOE1", "KANLERGEMSDOE2", "KANLERGEMSDOE3",
        "EUGGEMSDOE1", "EUGGEMSDOE2", "EUGGEMSDOE3",
        "WBGGEMSDOE1", "WBGGEMSDOE2", "WBGGEMSDOE3",
        "GINNYGEMSDOE1", "GINNYGEMSDOE2", "GINNYGEMSDOE3",
        "GEMSDOEkarage1", "GEMSDOEkarage2", "GEMSDOEkarage3",
        "ApartGEMSDOE1", "ApartGEMSDOE2", "ApartGEMSDOE3",
        "GEMSDOESASS1", "GEMSDOESASS2", "GEMSDOESASS3",
    }
    assert {sr["site"] for sr in fl["sister_24_audit"]} == expected_sisters

    feed = _load("docs/data/status_feed.json")
    assert "kg2s3_hptr_lane" in feed
    assert feed["kg2s3_hptr_lane"]["verdict"] == "negative"
    assert feed["kg2s3_hptr_lane"]["ok_to_submit"] is False
    assert feed["kg2s3_hptr_lane"]["beats_02778_leaderboard_score"] is None
    assert "not a holdout DTI" in feed["kg2s3_hptr_lane"]["comparison_warning"]

    for page_name in ("index.html", "executive-summary.html", "submission-table.html", "research.html", "irregularities.html"):
        html_txt = (ROOT / "docs" / page_name).read_text(encoding="utf-8")
        assert "675d0ff8" in html_txt or "KG2-S3-HPTR" in html_txt
        assert "DO NOT SUBMIT" in html_txt.upper()
