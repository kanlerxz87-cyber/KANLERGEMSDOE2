#!/usr/bin/env python3
"""Fail-closed local GEMS GeoTIFF format validator (not a score/uniqueness test).

Requires rasterio. Run only against the official sample/template GeoTIFF:
  python scripts/validate_submission.py --template data/sample_submission.tif --candidate candidate.tif
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def validate(template_path: Path, candidate_path: Path) -> dict[str, Any]:
    try:
        import numpy as np
        import rasterio
    except ImportError as exc:
        raise RuntimeError(
            "GeoTIFF validation requires rasterio and numpy; install the project's "
            "geospatial environment before validating. No validation was performed."
        ) from exc

    checks: dict[str, Any] = {
        "template": str(template_path),
        "candidate": str(candidate_path),
        "format_valid": False,
        "checks": {},
        "errors": [],
        "scope_note": "Format only; does not establish holdout performance, uniqueness, or organizer acceptance.",
    }
    if not template_path.is_file():
        checks["errors"].append(f"Template not found: {template_path}")
        return checks
    if candidate_path.suffix.lower() != ".tif":
        checks["errors"].append("Candidate filename must use the .tif extension.")
        return checks
    if not candidate_path.is_file():
        checks["errors"].append(f"Candidate not found: {candidate_path}")
        return checks

    try:
        with rasterio.open(template_path) as template, rasterio.open(candidate_path) as candidate:
            template_grid = (template.crs, template.width, template.height, template.transform)
            candidate_grid = (candidate.crs, candidate.width, candidate.height, candidate.transform)
            grid_match = template_grid == candidate_grid
            template_single_band = template.count == 1
            official_crs = template.crs is not None and template.crs.to_epsg() == 32611
            resolution_100m = (
                abs(abs(template.transform.a) - 100.0) < 1e-9
                and abs(abs(template.transform.e) - 100.0) < 1e-9
            )
            single_band = candidate.count == 1
            float32 = candidate.dtypes == ("float32",)
            checks["checks"].update({
                "crs_shape_transform_match": grid_match,
                "template_single_band": template_single_band,
                "template_epsg_32611": official_crs,
                "template_pixel_size_100m": resolution_100m,
                "single_band": single_band,
                "float32": float32,
                "crs": str(candidate.crs),
                "shape": [candidate.height, candidate.width],
                "transform": list(candidate.transform),
            })
            if not grid_match:
                checks["errors"].append("Candidate CRS, dimensions, or affine transform differ from template.")
            if not template_single_band:
                checks["errors"].append(f"Expected a single-band template; found {template.count} bands.")
            if not official_crs:
                checks["errors"].append("Template is not EPSG:32611 (UTM zone 11N).")
            if not resolution_100m:
                checks["errors"].append("Template pixel size is not 100 m.")
            if not single_band:
                checks["errors"].append(f"Expected exactly one band; found {candidate.count}.")
            if not float32:
                checks["errors"].append(f"Expected float32; found {candidate.dtypes}.")

            if grid_match and single_band:
                footprint = template.dataset_mask() > 0
                values = candidate.read(1, masked=False)
                candidate_mask = candidate.dataset_mask() > 0
                nonempty_footprint = bool(footprint.any())
                inside_finite = nonempty_footprint and bool(np.isfinite(values[footprint]).all())
                inside_range = nonempty_footprint and bool(((values[footprint] >= 0.0) & (values[footprint] <= 1.0)).all())
                same_footprint_mask = bool(np.array_equal(candidate_mask, footprint))
                checks["checks"].update({
                    "footprint_cells": int(footprint.sum()),
                    "nonempty_template_footprint": nonempty_footprint,
                    "no_nan_or_infinity_inside_footprint": inside_finite,
                    "inside_values_inclusive_0_1": inside_range,
                    "candidate_mask_matches_template_footprint": same_footprint_mask,
                    "observed_inside_min": float(values[footprint].min()) if footprint.any() else None,
                    "observed_inside_max": float(values[footprint].max()) if footprint.any() else None,
                })
                if not nonempty_footprint:
                    checks["errors"].append("Template has an empty data footprint.")
                if not inside_finite:
                    checks["errors"].append("NaN or infinity found inside the template footprint.")
                if not inside_range:
                    checks["errors"].append("Predicted values inside the footprint must be within [0, 1].")
                if not same_footprint_mask:
                    checks["errors"].append("Candidate valid-data mask differs from the template footprint; outside cells must be null/nodata.")

    except Exception as exc:  # malformed/unsupported raster is a validation failure
        checks["errors"].append(f"Could not inspect GeoTIFF: {type(exc).__name__}: {exc}")

    checks["format_valid"] = not checks["errors"]
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", required=True, type=Path, help="Official sample/template GeoTIFF")
    parser.add_argument("--candidate", required=True, type=Path, help="Candidate single-band GeoTIFF")
    parser.add_argument("--json", type=Path, help="Optional path to write the complete JSON report")
    args = parser.parse_args()
    try:
        report = validate(args.template, args.candidate)
    except RuntimeError as exc:
        print(json.dumps({"format_valid": False, "errors": [str(exc)]}, indent=2), file=sys.stderr)
        return 2
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report["format_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
