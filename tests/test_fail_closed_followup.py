"""Adversarial follow-up: no unverified promotion, clipping, or silent restore failure."""
from __future__ import annotations

import hashlib
import json
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
from gems import metric as gmetric  # noqa: E402
from gems32 import holdout, metric, submission  # noqa: E402
import restore_data  # noqa: E402


def tiny_context():
    foot = np.ones((12, 12), dtype=bool)
    foot[0, 0] = False
    known = np.zeros_like(foot)
    known[5, 5] = True
    truth = np.zeros_like(foot)
    truth[6, 6] = True
    ty, tx = np.nonzero(truth)
    k = holdout.kernel(distance_transform_edt(~truth)).astype(np.float32)
    cells = [
        holdout.PreparedCell(
            key=f"draw{seed}_fold{fold}", fold=fold, seed=seed,
            bbox=(slice(0, 12), slice(0, 12)), active_sub=foot & ~known,
            truth_coords=(ty, tx), k_dg_sub=k, n_truth=1,
        )
        for seed in holdout.DRAWS for fold in holdout.FOLDS
    ]
    return holdout.HoldoutContext(
        foot=foot, labels=known, sgmc_off=truth, near_visible=np.zeros_like(foot),
        quad=np.zeros(foot.shape, np.int8), quad_bboxes={}, cells=cells,
        sgmc_truth_coords=(ty, tx), sgmc_k_dg=k, sgmc_n_truth=1,
        sgmc_quad_truth_coords={}, sgmc_quad_n_truth={},
    )


def test_both_legacy_validator_modes_fail_closed_on_unavailable_inputs(tmp_path):
    card = tmp_path / "claimed.json"
    card.write_text(json.dumps({"verdict": "promote", "ok_to_submit": True,
                                "raster_sha256": "a" * 64}))
    for mode in ("champion", "unique-slot"):
        p = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_submission_kg2s2.py"),
             "--tif", str(tmp_path / "missing.tif"), "--run-card", str(card),
             "--data-dir", str(tmp_path), "--mode", mode], capture_output=True, text=True,
        )
        out = json.loads(p.stdout)
        assert p.returncode == 1
        assert out["legacy_mode_ignored"] == mode
        assert out["ok_to_submit"] is False and out["verdict"] == "negative"
        assert not any(out["gates"].values())


@pytest.mark.parametrize("runner", [
    "run_dslup_experiments.py", "run_dslup_unique_slot.py", "run_darp_mt10_experiments.py",
    "run_ecpu_experiments.py", "run_cpr_experiments.py",
])
def test_parallel_legacy_runners_stop_before_fit_or_write(tmp_path, runner):
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / runner)],
                       cwd=tmp_path, capture_output=True, text=True, timeout=45)
    assert p.returncode != 0
    assert "Archived runner disabled" in p.stderr
    assert not list(tmp_path.rglob("*.tif"))


def test_idealized_marginal_threshold_is_consistent_across_shared_modules():
    for score in (0, 0.2778, 0.5, 1):
        assert gmetric.marginal_inclusion_threshold(score) == pytest.approx(0.2 * score)
        assert gmetric.marginal_inclusion_threshold(score) == metric.marginal_inclusion_threshold(score)
    # For an isolated addition, the exact score changes sign at k=alpha*score.
    tp, fp, fn = 10.0, 20.0, 20.0
    denom = tp + .2 * fp + .8 * fn
    score = tp / denom
    for k in (0.2 * score - .01, 0.2 * score + .01):
        next_score = (tp + k) / (denom + .2)
        assert (next_score > score) == (k > 0.2 * score)


