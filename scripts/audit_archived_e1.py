#!/usr/bin/env python3
"""Check a quarantined parallel-run raster against one pinned registry lattice.

This is a retrospective binary-pixel audit, not a new model, holdout, or upload.
"""
from __future__ import annotations
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from lattice_feasibility import REGISTRY_SHA, TEMPLATE_SHA, lower_bound, sha256

ROOT = Path(__file__).resolve().parents[1]
ARCHIVED_RELATIVE = Path('research/quarantine/prior-docs/downloads/kanler-e1-xg-hgb-37654d-20261026T214616Z-7ab68c3efd-allfinite.tif')
ARCHIVED_SHA = '8e35f810f2426f6e70e68f1075439352b363ba1059b40d6237ed306275f5b154'
SOURCE_COMMIT = '4ff78870f8e9d92520a3d0e74ca7f7a388e488ba'


def audit(candidate: Path, template: Path, registry: Path) -> dict:
    for name, path, expected in [('archived raster', candidate, ARCHIVED_SHA),
                                  ('owner-mirror template', template, TEMPLATE_SHA),
                                  ('registered lattice', registry, REGISTRY_SHA)]:
        if sha256(path) != expected:
            raise ValueError(f'{name} does not match pinned bytes')
    with rasterio.open(template) as src:
        footprint = np.isfinite(src.read(1))
        grid = (src.shape, src.crs, src.transform)
    with rasterio.open(registry) as src:
        if (src.shape, src.crs, src.transform) != grid or src.count != 1:
            raise ValueError('registry grid mismatch')
        values = src.read(1)
        if not np.isfinite(values[footprint]).all():
            raise ValueError('nonfinite registry in footprint')
        points = np.isfinite(values) & (values > 0) & footprint
    with rasterio.open(candidate) as src:
        if (src.shape, src.crs, src.transform) != grid or src.count != 1 or src.dtypes[0] != 'float32':
            raise ValueError('archived raster grid or band mismatch')
        values = src.read(1)[footprint]
        if not np.isfinite(values).all() or not np.isin(values, [0, 1]).all():
            raise ValueError('archived raster is not finite binary in footprint')
        dots = np.zeros(footprint.shape, bool)
        dots[footprint] = values > 0
    n = int(dots.sum())
    if n != 37654:
        raise ValueError('unexpected archived dot count')
    within = int(np.count_nonzero(dots & (distance_transform_edt(~points) <= 3.0)))
    bound = lower_bound(footprint, points, n)
    return {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'scope': 'retrospective directed final-dot overlap vs one registered lattice only; no new candidate or surface',
        'archived_source_commit': SOURCE_COMMIT,
        'archived_source_path': str(ARCHIVED_RELATIVE),
        'archived_raster_sha256': ARCHIVED_SHA,
        'template_sha256': TEMPLATE_SHA,
        'registry_raster_sha256': REGISTRY_SHA,
        'candidate_dots': n,
        'candidate_dots_within_3px': within,
        'actual_directed_fraction_within_3px': within / n,
        'minimum_possible_fraction_for_budget': bound['minimum_fraction_inside_halo'],
        'strict_more_than_70_percent': within * 10 > n * 7,
        'verdict': 'duplicate-stop' if within * 10 > n * 7 else 'inconclusive-not-a-novelty-pass',
        'surface_correlation': 'not evaluated; original surface unavailable',
        'ok_to_submit': False,
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, default=ROOT / ARCHIVED_RELATIVE)
    p.add_argument('--template', type=Path, default=ROOT / '.cache/owner-data/sample_submission.tif')
    p.add_argument('--registry', type=Path, default=ROOT / '.cache/registry-lattice-nan.tif')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    text = json.dumps(audit(args.candidate, args.template, args.registry), indent=2, allow_nan=False) + '\n'
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text)
    print(text, end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
