#!/usr/bin/env python3
"""Replay the literal witness stop and focus-nine geometry; never authorizes a slot.

Inputs are hash-pinned owner mirrors, not authenticated competition downloads.
Only these nine locally published rasters and one registry witness are checked.
"""
from __future__ import annotations
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from gems.release_audit import _circle3, _grid, assess_file, forced_budget_result, load_reference
from gems.validator import sha256_file


def review(data: Path) -> dict:
    ref = load_reference(ROOT, data)
    budget = forced_budget_result(ref, 37654)
    manifest = json.loads((ROOT / 'registry/focus_sites_20261027.json').read_text())['sites']
    masks, rows = {}, []
    for entry in manifest:
        path = ROOT / 'docs/downloads' / Path(entry['path']).name
        if not path.is_file() or sha256_file(path) != entry['sha256']:
            raise ValueError(f"Focus raster missing or hash mismatch: {entry['site']}")
        with rasterio.open(path) as ds:
            if ds.count != 1 or _grid(ds) != ref['grid']:
                raise ValueError(f"Focus raster grid mismatch: {entry['site']}")
            a = ds.read(1)
        mask = ref['foot'] & np.isfinite(a) & (a > 0)
        if not mask.any():
            raise ValueError(f"Empty focus raster: {entry['site']}")
        masks[entry['site']] = mask
        rows.append({'site': entry['site'], 'file': path.name, 'sha256': entry['sha256'],
                     'score_user_reported': entry['owner_reported_score'],
                     'score_receipt_available': False, 'positive_pixels': int(mask.sum())})
    if len(masks) != 9:
        raise ValueError('Expected nine distinct focus sites')
    for row in rows:
        candidate = masks[row['site']]
        overlaps = {site: float((candidate & binary_dilation(mask, structure=_circle3())).sum() / candidate.sum())
                    for site, mask in masks.items() if site != row['site']}
        closest = max(overlaps, key=overlaps.get)
        row.update(nearest_focus_site=closest, overlap_within_3px=overlaps[closest],
                   duplicate_vs_focus=overlaps[closest] > .70)
    dcat = distance_transform_edt(~ref['catalogue'])
    s25, s30, s32, s36 = (masks[s] for s in ('GEMSDOE25','GEMSDOE30','GEMSDOE32','GEMSDOE36'))
    forensics = {
        'g25_g30_positive_mask_xor': int(np.count_nonzero(s25 ^ s30)),
        'g32_vs_g25_with_gt_2px_catalogue_collar_xor': int(np.count_nonzero(s32 ^ (s25 & (dcat > 2)))),
        'g25_dots_removed_in_g32': int(np.count_nonzero(s25 & ~s32)),
        'g32_dots_not_in_g36': int(np.count_nonzero(s32 & ~s36)),
        'g36_extra_dots_over_g32': int(np.count_nonzero(s36 & ~s32)),
    }
    name = 'kanlergems2-hptr-exp-2-37654dots-20261028T014401Z-675d0ff8-zeros.tif'
    hptr = assess_file(ROOT / 'docs/downloads' / name, ref)
    return {'schema': 'gems.preflight-review.v1', 'generated_utc': datetime.now(timezone.utc).isoformat(),
            'scope': 'Local nine files and one registered witness only; no full-registry or surface clearance.',
            'provenance': 'SHA-pinned owner mirrors; not authenticated against organizer originals.',
            'preflight': budget, 'focus_nine': rows, 'forensics': forensics,
            'historical_hptr_witness_audit': hptr, 'new_experiments': 0, 'new_raster': None,
            'verdict': 'negative', 'ok_to_submit': False}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--data-dir', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = review(args.data_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'verdict': result['verdict'], 'preflight': result['preflight'],
                      'forensics': result['forensics']}, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
