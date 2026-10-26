#!/usr/bin/env python3
"""Metric-only adapter for four independent OOF maps and a frozen baseline.

Uses the pinned whole-component SegmentHoldout, not the legacy E1 evaluator.
This CLI cannot prove training/feature provenance from final maps, and explicitly
cannot promote them. Caller must supply fold-local generation receipts separately.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/template/src'))
from gems.holdout import SegmentHoldout


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, nargs=4, required=True, help='NW NE SW SE binary .npy maps')
    p.add_argument('--baseline', type=Path, nargs=4, required=True)
    p.add_argument('--template', type=Path, default=ROOT / 'data/sample_submission.tif')
    p.add_argument('--labels', type=Path, default=ROOT / 'data/existing_faults.tif')
    p.add_argument('--out', type=Path, required=True)
    args = p.parse_args()
    with rasterio.open(args.template) as sample, rasterio.open(args.labels) as labels:
        if (sample.shape, sample.crs, sample.transform) != (labels.shape, labels.crs, labels.transform) or labels.count != 1:
            p.error('Catalogue and template grids must match')
        if sample.crs is None or sample.crs.to_epsg() != 32611 or tuple(sample.transform)[:6] != (100., 0., 243350., 0., -100., 4508550.):
            p.error('Shared 300 m evaluator requires the competition 100 m UTM grid')
        footprint = np.isfinite(sample.read(1)) & (sample.read_masks(1) > 0)
        truth = (labels.read(1) > 0) & (labels.read_masks(1) > 0) & footprint
    context = SegmentHoldout(footprint, truth, buffer_px=15)
    candidate = [np.load(f, mmap_mode='r', allow_pickle=False) for f in args.candidate]
    baseline = [np.load(f, mmap_mode='r', allow_pickle=False) for f in args.baseline]
    report = {'candidate': context.summarize(candidate), 'baseline': context.summarize(baseline),
              'paired': context.compare_paired(candidate, baseline), 'authorized_to_submit': False,
              'fold_local_features_verified': False,
              'limitation': 'Metric calculation only; input maps do not prove fold-local generation, canaries, or novelty.',
              'inputs': {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in args.candidate + args.baseline + [args.template, args.labels]},
              'template_pins_sha256': hashlib.sha256((ROOT / 'vendor/template/pins.json').read_bytes()).hexdigest()}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
