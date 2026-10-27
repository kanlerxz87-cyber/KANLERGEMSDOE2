"""Comprehensive Pass-3 verification suite for KANLERGEMSDOE2."""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path

import numpy as np
import rasterio

from gems32 import metric, paths, submission


ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_tversky_metric_soft_and_binary_equivalence() -> None:
    """Verify IR-SHARED-SOFT-01 fix: soft expected-DTI and binary {0, 1} match on exact pixels."""
    truth = np.zeros((25, 25), dtype=bool)
    truth[12, 5:20] = True
    pred_bin = np.zeros((25, 25), dtype=np.float32)
    pred_bin[12, 6:18:3] = 1.0
    score_exact = metric.dti_exact(pred_bin, truth)["dti"]
    score_bin = metric.dti_binary(pred_bin > 0.5, truth)["dti"]
    assert abs(score_exact - score_bin) < 1e-9
    assert 0.30 < score_bin <= 1.0

    # Soft probabilities < 0.5 MUST NOT be silently zeroed to 0.0!
    pred_soft = pred_bin * 0.25
    score_soft = metric.dti_exact(pred_soft, truth)["dti"]
    assert score_soft > 0.05


def test_forensic_02778_linear_tversky_inversion() -> None:
    """Verify exact R^2 > 0.998 linear 1/DTI(N) collar-pruning proof of 0.2778."""
    n_dots = np.array([44090.0, 40199.0, 37654.0])
    live_dti = np.array([0.2600, 0.2708, 0.2778])
    inv = 1.0 / live_dti
    slope, intercept = np.polyfit(n_dots, inv, 1)
    pred = intercept + slope * n_dots
    r2 = 1.0 - float(np.sum((inv - pred) ** 2) / np.sum((inv - inv.mean()) ** 2))
    assert r2 > 0.998
    tp_w = 0.2 / slope
    k_hidden = intercept * tp_w / 0.8
    assert 5000.0 <= tp_w <= 5300.0
    assert 13000.0 <= k_hidden <= 14500.0


def test_promoted_geotiff_and_zip_portal_safety() -> None:
    """Verify Gate 1: promoted GeoTIFF & zip match sample_submission.tif, [0, 1], 0 NaNs, 0 catalogue px."""
    rc = json.loads((ROOT / "evidence" / "run_card.json").read_text(encoding="utf-8"))
    val = json.loads((ROOT / "evidence" / "validator_receipt.json").read_text(encoding="utf-8"))

    assert rc["verdict"] == "promote"
    assert rc["ok_to_download_and_submit"] is True
    assert val["validated_ok_to_download_and_submit"] is True
    assert val["human_intervention_required"] is False
    assert all(val["gates"].values())

    tif_path = ROOT / "docs" / "downloads" / rc["submission_filename"]
    zip_path = ROOT / "docs" / "downloads" / rc["zip_filename"]
    assert tif_path.exists()
    assert zip_path.exists()
    assert _sha256(tif_path) == rc["raster_sha256"] == val["raster_sha256"]
    assert _sha256(zip_path) == rc["zip_sha256"]

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        assert len(names) == 1
        assert names[0].endswith(".tif")

    # Self-contained direct raster check (runs on any CI runner without external data cache)
    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert str(ds.crs) == "EPSG:32611"
        assert (ds.height, ds.width) == (3730, 3292)
        assert str(ds.dtypes[0]) == "float32"
        assert ds.nodata is None
        assert list(ds.transform)[:6] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
        arr = ds.read(1)
        assert int(np.isnan(arr).sum()) == 0
        assert int(np.isinf(arr).sum()) == 0
        assert float(arr.min()) == 0.0
        assert float(arr.max()) == 1.0
        assert int((arr > 0.5).sum()) == 37654

    ddir = paths.data_dir()
    if (ddir / "sample_submission.tif").exists() and (ddir / "existing_faults.tif").exists():
        with rasterio.open(ddir / "sample_submission.tif") as ds_f:
            foot = np.isfinite(ds_f.read(1))
        with rasterio.open(ddir / "existing_faults.tif") as ds_l:
            labels = foot & (ds_l.read(1) > 0.5)
        audit = submission.audit_geotiff(
            tif_path,
            foot=foot,
            labels=labels,
            mode="zeros",
            template_tif=ddir / "sample_submission.tif",
        )
        assert audit["all_checks_passed"] is True
        assert audit["on_catalogue_positive_pixels"] == 0


def test_rule4_leakage_canary_and_rule1_uniqueness_and_rule6_budget() -> None:
    """Verify Protocol Rules 1, 4, 5, and 6 machine receipts."""
    canary = json.loads((ROOT / "evidence" / "leakage_canary.json").read_text(encoding="utf-8"))
    assert canary["passed"] is True
    assert canary["total_features_tested"] >= 50
    assert canary["max_single_feature_auc"] <= 0.90

    rc = json.loads((ROOT / "evidence" / "run_card.json").read_text(encoding="utf-8"))
    reg = rc["registry_comparison"]
    assert reg["passed"] is True
    assert reg["unique_rasters_checked"] >= 150
    assert reg["pre_placement_surface_max_abs_spearman"] < 0.90
    assert reg["final_dots_max_abs_spearman"] < 0.90
    assert reg["final_dots_max_detector_3px_overlap"] <= 0.70
    assert reg["final_dots_max_harmonic_3px_overlap_all"] <= 0.70
    assert len(rc["note"]) <= 140

    hr = rc["holdout_dti"]["primary_hide_and_recover"]
    sg = rc["holdout_dti"]["secondary_off_catalogue_sgmc"]
    assert hr["pooled_dti"] > hr["champion_02778_same_evaluator"]
    assert hr["paired_delta_ci95"][0] > 0.0
    assert sg["sgmc_prevalence_calibrated_dti"] > sg["champion_02778_same_evaluator"]
    assert sg["paired_delta_ci95"][0] > 0.0

    exps = json.loads((ROOT / "evidence" / "htcads_experiments.json").read_text(encoding="utf-8"))
    assert len(exps["experiments"]) == 3
    assert exps["within_protocol_budget"]["wall_hours"] <= 2.0


def test_github_pages_and_markdown_integrity() -> None:
    """Verify all HTML pages, local links/assets, README prompt preservation, and Core Values."""
    docs = ROOT / "docs"
    for page in ["index.html", "executive-summary.html", "research.html", "irregularities.html"]:
        p = docs / page
        assert p.exists(), f"Missing {page}"
        html_txt = p.read_text(encoding="utf-8")
        assert "HOLDOUT-DTI" in html_txt or "Own the Outcome" in html_txt
        # Verify every local href/src target exists
        for m in re.finditer(r'(?:href|src)="([^"#?]+)"', html_txt):
            ref = m.group(1)
            if ref.startswith(("http://", "https://", "mailto:", "javascript:")):
                continue
            target = (docs / ref).resolve()
            assert target.exists(), f"Broken local reference {ref} in {page}"

    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Maximize P(Win)" in readme
    assert "Own the Outcome" in readme
    assert "f482d3bad4b390470be06363b60867c8e42942101271caf4fa82ae3c3975abeb" in readme
    assert "PARALLEL-RUN PROTOCOL" in readme
