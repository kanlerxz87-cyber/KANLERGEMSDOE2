"""Literal threshold, geometry, undefined-rank and pre-placement safety checks."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

from gems import novelty, preflight

ROOT = Path(__file__).resolve().parents[1]


def raster(path: Path, values: np.ndarray, *, x: float = 0.0) -> None:
    with rasterio.open(path, "w", driver="GTiff", count=1, height=values.shape[0], width=values.shape[1],
                       dtype="float32", crs="EPSG:32611", transform=from_origin(x, 10, 1, 1), nodata=None) as ds:
        ds.write(np.asarray(values, dtype=np.float32), 1)


def entry(path: Path, a: np.ndarray, fp: np.ndarray) -> dict:
    return {"id": "r1", "file": path.name, "cache_path": path.name,
            "footprint_sha256": hashlib.sha256(np.asarray(a[fp], dtype="<f4").tobytes()).hexdigest()}


def test_strict_greater_than_70_boundary_and_radius() -> None:
    fp = np.ones((1, 11), dtype=bool)
    ref = np.zeros_like(fp)
    ref[0, :8] = True  # U = 3; K=10 => lower bound exactly 70%
    at, _ = preflight.coverage_witness(fp, ref, 10, radius_px=0)
    above, _ = preflight.coverage_witness(fp, ref, 11, radius_px=0)
    assert at["minimum_possible_directional_overlap"] == 0.70
    assert at["duplicate_forced"] is False and at["status"] == "INCONCLUSIVE_NOT_A_PASS"
    assert above["duplicate_forced"] is True and above["first_budget_forced_to_exceed_limit"] == 11
    assert novelty.is_duplicate(0.90, 0.70) is False
    assert novelty.is_duplicate(0.900001, 0.70) is True
    assert novelty.is_duplicate(0.90, 0.700001) is True
    with pytest.raises(ValueError):
        novelty.is_duplicate(float("nan"), 0.5)
    grid = np.ones((7, 7), bool)
    center = np.zeros_like(grid)
    center[3, 3] = True
    result, halo = preflight.coverage_witness(grid, center, 49, radius_px=3)
    assert result["covered_pixels"] == 29 and halo[3, 0] and halo[1, 1] and not halo[0, 2]


def test_counting_bound_matches_brute_force() -> None:
    fp = np.ones((4, 4), bool)
    ref = np.zeros_like(fp)
    ref[1, 1] = True
    for budget in (3, 6, 10):
        result, halo = preflight.coverage_witness(fp, ref, budget, radius_px=1)
        hits = [sum(halo.ravel()[i] for i in combo)
                for combo in itertools.combinations(range(fp.size), budget)]
        assert min(hits) == result["at_least_overlapping_dots"]
        assert all(h / budget >= result["minimum_possible_directional_overlap"] for h in hits)


def test_control_is_not_exempt_and_missing_support_is_not_a_pass(tmp_path: Path) -> None:
    fp = np.ones((12, 12), bool)
    scores = np.arange(fp.size, dtype=np.float32).reshape(fp.shape)
    control = np.zeros(fp.shape, dtype=np.float32)
    control[::2, ::2] = 1
    template, ref = tmp_path / "template.tif", tmp_path / "control.tif"
    raster(template, np.zeros_like(scores))
    raster(ref, control)
    rows = [entry(ref, control, fp)]
    no_support = novelty.compare_registry(scores, fp, rows, tmp_path, template_path=template,
                                           separate_calibration_controls=True)
    assert no_support["passed"] is False and no_support["support_checked"] is False
    support = novelty.topk_surface_support(scores, fp, 12)
    result = novelty.compare_registry(scores, fp, rows, tmp_path, surface_support=support,
                                      template_path=template, separate_calibration_controls=True)
    assert result["rows"][0]["comparator_class"] == "space_filling_calibration_control"
    assert result["rows"][0]["candidate_dot_overlap_within_3px"] == 1.0
    assert result["rows"][0]["duplicate"] is True and result["passed"] is False
    assert len(result["literal_duplicate_rows"]) == 1
    # A caller-supplied subset is still only a subset, never a full-registry certificate.
    assert result["registry_unique_rasters"] == 1


def test_topk_unsigned_values_and_tie_breaking() -> None:
    values = np.array([[0, 1, 255], [255, 2, 3]], dtype=np.uint8)
    chosen = novelty.topk_surface_support(values, np.ones_like(values, bool), 2)
    assert np.flatnonzero(chosen).tolist() == [2, 3]
    assert novelty.topk_surface_support(values, np.ones_like(values, bool), 1).ravel()[2]


def test_registry_must_have_aligned_geometry_and_defined_rank(tmp_path: Path) -> None:
    fp = np.ones((8, 8), bool)
    scores = np.arange(fp.size, dtype=np.float32).reshape(fp.shape)
    ref_values = np.zeros(fp.shape, np.float32)
    ref_values[0, 0] = 1
    template, ref = tmp_path / "template.tif", tmp_path / "ref.tif"
    raster(template, np.zeros_like(scores))
    raster(ref, ref_values)
    rows = [entry(ref, ref_values, fp)]
    support = novelty.topk_surface_support(scores, fp, 2)
    no_grid = novelty.compare_registry(scores, fp, rows, tmp_path, surface_support=support)
    assert no_grid["passed"] is False and no_grid["geometry_checked"] is False
    assert "geometry" in no_grid["stop_reason"]
    raster(ref, ref_values, x=1)
    with pytest.raises(ValueError, match="grid mismatch"):
        novelty.compare_registry(scores, fp, rows, tmp_path, surface_support=support, template_path=template)
    constant = np.zeros(fp.shape, np.float32)
    raster(ref, constant)
    undefined = novelty.compare_registry(scores, fp, [entry(ref, constant, fp)], tmp_path,
                                          surface_support=support, template_path=template)
    assert undefined["passed"] is False and "undefined" in undefined["stop_reason"]
    assert undefined["rows"][0]["raw_rank_defined"] is False


def test_pinned_witness_rejects_tampered_input(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    template, ref = tmp_path / "template.tif", tmp_path / "ref.tif"
    raster(template, np.zeros((6, 6), np.float32))
    a = np.zeros((6, 6), np.float32)
    a[::2, ::2] = 1
    raster(ref, a)
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    monkeypatch.setattr(preflight, "TEMPLATE_SHA256", digest(template))
    monkeypatch.setattr(preflight, "LATTICE_SHA256", digest(ref))
    monkeypatch.setattr(preflight, "LATTICE_NAME", ref.name)
    registry = tmp_path / "registry.json"
    registry.write_text(json.dumps({"entries": [{"filename": ref.name, "sha256": digest(ref)}]}))
    result, _, _ = preflight.pinned_witness(template, ref, registry, 10)
    assert result["duplicate_forced"] is True
    with ref.open("ab") as f:
        f.write(b"changed")
    with pytest.raises(ValueError, match="registered bytes"):
        preflight.pinned_witness(template, ref, registry, 10)


def test_missing_inputs_block_legacy_runners_and_validator(tmp_path: Path) -> None:
    env = {**os.environ, "GEMS_DATA_DIR": str(tmp_path)}
    for script, args in (("run_htcads_experiments.py", []), ("run_fvca_experiments.py", []),
                         ("run_kg2_lane.py", ["--stage", "features_and_canary"]), ("prepare_htcads_data.py", [])):
        p = subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], env=env,
                           capture_output=True, text=True, timeout=40)
        assert p.returncode != 0 and "BLOCKED" in p.stdout + p.stderr, (script, p.stderr)
    p = subprocess.run([sys.executable, str(ROOT / "scripts/validate_submission.py"),
                        "--tif", str(tmp_path / "missing.tif")], env=env, capture_output=True, text=True, timeout=40)
    result = json.loads(p.stdout)
    assert p.returncode != 0 and result["ok_to_submit"] is False
    assert result["gates"]["separate_account_quota_selector_verified"] is False
