"""KG2-S3 unit tests: exact kernel aggregates, greedy bookkeeping, the automated format gate."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems32 import lope  # noqa: E402
from gems32.metric import kernel  # noqa: E402


def _brute_kernel_sum(lam):
    H, W = lam.shape
    out = np.zeros_like(lam, dtype=np.float64)
    for y in range(H):
        for x in range(W):
            acc = 0.0
            for yy in range(max(0, y - 3), min(H, y + 4)):
                for xx in range(max(0, x - 3), min(W, x + 4)):
                    acc += lam[yy, xx] * float(kernel(np.hypot(yy - y, xx - x)))
            out[y, x] = acc
    return out


def test_kernel_sum_matches_bruteforce():
    rng = np.random.default_rng(0)
    lam = rng.random((17, 13)).astype(np.float32)
    assert np.allclose(lope.kernel_sum(lam), _brute_kernel_sum(lam), atol=1e-4)


def test_marginal_gain_matches_bruteforce_with_existing_dots():
    rng = np.random.default_rng(1)
    lam = (rng.random((15, 16)) * 0.1).astype(np.float32)
    kmax = np.zeros_like(lam)
    lope.add_dots(kmax, np.array([3, 9]), np.array([4, 10]))
    g = lope.marginal_gain(lam, kmax)
    H, W = lam.shape
    for (y, x) in [(0, 0), (3, 4), (5, 6), (14, 15), (8, 9)]:
        acc = 0.0
        for yy in range(max(0, y - 3), min(H, y + 4)):
            for xx in range(max(0, x - 3), min(W, x + 4)):
                k = float(kernel(np.hypot(yy - y, xx - x)))
                acc += lam[yy, xx] * max(0.0, k - kmax[yy, xx])
        assert g[y, x] == pytest.approx(acc, abs=1e-5)


def test_greedy_tracked_tp_equals_exact_projection_and_first_n():
    rng = np.random.default_rng(2)
    lam = np.zeros((60, 60), np.float32)
    lam[20:23, 5:55] = 0.3          # a rich "fault corridor"
    lam += (rng.random(lam.shape) * 0.002).astype(np.float32)
    elig = np.ones(lam.shape, bool)
    g = float(lam.sum())
    dots, info = lope.emit_threshold_greedy(lam, elig, g)
    assert dots.sum() > 0
    exact = lope.projected_components(lam, dots, g)
    # TP tracked from per-round marginal gains must equal the exact coverage of the final set.
    kmax = np.zeros_like(lam)
    ys, xs = np.nonzero(dots)
    lope.add_dots(kmax, ys, xs)
    assert float((lam * kmax).sum()) == pytest.approx(exact["tp"], rel=1e-5)
    assert info["tau_projected"] == pytest.approx(exact["dti"], rel=5e-3)
    sub = lope.first_n(dots, info, 5)
    assert sub.sum() == 5 and not (sub & ~dots).any()
    # Dots concentrate on the corridor.
    assert dots[18:25].sum() >= 0.8 * dots.sum()


def test_level_codes():
    d = np.array([0.0, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 7.0, 12.0, 40.0])
    assert lope.dref_levels(d).tolist() == [1, 2, 3, 3, 4, 4, 5, 6, 7, 8, 0]
    assert lope.dcat_levels(d).tolist() == [0, 1, 1, 1, 2, 2, 3, 3, 4, 5, 0]


def _write(path, arr, nodata=None):
    prof = dict(driver="GTiff", height=arr.shape[0], width=arr.shape[1], count=1, dtype="float32",
                crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100), nodata=nodata)
    with rasterio.open(path, "w", **prof) as d:
        d.write(arr.astype(np.float32), 1)


def test_format_gate_rejects_out_of_range_nan_nodata_and_catalogue(tmp_path):
    import validate_submission_kg2s3 as v
    foot = np.full((20, 20), np.nan, np.float32)
    foot[2:18, 2:18] = 0.0
    _write(tmp_path / "sample_submission.tif", foot, nodata=None)
    lab = np.zeros((20, 20), np.float32)
    lab[5, 5:10] = 1
    _write(tmp_path / "labels.tif", lab)
    good = np.zeros((20, 20), np.float32)
    good[10, 10] = 1.0
    _write(tmp_path / "good.tif", good)
    res, dots = v.gate_format(tmp_path / "good.tif", tmp_path)
    assert res["passed"] and dots.sum() == 1
    for name, arr, nd in (("over.tif", np.where(good > 0, 1.5, 0.0), None),
                          ("nan.tif", np.where(good > 0, np.nan, 0.0), None),
                          ("nodata.tif", good, -9999.0),
                          ("outside.tif", np.where(np.arange(400).reshape(20, 20) == 0, 1.0, good), None)):
        _write(tmp_path / name, arr, nodata=nd)
        r, d = v.gate_format(tmp_path / name, tmp_path)
        assert not r["passed"] and d is None, name
    oncat = good.copy()
    oncat[5, 6] = 1.0
    _write(tmp_path / "oncat.tif", oncat)
    r, _ = v.gate_format(tmp_path / "oncat.tif", tmp_path)
    assert not r["passed"] and not r["checks"]["zero_on_public_catalogue"]
