"""Regression coverage for literal gating, shared scoring and published decisions.

All arrays in these tests are synthetic; they are not geological experiments or
leaderboard scores. No organizer credentials or competition data are required.
"""
from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from affine import Affine
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems import footprint, metric as metric_a, novelty, submission  # noqa: E402
from gems.holdout import SegmentHoldout  # noqa: E402
from gems32 import holdout, metric as metric_b  # noqa: E402


def test_marginal_credit_threshold_and_general_scope():
    # One uncovered truth: adding unit mass gives (dTP,dFP,dFN)=(k,1-k,-k).
    tp, fp, fn = 20.0, 40.0, 80.0
    old_score = tp / (tp + 0.2 * fp + 0.8 * fn)
    actual_bar = 0.2 * old_score
    incorrect_bar = actual_bar / (1.0 - actual_bar)
    credit = (actual_bar + incorrect_bar) / 2
    new_score = (tp + credit) / ((tp + credit) + 0.2 * (fp + 1-credit) + 0.8 * (fn-credit))
    assert new_score > old_score  # the old formula wrongly rejected this gain
    assert metric_a.marginal_inclusion_threshold(old_score) == pytest.approx(actual_bar)
    assert metric_b.marginal_inclusion_threshold(old_score) == pytest.approx(actual_bar)
    for invalid in (float('nan'), -0.1, 1.1):
        with pytest.raises(ValueError):
            metric_a.marginal_inclusion_threshold(invalid)
        with pytest.raises(ValueError):
            metric_b.marginal_inclusion_threshold(invalid)


def test_metric_implementations_match_literal_formula_for_soft_and_binary():
    rng = np.random.default_rng(144)
    for _ in range(12):
        truth = rng.random((8, 9)) < .1
        pred = rng.random((8, 9)) * (rng.random((8, 9)) < .18)
        brute = metric_b.dti_bruteforce(pred, truth)
        g32 = metric_b.dti_exact(pred, truth)
        shared = metric_a.dti_components_exact(pred, truth)
        assert g32['tp'] == pytest.approx(brute['tp'])
        assert g32['fp'] == pytest.approx(brute['fp'])
        assert g32['fn'] == pytest.approx(brute['fn'])
        assert shared['TP_w'] == pytest.approx(brute['tp'])
        assert shared['FP_w'] == pytest.approx(brute['fp'])
        assert shared['FN_w'] == pytest.approx(brute['fn'])
        binary = (pred > 0).astype(np.float32)
        assert metric_b.dti_binary(binary, truth)['dti'] == pytest.approx(metric_b.dti_exact(binary, truth)['dti'])


def test_metric_rejects_bad_masks_truth_and_binary_coercion():
    truth = np.zeros((4, 4), dtype=float)
    pred = np.zeros_like(truth)
    for bad_value in (np.nan, np.inf, -.1, 1.1):
        bad = pred.copy()
        bad[1, 1] = bad_value
        with pytest.raises(ValueError):
            metric_b.dti_exact(bad, truth)
        with pytest.raises(ValueError):
            metric_b.dti_binary(bad, truth)
        with pytest.raises(ValueError):
            metric_a.dti_components_exact(bad, truth)
    soft = pred.copy()
    soft[1, 1] = 0.25
    with pytest.raises(ValueError, match='binary predictions'):
        metric_b.dti_binary(soft, truth)
    invalid_truth = truth.copy()
    invalid_truth[1, 1] = np.nan
    with pytest.raises(ValueError, match='ground truth'):
        metric_b.dti_exact(pred, invalid_truth)
    with pytest.raises(ValueError, match='Ground truth'):
        metric_a.dti_components_exact(pred, invalid_truth)
    invalid_mask = np.ones_like(pred)
    invalid_mask[0, 0] = np.nan
    with pytest.raises(ValueError, match='masks'):
        metric_b.dti_binary(pred, truth, valid=invalid_mask)
    # Invalid exterior values remain permissible when the domain excludes them.
    valid = np.ones_like(truth, bool)
    valid[0, 0] = False
    pred[0, 0] = np.nan
    assert metric_b.dti_exact(pred, truth, valid=valid)['dti'] == 0


