#!/usr/bin/env python3
"""Run the shared literal registry novelty check; never change a candidate to pass it.

Surface checks must precede placement. Final-dot audits require the matching saved
surface report. A scoped registry result is NOT a complete-registry certificate.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.novelty import compare_registry  # noqa: E402
from validate_raster import sha256_file  # noqa: E402


def audit(surface_path: Path, template: Path, registry_path: Path, *, dots_path: Path | None = None,
          previous_report: Path | None = None, root: Path = ROOT) -> dict:
    registry = json.loads(registry_path.read_text())
    entries = registry.get("entries")
    if not isinstance(entries, list) or not entries:
        raise ValueError("A nonempty pinned registry manifest is required")
    surface_sha = sha256_file(surface_path)
    manifest_sha = sha256_file(registry_path)
    template_sha = sha256_file(template)
    if dots_path is not None:
        if previous_report is None:
            raise ValueError("Final-dot audit needs the earlier surface report")
        pre = json.loads(previous_report.read_text())
        if (pre.get("stage") != "surface_before_placement" or pre.get("technical_passed") is not True
                or pre.get("surface_sha256") != surface_sha or pre.get("registry_manifest_sha256") != manifest_sha
                or pre.get("template_sha256") != template_sha):
            raise ValueError("Missing, duplicate, or mismatched pre-placement surface report")
    surface = np.load(surface_path, allow_pickle=False, mmap_mode="r")
    with rasterio.open(template) as ds:
        if (ds.count != 1 or ds.crs is None or ds.crs.to_epsg() != 32611
                or (ds.transform.a, ds.transform.b, ds.transform.d, ds.transform.e) != (100, 0, 0, -100)):
            raise ValueError("Template must be a single-band EPSG:32611 100 m grid")
        if len(ds.files) != 1:
            raise ValueError("Template must not rely on external sidecars")
        footprint = np.isfinite(ds.read(1)) & (ds.read_masks(1) > 0)
        grid = (ds.shape, ds.crs, ds.transform)
    if not footprint.any():
        raise ValueError("Template footprint is empty")
    if surface.shape != footprint.shape or not np.isfinite(surface[footprint]).all():
        raise ValueError("Surface must be finite and aligned inside the footprint")
    ids = set()
    for row in entries:
        if row.get("id") in ids or not row.get("id"):
            raise ValueError("Registry IDs must be nonempty and unique")
        ids.add(row["id"])
        path = (root / row["cache_path"]).resolve()
        if root.resolve() not in path.parents or not path.is_file() or sha256_file(path) != row.get("sha256"):
            raise ValueError(f"Missing/invalid registry bytes: {path}")
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
                raise ValueError(f"Registry grid mismatch: {path}")
            if len(ds.files) != 1:
                raise ValueError(f"Registry depends on external sidecars: {path}")
            if not np.isfinite(ds.read(1)[footprint]).all() or np.any(ds.read_masks(1)[footprint] == 0):
                raise ValueError(f"Non-finite or masked registry values in footprint: {path}")
    dots = None
    if dots_path is not None:
        if dots_path.suffix.lower() == ".npy":
            dots_array = np.load(dots_path, allow_pickle=False)
        else:
            with rasterio.open(dots_path) as ds:
                if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
                    raise ValueError("Candidate dot grid mismatch")
                dots_array = ds.read(1)
        if dots_array.shape != footprint.shape or not np.isfinite(dots_array[footprint]).all():
            raise ValueError("Dots must be finite and footprint-aligned")
        if not np.isin(dots_array[footprint], [0, 1]).all():
            raise ValueError("Dots must be binary on the footprint")
        exterior = dots_array[~footprint]
        if np.isinf(exterior).any() or np.any(np.isfinite(exterior) & (exterior != 0)):
            raise ValueError("Dots outside the footprint must be zero or NaN")
        dots = footprint & (dots_array > 0)
        if not dots.any():
            raise ValueError("Empty dot sets cannot pass novelty")
    comparison = compare_registry(surface, footprint, entries, root, dots=dots,
                                  separate_calibration_controls=False)
    # Undefined rank means the test cannot establish uniqueness; fail closed.
    undefined = [r["registry_id"] for r in comparison["rows"] if r["raw_spearman"] is None]
    technical_pass = comparison["passed"] and not undefined
    return {
        "schema_version": 1,
        "stage": comparison["stage"],
        "surface_sha256": surface_sha,
        "registry_manifest_sha256": manifest_sha,
        "template_sha256": template_sha,
        "preplacement_report_sha256": sha256_file(previous_report) if previous_report is not None else None,
        "dots_sha256": sha256_file(dots_path) if dots_path is not None else None,
        "scope": registry.get("scope", "unspecified"),
        "registry_complete_asserted_by_manifest": registry.get("registry_complete") is True,
        "registry_completeness_independently_verified": False,
        "technical_passed": technical_pass,
        "undefined_full_footprint_ranks": undefined,
        "literal_calibration_inclusive": True,
        "eligible_for_selector": False,
        "reason": "A scoped similarity test alone cannot verify full-registry coverage, scientific merit, or slot eligibility.",
        "comparison": comparison,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--surface", type=Path, required=True, help="Pre-placement 2D .npy surface")
    ap.add_argument("--template", type=Path, default=ROOT / "data/sample_submission.tif")
    ap.add_argument("--registry", type=Path, required=True)
    ap.add_argument("--dots", type=Path, help="Existing binary .npy or GeoTIFF for final-dot audit")
    ap.add_argument("--preplacement-report", type=Path)
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    result = audit(a.surface, a.template, a.registry, dots_path=a.dots, previous_report=a.preplacement_report)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ("stage", "scope", "technical_passed", "registry_completeness_independently_verified", "eligible_for_selector")}, indent=2))
    if not result["technical_passed"]:
        raise SystemExit(2)
    if not result["registry_completeness_independently_verified"]:
        raise SystemExit(3)


if __name__ == "__main__":
    main()
