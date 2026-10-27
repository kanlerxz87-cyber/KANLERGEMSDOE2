"""2026-10-27 verification suite for DARP-MT10, shared-tool fixes, sister-site audit, and unified Run Card."""
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

from gems32 import holdout as g32_holdout  # noqa: E402


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def test_shared_holdout_empty_truth_fold_counts_false_positives() -> None:
    """Regression test for IR-SHARED-EMPTY-TRUTH-FP-04 in src/gems32/holdout.py."""
    from scipy.ndimage import distance_transform_edt

    foot = np.ones((32, 32), dtype=bool)
    labels = np.zeros((32, 32), dtype=bool)
    labels[4, 4:10] = True  # truth exists ONLY in top half (fold 0)

    quad = np.zeros((32, 32), dtype=np.int8)
    quad[16:, :] = 2
    ty, tx = np.nonzero(labels[:16, :])
    dg0 = distance_transform_edt(~labels[:16, :])
    k_dg0 = np.clip(1.0 - dg0 / 3.0, 0.0, 1.0).astype(np.float32)

    cells = [
        g32_holdout.PreparedCell(
            key=f"draw{ds}_fold{f}",
            fold=f,
            seed=ds,
            bbox=(slice(0, 16), slice(0, 32)) if f in (0, 1) else (slice(16, 32), slice(0, 32)),
            active_sub=np.ones((16, 32), dtype=bool),
            truth_coords=(ty, tx) if f in (0, 1) else (np.array([], dtype=int), np.array([], dtype=int)),
            k_dg_sub=k_dg0 if f in (0, 1) else np.zeros((16, 32), dtype=np.float32),
            n_truth=int(ty.size) if f in (0, 1) else 0,
            d_visible_sub=np.full((16, 32), 99.0, dtype=np.float32),
        )
        for ds in g32_holdout.DRAWS
        for f in g32_holdout.FOLDS
    ]
    ctx = g32_holdout.HoldoutContext(
        foot=foot,
        labels=labels,
        sgmc_off=np.zeros_like(foot),
        near_visible=np.zeros_like(foot),
        quad=quad,
        quad_bboxes={0: (slice(0, 16), slice(0, 16)), 1: (slice(0, 16), slice(16, 32)),
                     2: (slice(16, 32), slice(0, 16)), 3: (slice(16, 32), slice(16, 32))},
        cells=cells,
        sgmc_truth_coords=(np.array([], dtype=int), np.array([], dtype=int)),
        sgmc_k_dg=np.zeros_like(foot, dtype=np.float32),
        sgmc_n_truth=0,
        sgmc_quad_truth_coords={},
        sgmc_quad_n_truth={},
    )

    pred_clean = np.zeros(foot.shape, dtype=np.float32)
    pred_clean[4, 5:9] = 1.0

    pred_noisy_empty = pred_clean.copy()
    pred_noisy_empty[20:30, 4:28] = 1.0  # 240 pure FPs inside empty-truth folds 2 & 3!

    r_clean = g32_holdout.evaluate_hide_and_recover(pred_clean, ctx, grid_n=4, n_boot=50)
    r_noisy = g32_holdout.evaluate_hide_and_recover(pred_noisy_empty, ctx, grid_n=4, n_boot=50)
    assert r_noisy["pooled_dti"] < r_clean["pooled_dti"] - 0.25

    # Also verify soft [0, 1] branch
    r_soft_clean = g32_holdout.evaluate_hide_and_recover(pred_clean * 0.8, ctx, grid_n=4, n_boot=50)
    r_soft_noisy = g32_holdout.evaluate_hide_and_recover(pred_noisy_empty * 0.8, ctx, grid_n=4, n_boot=50)
    assert r_soft_noisy["pooled_dti"] < r_soft_clean["pooled_dti"] - 0.20