def tiny_context(empty_sgmc: bool = False) -> holdout.HoldoutContext:
    shape = (16, 32)
    foot = np.ones(shape, bool)
    quad = np.zeros(shape, np.int8)
    quad[:8, 16:] = 1
    quad[8:, :16] = 2
    quad[8:, 16:] = 3
    cells = []
    for seed in holdout.DRAWS:
        for fold in holdout.FOLDS:
            truth = np.zeros(shape, bool)
            truth[(2 if fold < 2 else 10), (4 if fold % 2 == 0 else 20)] = True
            active = quad == fold
            cells.append(holdout.PreparedCell(
                key=f'draw{seed}_fold{fold}', fold=fold, seed=seed,
                bbox=(slice(0, shape[0]), slice(0, shape[1])),
                active_sub=active, truth_coords=np.nonzero(truth),
                k_dg_sub=holdout.kernel(distance_transform_edt(~truth)), n_truth=1,
                visible_sub=np.zeros(shape, bool), d_visible_sub=np.full(shape, 99.0),
            ))
    sg = np.zeros(shape, bool)
    if not empty_sgmc:
        sg[3, 3] = True
    return holdout.HoldoutContext(
        foot=foot, labels=np.zeros(shape, bool), sgmc_off=sg, near_visible=np.zeros(shape, bool),
        quad=quad, quad_bboxes={i: (slice(0, 16), slice(0, 32)) for i in range(4)},
        cells=cells, sgmc_truth_coords=np.nonzero(sg),
        sgmc_k_dg=holdout.kernel(distance_transform_edt(~sg)) if sg.any() else np.zeros(shape),
        sgmc_n_truth=int(sg.sum()), sgmc_quad_truth_coords={}, sgmc_quad_n_truth={},
    )


def test_shared_holdout_rejects_invalid_static_and_fold_predictions():
    ctx = tiny_context()
    good = np.zeros(ctx.foot.shape, np.float32)
    good[2, 4] = .7
    out = holdout.evaluate_hide_and_recover(good, ctx, grid_n=2, n_boot=20)
    assert 0 <= out['pooled_dti'] <= 1
    for bad_value in (np.nan, np.inf, -.01, 1.01):
        bad = good.copy()
        bad[2, 4] = bad_value
        with pytest.raises(ValueError, match='finite and in'):
            holdout.evaluate_hide_and_recover(bad, ctx, grid_n=2, n_boot=20)
        cells = {cell.key: good.copy() for cell in ctx.cells}
        cells[ctx.cells[0].key][2, 4] = bad_value
        with pytest.raises(ValueError, match='finite and in'):
            holdout.evaluate_hide_and_recover(cells, ctx, grid_n=2, n_boot=20)
        with pytest.raises(ValueError, match='finite and in'):
            holdout.evaluate_sgmc_with_ci(bad, ctx, grid_n=2, n_boot=20)
    with pytest.raises(ValueError, match='footprint grid'):
        holdout.evaluate_hide_and_recover(np.zeros((2, 2)), ctx, grid_n=2, n_boot=20)


def test_sgmc_empty_truth_retains_binary_and_soft_false_positive_mass():
    ctx = tiny_context(empty_sgmc=True)
    for value in (1.0, 0.25):
        prediction = np.full(ctx.foot.shape, value, np.float32)
        result = holdout.evaluate_sgmc_with_ci(prediction, ctx, grid_n=2, n_boot=20)
        assert result['sgmc_raw_pooled_dti'] == 0
        assert result['raw_components']['fp'] == pytest.approx(prediction.sum())
        assert result['raw_components']['prediction_mass'] == pytest.approx(prediction.sum())
        assert 'not a holdout DTI' in result['calibration_status']


def test_segment_holdout_hides_whole_components_and_canary_flags_leakage():
    foot = np.ones((100, 100), bool)
    labels = np.zeros_like(foot)
    for row, col in ((20, 20), (20, 70), (70, 20), (70, 70)):
        labels[row:row+6, col] = True
    ctx = SegmentHoldout(foot, labels, buffer_px=3)
    for fold in ctx.folds:
        assert not np.any(fold['truth'] & fold['visible'])
        assert not np.any(np.isin(ctx.components[fold['visible']], fold['hidden_component_ids']))
        assert not np.any(fold['train'] & fold['valid'])
    result = ctx.canary({'intentional_label_leak': labels.astype(float)}, max_per_class=100)
    assert result['passed'] is False
    assert result['features']['intentional_label_leak']['leakage_suspected'] is True


def test_footprint_decoder_fails_cleanly_for_corruption(tmp_path):
    for payload in (b'\x80', b'\x81' * 11, b'\x06'):
        with pytest.raises(ValueError):
            footprint.decode_runs(payload, total=5)
    bad = tmp_path / 'footprint.bin'
    bad.write_bytes((ROOT / 'docs/data/footprint.bin').read_bytes()[:-1])
    with pytest.raises(ValueError, match='checksum'):
        footprint.load_footprint(bad)


def test_novelty_masks_cannot_silently_coerce_invalid_or_soft_values():
    mask = np.zeros((4, 4), dtype=float)
    invalid = mask.copy()
    invalid[0, 0] = np.nan
    with pytest.raises(ValueError, match='finite binary'):
        novelty.dot_overlap(invalid, mask)
    invalid[0, 0] = .5
    with pytest.raises(ValueError, match='finite binary'):
        novelty.compare_registry(mask, np.ones((4, 4), bool), [], '.', dots=invalid)
    with pytest.raises(ValueError, match='binary footprint'):
        novelty.compare_registry(mask, invalid, [], '.')


