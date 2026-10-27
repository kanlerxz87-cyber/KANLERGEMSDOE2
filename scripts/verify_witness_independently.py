#!/usr/bin/env python3
"""Recheck the literal lattice stop with a Euclidean distance transform.

This intentionally does not call the release auditor's binary-dilation code.
It only checks the pinned owner-mirror inputs, exact candidate bytes and their
geometry. It does not fit a model, establish a score, prove the full registry,
contact the portal, or authorize a weekly slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/independent_witness_20261027.json")
    args = ap.parse_args(argv)
    data = args.data_dir or data_dir()
    manifest = json.loads((ROOT / "registry/data_manifest.json").read_text())
    audit = json.loads((ROOT / "evidence/release_recheck_20261027.json").read_text())
    reg = json.loads((ROOT / "registry/comparison_registry.json").read_text())
    witness_sha = audit["preflight"]["witness_sha256"]
    witness_name = audit["preflight"]["witness_filename"]
    if not any(x.get("filename") == witness_name and x.get("sha256") == witness_sha for x in reg["entries"]):
        raise ValueError("Witness is not registered")
    inputs = {}
    for row in manifest["files"]:
        if row["id"] == "sample_submission" or row["id"] == "labels" or row["sha256"] == witness_sha:
            path = data / row["dest"]
            if not path.is_file() or sha(path) != row["sha256"]:
                raise ValueError(f"Missing or hash-mismatched mirror: {row['dest']}")
            inputs["witness" if row["sha256"] == witness_sha else row["id"]] = path
    if set(inputs) != {"sample_submission", "labels", "witness"}:
        raise ValueError("Incomplete manifest reference inputs")

    with rasterio.open(inputs["sample_submission"]) as ds:
        if ds.count != 1:
            raise ValueError("Template must have one band")
        grid = (ds.shape, ds.crs, ds.transform)
        foot = np.isfinite(ds.read(1))
    with rasterio.open(inputs["witness"]) as ds:
        if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
            raise ValueError("Witness grid mismatch")
        witness_array = ds.read(1)
    if not np.isfinite(witness_array[foot]).all() or not np.isin(witness_array[foot], [0, 1]).all():
        raise ValueError("Witness must be finite and binary inside footprint")
    witness = foot & (witness_array > 0)
    if not witness.any():
        raise ValueError("Empty witness")
    # EDT uses a different algorithm than the audit's 29-cell binary dilation.
    near = distance_transform_edt(~witness) <= 3.0
    coverage = int((foot & near).sum())
    uncovered = int((foot & ~near).sum())
    budget = audit["preflight"]["candidate_dot_budget"]
    minimum = max(0, budget - uncovered)
    independently_recomputed = {
        "footprint_pixels": int(foot.sum()), "covered_pixels_within_3px": coverage,
        "uncovered_pixels": uncovered, "candidate_dot_budget": budget,
        "minimum_overlapping_dots": minimum, "minimum_directional_overlap": minimum / budget,
        "forced_duplicate": minimum * 10 > budget * 7,
    }
    for key, value in independently_recomputed.items():
        if audit["preflight"][key] != value:
            raise AssertionError(f"Independent witness mismatch for {key}")

    candidates = []
    for name_part in ("-dslup-", "-htcads-", "-darp-", "-ecpu-"):
        row = next(r for r in audit["all_local_candidate_artifacts"] if name_part in r["file"])
        path = ROOT / "docs/downloads" / row["file"]
        if sha(path) != row["sha256"]:
            raise ValueError(f"Candidate SHA-256 mismatch: {path.name}")
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != grid or ds.count != 1:
                raise ValueError(f"Candidate grid mismatch: {path.name}")
            arr = ds.read(1)
        dots = foot & np.isfinite(arr) & (arr > 0)
        count = int(dots.sum())
        overlap = int((dots & near).sum())
        if count != row["inside_positive_pixels"] or overlap != row["witness_overlap_dots"]:
            raise AssertionError(f"Independent candidate counts disagree: {path.name}")
        candidates.append({"file": path.name, "sha256": row["sha256"], "dots": count,
                           "within_3px": overlap, "overlap_fraction": overlap / count,
                           "duplicate": overlap * 10 > count * 7})

    result = {
        "schema": "gems.independent-witness-review.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "Euclidean distance transform, compared against independently implemented binary dilation audit",
        "source": "Hash-pinned owner mirrors, not authenticated organizer data",
        "witness_sha256": witness_sha,
        "independent_preflight": independently_recomputed,
        "candidates": candidates,
        "matches_release_recheck": True,
        "complete_registry_replayed": False,
        "holdout_or_leakage_replayed": False,
        "portal_or_quota_checked": False,
        "ok_to_submit": False,
        "verdict": "negative",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
