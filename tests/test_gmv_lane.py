"""KG2-S3-GMV lane tests: synthetic feature builders, RANSAC, gates (no bulk data)."""
from __future__ import annotations

import inspect
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))


def test_preregistration_frozen_before_experiments() -> None:
    pre = json.loads((ROOT / "registry" / "preregistration_gmv.json").read_text())
    assert pre["lane_id"] == "KG2-S3-GMV"
    assert pre["budget"]["max_experiments"] == 3
    assert [e["id"] for e in pre["experiments"]] == ["EXP-A", "EXP-B", "EXP-C"]
    assert "dist_known_fault_px" in pre["forbidden_columns"]
    assert (ROOT / "knowledge" / "03_preregistered_hypotheses_gmv_20261027.md").exists()
    # GDR CSVs must never be READ with the forbidden catalogue-distance column
    # (a docstring statement that it is never read is required, not a violation).
    src = (ROOT / "src" / "gems32" / "gmv.py").read_text()
    assert "NEVER read" in src
    in_doc = False
    code_lines = []
    for ln in src.splitlines():
        s = ln.strip()
        if s.startswith('"""'):
            in_doc = not in_doc
            continue
        if in_doc or s.startswith("#"):
            continue
        code_lines.append(ln.split("#")[0])
    code = "\n".join(code_lines)
    assert "dist_known_fault_px" not in code


def test_manifest_heatflow_path_fixed() -> None:
    man = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    byid = {f["id"]: f for f in man["files"]}
    e = byid["ext_sb_heat_flow"]
    assert e["path"] == "docs/data/sb_heat_flow_in_footprint.csv"
    assert e["sha256"] == "9845263e658aeb66a4aeca6e64d995e74f0eb14b89768219ea9d223006dc8baf"


def test_registry_collector_covers_repo_downloads() -> None:
    import run_htcads_experiments as tmpl

    src = inspect.getsource(tmpl._collect_registry_rasters)
    assert "docs" in src and "downloads" in src  # IR-KG2S3-REG-01: no silent /tmp-only registry
    assert "GEMS_REGISTRY_DIR" in src


def test_gmv_front_sinuosity_straight_vs_wiggly() -> None:
    from gems32 import gmv

    rng = np.random.default_rng(1)
    foot = np.ones((240, 200), bool)
    slope = np.clip(rng.normal(2, 0.5, (240, 200)).astype(np.float32), 0, None)
    slope[48:52, :] += 8.0  # straight front (top half)
    for c in range(200):  # wiggly front (bottom half, same grid => same normalization)
        r = 170 + int(12 * np.sin(c / 9.0))
        slope[r - 2:r + 2, c] += 8.0
    out = gmv._front_sinuosity(slope, foot)
    assert float(out.max()) > 0.5, "fronts should score"
    s_top = float(out[40:60, :][out[40:60, :] > 0].mean())
    s_bot = float(out[150:190, :][out[150:190, :] > 0].mean())
    assert s_top > s_bot, "straighter front must outscore wiggly front under one normalization"


def test_gmv_valley_vf_finds_incised_valley() -> None:
    from gems32 import gmv

    foot = np.ones((80, 80), bool)
    yy, xx = np.mgrid[0:80, 0:80].astype(np.float32)
    elev = (np.abs(xx - 40) + 0.05 * yy).astype(np.float32)
    v = gmv._valley_vf_score(elev, foot)
    assert float(v.max()) > 0.5
    # valley bottom column scores higher than the divide edge
    assert float(v[:, 38:43].mean()) > float(v[:, 0:5].mean())


def test_gmv_tilt_and_tpi_respond() -> None:
    from gems32 import gmv

    foot = np.ones((80, 80), bool)
    yy, xx = np.mgrid[0:80, 0:80].astype(np.float32)
    tilt_block = (0.5 * xx + 0.1 * yy).astype(np.float32)
    t = gmv._tilt_coherence(tilt_block, foot)
    assert float(t.mean()) > 0.1
    step = np.where(xx > 40, 50.0, 0.0).astype(np.float32)
    d = gmv._tpi_discord_ridge(step, foot)
    assert float(d[:, 36:45].mean()) > float(d[:, 0:5].mean())


