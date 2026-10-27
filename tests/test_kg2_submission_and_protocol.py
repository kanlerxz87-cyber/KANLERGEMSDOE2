"""Synthetic regression tests for literal novelty, grids, holdout, format and selector."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import zipfile
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from scipy.ndimage import distance_transform_edt

from gems import holdout, metric, novelty, selector, submission
from gems.validator import sha256_file

ROOT = Path(__file__).resolve().parents[1]
TRANSFORM = Affine(100, 0, 243350, 0, -100, 4508550)


def raster(path, array, *, crs="EPSG:32611", transform=TRANSFORM, count=1):
    array = np.asarray(array, np.float32)
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1],
                       count=count, dtype="float32", crs=crs, transform=transform) as ds:
        for band in range(1, count + 1):
            ds.write(array, band)
    return path


def entry(path, fp, registry_name=None):
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return {"id": "test-registry", "file": registry_name or path.name,
            "cache_path": path.name,
            "footprint_sha256": hashlib.sha256(np.asarray(a[fp], dtype="<f4").tobytes()).hexdigest()}


def test_lattice_control_cannot_exempt_literal_duplicate(tmp_path: Path) -> None:
    fp = np.ones((30, 30), bool)
    template = raster(tmp_path / "template.tif", np.zeros(fp.shape))
    lattice = np.zeros(fp.shape, np.float32)
    lattice[::5, ::5] = 1
    path = raster(tmp_path / "lattice.tif", lattice)
    row = entry(path, fp, "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif")
    rng = np.random.default_rng(55)
    surface = rng.random(fp.shape)
    dots = np.zeros(fp.shape, bool)
    dots[5:25:2, 5:25:2] = True

    pre = novelty.compare_registry(surface, fp, [row], tmp_path, template=template)
    assert pre["stage"] == "surface_before_placement" and pre["rows"][0]["rank_defined"]
    final = novelty.compare_registry(surface, fp, [row], tmp_path, template=template,
                                     dots=dots, separate_calibration_controls=True)
    assert final["rows"][0]["comparator_class"] == "space_filling_calibration_control"
    assert final["max_dot_overlap"] > .70
    assert final["rows"][0]["duplicate"] is True and final["rows"][0]["literal_duplicate"] is True
    assert final["passed"] is False and final["literal_unseparated_passed"] is False
    prospective = novelty.compare_prospective_registry(surface, fp, [row], tmp_path, template=template, dots=dots)
    assert prospective["literal_all_entries_passed"] is False
    assert prospective["literal_duplicate_rows"][0]["registry_id"] == row["id"]
    assert prospective["calibration_control_rasters_count"] == 1


def test_undefined_rank_and_empty_registry_fail_closed(tmp_path: Path) -> None:
    fp = np.ones((12, 12), bool)
    template = raster(tmp_path / "template.tif", np.zeros(fp.shape))
    zero = raster(tmp_path / "zero.tif", np.zeros(fp.shape))
    ref = entry(zero, fp)
    surface = np.arange(fp.size, dtype=float).reshape(fp.shape)
    result = novelty.compare_registry(surface, fp, [ref], tmp_path, template=template)
    assert result["passed"] is False and result["undefined_rank_rows"] == [ref["id"]]
    assert novelty.compare_registry(surface, fp, [], tmp_path, template=template)["passed"] is False
    assert novelty.correlation(np.ones(4), np.arange(4)) is None
    with pytest.raises(ValueError, match="Undefined"):
        novelty.is_duplicate(None, .1)
    assert novelty.is_duplicate(None, .71) is True
    assert novelty.is_duplicate(.90, .70) is False
    assert novelty.is_duplicate(.901, .70) is True
    assert novelty.is_duplicate(.90, .701) is True


@pytest.mark.parametrize("crs,transform", [
    ("EPSG:32611", Affine(100, 0, 243450, 0, -100, 4508550)),
    ("EPSG:32612", TRANSFORM),
    (None, TRANSFORM),
])
def test_registry_must_match_crs_and_transform(tmp_path: Path, crs, transform) -> None:
    fp = np.ones((12, 12), bool)
    template = raster(tmp_path / "template.tif", np.zeros(fp.shape))
    a = np.arange(fp.size, dtype=np.float32).reshape(fp.shape)
    ref = raster(tmp_path / "ref.tif", a, crs=crs, transform=transform)
    with pytest.raises(ValueError, match="CRS/shape/transform"):
        novelty.compare_registry(a, fp, [entry(ref, fp)], tmp_path, template=template)


def test_comparison_requires_explicit_grid_and_binary_masks(tmp_path: Path) -> None:
    fp = np.ones((8, 8), bool)
    surf = np.arange(fp.size).reshape(fp.shape)
    with pytest.raises(ValueError, match="reference template"):
        novelty.compare_registry(surf, fp, [], tmp_path)
    template = raster(tmp_path / "template.tif", np.zeros(fp.shape))
    bad_fp = fp.astype(float)
    bad_fp[1, 1] = np.nan
    with pytest.raises(ValueError, match="Footprint"):
        novelty.compare_registry(surf, bad_fp, [], tmp_path, template=template)
    bad_dots = np.zeros(fp.shape)
    bad_dots[1, 1] = np.nan
    with pytest.raises(ValueError, match="dots"):
        novelty.compare_registry(surf, fp, [], tmp_path, template=template, dots=bad_dots)
    no_crs = raster(tmp_path / "no-crs.tif", np.zeros(fp.shape), crs=None)
    with pytest.raises(ValueError, match="needs a CRS"):
        novelty.compare_registry(surf, fp, [], tmp_path, template=no_crs)


def test_directional_dot_overlap_and_pigeonhole_bound() -> None:
    fp = np.ones((25, 25), bool)
    ref = np.zeros(fp.shape, bool)
    ref[::5, ::5] = True
    cand = np.zeros(fp.shape, bool)
    cand[5:20:2, 5:20:2] = True
    overlap = novelty.dot_overlap(cand, ref)
    controls = novelty.classify_space_filling_control(fp, ref, candidate_dot_count=int(cand.sum()))
    assert controls["is_space_filling_calibration_control"]
    assert overlap["candidate_within_3px_of_reference"] >= controls["pigeonhole_min_overlap_for_candidate_size"]
    a, b = np.zeros((8, 8), bool), np.zeros((8, 8), bool)
    a[2, 2] = True
    b[2, 5] = True
    assert novelty.dot_overlap(a, b)["candidate_within_3px_of_reference"] == 1.0  # inclusive 3px
    assert novelty.dot_overlap(np.zeros_like(a), b)["candidate_within_3px_of_reference"] is None


def test_segment_holdout_hides_whole_components_and_buffers() -> None:
    fp = np.ones((60, 60), bool)
    labels = np.zeros(fp.shape, bool)
    labels[8, 5:12] = True
    labels[8, 45:52] = True
    labels[48, 5:12] = True
    labels[48, 45:52] = True
    labels[15, 27:34] = True  # component crossing the quadrant boundary
    folds = list(holdout.segment_folds(fp, labels, buffer_px=3))
    assert len(folds) == 4
    assert sum(f["n_withheld_positives"] for f in folds) == int(labels.sum())
    for f in folds:
        assert not (f["hidden"] & f["visible"]).any()
        assert np.array_equal(f["hidden"] | f["visible"], labels)
        assert not (f["training"] & (f["test"] | f["hidden"])).any()
        assert np.all(distance_transform_edt(~(f["test"] | f["hidden"]))[f["training"]] > 3)
    assert folds[0]["hidden"][15, 33] and folds[1]["hidden"][15, 27]
    context = holdout.SegmentHoldout(fp, labels, buffer_px=3)
    for f in context.folds:
        assert not np.isin(context.components[f["visible"]], f["hidden_component_ids"]).any()
        assert not (f["train"] & f["valid"]).any()
    # A forbidden oracle feature should trigger the per-feature canary.
    canary = context.canary({"full_catalogue_leak": labels.astype(float)}, max_per_class=100)
    assert canary["features"]["full_catalogue_leak"]["leakage_suspected"]
    assert canary["passed"] is False


def test_pooled_dti_triangle_and_exact_pixel_mask() -> None:
    fp = np.ones((20, 20), bool)
    truth = np.zeros_like(fp)
    pred = np.zeros(fp.shape, np.float32)
    truth[10, 10] = True
    pred[10, 12] = 1.0
    result = metric.dti_components_exact(pred, truth, fp)
    assert result["TP_w"] == pytest.approx(1 / 3)
    assert result["FP_w"] == pytest.approx(2 / 3)
    assert result["FN_w"] == pytest.approx(2 / 3)
    assert result["dti"] == pytest.approx(metric.dti_score_fast(pred, truth, fp)["dti"])
    known = np.zeros_like(fp)
    known[10, 12] = True
    masked = metric.dti_components_exact(pred, truth, fp, known)
    assert masked["TP_w"] == 0 and masked["FP_w"] == 0
    assert holdout.pooled_dti([[1, 2, 3], [2, 1, 4]]) == pytest.approx(3 / (3 + .2*3 + .8*7 + metric.EPS))
    pred[0, 0] = np.nan
    with pytest.raises(ValueError, match="probabilities"):
        metric.dti_components_exact(pred, truth, fp)


@pytest.fixture
def synthetic_submission(tmp_path: Path, monkeypatch):
    arr = np.zeros((8, 8), np.float32)
    arr[0, :] = np.nan
    template = raster(tmp_path / "template.tif", arr)
    monkeypatch.setitem(submission.EXPECTED, "shape", (8, 8))
    monkeypatch.setitem(submission.EXPECTED, "footprint_pixels", 56)
    prediction = np.zeros_like(arr)
    prediction[4, 4] = .7
    tif = submission.write_submission(prediction, template, tmp_path / "candidate.tif", outside="zero")
    return tmp_path, template, prediction, tif


def test_format_zip_and_outside_nan_diagnostics(synthetic_submission) -> None:
    tmp_path, template, pred, tif = synthetic_submission
    checks = submission.check_variants(tif, template)
    assert checks["format_valid"] and checks["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
    assert checks["official_format_compliant"] is None and not checks["submission_authorized"]
    z = submission.zip_single(tif)
    with zipfile.ZipFile(z) as archive:
        assert archive.namelist() == [tif.name]
        assert hashlib.sha256(archive.read(tif.name)).hexdigest() == sha256_file(tif)
    nan_tif = submission.write_submission(pred, template, tmp_path / "nan.tif", outside="nan")
    nan_report = submission.check_variants(nan_tif, template)
    assert nan_report["format_valid"] and not nan_report["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]
    assert nan_report["official_format_compliant"] is None
    for invalid in (np.nan, -0.1, 1.1, np.inf):
        wrong = pred.copy()
        wrong[4, 4] = invalid
        with pytest.raises(ValueError, match="finite and in"):
            submission.write_submission(wrong, template, tmp_path / "bad.tif")
    shifted = raster(tmp_path / "shifted.tif", np.zeros((8, 8)), transform=Affine.translation(1, 0) @ TRANSFORM)
    assert not submission.check_variants(shifted, template)["format_valid"]
    multiband = raster(tmp_path / "multi.tif", np.zeros((8, 8)), count=2)
    assert not submission.check_variants(multiband, template)["format_valid"]


def test_selector_remains_negative_even_with_fabricated_passing_flags(synthetic_submission) -> None:
    _, template, _, tif = synthetic_submission
    best = selector.RECORDED_BEST_DTI
    card = {
        "raster_sha256": sha256_file(tif), "submission_name": tif.name, "note": "synthetic test only",
        "leakage_canary": {"passed": True, "worst_polarity_extremity": .7},
        "holdout": {"dti": best + .01, "label": "HOLDOUT-DTI", "evaluator_version": selector.RECORDED_BEST_EVALUATOR, "n_withheld_positive_pixels": 60988},
        "paired_vs_baseline": {"ci95": [.001, .02]}, "baseline_reproduced": True,
        "paired_vs_current_best": {"baseline_dti": best, "evaluator_version": selector.RECORDED_BEST_EVALUATOR,
                                   "n_withheld_positive_pixels": 60988, "baseline_replayed": True, "ci95": [.001, .02]},
        "novelty": {"surface": {"literal_all_entries_passed": True, "max_abs_rank_correlation": .2},
                    "final_dots": {"literal_all_entries_passed": True, "literal_duplicate_rows": [], "max_abs_rank_correlation": .2,
                                   "method_lane_max_dot_overlap": .4, "method_lane_passed": True},
                    "peers_final": {"max_dot_overlap_within_3px": .4, "passed": True}},
        "c2st_exact_file": {"strict_gate_passed": True, "labels_audited_first": True},
        "experiments_run": 1, "submission_slots_used": 0,
        "quota_confirmed": True, "independent_replay_certificate": True,
    }
    decision = selector.verify_selector(tif, template, card)
    assert decision["recorded_scientific_screen_passed"] is True
    assert decision["ok_to_submit"] is False and decision["decision"] == "DO_NOT_SUBMIT"
    assert not decision["gates"]["current_account_quota_independently_verified"]
    assert not decision["gates"]["complete_independent_replay_certificate"]
    card["novelty"]["final_dots"]["literal_all_entries_passed"] = False
    assert not selector.verify_selector(tif, template, card)["gates"]["g4_registry_novelty"]


def test_fold_array_cli_scores_without_authorizing(tmp_path: Path) -> None:
    template = raster(tmp_path / "template.tif", np.zeros((220, 220)))
    labels = np.zeros((220, 220), np.float32)
    labels[10, 6:10] = 1
    labels[10, 208:212] = 1
    labels[208, 6:10] = 1
    labels[208, 208:212] = 1
    label_file = raster(tmp_path / "labels.tif", labels)
    npz = tmp_path / "folds.npz"
    zero = np.zeros_like(labels)
    np.savez(npz, NW=zero, NE_LidarGapHeavy=zero, SW=zero, SE=zero)
    command = [sys.executable, str(ROOT / "scripts/evaluate_holdout.py"), "--score-folds", str(npz),
               "--template", str(template), "--labels", str(label_file)]
    proc = subprocess.run(command, capture_output=True, text=True, check=True)
    result = json.loads(proc.stdout)
    assert result["label"] == "HOLDOUT-DTI" and result["n_withheld_positive_pixels"] == 16
    assert result["dti"] == 0 and result["ok_to_submit"] is False
    assert "were not certified" in result["provenance_warning"]
    labels[2, 2] = np.nan
    raster(label_file, labels)
    bad = subprocess.run(command, capture_output=True, text=True)
    assert bad.returncode != 0 and "finite binary" in bad.stderr


def test_verify_kg2_cli_is_research_only() -> None:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_holdout.py"), "--verify-kg2"],
                          capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)
    assert out["verified"] is True and out["ok_to_submit"] is False and out["verdict"] == "negative"
