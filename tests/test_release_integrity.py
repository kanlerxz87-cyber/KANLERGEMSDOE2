"""Regression tests for fail-closed release checks and the public evidence feed."""
from __future__ import annotations

import hashlib
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
from rasterio.crs import CRS
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems import novelty, release_audit  # noqa: E402
from gems.validator import sha256_file  # noqa: E402
import refresh_public_feed  # noqa: E402
import validate_submission  # noqa: E402


def test_strict_counting_boundary_and_invalid_budget():
    assert not novelty.budget_forced_duplicate(3, 10)  # exactly 70% is allowed
    assert novelty.budget_forced_duplicate(3, 11)
    assert not novelty.budget_forced_duplicate(6649, 22163)
    assert novelty.budget_forced_duplicate(6649, 22164)
    assert novelty.budget_forced_duplicate(6649, 37654)
    for u, n in [(-1, 10), (0, 0), (1.0, 2), (True, 5), (0, True)]:
        with pytest.raises(ValueError):
            novelty.budget_forced_duplicate(u, n)
    assert not novelty.is_duplicate(0.90, 0.70)
    assert novelty.is_duplicate(0.900001, 0.70)
    assert novelty.is_duplicate(0.0, 0.700001)
    assert novelty.is_duplicate(-1.0, 0.0)  # extra conservative preregistered |rho| cap
    with pytest.raises(ValueError):
        novelty.is_duplicate(float("nan"), 0.0)


def test_directional_overlap_uses_inclusive_euclidean_radius():
    candidate = np.zeros((15, 15), bool)
    reference = np.zeros_like(candidate)
    candidate[5, 5] = candidate[13, 13] = True
    reference[5, 8] = reference[0, 0] = reference[0, 1] = True
    result = novelty.dot_overlap(candidate, reference, radius_px=3)
    assert result["candidate_within_3px_of_reference"] == 0.5  # distance exactly 3 included
    assert result["reference_within_3px_of_candidate"] == 1 / 3


def test_binary_rho_matches_scipy_and_constant_is_undefined():
    rng = np.random.default_rng(11)
    foot = np.ones((20, 30), bool)
    a, b = rng.random(foot.shape) < 0.2, rng.random(foot.shape) < 0.3
    assert release_audit._binary_rho(a, b, foot) == pytest.approx(spearmanr(a.ravel(), b.ravel()).statistic)
    assert release_audit._binary_rho(np.zeros_like(a), b, foot) is None


def make_registry(tmp_path: Path):
    foot = np.ones((20, 20), bool)
    reference = np.zeros(foot.shape, np.float32)
    reference[::5, ::5] = 1
    transform = Affine(100, 0, 1000, 0, -100, 2000)
    crs = CRS.from_epsg(32611)
    path = tmp_path / "lattice.tif"
    with rasterio.open(path, "w", driver="GTiff", width=20, height=20, count=1,
                       dtype="float32", crs=crs, transform=transform) as ds:
        ds.write(reference, 1)
    row = {"id": "lattice", "file": path.name, "cache_path": path.name,
           "footprint_sha256": hashlib.sha256(reference.astype("<f4").tobytes()).hexdigest()}
    return foot, reference, [row], (foot.shape, crs, transform)


def test_control_never_exempt_and_grid_and_ranks_fail_closed(tmp_path):
    foot, reference, entries, grid = make_registry(tmp_path)
    surface = np.random.default_rng(0).random(foot.shape)
    dots = np.zeros_like(foot)
    dots[0, 0] = dots[5, 5] = dots[10, 10] = True
    result = novelty.compare_registry(surface, foot, entries, tmp_path, dots=dots,
                                      separate_calibration_controls=True, reference_grid=grid)
    assert not result["passed"]
    assert not result["literal_unseparated_passed"]
    assert result["rows"][0]["comparator_class"] == "space_filling_calibration_control"
    assert result["rows"][0]["candidate_dot_overlap_within_3px"] == 1
    assert result["rows"][0]["literal_duplicate"] is True
    assert result["rows"][0]["duplicate"] is True
    # Neither an absent template grid nor an undefined constant rank can pass.
    no_grid = novelty.compare_registry(surface, foot, entries, tmp_path)
    assert no_grid["reference_grid_verified"] is False and no_grid["passed"] is False
    constant = novelty.compare_registry(np.ones_like(surface), foot, entries, tmp_path, reference_grid=grid)
    assert constant["all_raw_ranks_defined"] is False and constant["passed"] is False
    wrong_grid = (grid[0], grid[1], Affine(100, 0, 0, 0, -100, 0))
    with pytest.raises(ValueError, match="CRS/transform mismatch"):
        novelty.compare_registry(surface, foot, entries, tmp_path, reference_grid=wrong_grid)