def test_binary_metric_does_not_coerce_soft_nan_or_infinite_values():
    truth = np.zeros((6, 6), dtype=bool)
    truth[2, 2] = True
    for invalid in (0.2, np.nan, np.inf, -0.1, 1.1):
        pred = np.zeros((6, 6))
        pred[2, 2] = invalid
        with pytest.raises(ValueError):
            metric.dti_binary(pred, truth)
    valid = np.ones((6, 6), bool)
    valid[0, 0] = False
    pred = np.zeros((6, 6)); pred[0, 0] = np.nan; pred[2, 2] = 1
    assert metric.dti_binary(pred, truth, valid=valid)["dti"] == pytest.approx(
        metric.dti_exact(pred, truth, valid=valid)["dti"])
    valid = valid.astype(float); valid[0, 0] = np.nan
    with pytest.raises(ValueError):
        metric.dti_binary(pred, truth, valid=valid)


@pytest.mark.parametrize("invalid", [np.nan, np.inf, -0.1, 1.1])
def test_holdout_rejects_invalid_inside_even_for_cell_dict(invalid):
    ctx = tiny_context()
    pred = np.zeros(ctx.foot.shape, dtype=float)
    pred[0, 0] = np.nan  # official-style exterior is permitted
    pred[4, 4] = invalid
    with pytest.raises(ValueError, match="finite and in"):
        holdout.evaluate_hide_and_recover(pred, ctx, grid_n=2, n_boot=10)
    with pytest.raises(ValueError, match="finite and in"):
        holdout.evaluate_sgmc_with_ci(pred, ctx, grid_n=2, n_boot=10)
    cells = {cell.key: pred.copy() for cell in ctx.cells}
    with pytest.raises(ValueError, match="finite and in"):
        holdout.evaluate_hide_and_recover(cells, ctx, grid_n=2, n_boot=10)


def test_holdout_masks_visible_pixels_exactly_and_accepts_exterior_nan():
    ctx = tiny_context()
    pred = np.zeros(ctx.foot.shape, float); pred[0, 0] = np.nan
    pred[5, 5] = 1  # known/visible pixel cannot provide TP credit
    masked = holdout.evaluate_hide_and_recover(pred, ctx, grid_n=2, n_boot=10)
    assert masked["pooled_dti"] == 0
    pred[6, 6] = 0.7  # hidden truth remains available and soft scores are not binarized
    recovered = holdout.evaluate_hide_and_recover(pred, ctx, grid_n=2, n_boot=10)
    assert 0 < recovered["pooled_dti"] < 1
    assert recovered["n_withheld_positives"] == 8
    cells = {cell.key: pred.copy() for cell in ctx.cells}
    assert holdout.evaluate_hide_and_recover(cells, ctx, grid_n=2, n_boot=10)["pooled_dti"] == pytest.approx(recovered["pooled_dti"])
    cells.pop(ctx.cells[0].key)
    with pytest.raises(ValueError, match="Missing prediction"):
        holdout.evaluate_hide_and_recover(cells, ctx, grid_n=2, n_boot=10)


def test_sgmc_empty_truth_retains_false_positive_mass():
    ctx = tiny_context()
    ctx.sgmc_n_truth = 0
    ctx.sgmc_truth_coords = (np.array([], dtype=int), np.array([], dtype=int))
    ctx.sgmc_k_dg = np.zeros_like(ctx.foot, dtype=np.float32)
    for prob in (1.0, 0.4):
        pred = np.zeros(ctx.foot.shape, float)
        pred[7, 7] = prob
        result = holdout.evaluate_sgmc_with_ci(pred, ctx, grid_n=2, n_boot=10)
        assert result["_block_totals"][1].sum() == pytest.approx(prob)
        assert result["sgmc_raw_pooled_dti"] == 0


