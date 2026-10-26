#!/usr/bin/env python3
"""Shared fail-closed submission GeoTIFF writer and saved-byte validator.

Implements Parallel-Run Protocol Rule 2 and Rule 5:
  - Refuse any prediction with NaN/Inf or values outside [0.0, 1.0] inside the
    footprint (no silent clipping).
  - Enforce submission note length <= 140 characters.
  - Write both the all-finite ``-zeros.tif`` variant (0.0 outside footprint,
    nodata=None, guaranteeing whole-array range [0, 1] compliance on portals that
    check the unmasked 2D array) and the ``-nan.tif`` variant (NaN outside
    footprint, nodata=NaN).
  - Re-open the saved bytes from disk and run the exact grid/CRS/shape/transform/
    range validator against ``sample_submission.tif``.
"""
from __future__ import annotations

import hashlib
import json
import sys
import zipfile
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe33 import grid  # noqa: E402
from validate_submission import audit as validate_audit  # noqa: E402

PROTOCOL_MAX_NOTE = 140


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def content_digest12(arr_in_footprint: np.ndarray) -> str:
    a = np.asarray(arr_in_footprint, dtype=np.float32)
    if np.all((a == 0.0) | (a == 1.0)):
        payload = np.packbits(a > 0.5, axis=None).tobytes()
    else:
        payload = a.tobytes()
    return hashlib.sha256(payload).hexdigest()[:12]


