"""Local format, invalid-input and quota-selector fail-closed regression tests."""
from __future__ import annotations

import hashlib
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gems import metric, selector, submission
from gems32 import submission as legacy_submission


def make_template(path: Path) -> tuple[np.ndarray, np.ndarray]:
    a = np.array([[0, 0, np.nan], [0, 0, np.nan]], dtype=np.float32)
    with rasterio.open(path, "w", driver="GTiff", height=2, width=3, count=1,
                       dtype="float32", crs="EPSG:32611", nodata=np.nan,
                       transform=from_origin(243350, 4508550, 100, 100)) as ds:
        ds.write(a, 1)
    return a, np.isfinite(a)


def test_shared_writer_rejects_invalid_inside_and_preserves_exterior(tmp_path: Path) -> None:
    template = tmp_path / "template.tif"
    _, fp = make_template(template)
    valid = np.array([[0, 0.25, np.nan], [1, 0.5, np.inf]], dtype=np.float64)
    zeros = submission.write_submission(valid, template, tmp_path / "zeros.tif", outside="zero")
    nan = submission.write_submission(valid, template, tmp_path / "nan.tif", outside="nan")
    with rasterio.open(zeros) as ds:
        arr = ds.read(1)
        assert ds.dtypes == ("float32",) and ds.nodata is None
        assert np.isfinite(arr).all() and np.all(arr[~fp] == 0)
        assert np.allclose(arr[fp], valid[fp])
    with rasterio.open(nan) as ds:
        assert np.isnan(ds.read(1)[~fp]).all()
    for bad_value in (float("nan"), float("inf"), -0.01, 1.0 + 1e-10):
        bad = valid.copy()
        bad[0, 0] = bad_value
        dest = tmp_path / "bad.tif"
        with pytest.raises(ValueError):
            submission.write_submission(bad, template, dest)
        assert not dest.exists()
    with pytest.raises(ValueError):
        submission.write_submission(np.zeros((1, 1)), template, tmp_path / "bad.tif")
    before = template.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        submission.write_submission(valid, template, template)
    assert template.read_bytes() == before


def test_legacy_bundle_checks_before_writing_and_does_not_clip(tmp_path: Path) -> None:
    template = tmp_path / "template.tif"
    _, fp = make_template(template)
    labels = np.zeros(fp.shape, dtype=bool)
    raw = np.zeros(fp.shape, dtype=np.float64)
    raw[0, 0] = 1.0 + 1e-10  # rounds to 1 if cast prematurely to float32
    out = tmp_path / "out"
    with pytest.raises(ValueError, match="invalid in-footprint"):
        legacy_submission.write_submission_bundle(raw, fp, labels, template, out, "x", "t", {})
    assert not out.exists()
    raw[0, 0] = 0.5
    with pytest.raises(ValueError, match="140"):
        legacy_submission.write_submission_bundle(raw, fp, labels, template, out, "x", "t", {"submission_note": "x" * 141})
    assert not out.exists()
    fake_fp = np.ones_like(fp)
    with pytest.raises(ValueError, match="footprint does not match"):
        legacy_submission.write_submission_bundle(raw, fake_fp, labels, template, out, "x", "t", {})
    assert not out.exists()


def test_selector_never_authorizes_a_forged_quota_or_recorded_flags(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    artifact = tmp_path / "candidate.tif"
    artifact.write_bytes(b"fixture-not-a-raster")
    monkeypatch.setattr(selector.submission, "check_variants", lambda *_: {
        "format_valid": True,
        "checks": {k: {"pass": True} for k in
                   ("variant_strict_whole_array_no_nan_allowed", "footprint_range_0_1", "footprint_all_finite")},
    })
    monkeypatch.setattr(selector, "RECORDED_BEST_DTI", 0.17)
    version = selector.RECORDED_BEST_EVALUATOR
    nov_stage = {"max_abs_rank_correlation": 0.2, "literal_all_entries_passed": True, "literal_duplicate_rows": []}
    card = {
        "raster_sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(), "submission_name": artifact.name,
        "leakage_canary": {"passed": True, "worst_polarity_extremity": 0.7},
        "holdout": {"dti": 0.2, "label": "HOLDOUT-DTI", "evaluator_version": version, "n_withheld_positive_pixels": 60988},
        "paired_vs_baseline": {"ci95": [0.01, 0.03]}, "baseline_reproduced": True,
        "paired_vs_current_best": {"baseline_dti": 0.17, "evaluator_version": version,
                                   "n_withheld_positive_pixels": 60988, "baseline_replayed": True, "ci95": [0.01, 0.03]},
        "novelty": {"surface": dict(nov_stage), "final_dots": {**nov_stage, "method_lane_max_dot_overlap": 0.2, "method_lane_passed": True},
                    "peers_final": {"max_dot_overlap_within_3px": 0.2, "passed": True}},
        "c2st_exact_file": {"strict_gate_passed": True, "labels_audited_first": True},
        "note": "Research only", "experiments_run": 1, "submission_slots_used": 0,
        "quota_confirmed": True,
    }
    out = selector.verify_selector(artifact, tmp_path / "template.tif", card)
    assert out["recorded_scientific_screen_passed"] is True
    assert out["ok_to_submit"] is False and out["decision"] == "DO_NOT_SUBMIT"
    assert out["gates"]["current_account_quota_independently_verified"] is False
    assert out["gates"]["complete_independent_replay_certificate"] is False
    card["novelty"]["surface"]["literal_duplicate_rows"] = [{"id": "control"}]
    assert selector.verify_selector(artifact, tmp_path / "template.tif", card)["gates"]["g4_registry_novelty"] is False


def test_dti_triangle_distance_algebra() -> None:
    fp = np.ones((20, 20), dtype=bool)
    truth = np.zeros((20, 20), dtype=bool)
    pred = np.zeros((20, 20), dtype=np.float32)
    truth[10, 10], pred[10, 12] = True, 1.0
    result = metric.dti_components_exact(pred, truth, fp)
    w = 1 - 2 / 3
    assert np.isclose(result["dti"], w / (w + 0.2 * (1 - w) + 0.8 * (1 - w)), atol=1e-6)
