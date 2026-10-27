"""KG2-ECPU-20261027 lane: negative-result integrity tests (fail-closed)."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_ecpu_run_card_is_negative_and_consistent() -> None:
    card = json.loads((ROOT / "evidence" / "run_card_ecpu_20261027.json").read_text())
    val = json.loads((ROOT / "evidence" / "validator_receipt_ecpu_20261027.json").read_text())
    assert card["lane_id"] == "KG2-ECPU-20261027"
    assert card["verdict"] == "negative"
    assert card["ok_to_download_and_submit"] is False
    assert val["validated_ok_to_download_and_submit"] is False
    assert val["verdict"] == "negative"
    assert val["gates"]["gate_4_holdout_beats_champion"] is False
    # Format/canary/uniqueness/metadata gates pass - only holdout fails.
    for g in ("gate_1_format_and_range_0_1", "gate_2_leakage_canary_le_090",
              "gate_3_registry_uniqueness", "gate_5_portal_metadata_le_140"):
        assert val["gates"][g] is True, g
    hr = card["holdout_dti"]["primary_hide_and_recover"]
    sg = card["holdout_dti"]["secondary_off_catalogue_sgmc"]
    assert hr["pooled_dti"] < hr["champion_02778_same_evaluator"]
    assert hr["pooled_dti"] < hr["prior_best_htcads_oof_same_evaluator_recorded"]
    assert sg["sgmc_prevalence_calibrated_dti"] < sg["prior_best_htcads_same_evaluator"]
    assert len(card["note"]) <= 140
    assert card["leakage_canary"]["max_single_feature_auc"] <= 0.90
    reg = card["registry_comparison"]
    assert reg["final_dots_max_detector_3px_overlap"] <= 0.70
    assert reg["pre_placement_surface_max_abs_spearman"] < 0.90
    assert reg["unique_rasters_checked"] >= 200


def test_ecpu_geotiff_format_and_hash() -> None:
    card = json.loads((ROOT / "evidence" / "run_card_ecpu_20261027.json").read_text())
    tif = ROOT / "docs" / "downloads" / card["submission_filename"]
    assert tif.exists()
    assert _sha256(tif) == card["raster_sha256"]
    with rasterio.open(tif) as ds:
        assert ds.count == 1 and str(ds.crs) == "EPSG:32611"
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.dtypes[0]) == "float32" and ds.nodata is None
        arr = ds.read(1)
    assert int(np.isnan(arr).sum()) == 0 and int(np.isinf(arr).sum()) == 0
    assert float(arr.min()) == 0.0 and float(arr.max()) == 1.0
    assert int((arr > 0).sum()) == 37654


def test_ecpu_experiments_budget_and_ablation() -> None:
    exps = json.loads((ROOT / "evidence" / "ecpu_experiments_20261027.json").read_text())
    assert exps["verdict"] == "negative"
    assert exps["selected_experiment"] == "EXP-1"
    promotable = [e for e in exps["experiments"] if e.startswith("EXP-")]
    assert len(promotable) == 3
    assert exps["total_wall_seconds"] < 7200
    # Preregistered selection = max HR-OOF among promotable.
    hrs = {e: exps["experiments"][e]["holdout_hide_recover_oof"]["pooled_dti"] for e in promotable}
    assert max(hrs, key=hrs.get) == "EXP-1"
    # Ablation: weighting helps blind SGMC, hurts (or does not help) Hide-Recover.
    abl = exps["ablation_weighted_minus_unweighted"]
    assert abl["sgmc_paired"]["ci95_strictly_positive"] is True
    assert abl["hr_oof_paired"]["delta"] < 0


def test_nine_site_reaudit_integrity() -> None:
    ra = json.loads((ROOT / "evidence" / "nine_site_reaudit_20261027.json").read_text())
    assert len(ra["focus_9_sites"]) == 9
    assert all(s["sha256_matches_20261026_audit"] for s in ra["focus_9_sites"])
    assert ra["exact_duplicate_pairs_xor0"] == ["GEMSDOE25|GEMSDOE30"]
    assert not any(s["unique_among_focus9_le_0p70"] for s in ra["focus_9_sites"])
    led = ra["ledger_inversion_4point_primary"]
    assert abs(led["inferred_TPw_px"] - 5151.3) < 1.0
    assert led["r_squared"] > 0.998
    # Projections are labelled as projections, HTCADS range above champion score,
    # ECPU HR-based projection below it.
    proj = ra["candidate_projections"]
    assert proj["HTCADS-EXP2-prior-promoted"]["range"][0] > 0.30
    assert proj["ECPU-EXP-1"]["via_hr_oof_ratio"] < 0.2778
