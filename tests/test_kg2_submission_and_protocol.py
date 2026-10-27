from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems import footprint, metric  # noqa: E402
from gems.validator import sha256_file  # noqa: E402


def test_geotiff_strict_competition_compliance_without_human_intervention() -> None:
    card = json.loads((ROOT / "run_card.json").read_text())
    tif_path = ROOT / "docs/downloads" / card["submission_filename"]
    zip_path = ROOT / "docs/downloads" / card["zip_artifact"]
    assert tif_path.exists(), f"Missing GeoTIFF: {tif_path}"
    assert zip_path.exists(), f"Missing ZIP: {zip_path}"
    assert sha256_file(tif_path) == card["raster_sha256"]
    assert sha256_file(zip_path) == card["zip_sha256"]

    fp = footprint.load_footprint()
    assert fp.shape == (3730, 3292)
    assert int(fp.sum()) == 5_167_373

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert (ds.height, ds.width) == (3730, 3292)
        assert ds.dtypes == ("float32",)
        assert ds.crs is not None and ds.crs.to_epsg() == 32611
        assert ds.transform == Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
        assert ds.nodata is None  # zeros-outside local variant; acceptance unverified
        arr = ds.read(1)

    # Whole-array local [0, 1] check; it does not establish portal acceptance.
    assert int(np.isnan(arr).sum()) == 0
    assert int(np.isinf(arr).sum()) == 0
    assert np.isfinite(arr).all()
    assert float(arr.min()) >= 0.0
    assert float(arr.max()) <= 1.0
    assert float(arr[~fp].max()) == 0.0
    assert float(arr[~fp].min()) == 0.0
    assert int((arr[fp] > 0).sum()) == 37_654
    assert set(np.unique(arr).tolist()).issubset({0.0, 1.0})

    # Verify ZIP contains byte-identical GeoTIFF
    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert names == [tif_path.name]
        raw_bytes = zf.read(tif_path.name)
    assert hashlib.sha256(raw_bytes).hexdigest() == card["raster_sha256"]


def test_run_card_and_parallel_run_protocol_gates() -> None:
    card = json.loads((ROOT / "run_card.json").read_text())
    card_ev = json.loads((ROOT / "evidence/kg2_run_card_20261026.json").read_text())
    card_docs = json.loads((ROOT / "docs/data/run_card.json").read_text())
    assert card == card_ev == card_docs

    required = {
        "hypothesis",
        "mechanism",
        "non_fault_mimic_process",
        "holdout_dti",
        "correlation_overlap_vs_registry",
        "raster_sha256",
        "validator_output",
        "submission_name",
        "submission_note",
        "verdict",
    }
    assert required.issubset(card.keys())
    assert card["verdict"] == "negative"
    assert card["ok_to_submit"] is False
    assert len(card["submission_note"]) <= 140
    assert card["experiments_used"] <= card["budget_max_experiments"] <= 3
    assert card["weekly_slot_spent_automatically"] is False

    # Gate 1: Uniqueness BOTH pre-placement continuous surface AND post-placement final dots
    uniq = card["correlation_overlap_vs_registry"]
    assert uniq["rasters_checked"] == 360
    assert uniq["competing_detectors_checked"] == 359
    assert uniq["pre_placement_surface_max_abs_spearman"] <= 0.90
    assert uniq["pre_placement_surface_pass_le_0p90"] is True
    assert uniq["post_placement_dots_max_abs_spearman"] <= 0.90
    assert uniq["post_placement_competing_max_3px_overlap"] <= 0.70
    assert uniq["post_placement_competing_pass_le_0p70"] is True  # historical subset only
    assert uniq["post_placement_literal_all360_max_3px_overlap"] > 0.70
    assert uniq["literal_all_entries_pass"] is False

    # Gate 4: Leakage canary on all 78 channels
    canary = json.loads((ROOT / "evidence/kg2_canary_20261026.json").read_text())
    assert canary["n_features_checked"] == 78
    assert canary["passed"] is True
    assert canary["worst_two_polarity_auc_all78"] <= 0.90
    assert all(not v["leakage_suspected"] for v in canary["features"].values())

    # Holdout beat prior record and paired 95% CIs vs controls all > 0
    hold = json.loads((ROOT / "evidence/kg2_holdout_20261026.json").read_text())
    assert card["holdout_dti"]["evaluator_version"] == "gems-segment-pooled-v1"
    assert card["holdout_dti"]["withheld_positive_pixels"] == 60_988
    assert card["holdout_dti"]["dti"] > 0.1637924246971501
    for comp_key, comp in card["holdout_dti"]["paired_delta_ci95"].items():
        assert comp["paired_delta_ci95"][0] > 0.0, f"Paired 95% CI lower bound <= 0 for {comp_key}"
    assert len(hold["arms"]) == 3 and card["experiments_used"] == 3


def test_c2st_ben_david_and_nine_site_receipts() -> None:
    c2st = json.loads((ROOT / "evidence/kg2_c2st_nuisance_20261026.json").read_text())
    assert c2st["candidate"]["strict_gate_passed"] is True
    assert c2st["candidate"]["observed_auc"] < 0.55

    bd = json.loads((ROOT / "evidence/kg2_ben_david_domain_20261026.json").read_text())
    assert bd["source_domain"]["pixels"] + bd["target_domain"]["pixels"] == 5_167_373
    assert bd["empirical_proxy_d_HDeltaH"]["quantile_aligned_10m_dem_and_geophysics"] < 0.1

    nine = json.loads((ROOT / "evidence/release_audit_20261027.json").read_text())
    assert len(nine["focus_nine"]) == 9
    for row in nine["focus_nine"]:
        assert len(row["sha256"]) == 64
        assert row["max_directional_focus_overlap_within_3px"] > 0.70
        assert row["score_evidence_class"] == "USER/OWNER-REPORTED; not an organizer receipt"


def test_dti_tversky_metric_algebra() -> None:
    fp = np.ones((20, 20), dtype=bool)
    truth = np.zeros((20, 20), dtype=bool)
    pred = np.zeros((20, 20), dtype=np.float32)
    truth[10, 10] = True
    pred[10, 12] = 1.0  # distance d = 2.0 px -> kernel weight max(0, 1 - 2/3) = 1/3
    res = metric.dti_components_exact(pred, truth, fp)
    w = 1.0 - 2.0 / 3.0
    expected = w / (w + 0.2 * (1.0 - w) + 0.8 * (1.0 - w))
    assert np.isclose(res["dti"], expected, atol=1e-6)


def test_evaluate_holdout_cli_verify_kg2() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/evaluate_holdout.py"), "--verify-kg2"],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(proc.stdout)
    assert out["verified"] is True
    assert out["ok_to_download"] is True
    assert out["ok_to_submit"] is False
    assert out["verdict"] == "negative"
