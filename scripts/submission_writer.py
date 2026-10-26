#!/usr/bin/env python3
"""Strict research-artifact adapter around the unchanged shared template writer.

Never silently thresholds or clips model outputs. Never publishes to docs/ and
never authorizes a competition slot. The separate selector owns promotion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/template/src'))
from gems.submission import write_submission, zip_single
from validate_raster import validate


def write_candidate(predictions, template, output, *, name, note):
    template, output = Path(template), Path(output)
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,99}', name):
        raise ValueError('Name must be a safe model identifier (1–100 characters)')
    if not isinstance(note, str) or not note.strip() or len(note) > 140:
        raise ValueError('A nonempty note of at most 140 characters is required')
    if output.suffix.lower() != '.tif' or output.resolve().is_relative_to((ROOT / 'docs').resolve()):
        raise ValueError('Write research TIFFs outside docs/; publishing requires a separate selector')
    a = np.asarray(predictions)
    if a.ndim != 2 or not np.isfinite(a).all() or ((a < 0) | (a > 1)).any():
        raise ValueError('Raw predictions must be finite and in [0,1]; no implicit clipping or thresholding')
    if output.exists():
        raise FileExistsError('Refusing to overwrite an existing candidate')
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        staged = Path(temp) / output.name
        write_submission(a, template, staged, outside='zero')
        receipt = validate(staged, template)
        if not receipt['format_valid']:
            raise ValueError('Written artifact failed strict format validation')
        staged.replace(output)
    receipt.update(path=str(output), submission_name=name, note=note, note_chars=len(note),
                   scope='FORMAT ONLY; scientific novelty and holdout eligibility NOT evaluated',
                   unique_submission=None, authorized_to_submit=False,
                   writer='vendor/template/src/gems/submission.py',
                   writer_sha256=hashlib.sha256((ROOT / 'vendor/template/src/gems/submission.py').read_bytes()).hexdigest())
    output.with_suffix('.receipt.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    zip_single(output)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('prediction', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--template', type=Path, default=ROOT / 'data/sample_submission.tif')
    p.add_argument('--name', required=True)
    p.add_argument('--note', required=True)
    args = p.parse_args()
    if args.prediction.suffix == '.npy':
        a = np.load(args.prediction, allow_pickle=False)
    else:
        with rasterio.open(args.prediction) as src, rasterio.open(args.template) as template:
            if (src.count, src.shape, src.crs, src.transform) != (1, template.shape, template.crs, template.transform):
                p.error('Prediction raster must match the template grid and be single-band')
            a = src.read(1)
    print(json.dumps(write_candidate(a, args.template, args.output, name=args.name, note=args.note), indent=2))


if __name__ == '__main__':
    main()
