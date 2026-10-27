"""Independent, exact-byte checks for the current release review.

A single hash-pinned duplicate witness is enough for a STOP. Conversely, one
witness can never establish full-registry uniqueness or scientific validity.
Owner-hosted mirrors are hash-pinned, not independently organizer-authenticated.
"""
from __future__ import annotations

from pathlib import Path
import json

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

from . import novelty
from .validator import sha256_file

WITNESS_NAME = "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
WITNESS_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
TEMPLATE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
LABELS_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"


def _circle3() -> np.ndarray:
    y, x = np.mgrid[-3:4, -3:4]
    return y * y + x * x <= 9


def _grid(ds) -> tuple:
    return ds.shape, ds.crs, ds.transform


def load_reference(root: Path, data: Path) -> dict:
    """Load the pinned template, catalogue and a registered 3-px witness.

    Refuse mismatched hashes/grids, and require the witness to actually appear
    in the repository registry. The template and fault data are owner mirrors.
    """
    root, data = Path(root), Path(data)
    template, labels = data / "sample_submission.tif", data / "labels.tif"
    witness = data / "scored" / WITNESS_NAME
    for p, expected in ((template, TEMPLATE_SHA), (labels, LABELS_SHA), (witness, WITNESS_SHA)):
        if not p.is_file() or sha256_file(p) != expected:
            raise ValueError(f"Missing or unverified pinned reference: {p.name}")
    reg = json.loads((root / "registry/comparison_registry.json").read_text())
    if not any(e.get("sha256") == WITNESS_SHA and e.get("filename") == WITNESS_NAME for e in reg["entries"]):
        raise ValueError("Pinned lattice is not present in the declared registry")
    with rasterio.open(template) as ds:
        grid = _grid(ds)
        if ds.count != 1:
            raise ValueError("Template must be single-band")
        foot = np.isfinite(ds.read(1))
    # Validate against the repository's compressed copy, not only its count.
    from .footprint import load_footprint
    packed = load_footprint(root / "docs/data/footprint.bin")
    if not np.array_equal(foot, packed):
        raise ValueError("Template footprint differs from checked-in footprint")
    with rasterio.open(labels) as ds:
        if _grid(ds) != grid or ds.count != 1:
            raise ValueError("Catalogue grid mismatch")
        a = ds.read(1)
        catalogue = foot & np.isfinite(a) & (a > 0)
    with rasterio.open(witness) as ds:
        if _grid(ds) != grid or ds.count != 1:
            raise ValueError("Witness grid mismatch")
        a = ds.read(1)
        if not np.isfinite(a[foot]).all() or not np.isin(a[foot], [0, 1]).all():
            raise ValueError("Witness has nonfinite or non-binary cells inside footprint")
        reference = foot & (a > 0)
    if not reference.any():
        raise ValueError("Empty witness does not establish a duplicate")
    near = binary_dilation(reference, structure=_circle3())
    uncovered = int((foot & ~near).sum())
    return {"grid": grid, "foot": foot, "catalogue": catalogue, "reference": reference,
            "near": near, "uncovered": uncovered, "witness_path": witness,
            "template_path": template, "labels_path": labels}


def forced_budget_result(ref: dict, dots: int) -> dict:
    if type(dots) is not int or not 1 <= dots <= int(ref["foot"].sum()):
        raise ValueError("Candidate budget must fit in the footprint")
    u = ref["uncovered"]
    minimum_overlap = max(0, dots - u)
    return {
        "candidate_dot_budget": dots,
        "footprint_pixels": int(ref["foot"].sum()),
        "witness_positive_pixels": int(ref["reference"].sum()),
        "covered_pixels_within_3px": int((ref["foot"] & ref["near"]).sum()),
        "uncovered_pixels": u,
        "minimum_overlapping_dots": minimum_overlap,
        "minimum_directional_overlap": minimum_overlap / dots,
        "limit": 0.70,
        "forced_duplicate": novelty.budget_forced_duplicate(u, dots),
        "witness_filename": WITNESS_NAME,
        "witness_sha256": WITNESS_SHA,
        "scope": "Exact counting lower bound for any set of distinct in-footprint dots; not a complete registry audit",
    }


def _binary_rho(a: np.ndarray, b: np.ndarray, fp: np.ndarray) -> float | None:
    """Exact Spearman for two binary fields (their average ranks are affine)."""
    n = int(fp.sum())
    na, nb, both = int((a & fp).sum()), int((b & fp).sum()), int((a & b & fp).sum())
    denom = na * (n - na) * nb * (n - nb)
    if denom == 0:
        return None
    return float((n * both - na * nb) / np.sqrt(float(denom)))


def assess_file(path: Path, ref: dict) -> dict:
    """Reopen a raster, audit grid/range, and test it against the witness."""
    fp, cat, near = ref["foot"], ref["catalogue"], ref["near"]
    path = Path(path)
    with rasterio.open(path) as ds:
        grid_match = _grid(ds) == ref["grid"]
        if not grid_match or ds.count != 1:
            raise ValueError(f"Grid or band mismatch: {path.name}")
        arr = ds.read(1)
        dtype, nodata = ds.dtypes[0], ds.nodata
    inside, outside = arr[fp], arr[~fp]
    finite = np.isfinite(arr)
    good_inside = bool(np.isfinite(inside).all() and np.all((inside >= 0) & (inside <= 1)))
    strict_all = bool(finite.all() and np.all((arr >= 0) & (arr <= 1)))
    dots = fp & finite & (arr > 0)
    n = int(dots.sum())
    overlap = int((dots & near).sum())
    exact_duplicate = n > 0 and overlap * 10 > n * 7
    if not np.isfinite(inside).all():
        rho = None
    elif np.isin(inside, [0, 1]).all():
        rho = _binary_rho(dots, ref["reference"], fp)
    else:
        # Preserve continuous ranks; binarizing a soft raster can conceal a
        # genuine surface/raster rank match. The witness is checked binary.
        rho = novelty.correlation(inside, ref["reference"][fp].astype(np.uint8))
    return {
        "file": path.name, "sha256": sha256_file(path), "size_bytes": path.stat().st_size,
        "count": 1, "shape": list(ref["grid"][0]), "crs": str(ref["grid"][1]),
        "transform": list(ref["grid"][2])[:6], "dtype": dtype,
        "nodata": "NaN" if nodata is not None and np.isnan(nodata) else nodata,
        "grid_matches_pinned_owner_template": grid_match,
        "no_nan_inside_footprint": bool(not np.isnan(inside).any()),
        "no_inf_inside_footprint": bool(not np.isinf(inside).any()),
        "inside_range_0_1": good_inside,
        "local_grid_dtype_inside_range_pass": bool(grid_match and dtype == "float32" and good_inside),
        "strict_whole_array_finite_0_1": strict_all,
        "outside_footprint_all_nan": bool(np.isnan(outside).all()),
        "outside_footprint_all_zero": bool((outside == 0).all()),
        "inside_positive_pixels": n,
        "outside_positive_pixels": int((finite & (arr > 0) & ~fp).sum()),
        "on_catalogue_positive_pixels": int((dots & cat).sum()),
        "witness_overlap_dots": overlap,
        "witness_overlap_fraction": overlap / n if n else None,
        "witness_final_dots_spearman": rho,
        "rank_scope": "Exact raw in-footprint ranks against binary witness; soft candidates are not binarized",
        "duplicate_under_literal_rule": exact_duplicate or (rho is not None and rho > 0.90),
        "organizer_acceptance_verified": False,
    }
