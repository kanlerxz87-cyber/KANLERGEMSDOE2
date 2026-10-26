#!/usr/bin/env python3
"""Guarded adapter to the shared, literal all-entry novelty checker.

Use --stage surface before placing dots. Final dots require a passing surface
receipt bound to the same surface and registry manifest. A receipt is evidence,
not proof that a registry is complete or that a submission may be uploaded.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor/template/src"))
from gems.novelty import compare_registry  # noqa: E402
if __package__:
    from .registry_guard import require_candidate_generation_allowed
    from .restore_competition_data import sha256_file
else:
    from registry_guard import require_candidate_generation_allowed
    from restore_competition_data import sha256_file


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", required=True, choices=("surface", "dots"))
    parser.add_argument("--surface", required=True, type=Path)
    parser.add_argument("--dots", type=Path)
    parser.add_argument("--surface-receipt", type=Path)
    parser.add_argument("--registry", required=True, type=Path,
                        help="JSON array of shared-template entries, including footprint_sha256")
    parser.add_argument("--registry-root", required=True, type=Path)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    require_candidate_generation_allowed(args.data_dir)
    entries = json.loads(args.registry.read_text())
    if not isinstance(entries, list) or not entries:
        raise ValueError("A nonempty registry manifest is required")
    registry_root = args.registry_root.resolve()
    ids = set()
    for entry in entries:
        if not all(entry.get(key) for key in ('id', 'file', 'cache_path', 'sha256', 'footprint_sha256')):
            raise ValueError("Every registry entry needs identity, byte hash and footprint hash")
        path = (registry_root / entry['cache_path']).resolve()
        if not path.is_relative_to(registry_root) or entry['id'] in ids or sha256_file(path) != entry['sha256']:
            raise ValueError(f"Invalid or duplicate registry entry: {entry['id']}")
        ids.add(entry['id'])
    surface_sha, registry_sha = sha256_file(args.surface), sha256_file(args.registry)
    sample_path = args.data_dir / "sample_submission.tif"
    with rasterio.open(sample_path) as sample:
        footprint = np.isfinite(sample.read(1))
    surface = np.load(args.surface, allow_pickle=False)
    if args.stage == "dots":
        if not args.dots or not args.surface_receipt:
            raise ValueError("Final-dot check requires dots and a prior surface receipt")
        prior = json.loads(args.surface_receipt.read_text())
        if not prior.get("passed") or prior.get("stage") != "surface_before_placement" or prior.get("surface_sha256") != surface_sha or prior.get("registry_manifest_sha256") != registry_sha:
            raise ValueError("Missing/failed/mismatched pre-placement surface receipt")
        dots = np.load(args.dots, allow_pickle=False)
        if dots.shape != footprint.shape or not np.isin(dots, [0, 1]).all():
            raise ValueError("Final dots must be a finite aligned binary array")
        result = compare_registry(dots.astype(np.float32), footprint, entries, args.registry_root,
                                  dots=dots.astype(bool), template_path=sample_path)
        result["dots_sha256"] = sha256_file(args.dots)
    else:
        if args.dots or args.surface_receipt:
            raise ValueError("Do not place/load final dots before the surface gate")
        result = compare_registry(surface, footprint, entries, args.registry_root,
                                  template_path=sample_path)
    result.update({"surface_sha256": surface_sha, "registry_manifest_sha256": registry_sha,
                   "registry_completeness": "not independently certified by this comparison",
                   "authorized_to_submit": False})
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    if not result["passed"]:
        raise SystemExit("DUPLICATE OR UNDEFINED: stop the lane")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