def test_assess_local_nan_inside_and_range_without_portal_claim(tmp_path):
    foot = np.ones((4, 5), bool)
    foot[0, 0] = False
    refdots = np.zeros_like(foot)
    refdots[2, 2] = True
    data = np.zeros(foot.shape, np.float32)
    data[1, 1] = np.nan
    data[1, 2] = 1.2
    data[3, 4] = 1
    transform = Affine(100, 0, 0, 0, -100, 400)
    crs = CRS.from_epsg(32611)
    path = tmp_path / "bad.tif"
    with rasterio.open(path, "w", driver="GTiff", width=5, height=4, count=1,
                       dtype="float32", crs=crs, transform=transform) as ds:
        ds.write(data, 1)
    ref = {"foot": foot, "catalogue": np.zeros_like(foot), "near": np.ones_like(foot),
           "grid": (foot.shape, crs, transform), "reference": refdots}
    result = release_audit.assess_file(path, ref)
    assert not result["no_nan_inside_footprint"]
    assert not result["inside_range_0_1"]
    assert not result["strict_whole_array_finite_0_1"]
    assert not result["local_grid_dtype_inside_range_pass"]
    assert result["organizer_acceptance_verified"] is False
    # Soft values must retain their ranks; thresholding all nonzero cells would
    # incorrectly make this 1.0-correlated candidate constant and undefined.
    soft = np.full(foot.shape, 0.1, np.float32)
    soft[2, 2] = 0.9
    with rasterio.open(path, "w", driver="GTiff", width=5, height=4, count=1,
                       dtype="float32", crs=crs, transform=transform) as ds:
        ds.write(soft, 1)
    soft_result = release_audit.assess_file(path, ref)
    assert soft_result["witness_final_dots_spearman"] == pytest.approx(1.0)
    assert soft_result["duplicate_under_literal_rule"] is True


def test_validator_fails_closed_for_missing_references_and_identity(tmp_path, monkeypatch):
    card = tmp_path / "card.json"
    card.write_text(json.dumps({"raster_sha256": "0" * 64, "verdict": "promote"}))
    missing = validate_submission.validate_all_gates(tmp_path / "missing.tif", card, tmp_path)
    assert missing["ok_to_submit"] is False and not any(missing["gates"].values())
    assert "unavailable" in missing["reasons"][0]
    monkeypatch.setattr(validate_submission, "load_reference", lambda *args: {})
    monkeypatch.setattr(validate_submission, "assess_file", lambda *args: {
        "sha256": "1" * 64, "local_grid_dtype_inside_range_pass": True,
        "witness_final_dots_spearman": 0.1, "inside_positive_pixels": 1,
        "duplicate_under_literal_rule": False, "outside_footprint_all_zero": False,
    })
    mismatch = validate_submission.validate_all_gates(tmp_path / "file.tif", card, tmp_path)
    assert mismatch["gates"]["exact_file_identity"] is False
    assert mismatch["gates"]["local_grid_dtype_inside_range"] is True
    assert mismatch["gates"]["literal_witness_not_duplicate"] is True
    assert mismatch["ok_to_submit"] is False  # self-attested promotion and quota cannot override
    card.write_text(json.dumps({"raster_sha256": "1" * 64, "submission_filename": "other.tif"}))
    renamed = validate_submission.validate_all_gates(tmp_path / "file.tif", card, tmp_path)
    assert renamed["gates"]["exact_file_identity"] is False
    card.write_text(json.dumps({"raster_sha256": "1" * 64, "submission_filename": "file.tif"}))
    exact = validate_submission.validate_all_gates(tmp_path / "file.tif", card, tmp_path)
    assert exact["gates"]["exact_file_identity"] is True and exact["ok_to_submit"] is False


def test_current_evidence_new_unique_submission():
    # PR #36 generated an off-catalogue file whose card said "promote". The review
    # overrode that: no holdout DTI, placement chosen to pass the lattice gate, and a
    # reduced budget. The authoritative card stays fail-closed.
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    audit = json.loads((ROOT / "evidence/release_audit_20261027.json").read_text())
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["holdout_dti"] is None and card["experiments_run"] == 0
    assert len(card["note"]) <= 140
    superseded = json.loads((ROOT / "evidence/superseded/current_run_card_pr36_promote_20261027.json").read_text())
    assert superseded["verdict"] == "promote" and superseded["holdout_dti"] is None
    assert superseded["raster_sha256"] == "0e7e1da78fb80ba3ce0849cd32967836d4f3d73206426d43435fbe3958a446c4"
    tif = ROOT / "docs" / "downloads" / superseded["submission_name"]
    assert tif.is_file() and sha256_file(tif) == superseded["raster_sha256"]
    receipt = json.loads((ROOT / "evidence/off36_independent_check_20261027.json").read_text())
    assert receipt["sha256"] == superseded["raster_sha256"]
    assert receipt["dots"] == 15000 and receipt["holdout_dti"] is None
    assert receipt["lattice_overlap_3px"] == 0.66 and receipt["dots_in_lattice_gap_fraction"] >= 0.30
    assert receipt["on_catalogue_positive_pixels"] == 107
    assert receipt["max_overlap_3px_restored_registry"]["fraction"] <= 0.70 + 1e-9
    assert audit["preflight"]["uncovered_pixels"] == 6649
    assert audit["preflight"]["minimum_overlapping_dots"] == 31005
    assert audit["prior_candidate"]["witness_overlap_dots"] == 37642
    assert audit["prior_candidate"]["duplicate_under_literal_rule"] is True
    assert audit["prior_candidate"]["organizer_acceptance_verified"] is False
    assert len(audit["focus_nine"]) == 9