def test_legacy_writer_rejects_invalid_values_before_writing(tmp_path):
    sample = tmp_path / "sample.tif"
    arr = np.zeros((4, 4), np.float32); arr[0, 0] = np.nan
    with rasterio.open(sample, "w", driver="GTiff", height=4, width=4, count=1,
                       dtype="float32", crs="EPSG:32611", transform=Affine(100, 0, 1, 0, -100, 1)) as ds:
        ds.write(arr, 1)
    foot = np.isfinite(arr); labels = np.zeros_like(foot)
    for invalid in (np.nan, np.inf, -0.1, 1.1):
        raw = np.zeros((4, 4), float); raw[1, 1] = invalid
        with pytest.raises(ValueError, match="finite and in"):
            submission.write_submission_bundle(raw, foot, labels, sample, tmp_path / "out",
                                               "test", "timestamp", {})
    with pytest.raises(ValueError, match="note exceeds"):
        submission.write_submission_bundle(np.zeros((4, 4)), foot, labels, sample,
                                           tmp_path / "out", "test", "timestamp",
                                           {"submission_note": "x" * 141})
    assert not (tmp_path / "out").exists()


def test_restore_reports_partial_failure_and_preserves_existing_bytes(tmp_path, monkeypatch):
    good = b"verified contents"
    expected = hashlib.sha256(good).hexdigest()
    entries = [
        {"id": name, "group": "external", "dest": name, "repo": "org/repo", "ref": "pinned",
         "path": name, "sha256": expected}
        for name in ("bad", "good")
    ]
    manifest = tmp_path / "manifest.json"; manifest.write_text(json.dumps({"files": entries}))
    cache = tmp_path / "cache"; cache.mkdir(); (cache / "bad").write_bytes(b"old unverified")
    def fake_fetch(repo, ref, path, dest):
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(b"wrong" if path == "bad" else good)
    monkeypatch.setattr(restore_data, "fetch", fake_fetch)
    monkeypatch.setattr(restore_data, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["restore_data.py", "--manifest", str(manifest),
                                     "--group", "external", "--target-dir", str(cache)])
    assert restore_data.main() == 1
    result = json.loads((tmp_path / "data/restore_receipt_external.json").read_text())
    assert result["complete"] is False and result["verified_files_count"] == 1
    assert result["failed_files_count"] == 1
    assert [r["status"] for r in result["files"]] == ["failed", "restored"]
    assert (cache / "bad").read_bytes() == b"old unverified"
    assert (cache / "good").read_bytes() == good
    assert not list(cache.rglob("*.assembling"))


def test_parallel_raster_correction_and_public_status():
    rec = json.loads((ROOT / "evidence/parallel_hypothesis1_literal_audit_20261027.json").read_text())
    audit = rec["audit"]
    tif = ROOT / "docs/downloads" / audit["file"]
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == audit["sha256"]
    assert audit["witness_overlap_dots"] == 37652
    assert audit["on_catalogue_positive_pixels"] == 184
    assert audit["duplicate_under_literal_rule"] and rec["ok_to_submit"] is False
    feed = json.loads((ROOT / "docs/data/status_feed.json").read_text())
    assert feed["verdict"] == "negative" and feed["ok_to_submit"] is False
    assert "promote" not in json.dumps(feed).lower()
    for p in [ROOT / "README.md", ROOT / "EXECUTIVE_SUMMARY.md", *sorted((ROOT / "docs").glob("*.html"))]:
        text = p.read_text()
        assert "PROMOTE — OK TO SUBMIT" not in text, p
        assert "TWO VERDICTS, YOUR CALL" not in text, p


@pytest.mark.parametrize("runner", ["build_ecpu_run_card.py", "audit_sister_and_focus_20261027.py"])
def test_legacy_evidence_writers_cannot_overwrite_current_cards(tmp_path, runner):
    p = subprocess.run([sys.executable, str(ROOT / "scripts" / runner)],
                       cwd=tmp_path, capture_output=True, text=True, timeout=45)
    assert p.returncode != 0 and "Archived audit writer disabled" in p.stderr
    assert not list(tmp_path.iterdir())


