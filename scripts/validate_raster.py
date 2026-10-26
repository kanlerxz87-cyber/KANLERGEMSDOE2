#!/usr/bin/env python3
"""Validate a saved GeoTIFF against a template; format PASS never authorizes upload.

Published format allows null/NaN outside the footprint and requires finite [0, 1]
float32 predictions inside. A separate whole-grid-finite check is diagnostic:
zeroing outside is NOT represented as organizer-approved or guaranteed accepted.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def digest(path: str | Path) -> str:
    """Compatibility name for the saved-byte hash used by other validators."""
    return sha256_file(path)


def validate(path: str | Path, template: str | Path) -> dict:
    path, template = Path(path), Path(template)
    candidate_before, template_before = digest(path), digest(template)
    with rasterio.open(template) as t, rasterio.open(path) as r:
        sample = t.read(1)
        template_mask = t.read_masks(1)
        footprint = np.isfinite(sample) & (template_mask > 0)
        # A lone GeoTIFF upload cannot depend on external .msk/.aux sidecars.
        template_dependencies = [str(f) for f in t.files if Path(f).resolve() != template.resolve()]
        candidate_dependencies = [str(f) for f in r.files if Path(f).resolve() != path.resolve()]
        a = r.read(1)
        aligned = r.shape == t.shape
        raster_mask = r.read_masks(1) if aligned else None
        if aligned:
            inside, outside = a[footprint], a[~footprint]
            inside_mask, outside_mask = raster_mask[footprint], raster_mask[~footprint]
            inside_finite = bool(inside.size and np.isfinite(inside).all())
            inside_range = bool(inside_finite and np.all((inside >= 0) & (inside <= 1)))
            inside_not_masked = bool(inside_mask.size and np.all(inside_mask != 0))
            # A masked nodata value is null even if its stored representation is
            # finite. Infinity is not treated as valid nodata. An empty exterior
            # is valid (the template footprint fills the rectangular grid).
            outside_null = bool(np.all(np.isnan(outside) | ((outside_mask == 0) & ~np.isinf(outside))))
            outside_nan = bool(np.isnan(outside).all())
        else:
            inside = np.array([], dtype=np.float32)
            inside_finite = inside_range = inside_not_masked = outside_null = outside_nan = False
        finite = np.isfinite(a)
        checks = {
            "tif_extension_and_driver": path.suffix.lower() == ".tif" and r.driver == "GTiff",
            "template_single_band": t.count == 1,
            "template_nonempty_footprint": bool(footprint.any()),
            "template_footprint_unambiguous": bool(not np.isinf(sample).any() and not np.any(np.isfinite(sample) & (template_mask == 0))),
            "template_self_contained": not template_dependencies,
            "candidate_self_contained": not candidate_dependencies,
            "no_external_template_dependencies": not template_dependencies,
            "no_external_candidate_dependencies": not candidate_dependencies,
            "single_band": r.count == 1,
            "float32": r.dtypes == ("float32",),
            "crs_matches": r.crs is not None and t.crs is not None and r.crs == t.crs,
            "epsg_32611": r.crs is not None and r.crs.to_epsg() == 32611,
            "shape_matches": aligned,
            "transform_matches": r.transform == t.transform,
            "axis_aligned_100m": (r.transform.a, r.transform.b, r.transform.d, r.transform.e) == (100, 0, 0, -100),
            "finite_inside_footprint": inside_finite,
            "unmasked_inside_footprint": inside_not_masked,
            "values_in_0_1_inside_footprint": inside_range,
            "outside_footprint_null_or_nan": outside_null,
            "no_inf_whole_grid": bool(not np.isinf(a).any()),
            "no_nan_or_inf_whole_grid": bool(finite.all()),
            "values_in_0_1_whole_grid": bool(finite.all() and np.all((a >= 0) & (a <= 1))),
        }
        candidate_after, template_after = digest(path), digest(template)
        checks["candidate_unchanged_during_audit"] = candidate_before == candidate_after
        checks["template_unchanged_during_audit"] = template_before == template_after
        required = (
            "tif_extension_and_driver", "template_single_band", "template_nonempty_footprint", "template_footprint_unambiguous", "template_self_contained",
            "candidate_self_contained", "candidate_unchanged_during_audit", "template_unchanged_during_audit", "single_band", "float32",
            "crs_matches", "epsg_32611", "shape_matches", "transform_matches", "axis_aligned_100m", "finite_inside_footprint",
            "unmasked_inside_footprint", "values_in_0_1_inside_footprint",
            "outside_footprint_null_or_nan", "no_inf_whole_grid",
        )
        official_format = all(checks[key] for key in required)
        strict_range_grid = all(checks[key] for key in (
            "tif_extension_and_driver", "template_single_band", "template_nonempty_footprint", "template_footprint_unambiguous", "template_self_contained",
            "candidate_self_contained", "candidate_unchanged_during_audit", "template_unchanged_during_audit", "single_band", "float32",
            "crs_matches", "epsg_32611", "shape_matches", "transform_matches", "axis_aligned_100m",
            "unmasked_inside_footprint", "no_nan_or_inf_whole_grid", "values_in_0_1_whole_grid",
        ))
        return {
            "path": str(path),
            "sha256": candidate_after,
            "template_sha256": template_after,
            "candidate_external_dependencies": candidate_dependencies,
            "template_external_dependencies": template_dependencies,
            "inside_masked_count": int((inside_mask == 0).sum()) if aligned else None,
            "checks": checks,
            "format_valid": official_format,
            "strict_whole_grid_range_and_grid_valid": strict_range_grid,
            "all_outside_values_nan": outside_nan,
            "portal_acceptance": "unknown; no organizer submission-page receipt",
            "format_policy": "Conservatively require null/NaN outside the peer template's finite footprint. The public page says outside bounds; whether that means every footprint hole is not independently confirmed.",
            "template_provenance": "not authenticated by this validator",
            "ok_to_submit": False,
            "authorization": "format only; holdout, complete novelty and a separate selector are required",
            "crs": str(r.crs),
            "shape": list(r.shape),
            "transform": list(r.transform)[:6],
            "positive_pixels": int(np.count_nonzero(inside > 0)),
            "footprint_pixels": int(footprint.sum()),
            "finite_min": float(a[finite].min()) if finite.any() else None,
            "finite_max": float(a[finite].max()) if finite.any() else None,
        }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("raster", type=Path)
    parser.add_argument("template", type=Path)
    args = parser.parse_args()
    report = validate(args.raster, args.template)
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report["format_valid"] else 1)


if __name__ == "__main__":
    main()
