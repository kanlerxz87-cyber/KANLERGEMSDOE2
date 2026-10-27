"""Legacy bundle adapter and local GeoTIFF checks.

Whole-array [0,1] checks can detect invalid values but cannot establish portal
acceptance or diagnose an earlier rejected file. The official description also
mentions null/NaN outside bounds; zero outside is a documented local variant.
The adapter delegates actual raster writing to the shared strict writer.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

EXPECTED_HEIGHT = 3730
EXPECTED_WIDTH = 3292
EXPECTED_TOTAL_PIXELS = EXPECTED_HEIGHT * EXPECTED_WIDTH
EXPECTED_FOOTPRINT_PIXELS = 5_167_373


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_geotiff(
    tif_path: Path,
    foot: np.ndarray,
    labels: np.ndarray,
    mode: str = "zeros",
    template_tif: Path | None = None,
) -> dict:
    """Run a strict local grid/range audit; this cannot certify portal acceptance."""
    foot_raw, labels_raw = np.asarray(foot), np.asarray(labels)
    if not np.isin(foot_raw, (0, 1)).all() or not np.isin(labels_raw, (0, 1)).all():
        raise ValueError("footprint and labels must be binary masks")
    foot, labels = foot_raw.astype(bool), labels_raw.astype(bool)
    if mode not in {"zeros", "nan"}:
        raise ValueError("mode must be zeros or nan")
    expected_crs = rasterio.crs.CRS.from_epsg(32611)
    expected_shape = (EXPECTED_HEIGHT, EXPECTED_WIDTH)
    expected_transform = rasterio.transform.from_origin(243350, 4508550, 100, 100)
    if template_tif is not None:
        with rasterio.open(template_tif) as tpl:
            expected_crs, expected_shape, expected_transform = tpl.crs, tpl.shape, tpl.transform
            if tpl.count != 1 or not np.array_equal(np.isfinite(tpl.read(1)), foot):
                raise ValueError("footprint does not match the template")
    with rasterio.open(tif_path) as src:
        grid_match = bool(
            src.crs == expected_crs
            and src.shape == expected_shape
            and src.transform == expected_transform
        )
        if not grid_match:
            raise ValueError("Submission CRS/shape/transform mismatch against reference grid")
        if foot.shape != src.shape or labels.shape != src.shape or not foot.any():
            raise ValueError("Invalid footprint or labels shape")
        arr = src.read(1)
        crs_str = str(src.crs)
        transform_tuple = tuple(round(float(x), 4) for x in src.transform)[:6]
        dtypes = src.dtypes
        count = src.count
        height, width = src.height, src.width
        nodata_val = src.nodata

    in_foot = arr[foot]
    out_foot = arr[~foot]

    in_foot_finite = int(np.isfinite(in_foot).sum())
    in_foot_nan = int(np.isnan(in_foot).sum())
    in_foot_inf = int(np.isinf(in_foot).sum())
    in_foot_sentinel = int((in_foot < -1e30).sum())
    in_foot_min = float(np.nanmin(in_foot))
    in_foot_max = float(np.nanmax(in_foot))
    in_foot_in_01 = bool(
        (in_foot_finite == EXPECTED_FOOTPRINT_PIXELS)
        and np.all((in_foot >= 0.0) & (in_foot <= 1.0))
    )

    if mode == "zeros":
        full_grid_in_01 = bool(
            (int(np.isfinite(arr).sum()) == EXPECTED_TOTAL_PIXELS)
            and np.all((arr >= 0.0) & (arr <= 1.0))
        )
        out_foot_ok = bool(np.all(out_foot == 0.0))
    else:
        full_grid_in_01 = in_foot_in_01
        out_foot_ok = bool(np.all(np.isnan(out_foot)))

    emitted_dots = int((in_foot > 0.0).sum())
    emitted_mass = float(np.nansum(in_foot))
    on_catalogue_dots = int(((np.isfinite(arr) & (arr > 0.0)) & labels).sum())

    checks = {
        "exact_reference_grid_match": grid_match,
        "single_band": count == 1,
        "dtype_float32": dtypes[0] == "float32",
        "dimensions_3730x3292": (height == EXPECTED_HEIGHT and width == EXPECTED_WIDTH),
        "crs_epsg_32611": expected_crs == rasterio.crs.CRS.from_epsg(32611),
        "in_footprint_all_finite": in_foot_finite == EXPECTED_FOOTPRINT_PIXELS,
        "in_footprint_zero_nan": in_foot_nan == 0,
        "in_footprint_zero_inf": in_foot_inf == 0,
        "in_footprint_zero_sentinel": in_foot_sentinel == 0,
        "in_footprint_range_0_1": in_foot_in_01,
        "outside_footprint_compliant": out_foot_ok,
        "zero_on_catalogue_leakage": on_catalogue_dots == 0,
        "validator_range_0_1_guaranteed": full_grid_in_01,
    }
    all_passed = all(checks.values())
    if not all_passed:
        failed = [k for k, v in checks.items() if not v]
        raise ValueError(f"Submission audit failed for {tif_path.name}: {failed}")

    return {
        "filename": tif_path.name,
        "size_bytes": tif_path.stat().st_size,
        "sha256": sha256_file(tif_path),
        "mode": mode,
        "geometry_reference": str(template_tif) if template_tif else "documented EPSG:32611 reference grid",
        "crs": crs_str,
        "transform": list(transform_tuple),
        "shape": [height, width],
        "dtype": dtypes[0],
        "nodata": None if nodata_val is None or (isinstance(nodata_val, float) and np.isnan(nodata_val)) else float(nodata_val),
        "nodata_repr": str(nodata_val),
        "emitted_positive_pixels": emitted_dots,
        "emitted_mass": round(emitted_mass, 4),
        "footprint_fraction": round(emitted_dots / float(EXPECTED_FOOTPRINT_PIXELS), 6),
        "on_catalogue_positive_pixels": on_catalogue_dots,
        "in_footprint_finite_pixels": in_foot_finite,
        "nan_inside_footprint": in_foot_nan,
        "full_grid_nan_pixels": int(np.isnan(arr).sum()),
        "in_footprint_min": in_foot_min,
        "in_footprint_max": in_foot_max,
        "full_grid_finite_pixels": int(np.isfinite(arr).sum()),
        "values_in_0_1": full_grid_in_01,
        "checks": checks,
        "all_checks_passed": all_passed,
        "portal_acceptance": "unknown",
        "submission_authorized": False,
    }


def write_submission_bundle(
    mask_or_probs: np.ndarray,
    foot: np.ndarray,
    labels: np.ndarray,
    template_tif: Path,
    out_dir: Path,
    slug: str,
    timestamp_tag: str,
    candidate_meta: dict,
    prefix: str = "kanlergems2",
) -> dict:
    """Write a locally checked `-zeros.tif`, single-file ZIP and receipt; portal acceptance is unknown."""
    from gems.submission import write_submission, zip_single

    note = str(candidate_meta.get("submission_note", "")).strip()
    if len(note) > 140:
        raise ValueError(f"Submission note exceeds 140 characters ({len(note)} chars)")
    raw, raw_foot, raw_labels = np.asarray(mask_or_probs), np.asarray(foot), np.asarray(labels)
    if not np.isin(raw_foot, (0, 1)).all() or not np.isin(raw_labels, (0, 1)).all():
        raise ValueError("footprint and labels must be binary masks")
    foot, labels = raw_foot.astype(bool), raw_labels.astype(bool)
    if raw.shape != foot.shape or labels.shape != foot.shape or not foot.any():
        raise ValueError("aligned, nonempty prediction/footprint/label grids required")
    if not np.isfinite(raw[foot]).all() or np.any((raw[foot] < 0) | (raw[foot] > 1)):
        raise ValueError("invalid in-footprint predictions: sanitize explicitly before writing")
    with rasterio.open(template_tif) as template:
        if template.count != 1 or not np.array_equal(np.isfinite(template.read(1)), foot):
            raise ValueError("footprint does not match the template")
    out_dir.mkdir(parents=True, exist_ok=True)
    clean_vals = np.where(foot & ~labels, raw, 0.0).astype(np.float32)
    digest8 = hashlib.sha256(clean_vals.tobytes()).hexdigest()[:8]

    zeros_name = f"{prefix}-{slug}-{timestamp_tag}-{digest8}-zeros.tif"
    zeros_path = out_dir / zeros_name
    write_submission(clean_vals, template_tif, zeros_path, outside="zero")
    audit_zeros = audit_geotiff(zeros_path, foot, labels, mode="zeros", template_tif=template_tif)
    zip_path = zip_single(zeros_path)

    bundle = {
        "candidate_id": candidate_meta.get("candidate_id", slug),
        "slug": slug,
        "content_digest8": digest8,
        "description": candidate_meta.get("description", ""),
        "submission_name": zeros_path.stem,
        "submission_note": note,
        "submission_note_length": len(note),
        "zeros_tif": audit_zeros,
        "zeros_zip": {
            "filename": zip_path.name,
            "size_bytes": zip_path.stat().st_size,
            "sha256": sha256_file(zip_path),
        },
    }
    sidecar_path = out_dir / f"{prefix}-{slug}-{timestamp_tag}-{digest8}-validation.json"
    sidecar_path.write_text(json.dumps(bundle, indent=2) + "\n", encoding="utf-8")
    bundle["validation_json"] = sidecar_path.name
    return bundle