def test_holdout_cli_checks_tiff_grid_and_never_self_attests_oof(tmp_path, monkeypatch):
    import evaluate_htcads_holdout as cli
    ctx = tiny_context()
    monkeypatch.setattr(cli.holdout, "load_holdout_context", lambda _: ctx)
    sample = tmp_path / "sample_submission.tif"
    bad = tmp_path / "shifted.tif"
    good = tmp_path / "same.tif"
    transform = Affine(100, 0, 1, 0, -100, 1201)
    data = np.zeros(ctx.foot.shape, np.float32); data[0, 0] = np.nan; data[6, 6] = 1
    for path, tr in ((sample, transform), (bad, Affine(100, 0, 101, 0, -100, 1201)), (good, transform)):
        with rasterio.open(path, "w", driver="GTiff", height=12, width=12, count=1,
                           dtype="float32", crs="EPSG:32611", transform=tr) as ds:
            ds.write(data, 1)
    with pytest.raises(ValueError, match="grid/CRS/transform"):
        cli.evaluate_path(bad, ddir=tmp_path)
    result = cli.evaluate_path(good, ddir=tmp_path)
    assert result["grid_identity_verified"] is True
    assert result["feature_and_training_provenance_verified"] is False
    assert result["eligible_for_promotion"] is False
    assert result["hide_and_recover"]["score_label"].startswith("DESCRIPTIVE-DTI")
    assert "not an independent holdout" in result["provenance_warning"]


def test_published_dslup_card_is_current_negative_and_preserves_archive():
    card = json.loads((ROOT / "docs/downloads/dslup_run_card.json").read_text())
    assert card["verdict"] == "negative" and card["ok_to_submit"] is False
    assert card["ok_to_download_and_submit"] is False
    original = ROOT / "evidence/dslup_unique_slot_run_card.json"
    assert hashlib.sha256(original.read_bytes()).hexdigest() == card["historical_record_sha256"]
    assert "retracted" in card["historical_record_warning"]


def test_restore_rejects_empty_group_instead_of_reporting_success(tmp_path, monkeypatch):
    manifest = tmp_path / "empty.json"; manifest.write_text('{"files": []}')
    monkeypatch.setattr(restore_data, "ROOT", tmp_path)
    monkeypatch.setattr(sys, "argv", ["restore_data.py", "--manifest", str(manifest), "--group", "external"])
    with pytest.raises(SystemExit, match="nothing verified"):
        restore_data.main()


@pytest.mark.parametrize("flag", ["--verify-tnr1", "--verify-recorded", "--verify-gvc1"])
def test_missing_legacy_verifiers_report_unavailable(flag):
    p = subprocess.run([sys.executable, str(ROOT / "scripts/evaluate_holdout.py"), flag],
                       capture_output=True, text=True, timeout=30)
    assert p.returncode != 0 and "not present in this checkout" in p.stderr
    assert "Traceback" not in p.stderr


def test_parallel_off36_retracted_and_generator_disabled(tmp_path):
    check = json.loads((ROOT / "evidence/off36_independent_check_20261027.json").read_text())
    receipt = json.loads((ROOT / "evidence/off36_literal_validation_20261027.json").read_text())
    sidecar = ROOT / "docs/downloads" / (check["file"][:-4] + "-validation.json")
    public = json.loads(sidecar.read_text())
    assert check["dots"] == 15000 and check["lattice_overlap_3px"] == 0.66
    assert check["dots_in_lattice_gap_fraction"] == 0.34 and check["on_catalogue_positive_pixels"] == 107
    assert receipt["gates"]["exact_file_identity"] is True and receipt["verdict"] == "negative"
    assert public["ok_to_submit"] is False and public["verdict"] == "negative"
    archived = ROOT / "evidence/superseded/off36_validation_pr36_promote_20261027.json"
    assert hashlib.sha256(archived.read_bytes()).hexdigest() == public["historical_receipt_sha256"]
    p = subprocess.run([sys.executable, str(ROOT / "scripts/generate_unique_submission.py")],
                       cwd=tmp_path, capture_output=True, text=True, timeout=30)
    assert p.returncode != 0 and "generator disabled" in p.stderr