def test_unified_run_cards_and_new_darp_geotiff_portal_safety() -> None:
    """Verify byte-identical DARP-MT10 run cards + 13/13 GeoTIFF checks + <=70% vs DSLUP/ECPU."""
    paths = [
        ROOT / "evidence/darp_mt10_run_card_20261027.json",
        ROOT / "docs/downloads/darp_mt10_run_card.json",
    ]
    blobs = [p.read_bytes() for p in paths]
    assert blobs[0] == blobs[1], "DARP run_card copies out of sync!"

    rc = json.loads(blobs[0].decode("utf-8"))
    assert rc["correlation_overlap_vs_registry"]["overlap_3px_vs_dslup_c71122d5"] <= 0.70
    assert rc["correlation_overlap_vs_registry"]["overlap_3px_vs_ecpu_cecbdca7"] <= 0.70
    assert rc["verdict"] == "negative"
    assert rc["ok_to_download_for_research"] is True
    assert rc["ok_to_download_and_submit"] is False
    assert rc["submission_filename"] == "kanlergems2-darp-exp-1-37654dots-20261027T181633Z-4ad35e71-zeros.tif"
    assert rc["submission_filename"] != "kanlergems2-htcads-exp-2-37654dots-20261026T235227Z-11a2f251-zeros.tif"
    assert 0 < len(rc["submission_note"]) <= 140

    tif_path = ROOT / "docs/downloads" / rc["submission_filename"]
    zip_path = ROOT / "docs/downloads" / rc["zip_filename"]
    assert tif_path.exists() and zip_path.exists()
    assert _sha256(tif_path) == rc["raster_sha256"]
    assert _sha256(zip_path) == rc["zip_sha256"]

    with zipfile.ZipFile(zip_path, "r") as zf:
        assert zf.namelist() == [tif_path.name]
        assert hashlib.sha256(zf.read(tif_path.name)).hexdigest() == rc["raster_sha256"]

    with rasterio.open(tif_path) as ds:
        assert ds.count == 1
        assert str(ds.crs) == "EPSG:32611"
        assert (ds.height, ds.width) == (3730, 3292)
        assert ds.dtypes == ("float32",)
        assert ds.nodata is None
        assert list(ds.transform)[:6] == [100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0]
        arr = ds.read(1)
        assert int(np.isnan(arr).sum()) == 0
        assert int(np.isinf(arr).sum()) == 0
        assert float(arr.min()) == 0.0
        assert float(arr.max()) == 1.0
        assert int((arr > 0.5).sum()) == 37_654


def test_68ch_canary_and_c_pied_breakthrough_and_pigeonhole_proof() -> None:
    """Verify 68-channel Rule 4 canary, DARP-EXP-2 +39.1% C_pied win, and exact U=6,649 Pigeonhole bound."""
    canary = json.loads((ROOT / "evidence/darp_mt10_canary_20261027.json").read_text(encoding="utf-8"))
    assert canary["passed"] is True
    assert canary["total_features_tested"] == 68
    assert canary["max_single_feature_auc"] <= 0.90

    darp = json.loads((ROOT / "evidence/darp_mt10_experiments_20261027.json").read_text(encoding="utf-8"))
    assert darp["within_protocol_budget"]["experiments_run"] == 3
    assert darp["within_protocol_budget"]["wall_hours"] <= 2.0
    assert darp["within_protocol_budget"]["live_drivendata_slots_spent"] == 0

    # Exact Pigeonhole proof on 13gems 5-px lattice
    ph = darp["exact_13gems_lattice_pigeonhole"]
    assert ph["footprint_pixels"] == 5_167_373
    assert ph["within_3px_pixels"] + ph["exact_uncovered_pixels_U"] == 5_167_373
    assert ph["exact_uncovered_pixels_U"] == 6649
    min_ov = (37_654 - ph["exact_uncovered_pixels_U"]) / 37_654
    assert min_ov > 0.8234

    # DARP-EXP-2 C-PIED-v1.0 breakthrough (+39.1% over 0.2778 Champion)
    exp2 = next(e for e in darp["experiments"] if e["id"] == "DARP-EXP-2")
    cp2 = exp2["c_pied_piedmont_off_catalogue"]
    champ_cp = darp["reference_benchmarks"]["GEMSDOE32_B2_0p2778_champ"]["c_pied_v1_0_dti"]
    assert cp2["pooled_dti"] > champ_cp + 0.035
    assert cp2["paired_delta_ci95"][0] > 0.015

    # Detector uniqueness <= 70% across all 3 experiments
    for e in darp["experiments"]:
        u = e["uniqueness"]
        assert u["unique_rasters_checked"] >= 285
        assert u["pre_placement_surface_max_abs_spearman"] < 0.90
        assert u["final_dots_max_abs_spearman"] < 0.90
        assert u["final_dots_max_detector_3px_overlap"] <= 0.70


def test_sister_sites_audited_and_evaluate_holdout_verify_darp() -> None:
    sis = json.loads((ROOT / "evidence/sister_and_focus_audit_20261027.json").read_text(encoding="utf-8"))
    audited_names = {r["site"] for r in sis["sister_and_fleet_audited_rasters"]}
    for s in ("KANLERGEMSDOE1", "KANLERGEMSDOE3", "WBGGEMSDOE1", "WBGGEMSDOE2", "WBGGEMSDOE3"):
        assert s in audited_names
    empty_names = {r["site"] for r in sis["empty_initialized_sister_repos"]}
    assert empty_names == {"EUGGEMSDOE1", "EUGGEMSDOE2", "EUGGEMSDOE3", "GINNYGEMSDOE1", "GINNYGEMSDOE2", "GINNYGEMSDOE3"}

    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/evaluate_holdout.py"), "--verify-darp"],
        capture_output=True,
        text=True,
        check=True,
    )
    out = json.loads(proc.stdout)
    assert out["verified"] is True
    assert out["verdict"] == "negative"
    assert out["ok_to_download_and_submit"] is False
