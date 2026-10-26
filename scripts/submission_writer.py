#!/usr/bin/env python3
"""Guarded adapter to the single shared TIFF writer; format validation is not approval."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.submission import write_submission, zip_single  # noqa: E402
if __package__:
    from .registry_guard import require_candidate_generation_allowed
    from .validate_raster import validate
    from .restore_competition_data import sha256_file
else:
    from registry_guard import require_candidate_generation_allowed
    from validate_raster import validate
    from restore_competition_data import sha256_file

LABELS_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"


def write_candidate(prediction, sample: Path, labels: Path, out_dir: Path, slug: str, note: str):
    """Write an unapproved research artifact after the required registry stop check."""
    require_candidate_generation_allowed(sample.parent)
    out_dir = Path(out_dir).resolve()
    staging = (ROOT / "data/candidates").resolve()
    if not out_dir.is_relative_to(staging):
        raise ValueError("Research artifacts must stay inside ignored data/candidates; no symlink escape or publication")
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,50}", slug):
        raise ValueError("slug must contain only letters, numbers, '_' or '-' (max 51 chars)")
    if not isinstance(note, str) or not note.strip() or len(note) > 140:
        raise ValueError("A nonempty note of at most 140 characters is required")
    if sha256_file(labels) != LABELS_SHA:
        raise ValueError("Catalogue mirror checksum mismatch")
    with rasterio.open(sample) as template, rasterio.open(labels) as lab:
        if (template.shape, template.crs, template.transform) != (lab.shape, lab.crs, lab.transform) or lab.count != 1:
            raise ValueError("Catalogue and sample grids differ")
        foot = np.isfinite(template.read(1))
        known = lab.read(1) > 0
    prediction = np.asarray(prediction)
    if prediction.shape != foot.shape or not np.isfinite(prediction[foot]).all() or np.any((prediction[foot] < 0) | (prediction[foot] > 1)):
        raise ValueError("Prediction must match the sample and be finite in [0,1] within the footprint")
    # Known pixels are excluded exactly, not by a broad proximity buffer.
    arr = np.where(foot & ~known, prediction, 0).astype(np.float32)
    if not np.any(arr > 0):
        raise ValueError("Empty prediction is not a meaningful candidate")
    content_id = hashlib.sha256(np.asarray(arr[foot], dtype="<f4").tobytes()).hexdigest()[:12]
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    filename = f"kanler-{slug.lower()}-{stamp}-{content_id}-allfinite.tif"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / filename
    if out.exists():
        raise FileExistsError(out)
    with tempfile.TemporaryDirectory(prefix='.stage-', dir=out_dir) as temporary:
        partial = Path(temporary) / filename
        write_submission(arr, sample, partial, outside="zero")
        report = validate(partial, sample)
        if not report["format_valid"]:
            raise ValueError(f"Written TIFF failed strict validation: {report['checks']}")
        with rasterio.open(partial) as result:
            if np.any(result.read(1)[known] != 0):
                raise ValueError("Written TIFF has positive known-fault pixels")
        partial.replace(out)
    report.update({"path": str(out), "submission_name": f"KANLER-{slug.upper()}-{content_id.upper()}",
                   "note": note, "note_characters": len(note), "portal_acceptance": "unknown",
                   "ok_to_submit": False, "authorization": "none; format is not scientific eligibility or selector approval"})
    receipt = out.with_suffix(".receipt.json")
    receipt.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def stage(predictions, template, output, *, name, note):
    """Compatibility format-only stage; the literal registry stop always runs first.

    Never approves a slot. It is retained for software-contract tests and old
    callers, but cannot generate a candidate under the current witness.
    """
    template, output = Path(template), Path(output).resolve()
    require_candidate_generation_allowed(template.parent)
    staging = (ROOT / 'data/candidates').resolve()
    if output.suffix != '.tif' or not output.is_relative_to(staging):
        raise ValueError('Write only under ignored data/candidates; no symlink escape')
    if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,79}', name):
        raise ValueError('Name must be a safe model identifier')
    if not isinstance(note, str) or not note.strip() or len(note) > 140:
        raise ValueError('A nonempty note of at most 140 characters is required')
    a = np.asarray(predictions)
    if a.ndim != 2 or not np.isfinite(a).all() or ((a < 0) | (a > 1)).any():
        raise ValueError('Raw predictions must be finite and in [0,1]; never clip or threshold')
    labels = template.parent / 'labels.tif'
    if sha256_file(labels) != LABELS_SHA:
        raise ValueError('Catalogue mirror checksum mismatch')
    with rasterio.open(template) as sample, rasterio.open(labels) as lab:
        if (sample.shape, sample.crs, sample.transform) != (lab.shape, lab.crs, lab.transform) or lab.count != 1 or a.shape != sample.shape:
            raise ValueError('Prediction, catalogue and template grids differ')
        foot = np.isfinite(sample.read(1))
        known = lab.read(1) > 0
    if any(p.exists() for p in (output, Path(str(output) + '.format.json'), output.with_suffix('.zip'))):
        raise FileExistsError('Refusing to overwrite a research artifact')
    arr = np.where(foot & ~known, a, 0).astype(np.float32)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.stage-', dir=output.parent) as temporary:
        partial = Path(temporary) / output.name
        write_submission(arr, template, partial, outside='zero')
        receipt = validate(partial, template)
        if not receipt['format_valid']:
            raise ValueError('Written artifact failed strict format validation')
        with rasterio.open(partial) as result:
            if np.any(result.read(1)[known] != 0):
                raise ValueError('Known-fault pixels were not masked exactly')
        partial.replace(output)
    receipt.update(path=str(output), submission_name=name, note=note, note_chars=len(note),
                   scope='FORMAT ONLY; scientific eligibility and novelty NOT established',
                   unique_submission=None, authorized_to_submit=False, verdict='negative',
                   ok_to_download_and_submit=False, eligible_for_selector=False)
    Path(str(output) + '.format.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    zip_single(output)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("prediction", type=Path, help="footprint-aligned 2D .npy, never a prior submission copy")
    p.add_argument("--slug", required=True)
    p.add_argument("--note", required=True)
    p.add_argument("--data-dir", type=Path, default=ROOT / "data")
    p.add_argument("--out-dir", type=Path, default=ROOT / "data/candidates")
    args = p.parse_args()
    # The literal uniqueness rule is decisive even before a model is loaded.
    require_candidate_generation_allowed(args.data_dir)
    prediction = np.load(args.prediction, allow_pickle=False)
    report = write_candidate(prediction, args.data_dir / "sample_submission.tif",
                             args.data_dir / "labels.tif", args.out_dir, args.slug, args.note)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
