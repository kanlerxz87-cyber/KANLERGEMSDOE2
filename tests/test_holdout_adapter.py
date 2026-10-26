"""Synthetic tests of whole-segment holdout and canary; no real model is trained."""
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from evaluate_holdout import evaluate, load_masks
from gems.holdout import SegmentHoldout
from gems.metric import dti_score_fast


def tif(path, array):
    with rasterio.open(path, "w", driver="GTiff", height=array.shape[0], width=array.shape[1], count=1,
                       dtype="float32", crs="EPSG:32611", transform=from_origin(0, 30000, 100, 100)) as dst:
        dst.write(array.astype("float32"), 1)
    return path


@pytest.fixture
def synthetic_holdout(tmp_path):
    truth = np.zeros((240, 240), np.float32)
    for y, x in [(25, 30), (25, 200), (190, 30), (190, 200)]:
        truth[y:y + 30, x] = 1
    truth[118:123, 60:180] = 1  # crosses the quadrant border as one connected component
    sample = tif(tmp_path / "sample.tif", np.zeros_like(truth))
    labels = tif(tmp_path / "labels.tif", truth)
    features = tmp_path / "features.npz"
    np.savez(features, physical_control=np.random.default_rng(10).normal(size=truth.shape))
    predictions = tmp_path / "folds.npz"
    np.savez(predictions, **{f"fold_{i}": np.zeros_like(truth) for i in range(4)})
    return tmp_path, truth, sample, labels, features, predictions


def test_component_crossing_boundary_hidden_everywhere(synthetic_holdout):
    _, truth, _, _, _, _ = synthetic_holdout
    ctx = SegmentHoldout(np.ones_like(truth, dtype=bool), truth > 0, buffer_px=5)
    component = ctx.components[120, 80]
    assert component > 0
    for fold in ctx.folds:
        if component in fold["hidden_component_ids"]:
            assert not fold["visible"][ctx.components == component].any()
            assert not (fold["train"] & (ctx.components == component)).any()
        assert not (fold["train"] & fold["valid"]).any()
        assert not (fold["visible"] & fold["truth"]).any()


def test_visible_faults_are_masked_pixel_exactly():
    truth = np.zeros((20, 20), bool)
    truth[10, 10] = True
    visible = np.zeros_like(truth)
    visible[2, 2] = True
    pred = np.zeros_like(truth)
    pred[10, 10] = True
    masked = dti_score_fast(pred, truth, valid_mask=np.ones_like(truth), catalogue_mask=visible)
    pred[2, 2] = True
    still_masked = dti_score_fast(pred, truth, valid_mask=np.ones_like(truth), catalogue_mask=visible)
    assert masked == still_masked


def test_canary_stops_before_scoring_a_leaked_feature(synthetic_holdout):
    root, truth, sample, labels, features, predictions = synthetic_holdout
    np.savez(features, leaked_catalogue=truth)
    result = evaluate(sample, labels, predictions, features, buffer_px=5, ci_draws=100)
    assert result["status"] == "stopped_leakage_canary"
    assert result["canary"]["max_two_polarity_auc"] > .90
    assert result["holdout"] is None and not result["eligible_for_selector"]


def test_valid_synthetic_diagnostic_never_authorizes_submission(synthetic_holdout):
    _, _, sample, labels, features, predictions = synthetic_holdout
    result = evaluate(sample, labels, predictions, features, buffer_px=5, baseline=predictions, ci_draws=100)
    assert result["status"] == "diagnostic_only" and not result["eligible_for_selector"]
    holdout = result["holdout"]
    assert holdout["label"] == "HOLDOUT-DTI" and holdout["evaluator_version"]
    assert holdout["n_withheld_positive_pixels"] > 0 and holdout["ci95"]["level"] == .95
    assert holdout["protocol"]["alpha"] == .2 and holdout["protocol"]["beta"] == .8
    assert holdout["protocol"]["triangular_kernel_radius_m"] == 300
    assert result["paired_baseline"]["paired_delta_dti"] == 0
    assert "cannot verify" in result["provenance_warning"]


def test_fold_file_rejects_missing_extra_and_soft_predictions(synthetic_holdout):
    root, truth, sample, labels, features, predictions = synthetic_holdout
    np.savez(predictions, fold_0=truth, fold_1=truth, extra=truth)
    with pytest.raises(ValueError, match="Expected exactly"):
        load_masks(predictions, 4)
    np.savez(predictions, **{f"fold_{i}": np.full_like(truth, .5) for i in range(4)})
    with pytest.raises(ValueError, match="binary prediction"):
        evaluate(sample, labels, predictions, features, buffer_px=5, ci_draws=100)