def write_submission_bundle(
    prediction: np.ndarray,
    *,
    name_prefix: str,
    note_template: str,
    outdir: Path,
    template_path: Path | None = None,
    max_note_chars: int = PROTOCOL_MAX_NOTE,
) -> dict:
    """Write and validate -zeros.tif, -nan.tif, .zip archives, and JSON receipt."""
    note_probe = note_template.replace("{cid}", "0" * 12).replace("{cid8}", "0" * 8)
    if len(note_probe) > max_note_chars:
        raise ValueError(f"submission note length {len(note_probe)} exceeds protocol limit {max_note_chars}: {note_probe!r}")

    pred_raw = np.asarray(prediction)
    finite_raw = pred_raw[np.isfinite(pred_raw)]
    if finite_raw.size and bool((finite_raw < 0.0).any() or (finite_raw > 1.0).any()):
        raise ValueError("prediction contains finite values outside [0.0, 1.0]")

    tpl_path = Path(template_path) if template_path else grid.DATA / grid.SAMPLE_SUBMISSION
    with rasterio.open(tpl_path) as src:
        tpl_arr = src.read(1)
        footprint = np.isfinite(tpl_arr)
        base_profile = src.profile.copy()

    pred = np.asarray(prediction, dtype=np.float32)
    if pred.shape != footprint.shape:
        raise ValueError(f"prediction shape {pred.shape} != template shape {footprint.shape}")

    inside = pred[footprint]
    if not np.isfinite(inside).all():
        n_bad = int((~np.isfinite(inside)).sum())
        raise ValueError(f"prediction contains {n_bad} NaN/Inf values inside footprint")
    if bool((inside < 0.0).any() or (inside > 1.0).any()):
        lo, hi = float(inside.min()), float(inside.max())
        raise ValueError(f"prediction values inside footprint [{lo}, {hi}] outside [0.0, 1.0]")

    cid = content_digest12(inside)
    note = note_template.replace("{cid}", cid).replace("{cid8}", cid[:8])
    if len(note) > max_note_chars:
        raise ValueError(f"submission note length {len(note)} exceeds protocol limit {max_note_chars}: {note!r}")

    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    stem = f"{name_prefix}-{cid}"
    zeros_path = outdir / f"{stem}-zeros.tif"
    nan_path = outdir / f"{stem}-nan.tif"
    zeros_zip = outdir / f"{stem}-zeros.zip"
    nan_zip = outdir / f"{stem}-nan.zip"

    # 1. Write -zeros.tif (0.0 outside footprint, nodata=None -> whole-array finite in [0,1])
    arr_zeros = np.zeros(footprint.shape, dtype=np.float32)
    arr_zeros[footprint] = inside
    prof_zeros = base_profile.copy()
    prof_zeros.update(count=1, dtype="float32", nodata=None, compress="deflate", predictor=3)
    with rasterio.open(zeros_path, "w", **prof_zeros) as dst:
        dst.write(arr_zeros, 1)
        dst.set_band_description(1, "fault probability")

    # 2. Write -nan.tif (NaN outside footprint, nodata=NaN)
    arr_nan = np.full(footprint.shape, np.nan, dtype=np.float32)
    arr_nan[footprint] = inside
    prof_nan = base_profile.copy()
    prof_nan.update(count=1, dtype="float32", nodata=np.nan, compress="deflate", predictor=3)
    with rasterio.open(nan_path, "w", **prof_nan) as dst:
        dst.write(arr_nan, 1)
        dst.set_band_description(1, "fault probability")

    # 3. Write .zip archives
    for tif_p, zip_p in ((zeros_path, zeros_zip), (nan_path, nan_zip)):
        with zipfile.ZipFile(zip_p, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            zf.write(tif_p, arcname=tif_p.name)

    # 4. Re-open saved bytes and run full template validation
    val_zeros = validate_audit(zeros_path, tpl_path, strict_zero_outside=True)
    val_nan = validate_audit(nan_path, tpl_path, strict_zero_outside=False)
    if not val_zeros["pass"] or not val_nan["pass"]:
        raise RuntimeError(f"Saved GeoTIFF failed validation: zeros={val_zeros['pass']}, nan={val_nan['pass']}")

    emitted_pos = int((inside > 0.0).sum())
    receipt = {
        "submission_name": stem,
        "content_id": cid,
        "note": note,
        "note_chars": len(note),
        "emitted_positive_pixels": emitted_pos,
        "footprint_cells": int(footprint.sum()),
        "emitted_fraction_of_footprint": round(float(emitted_pos / footprint.sum()), 6),
        "zeros_tif": {
            "file": str(zeros_path.relative_to(ROOT)) if zeros_path.is_relative_to(ROOT) else str(zeros_path),
            "bytes": zeros_path.stat().st_size,
            "sha256": sha256_file(zeros_path),
            "zip": str(zeros_zip.relative_to(ROOT)) if zeros_zip.is_relative_to(ROOT) else str(zeros_zip),
            "zip_bytes": zeros_zip.stat().st_size,
            "zip_sha256": sha256_file(zeros_zip),
            "validator": val_zeros,
        },
        "nan_tif": {
            "file": str(nan_path.relative_to(ROOT)) if nan_path.is_relative_to(ROOT) else str(nan_path),
            "bytes": nan_path.stat().st_size,
            "sha256": sha256_file(nan_path),
            "zip": str(nan_zip.relative_to(ROOT)) if nan_zip.is_relative_to(ROOT) else str(nan_zip),
            "zip_bytes": nan_zip.stat().st_size,
            "zip_sha256": sha256_file(nan_zip),
            "validator": val_nan,
        },
        "validator_summary": {
            "no_nan_inside_footprint": bool(val_zeros["in_range_0_1_footprint"] and val_nan["in_range_0_1_footprint"]),
            "values_in_0_1_footprint": bool(val_zeros["in_range_0_1_footprint"] and val_nan["in_range_0_1_footprint"]),
            "values_in_0_1_whole_array_zeros_variant": bool(val_zeros["in_range_0_1_whole_array"]),
            "crs_match": bool(val_zeros["epsg"] == 32611 and val_nan["epsg"] == 32611),
            "shape_match": bool(val_zeros["shape_match"] and val_nan["shape_match"]),
            "transform_match": bool(val_zeros["transform_match"] and val_nan["transform_match"]),
            "bounds_match": bool(val_zeros["bounds_match"] and val_nan["bounds_match"]),
            "all_checks_pass": bool(val_zeros["pass"] and val_nan["pass"]),
        },
    }
    (outdir / f"receipt-{stem}.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    (outdir / f"note-{stem}.txt").write_text(note + "\n", encoding="utf-8")
    return receipt