def test_format_rejects_same_count_shifted_template_footprint(tmp_path, monkeypatch):
    transform = Affine(100, 0, 0, 0, -100, 400)
    mask = np.ones((4, 4), bool)
    mask[0, 0] = False
    monkeypatch.setattr(footprint, 'load_footprint', lambda: mask)
    monkeypatch.setitem(submission.EXPECTED, 'shape', (4, 4))
    monkeypatch.setitem(submission.EXPECTED, 'transform', tuple(transform)[:6])
    template = tmp_path / 'template.tif'
    shifted = np.zeros((4, 4), np.float32)
    shifted[0, 1] = np.nan  # same 15 finite pixels, but the wrong footprint
    with rasterio.open(template, 'w', driver='GTiff', width=4, height=4, count=1,
                       dtype='float32', crs='EPSG:32611', transform=transform) as ds:
        ds.write(shifted, 1)
    target = tmp_path / 'candidate.tif'
    submission.write_submission(np.zeros((4, 4), np.float32), template, target)
    report = submission.check_variants(target, template)
    assert not report['checks']['official_template_grid_and_footprint']['pass']
    assert not report['format_valid']


def test_writer_preserves_existing_output_when_format_validation_fails(tmp_path):
    template = tmp_path / 'not-the-mirror.tif'
    with rasterio.open(template, 'w', driver='GTiff', width=4, height=4, count=1,
                       dtype='float32', crs='EPSG:32611', transform=Affine(100, 0, 0, 0, -100, 400)) as ds:
        ds.write(np.zeros((4, 4), np.float32), 1)
    source = tmp_path / 'source.npy'
    np.save(source, np.zeros((4, 4), np.float32))
    destination = tmp_path / 'candidate.tif'
    destination.write_bytes(b'pre-existing data')
    proc = subprocess.run([sys.executable, str(ROOT / 'scripts/submission_writer.py'), str(source),
                           str(destination), '--template', str(template)], capture_output=True, text=True)
    assert proc.returncode != 0
    assert 'failed pinned-mirror' in proc.stderr
    assert destination.read_bytes() == b'pre-existing data'
    assert not list(tmp_path.glob('.gems-writer-*'))


def test_retired_validator_and_parallel_entrypoints_never_authorize(tmp_path):
    legacy = importlib.import_module('validate_submission_kg2s2')
    card = tmp_path / 'card.json'
    card.write_text(json.dumps({'verdict': 'promote', 'raster_sha256': '0' * 64}))
    for mode in ('champion', 'unique-slot'):
        verdict = legacy.validate_all_gates(tmp_path / 'missing.tif', card, tmp_path, mode)
        assert verdict['verdict'] == 'negative'
        assert verdict['validated_ok_to_download_and_submit'] is False
    modules = ('run_cpr_experiments', 'run_darp_mt10_experiments', 'run_dslup_experiments',
               'run_dslup_unique_slot', 'run_ecpu_experiments')
    for module in modules:
        with pytest.raises(SystemExit, match='Archived lane disabled'):
            importlib.import_module(module).main()


def test_published_decision_cannot_contradict_literal_revalidation():
    receipt = json.loads((ROOT / 'evidence/dslup_literal_revalidation_20261027.json').read_text())
    feed = json.loads((ROOT / 'docs/data/status_feed.json').read_text())
    published = json.loads((ROOT / 'docs/downloads/dslup_run_card.json').read_text())
    assert receipt['verdict'] == 'negative' and receipt['ok_to_submit'] is False
    assert receipt['format_audit']['witness_overlap_dots'] == 37647
    assert receipt['format_audit']['inside_positive_pixels'] == 37654
    assert feed['verdict'] == 'negative' and feed['ok_to_submit'] is False
    assert feed['session2_candidate']['ok_to_submit'] is False
    assert feed['session2_candidate']['sha256'] == receipt['raster_sha256']
    assert published['verdict'] == 'negative' and published['ok_to_download_and_submit'] is False
    for filename in ('index.html', 'executive-summary.html', 'submission-table.html'):
        text = (ROOT / 'docs' / filename).read_text().upper()
        assert 'DO NOT SUBMIT' in text
        assert 'PROMOTE — OK TO SUBMIT' not in text
        assert 'TWO VERDICTS, YOUR CALL' not in text
    for filename in ('README.md', 'EXECUTIVE_SUMMARY.md'):
        text = (ROOT / filename).read_text().upper()
        assert 'DO NOT SUBMIT' in text
        assert 'PROMOTE — OK TO SUBMIT' not in text