def test_gmv_h1_all_finite_on_irregular_footprint() -> None:
    """IR-KG2S3-NAN-01: H1 builders must be all-finite with holes (no NaN-masked filtering)."""
    from gems32 import gmv

    rng = np.random.default_rng(3)
    foot = np.ones((90, 90), bool)
    foot[0:12, :] = False  # irregular boundary + hole, like the real footprint
    foot[70:90, 60:90] = False
    foot[40:50, 40:50] = False
    elev = (rng.normal(100, 8, (90, 90)) + np.mgrid[0:90, 0:90][1] * 0.4).astype(np.float32)
    slope = np.abs(rng.normal(3, 2, (90, 90))).astype(np.float32)
    slope[30:34, 15:80] += 9.0
    for fn, arg in ((gmv._front_sinuosity, slope), (gmv._valley_vf_score, elev),
                    (gmv._tilt_coherence, elev), (gmv._tpi_discord_ridge, elev)):
        g = fn(arg, foot)
        assert np.all(np.isfinite(g)), fn.__name__
        assert float(np.abs(g[~foot]).max()) == 0.0, fn.__name__


def test_gmv_ransac_recovers_lines() -> None:
    from gems32 import gmv

    rng = np.random.default_rng(0)
    y1 = np.linspace(10, 90, 25) + rng.normal(0, 0.5, 25)
    x1 = np.linspace(10, 90, 25) + rng.normal(0, 0.5, 25)
    y2 = np.full(20, 50) + rng.normal(0, 0.5, 20)
    x2 = np.linspace(10, 90, 20) + rng.normal(0, 0.5, 20)
    py = np.concatenate([y1, y2]).astype(np.int32)
    px = np.concatenate([x1, x2]).astype(np.int32)
    pw = np.ones(py.size, dtype=np.float32)
    lines = gmv._ransac_lines(py, px, pw, n_iter=2000)
    assert len(lines) >= 2
    assert max(t[3] for t in lines) >= 15.0  # support recovers a full line


def test_uniqueness_gate_logic_on_synthetic_registry() -> None:
    import run_htcads_experiments as tmpl

    rng = np.random.default_rng(7)
    foot = np.ones((40, 40), bool)
    dots = np.zeros((40, 40), bool)
    dots[5:35:4, 5:35:4] = True
    other = np.zeros((40, 40), bool)
    other[6:36:4, 6:36:4] = True  # shifted by 1px -> 100% within 3px
    n_fp = int(foot.sum())
    idx = np.arange(n_fp)
    reg = [{
        "name": "synth_peer.tif",
        "is_calibration_lattice": False,
        "n_dots": int(other.sum()),
        "cov3_of_footprint": 0.05,
        "unit_rank": tmpl._unit_rank_vec(other[foot].astype(np.float32)),
        "ry": np.nonzero(other)[0].astype(np.int16),
        "rx": np.nonzero(other)[1].astype(np.int16),
    }]
    pi = dots.astype(np.float32)
    uq = tmpl._check_uniqueness(pi, dots, foot, reg, idx)
    assert uq["final_dots_max_detector_3px_overlap"] == 1.0
    assert uq["passed"] is False  # literal gate trips on the near-duplicate
    far = np.zeros((40, 40), bool)
    far[0:40:9, 0] = True
    reg[0]["unit_rank"] = tmpl._unit_rank_vec(far[foot].astype(np.float32))
    reg[0]["ry"] = np.nonzero(far)[0].astype(np.int16)
    reg[0]["rx"] = np.nonzero(far)[1].astype(np.int16)
    reg[0]["n_dots"] = int(far.sum())
    uq2 = tmpl._check_uniqueness(pi, dots, foot, reg, idx)
    assert uq2["final_dots_max_detector_3px_overlap"] <= 0.70