def test_public_feed_parses_only_ranked_public_score_table(tmp_path):
    rows = ''.join(f'<tr><td>#{i}</td><td>Team {i}</td><td>{score:.4f}</td><td>2</td></tr>'
                   for i, score in enumerate([.4544, .40, .39, .37, .3566], 1))
    valid = '<html><table><tr><th>Rank</th><th>Participant</th><th>Best public DW-Tversky</th><th>Count</th></tr>' + rows + '</table></html>'
    values = refresh_public_feed.parse_leaderboard(valid)
    assert values[1] == .4544 and values[5] == .3566
    with pytest.raises(ValueError):
        refresh_public_feed.parse_leaderboard('<form>Log in</form>')
    with pytest.raises(ValueError):
        refresh_public_feed.parse_leaderboard(valid.replace('#3', '#1'))
    fixture = tmp_path / 'fixture.html'
    fixture.write_text(valid)
    out = tmp_path / 'snapshot.json'
    assert refresh_public_feed.main(['--input-html', str(fixture), '--out', str(out)]) == 0
    assert json.loads(out.read_text())['status'] == 'fixture_only'  # not an organizer observation
    fixture.write_text('<form>login</form>')
    assert refresh_public_feed.main(['--input-html', str(fixture), '--out', str(out), '--strict']) == 1
    failed = json.loads(out.read_text())
    assert failed['status'] == 'unavailable' and failed['top_public_dti'] is None
    assert failed['last_verified_snapshot'] is None
    out.write_text(json.dumps({'status': 'verified_snapshot', 'top_public_dti': .4544, 'observed_utc': '2026-10-27'}))
    assert refresh_public_feed.main(['--input-html', str(fixture), '--out', str(out), '--strict']) == 1
    stale = json.loads(out.read_text())
    assert stale['status'] == 'unavailable' and stale['top_public_dti'] is None
    assert stale['last_verified_snapshot']['top_public_dti'] == .4544


def test_site_builder_rejects_positive_card_or_missing_artifact(tmp_path, monkeypatch):
    builder = importlib.import_module('build_site')
    evidence = tmp_path / 'evidence'
    evidence.mkdir()
    (evidence / 'release_audit_20261027.json').write_text(json.dumps({'verdict': 'negative'}))
    (evidence / 'current_run_card.json').write_text(json.dumps({'verdict': 'promote', 'ok_to_submit': True}))
    monkeypatch.setattr(builder, 'ROOT', tmp_path)
    monkeypatch.setattr(builder, 'DOCS', tmp_path / 'docs')
    with pytest.raises(SystemExit, match='refusing stale or positive card'):
        builder.main()
    real = json.loads((ROOT / 'evidence/release_audit_20261027.json').read_text())
    (evidence / 'release_audit_20261027.json').write_text(json.dumps(real))
    (evidence / 'current_run_card.json').write_text(json.dumps({'verdict': 'negative', 'ok_to_submit': False}))
    with pytest.raises(SystemExit, match='artifact missing or differs'):
        builder.main()


def test_path_resolver_honors_environment_and_legacy_core(tmp_path, monkeypatch):
    from gems32 import paths as paths32
    monkeypatch.delenv('GEMS_DATA_DIR', raising=False)
    monkeypatch.setattr(paths32, 'ROOT', tmp_path)
    legacy = tmp_path / 'data' / 'core'
    legacy.mkdir(parents=True)
    (legacy / 'training_features.tif').touch()
    assert paths32.data_dir() == legacy
    monkeypatch.setenv('GEMS_DATA_DIR', str(tmp_path / 'custom'))
    assert paths32.data_dir() == tmp_path / 'custom'


def test_legacy_runner_stops_when_reference_is_absent(tmp_path):
    env = {**os.environ, 'GEMS_DATA_DIR': str(tmp_path)}
    result = subprocess.run([sys.executable, str(ROOT / 'scripts/run_htcads_experiments.py')],
                            cwd=ROOT, env=env, capture_output=True, text=True)
    assert result.returncode != 0
    assert 'fail closed' in result.stderr
    other = subprocess.run([sys.executable, str(ROOT / 'scripts/evaluate_holdout.py'), '--run-kg2'],
                           cwd=ROOT, env=env, capture_output=True, text=True)
    assert other.returncode != 0 and 'disabled' in other.stderr
