#!/usr/bin/env python3
"""Fail-closed independent read-back audit; never clips or approves a submission."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
import rasterio


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def audit(file: Path, template: Path, outside: str) -> dict:
    if outside not in {'nan', 'zero'}:
        raise ValueError('outside must be nan or zero')
    with rasterio.open(template) as t:
        if t.count != 1:
            raise ValueError('footprint template must have one band')
        reference = t.read(1)
        if np.isinf(reference).any():
            raise ValueError('footprint template contains infinite values')
        footprint = np.isfinite(reference)
        if not footprint.any() or footprint.all():
            raise ValueError('template does not contain a finite interior and a NaN/non-finite exterior')
        template_grid = (t.height, t.width, t.crs, t.transform)
    with rasterio.open(file) as t:
        a = t.read(1)
        same_grid = (t.height, t.width, t.crs, t.transform) == template_grid
        one_band = t.count == 1
        dtype_ok = t.dtypes == ('float32',)
        crs = str(t.crs)
        epsg_ok = bool(t.crs is not None and t.crs.to_epsg() == 32611)
        driver_ok = t.driver == 'GTiff'
        shape = [t.height, t.width]
        transform = list(tuple(t.transform)[:6])
    interior_shape_ok = a.shape == footprint.shape
    inside = a[footprint] if interior_shape_ok else np.array([], dtype=np.float32)
    exterior = a[~footprint] if interior_shape_ok else np.array([], dtype=np.float32)
    finite_inside = bool(inside.size and np.isfinite(inside).all())
    inside_range = bool(finite_inside and (inside >= 0).all() and (inside <= 1).all())
    all_finite = bool(np.isfinite(a).all())
    all_range = bool(all_finite and (a >= 0).all() and (a <= 1).all())
    exterior_ok = bool(exterior.size and (np.isnan(exterior).all() if outside == 'nan' else (exterior == 0).all()))
    conditions = {'tif_extension_and_driver': file.suffix.lower() == '.tif' and driver_ok,
                  'single_band': one_band, 'float32': dtype_ok, 'epsg_32611': epsg_ok,
                  'matching_crs_shape_transform': same_grid,
                  'finite_inside_footprint': finite_inside, 'inside_in_0_1': inside_range,
                  f'{outside}_outside': exterior_ok}
    if outside == 'zero':
        conditions['whole_array_finite_in_0_1'] = all_range
    return {'file': str(file), 'sha256': sha256(file), 'footprint_template_sha256': sha256(template),
            'checks': conditions, 'local_format_pass': all(conditions.values()),
            'outside_mode': outside, 'whole_array_finite': all_finite,
            'nonfinite_total': int((~np.isfinite(a)).sum()),
            'crs': crs, 'shape': shape, 'transform': transform,
            'portal_acceptance': None, 'ok_to_submit': False,
            'note': ('Local byte validation is not scientific promotion or a portal receipt. '
                     'The written specification says null/NaN outside; zero-outside acceptance is unresolved.')}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file', type=Path, help='Existing TIFF to reopen; no file is created')
    parser.add_argument('--template', type=Path, required=True, help='One-band footprint template with non-finite exterior')
    parser.add_argument('--outside', choices=('nan', 'zero'), required=True)
    parser.add_argument('--out', type=Path, help='Optional local JSON receipt')
    args = parser.parse_args()
    result = audit(args.file, args.template, args.outside)
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        temp = args.out.with_suffix(args.out.suffix + '.partial')
        temp.write_text(text)
        temp.replace(args.out)
    print(text, end='')
    return 0 if result['local_format_pass'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
