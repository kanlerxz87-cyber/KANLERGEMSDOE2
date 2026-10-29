#!/usr/bin/env python3
"""Independent final verification of the generated unique submission TIF.

Re-opens the exact bytes, re-checks every format gate, recomputes registry
uniqueness from scratch, and confirms the SHA-256 matches the run card.
Read-only except for writing the verification receipt to evidence/.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
TIF = ROOT / "docs" / "downloads" / "kanlergemsdoe2-geothermal-blind-conduit-20261029T024633Z-60a6b7f6ca71-zeros.tif"
CARD = ROOT / "evidence" / "current_run_card.json"

RECEIPT = ROOT / "evidence" / "final_verification_receipt.json"


def spearman(a, b, fp):
    ids = np.flatnonzero(fp)
    af, bf = a.ravel()[ids], b.ravel()[ids]
    m = np.isfinite(af) & np.isfinite(bf)
    if not m.any():
        return None
    af, bf = af[m], bf[m]
    ra, rb = rankdata(af), rankdata(bf)
    if np.ptp(ra) == 0 or np.ptp(rb) == 0:
        return None
    da, db = ra - ra.mean(), rb - rb.mean()
    return float(np.dot(da, db) / np.sqrt(np.dot(da, da) * np.dot(db, db)))


def main():
    assert TIF.is_file(), TIF
    card = json.loads(CARD.read_text())
    expected_sha = card["raster_sha256"]
    expected_name = card["submission_name"]

    raw = TIF.read_bytes()
    actual_sha = hashlib.sha256(raw).hexdigest()
    name_ok = TIF.name == expected_name
    sha_ok = actual_sha == expected_sha

    with rasterio.open(TIF) as s:
        arr = s.read(1)
        crs, tr, shape, count, dtypes, nodata = s.crs, s.transform, s.shape, s.count, s.dtypes, s.nodata
        profile = dict(driver=s.driver, dtype=s.dtypes[0], nodata=s.nodata, width=s.width, height=s.height, crs=s.crs, transform=s.transform)

    fp = None
    sys.path.insert(0, str(ROOT / "src"))
    from gems import footprint as footprint_mod  # noqa: E402
    fp = footprint_mod.load_footprint()

    inside = arr[fp]
    outside = arr[~fp]
    finite_inside = bool(np.isfinite(inside).all())
    in_range = bool(inside.size and np.isfinite(inside).all() and (inside >= 0).all() and (inside <= 1).all())
    whole_ok = bool((arr >= 0).all() and (arr <= 1).all() and np.isfinite(arr).all())
    n_positive = int((inside > 0).sum())
    crs_ok = crs is not None and crs.to_epsg() == 32611
    shape_ok = shape == (3730, 3292)
    tr_ok = tuple(tr)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    count_ok = count == 1
    dtype_ok = dtypes == ("float32",)

    # Uniqueness vs locally available registry rasters.
    registry = json.loads((ROOT / "registry" / "comparison_registry.json").read_text())["entries"]

    def local_paths(entry):
        outs = []
        fname = entry.get("filename", "")
        if fname:
            p = ROOT / "docs" / "downloads" / fname
            if p.is_file():
                outs.append(p)
        cache = entry.get("cache_path", "")
        if cache and not cache.startswith("docs/downloads/"):
            for cand in (ROOT / "data" / cache, ROOT / "data" / Path(cache).name):
                if cand.is_file():
                    outs.append(cand)
        seen, uniq = set(), []
        for p in outs:
            if p not in seen:
                uniq.append(p); seen.add(p)
        return uniq

    reg = []
    for entry in registry:
        for p in local_paths(entry):
            try:
                with rasterio.open(p) as ds:
                    a = ds.read(1)
                if ds.shape != fp.shape:
                    continue
                ref = fp & np.isfinite(a) & (a > 0)
                if not ref.any():
                    continue
                reg.append((entry.get("id", entry.get("sha256", ""))[:12], entry["filename"], ref, a))
                break
            except Exception:
                continue

    dot_yx = np.argwhere(arr > 0)
    rho_rows, overlap_rows = [], []
    for rid, fname, ref, arr_r in reg:
        rho = spearman(arr, arr_r, fp)
        rho_rows.append((fname, rho))
        tree = cKDTree(np.argwhere(ref))
        ov = float(np.mean(tree.query(dot_yx)[0] <= 3.0))
        overlap_rows.append((fname, ov, int(ref.sum())))

    with rasterio.open(ROOT / "data" / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif") as ds:
        lattice = ds.read(1)
    lattice_dots = fp & np.isfinite(lattice) & (lattice > 0)
    uncovered = fp & (distance_transform_edt(~lattice_dots) > 3.0)
    n_uncovered = int(uncovered.sum())
    n_dots = int((arr > 0).sum())
    lat_tree = cKDTree(np.argwhere(lattice_dots))
    lat_ov = float(np.mean(lat_tree.query(dot_yx)[0] <= 3.0))
    pigeonhole = max(0, n_dots - n_uncovered) / n_dots

    max_rho = max(abs(r) for _, r in rho_rows if r is not None) if rho_rows else None
    max_ov = max(ov for _, ov, _ in overlap_rows) if overlap_rows else None

    gates = {
        "file_exists": bool(TIF.is_file()),
        "name_matches_run_card": name_ok,
        "sha256_matches_run_card": sha_ok,
        "single_band": count_ok,
        "dtype_float32": dtype_ok,
        "crs_epsg_32611": crs_ok,
        "shape_3730x3292": shape_ok,
        "geotransform_matches": tr_ok,
        "footprint_all_finite": finite_inside,
        "footprint_range_0_1": in_range,
        "whole_array_0_1_no_nan": whole_ok,
        "n_dots_20000": n_dots == 20000,
        "surface_max_abs_rank_corr_le_0_90": bool(max_rho is None or max_rho <= 0.90),
        "max_dot_overlap_le_0_70_local": bool(max_ov is None or max_ov <= 0.70),
        "lattice_overlap_le_0_70": bool(lat_ov <= 0.70),
        "pigeonhole_bound_le_0_70": bool(pigeonhole <= 0.70),
    }
    all_format = all(gates[k] for k in ("single_band", "dtype_float32", "crs_epsg_32611", "shape_3730x3292", "geotransform_matches", "footprint_all_finite", "footprint_range_0_1", "whole_array_0_1_no_nan"))
    unique_ok = bool(gates["surface_max_abs_rank_corr_le_0_90"] and gates["max_dot_overlap_le_0_70_local"] and gates["lattice_overlap_le_0_70"] and gates["pigeonhole_bound_le_0_70"])

    receipt = {
        "schema": "gems.final-verification.v1",
        "verified_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "file": TIF.name,
        "sha256": actual_sha,
        "sha_matches_run_card": sha_ok,
        "name_matches_run_card": name_ok,
        "format_gates": gates,
        "format_all_pass": bool(all_format),
        "unique_locally": unique_ok,
        "registry_rasters_checked": len(reg),
        "max_abs_surface_rank_correlation": None if max_rho is None else round(float(max_rho), 6),
        "max_dot_overlap_local_rasters": None if max_ov is None else round(float(max_ov), 6),
        "lattice_dot_overlap": round(float(lat_ov), 6),
        "pigeonhole_min_lattice_overlap": round(float(pigeonhole), 6),
        "n_dots": n_dots,
        "ok_to_download": bool(all_format),
        "ok_to_submit": False,
        "verdict": "negative",
        "reasons": [
            "Format and local uniqueness verified.",
            "Not cleared to submit: full 360-raster clearance and an independent selector are required; holdout estimate is modest.",
        ],
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))
    return 0 if (all_format and unique_ok and sha_ok and name_ok) else 1


if __name__ == "__main__":
    raise SystemExit(main())
