#!/usr/bin/env python3
"""Compare historical GEMSDOE31 and GEMSDOE32 dot lineage; never score or submit."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from validate_raster import sha256_file

ROOT = Path(__file__).resolve().parents[1]


def compare_lineage(base, champion, catalogue, footprint):
    base, champion = np.asarray(base), np.asarray(champion)
    catalogue, footprint = np.asarray(catalogue, bool), np.asarray(footprint, bool)
    if base.ndim != 2 or base.shape != champion.shape or base.shape != catalogue.shape or base.shape != footprint.shape or not footprint.any():
        raise ValueError("A nonempty aligned footprint and rasters are required")
    if not np.isin(base[footprint], [0, 1]).all() or not np.isin(champion[footprint], [0, 1]).all():
        raise ValueError("Historical predictions must be binary in the footprint")
    known = catalogue & footprint
    if not known.any():
        raise ValueError("A nonempty known-fault catalogue is required")
    original = footprint & (base > 0)
    result = footprint & (champion > 0)
    removed = original & ~result
    added = result & ~original
    distance = distance_transform_edt(~known)
    predicted_removal = original & (distance <= 2.0)
    return {
        "base_positive_pixels": int(original.sum()),
        "champion_positive_pixels": int(result.sum()),
        "removed_pixels": int(removed.sum()), "added_pixels": int(added.sum()),
        "removed_within_2px_of_catalogue": int((removed & (distance <= 2.0)).sum()),
        "base_within_2px_of_catalogue": int(predicted_removal.sum()),
        "difference_from_exact_2px_catalogue_prune": int((removed ^ predicted_removal).sum()),
        "equals_exact_2px_pruned_base": bool(not added.any() and not (removed ^ predicted_removal).any()),
        "removed_at_exact_known_fault_pixels": int((removed & (distance == 0)).sum()),
        "removed_at_1px": int((removed & (distance == 1)).sum()),
        "removed_at_sqrt_2px": int((removed & np.isclose(distance, np.sqrt(2), rtol=0, atol=1e-12)).sum()),
        "removed_at_2px": int((removed & (distance == 2)).sum()),
        "distance": "Euclidean pixel-center distance on the 100 m grid; <= 2 pixels inclusive",
    }


def run():
    pins = {r["id"]: r for r in json.loads((ROOT / "research/input_pins.json").read_text())["records"]}
    manifest = {r["site"]: r for r in json.loads((ROOT / "research/raster_manifest.json").read_text())}
    paths = {
        "sample": (ROOT / pins["sample_submission"]["destination"], pins["sample_submission"]["sha256"]),
        "catalogue": (ROOT / pins["labels"]["destination"], pins["labels"]["sha256"]),
        "base": (ROOT / manifest["GEMSDOE31"]["local"], manifest["GEMSDOE31"]["sha256"]),
        "champion": (ROOT / manifest["GEMSDOE32"]["local"], manifest["GEMSDOE32"]["sha256"]),
    }
    arrays, grid = {}, None
    for name, (path, expected) in paths.items():
        if sha256_file(path) != expected:
            raise ValueError(f"Pinned raster checksum mismatch: {name}")
        with rasterio.open(path) as src:
            current = (src.shape, src.crs, src.transform)
            if src.count != 1 or src.crs is None or (grid is not None and current != grid):
                raise ValueError(f"Grid mismatch: {name}")
            grid = current
            arrays[name] = src.read(1)
            if name == "sample":
                footprint = np.isfinite(arrays[name]) & (src.read_masks(1) > 0)
    data = compare_lineage(arrays["base"], arrays["champion"], arrays["catalogue"] > 0, footprint)
    return {"audit_version": "h33-lineage-v1", "scope": "These exact two selected peer rasters and peer-mirrored known catalogue; no organizer receipt.",
            "inputs_sha256": {name: expected for name, (_, expected) in paths.items()},
            "base": "GEMSDOE31 selected historical raster", "champion": "GEMSDOE32 selected H33 B2 historical raster",
            "comparison": data,
            "reported_scores": {"GEMSDOE31": 0.2708, "GEMSDOE32": 0.2778,
                                "label": "Unverified owner reports; no organizer score-to-hash receipts found."},
            "interpretation": "Exact raster lineage does not establish that pruning caused the reported score difference; hidden truth and matching organizer receipts are unavailable.",
            "experiments_run": 0, "ok_to_submit": False}


def main():
    result = run()
    (ROOT / "evidence/h33_lineage_20261026.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
