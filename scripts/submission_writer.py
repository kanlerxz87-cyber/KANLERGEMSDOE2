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

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.submission import write_submission  # noqa: E402
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
    partial = out.with_name(out.stem + ".partial.tif")
    try:
        write_submission(arr, sample, partial, outside="zero")
        report = validate(partial, sample)
        if not report["format_valid"]:
            raise ValueError(f"Written TIFF failed strict validation: {report['checks']}")
        with rasterio.open(partial) as result:
            if np.any(result.read(1)[known] != 0):
                raise ValueError("Written TIFF has positive known-fault pixels")
        partial.replace(out)
    finally:
        partial.unlink(missing_ok=True)
    report.update({"path": str(out), "submission_name": f"KANLER-{slug.upper()}-{content_id.upper()}",
                   "note": note, "note_characters": len(note), "portal_acceptance": "unknown",
                   "ok_to_submit": False, "authorization": "none; format is not scientific eligibility or selector approval"})
    receipt = out.with_suffix(".receipt.json")
    receipt.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("prediction", type=Path, help="footprint-aligned 2D .npy, never a prior submission copy")
    p.add_argument("--slug", required=True)
    p.add_argument("--note", required=True)
    p.add_argument("--data-dir", type=Path, default=ROOT / "data")
    p.add_argument("--out-dir", type=Path, default=ROOT / "data/generated-research")
    args = p.parse_args()
    # The literal uniqueness rule is decisive even before a model is loaded.
    require_candidate_generation_allowed(args.data_dir)
    prediction = np.load(args.prediction, allow_pickle=False)
    report = write_candidate(prediction, args.data_dir / "sample_submission.tif",
                             args.data_dir / "labels.tif", args.out_dir, args.slug, args.note)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
