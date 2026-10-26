#!/usr/bin/env python3
"""Stage a research TIFF through the byte-pinned shared writer. NEVER publish/approve it."""
import argparse
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'vendor/template/src'))
sys.path.insert(0, str(ROOT))
import numpy as np
from gems.submission import write_submission
from scripts.validate_raster import validate


def stage(prediction, template, out, *, name, note):
    """Preserve probabilities; reject invalid inputs, paths and accidental overwrites.

    Staging does not test novelty, holdout improvement or eligibility. Deliberately
    only writes to ignored data/candidates, never a Pages download directory.
    """
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', name):
        raise ValueError('Use a nonempty alphanumeric submission slug (max 80 characters)')
    if not isinstance(note, str) or not note.strip() or len(note) > 140:
        raise ValueError('A nonempty note of at most 140 characters is required')
    out = Path(out).resolve()
    staging = (ROOT / 'data/candidates').resolve()
    if not out.is_relative_to(staging) or out.suffix != '.tif':
        raise ValueError('Research TIFF must be inside data/candidates with suffix .tif')
    receipt_path = Path(str(out) + '.format.json')
    if out.exists() or receipt_path.exists():
        raise FileExistsError('Refusing to overwrite TIFF or format report')
    # Shared writer validates the actual probabilities; never threshold NaN/Inf
    # into apparently valid binary dots or clip out-of-range model output.
    write_submission(prediction, template, out, outside='zero')
    report = validate(out, template)
    report.update(submission_name=name, note=note, verdict='negative',
                  eligible_for_selector=False, ok_to_download_and_submit=False,
                  scope='Research staging and format only; no scientific or uniqueness validation')
    receipt_path.write_text(json.dumps(report, indent=2, allow_nan=False) + '\n')
    if not report['format_valid']:
        raise ValueError('Staged TIFF failed format checks; see format report')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prediction', type=Path, required=True, help='2D probabilities .npy; not silently binarized')
    parser.add_argument('--template', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--note', required=True)
    args = parser.parse_args()
    report = stage(np.load(args.prediction, allow_pickle=False), args.template,
                   args.out, name=args.name, note=args.note)
    print(json.dumps(report, indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
