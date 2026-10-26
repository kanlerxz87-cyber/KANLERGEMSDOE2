#!/usr/bin/env python3
"""Re-open one TIFF with the pinned shared validator; never approve a slot.

This supplements, but does not fork or edit, GEMSDOE33's validator. It detects
inside-footprint GDAL masks and distinguishes the template's null-outside
encoding from the troubleshooting zero-outside encoding.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio

from lattice_feasibility import TEMPLATE_SHA, sha256

# Source is pinned to GEMSDOE33 commit 1d99d73f; this is not a private fork.
SHARED_VALIDATOR_SHA = "e7b822377038b0449c40568a5af8d9d78e804893f23f2b834a5e793ed426f80a"


def inspect(candidate: Path, template: Path, shared: Path, *, verify_template_pin: bool = True) -> dict:
    candidate, template, shared = map(Path, (candidate, template, shared))
    shared_validator = shared / 'scripts' / 'validate_submission.py'
    if not shared_validator.is_file() or sha256(shared_validator) != SHARED_VALIDATOR_SHA:
        raise ValueError('pinned shared template validator missing or modified; run bootstrap')
    template_before = sha256(template)
    if verify_template_pin and template_before != TEMPLATE_SHA:
        raise ValueError('sample template does not match the pinned owner-mirror bytes')
    if candidate.suffix.lower() != '.tif':
        raise ValueError('candidate must be a .tif file; this validator does not accept archives')
    before = sha256(candidate)
    proc = subprocess.run([sys.executable, str(shared_validator), '--submission', str(candidate.resolve()),
                           '--template', str(template.resolve())], text=True, capture_output=True)
    if proc.returncode not in (0, 2):
        raise RuntimeError('Shared validator could not read the candidate: ' + proc.stderr.strip())
    try:
        shared_report = json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError('Shared validator did not return a JSON report') from exc
    after = sha256(candidate)
    if before != after or shared_report.get('sha256') != before:
        raise RuntimeError('candidate bytes changed during validation')

    with rasterio.open(template) as t, rasterio.open(candidate) as ds:
        # A single-TIFF upload cannot rely on .msk, .aux.xml, or other GDAL
        # sidecars which are not covered by the file's SHA-256.
        template_dependencies = [name for name in t.files if Path(name).resolve() != template.resolve()]
        candidate_dependencies = [name for name in ds.files if Path(name).resolve() != candidate.resolve()]
        footprint = np.isfinite(t.read(1))
        shape_match = ds.shape == t.shape
        driver = ds.driver
        if shape_match:
            arr = ds.read(1)
            # GDAL validity mask matters independently of the underlying float.
            invalid = ds.read_masks(1) == 0
            inside = arr[footprint]
            outside = arr[~footprint]
            inside_masked = int(invalid[footprint].sum())
            inside_nonfinite = int((~np.isfinite(inside)).sum())
            finite_inside = np.isfinite(inside)
            inside_out_of_range = int(((inside[finite_inside] < 0) | (inside[finite_inside] > 1)).sum())
            null_outside = bool(np.all(np.isnan(outside) | invalid[~footprint]))
            all_finite = bool(np.isfinite(arr).all())
        else:
            inside_masked = inside_nonfinite = inside_out_of_range = None
            null_outside = all_finite = False
    if sha256(candidate) != before or sha256(template) != template_before or sha256(shared_validator) != SHARED_VALIDATOR_SHA:
        raise RuntimeError('candidate, template, or shared validator bytes changed during validation')
    local_pass = bool(shared_report.get('pass') and driver == 'GTiff' and shape_match
                      and not candidate_dependencies and not template_dependencies
                      and inside_masked == 0 and inside_nonfinite == 0
                      and inside_out_of_range == 0 and null_outside)
    return {
        'candidate': str(candidate), 'candidate_sha256': before,
        'template_sha256': template_before, 'shared_validator_sha256': SHARED_VALIDATOR_SHA,
        'shared_validator_source': 'GEMSDOE33 commit 1d99d73f, scripts/validate_submission.py',
        'shared_validator_result': shared_report,
        'driver': driver, 'candidate_external_dependencies': candidate_dependencies,
        'template_external_dependencies': template_dependencies,
        'inside_masked_count': inside_masked,
        'inside_nonfinite_count': inside_nonfinite, 'inside_out_of_range_count': inside_out_of_range,
        'matches_sample_null_mask_outside': null_outside, 'whole_array_finite': all_finite,
        'local_format_pass': local_pass,
        'format_only_no_organizer_acceptance': True,
        'scientific_and_registry_gates_checked': False,
        'weekly_slot_approved': False,
        'ok_to_submit': False,
        'outside_policy_note': 'Zero-outside is troubleshooting only; it does not match the sample null mask. Portal acceptance is unverified.',
    }


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--template', type=Path, required=True)
    p.add_argument('--shared', type=Path, default=Path('.cache/GEMSDOE33'))
    p.add_argument('--out', type=Path)
    a = p.parse_args()
    try:
        result = inspect(a.candidate, a.template, a.shared)
    except (OSError, ValueError, RuntimeError) as exc:
        result = {'local_format_pass': False, 'ok_to_submit': False, 'error': str(exc)}
    text = json.dumps(result, indent=2, allow_nan=False) + '\n'
    if a.out:
        a.out.parent.mkdir(parents=True, exist_ok=True)
        a.out.write_text(text)
    print(text, end='')
    return 0 if result['local_format_pass'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
