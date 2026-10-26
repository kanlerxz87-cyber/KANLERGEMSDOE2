#!/usr/bin/env python3
"""Restore and compare nine pinned historical rasters. Never score or submit them."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from lattice_feasibility import TEMPLATE_SHA, sha256

ROOT = Path(__file__).resolve().parents[1]


def restore_one(entry: dict, directory: Path) -> Path:
    """Fetch exact commit content via GitHub API, then hash before use."""
    directory.mkdir(parents=True, exist_ok=True)
    dest = directory / f"{entry['site']}.tif"
    if dest.exists() and sha256(dest) == entry['sha256']:
        return dest
    fd, tmpname = tempfile.mkstemp(dir=directory, prefix="download-", suffix=".partial")
    try:
        with os.fdopen(fd, 'wb') as out:
            subprocess.run(["gh", "api", f"repos/{entry['repository']}/contents/{entry['path']}?ref={entry['ref']}",
                            "-H", "Accept: application/vnd.github.raw"], stdout=out, check=True)
        tmp = Path(tmpname)
        if sha256(tmp) != entry['sha256']:
            raise ValueError(f"Hash mismatch for {entry['site']}; refusing bytes")
        tmp.replace(dest)
    finally:
        Path(tmpname).unlink(missing_ok=True)
    return dest


def audit(manifest: dict, template: Path, labels: Path, cache: Path) -> dict:
    if sha256(template) != TEMPLATE_SHA:
        raise ValueError("Unrecognized owner-mirror template")
    expected_label_sha = '7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093'
    if sha256(labels) != expected_label_sha:
        raise ValueError("Unrecognized owner-mirror catalogue")
    with rasterio.open(template) as src:
        foot = np.isfinite(src.read(1))
        grid = (src.height, src.width, src.crs, src.transform)
    with rasterio.open(labels) as src:
        if (src.height, src.width, src.crs, src.transform) != grid:
            raise ValueError("catalogue does not match template")
        catalogue = (src.read(1) > 0) & foot

    masks, rows = {}, []
    for entry in manifest['sites']:
        path = restore_one(entry, cache)
        with rasterio.open(path) as src:
            if (src.height, src.width, src.crs, src.transform) != grid or src.count != 1:
                raise ValueError(f"Grid mismatch for {entry['site']}")
            arr = src.read(1)
            dtype = src.dtypes[0]
        vals = arr[foot]
        if dtype != 'float32' or not np.isfinite(vals).all() or (vals < 0).any() or (vals > 1).any():
            raise ValueError(f"Invalid in-footprint values for {entry['site']}")
        if not np.isin(vals, [0.0, 1.0]).all():
            raise ValueError(f"Expected binary historical raster for {entry['site']}")
        mask = np.isfinite(arr) & (arr > 0) & foot
        if not mask.any():
            raise ValueError(f"Empty historical raster for {entry['site']}")
        masks[entry['site']] = mask
        rows.append({**entry, 'raster_sha256_verified': sha256(path),
                     'prediction_value_sha256': hashlib.sha256(np.packbits(mask[foot]).tobytes()).hexdigest(),
                     'positive_pixels': int(mask.sum()),
                     'inside_footprint_finite_in_0_1': True,
                     'template_grid_match': True,
                     'score_estimate': None,
                     'score_estimate_reason': 'No calibrated hidden-fault estimate; no organizer receipt',
                     'ok_to_submit': False})
        del arr, vals

    # Directed fraction, denominator = the candidate's positive pixels. Reversing
    # the pair can give a different number, particularly for subset/superset pairs.
    overlaps = {name: {} for name in masks}
    equality = {name: [] for name in masks}
    for ref_name, ref in masks.items():
        dist = distance_transform_edt(~ref)
        for cand_name, cand in masks.items():
            if ref_name == cand_name:
                continue
            overlaps[cand_name][ref_name] = float(np.count_nonzero(dist[cand] <= 3.0) / cand.sum())
            if np.array_equal(ref, cand):
                equality[cand_name].append(ref_name)
    for row in rows:
        name = row['site']
        maximum_peer = max(overlaps[name], key=overlaps[name].get)
        row['maximum_directed_3px_overlap_with_other_focus_champions'] = overlaps[name][maximum_peer]
        row['maximum_overlap_peer'] = maximum_peer
        row['identical_prediction_sites'] = equality[name]
        row['final_dot_uniqueness_against_eight_peers'] = overlaps[name][maximum_peer] <= 0.70
        row['surface_uniqueness'] = 'unknown: original pre-placement surfaces unavailable'
        row['full_registry_uniqueness'] = 'not established by this nine-file audit'

    dcat = distance_transform_edt(~catalogue)
    d28 = masks['GEMSDOE25']
    b1_pred, b2_pred = d28 & (dcat > 1), d28 & (dcat > 2)
    b1_actual, b2_actual = masks['GEMSDOE31'], masks['GEMSDOE32']
    g36 = masks['GEMSDOE36']
    lineage = {
        'd28_positive_pixels': int(d28.sum()),
        'b1_distance_prune_matches_gemsdoe31_exactly': bool(np.array_equal(b1_pred, b1_actual)),
        'b2_distance_prune_matches_gemsdoe32_exactly': bool(np.array_equal(b2_pred, b2_actual)),
        'b1_removed': int((d28 & ~b1_pred).sum()),
        'b2_removed_total': int((d28 & ~b2_pred).sum()),
        'b2_positive_pixels': int(b2_actual.sum()),
        'gemsdoe36_contains_every_b2_dot': not bool((b2_actual & ~g36).any()),
        'gemsdoe36_additional_dots_outside_b2': int((g36 & ~b2_actual).sum()),
        'interpretation': 'Pixel algebra only; it cannot show why hidden-label scores changed.',
    }
    return {'schema_version': 1, 'checked_utc': datetime.now(timezone.utc).isoformat(),
            'template_sha256': TEMPLATE_SHA, 'catalogue_sha256': expected_label_sha,
            'source_review': manifest['source_review'], 'score_evidence': manifest['provenance'],
            'scope': 'Nine pinned historical rasters, not all candidate or concurrent registry rasters; no candidate authorized.',
            'sites': rows, 'directed_3px_overlap': overlaps, 'lineage': lineage}


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, default=ROOT / 'registry/focus-sites.json')
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--labels', type=Path, required=True)
    p.add_argument('--cache', type=Path, default=ROOT / '.cache/focus')
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    result = audit(json.loads(a.manifest.read_text()), a.template, a.labels, a.cache)
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print('Audited', len(result['sites']), 'historical rasters. No organizer score or slot approval inferred.')
    print(json.dumps(result['lineage'], indent=2))
    for row in result['sites']:
        print(row['site'], row['positive_pixels'], row['maximum_overlap_peer'],
              f"{100*row['maximum_directed_3px_overlap_with_other_focus_champions']:.2f}%")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
