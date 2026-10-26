"""Strict whole-array format validation. Format validity does NOT authorize submission."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio


def digest(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def validate(path, template):
    path, template = Path(path), Path(template)
    candidate_before, template_before = digest(path), digest(template)
    with rasterio.open(template) as t, rasterio.open(path) as r:
        a = r.read(1)
        reference = t.read(1)
        reference_mask = t.read_masks(1)
        candidate_mask = r.read_masks(1)
        footprint = np.isfinite(reference)
        template_dependencies = [name for name in t.files if Path(name).resolve() != template.resolve()]
        candidate_dependencies = [name for name in r.files if Path(name).resolve() != path.resolve()]
        shape_matches = r.shape == t.shape
        masked_inside = int((candidate_mask[footprint] == 0).sum()) if shape_matches else None
        finite = bool(np.isfinite(a).all())
        checks = {
            'tif_extension_and_driver': path.suffix.lower() == '.tif' and r.driver == 'GTiff',
            'single_band': r.count == 1,
            'dtype_float32': r.dtypes == ('float32',),
            'single_band_float32': r.count == 1 and r.dtypes == ('float32',),
            'template_single_band': t.count == 1,
            'crs_matches': r.crs is not None and r.crs == t.crs,
            'epsg_32611': r.crs is not None and r.crs.to_epsg() == 32611,
            'shape_matches': shape_matches,
            'transform_matches': r.transform == t.transform,
            'no_nan_or_inf_whole_grid': finite,
            'values_in_0_1_whole_grid': bool(finite and ((a >= 0) & (a <= 1)).all()),
            'template_footprint_unambiguous': bool(footprint.any() and not np.isinf(reference).any()
                                                   and not np.any(footprint & (reference_mask == 0))),
            'unmasked_inside_footprint': masked_inside == 0,
            'no_external_candidate_dependencies': not candidate_dependencies,
            'no_external_template_dependencies': not template_dependencies,
        }
        crs, shape, transform = str(r.crs), list(r.shape), list(r.transform)[:6]
    candidate_after, template_after = digest(path), digest(template)
    checks['candidate_unchanged_during_audit'] = candidate_before == candidate_after
    checks['template_unchanged_during_audit'] = template_before == template_after
    return {
        'path': str(path), 'sha256': candidate_after, 'checks': checks,
        'format_valid': all(checks.values()), 'ok_to_submit': False,
        'authorization': 'format only; holdout + novelty + selector still required',
        'crs': crs, 'shape': shape, 'transform': transform,
        'inside_masked_count': masked_inside,
        'candidate_external_dependencies': candidate_dependencies,
        'template_external_dependencies': template_dependencies,
        'positive_pixels': int(np.count_nonzero(a > 0)),
        'finite_min': float(a[np.isfinite(a)].min()) if np.isfinite(a).any() else None,
        'finite_max': float(a[np.isfinite(a)].max()) if np.isfinite(a).any() else None,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('raster')
    p.add_argument('template')
    args = p.parse_args()
    report = validate(args.raster, args.template)
    print(json.dumps(report, indent=2, allow_nan=False))
    raise SystemExit(0 if report['format_valid'] else 1)


if __name__ == '__main__':
    main()
