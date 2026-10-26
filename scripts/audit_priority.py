#!/usr/bin/env python3
"""Reopen the nine owner-reported historical files and measure their lineage.

These are reference files only, never recommended downloads or organizer receipts.
This is a raster audit, not a holdout evaluator or score predictor.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def binary_rho(a: np.ndarray, b: np.ndarray) -> float | None:
    n = a.size
    na, nb, both = int(a.sum()), int(b.sum()), int((a & b).sum())
    denom = na * (n-na) * nb * (n-nb)
    if denom == 0:
        return None
    return float((both*n - na*nb) / np.sqrt(float(denom)))


def audit(claims_path: Path, verified_path: Path, template_root: Path,
          sample_path: Path, labels_path: Path) -> dict:
    claims = json.loads(claims_path.read_text())["items"]
    registry = json.loads(verified_path.read_text())
    lookup = {(e["repo"], e["path"]): e for e in registry["rasters"]}
    with rasterio.open(sample_path) as s:
        sample = s.read(1)
        footprint = np.isfinite(sample)
        grid = (s.shape, s.crs, s.transform)
    with rasterio.open(labels_path) as s:
        if (s.shape, s.crs, s.transform) != grid:
            raise ValueError("Labels do not match mirror template")
        labels = (s.read(1) > 0) & footprint
    items, masks = [], {}
    for claim in claims:
        site = claim["site"]
        e = lookup.get((site, claim["path"]))
        if not e:
            raise ValueError(f"Historical file not in verified snapshot: {site}/{claim['path']}")
        local = template_root / e["local"]
        if sha256(local) != e["sha256"]:
            raise ValueError(f"Historical file hash mismatch: {local}")
        with rasterio.open(local) as s:
            if s.count != 1 or (s.shape, s.crs, s.transform) != grid:
                raise ValueError(f"Grid mismatch in {local}")
            a = s.read(1)
        vals = a[footprint]
        if not np.isfinite(vals).all() or not ((vals == 0) | (vals == 1)).all():
            raise ValueError(f"Non-binary or non-finite in-footprint value in {local}")
        masks[site] = (np.isfinite(a) & (a > 0) & footprint)
        items.append({"site": site, "owner_reported_unverified": claim["claim"],
                      "filename": Path(e["path"]).name, "repo_path": e["path"],
                      "ref": e["ref"], "sha256": e["sha256"],
                      "dots": int(masks[site].sum()),
                      "research_only_url": f"https://github.com/buffedlizard55-lab/{site}/blob/{e['ref']}/{e['path']}?raw=true",
                      "leaderboard_estimate": None, "ok_to_submit": False})
    for item in items:
        me = masks[item["site"]]
        worst = {"site": None, "overlap": -1.0}
        exact, rhos = [], []
        for other, theirs in masks.items():
            if other == item["site"]:
                continue
            if np.array_equal(me, theirs):
                exact.append(other)
            near = distance_transform_edt(~theirs) <= 3
            overlap = float(near[me].mean())
            rho = binary_rho(me[footprint], theirs[footprint])
            if rho is not None:
                rhos.append(abs(rho))
            if overlap > worst["overlap"]:
                worst = {"site": other, "overlap": overlap}
        item.update(exact_prediction_aliases=exact,
                    worst_other_focus_overlap=worst,
                    max_abs_spearman_other_focus=max(rhos, default=None),
                    unique_among_nine=(not exact and worst["overlap"] <= 0.7 and (not rhos or max(rhos) <= 0.9)))
    d28, b1, h33 = masks["GEMSDOE25"], masks["GEMSDOE31"], masks["GEMSDOE32"]
    dist = distance_transform_edt(~labels)
    lineage = {"d28_dots": int(d28.sum()), "b1_dots": int(b1.sum()), "b2_dots": int(h33.sum()),
               "d28_gt_1px_xor_b1": int(np.count_nonzero((d28 & (dist > 1.0)) ^ b1)),
               "d28_gt_2px_xor_b2": int(np.count_nonzero((d28 & (dist > 2.0)) ^ h33)),
               "d28_equals_30": bool(np.array_equal(d28, masks["GEMSDOE30"])),
               "sample_prediction_equals_labels": bool(np.array_equal((sample > 0) & footprint, labels))}
    return {"audited_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "evidence_scope": "Owner-mirror inputs and nine historical rasters, not organizer submission receipts",
            "grid": {"shape": list(grid[0]), "crs": str(grid[1]), "transform": list(tuple(grid[2])[:6]),
                     "footprint_pixels": int(footprint.sum())},
            "sample_sha256": sha256(sample_path), "labels_sha256": sha256(labels_path),
            "lineage": lineage, "sites": items}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--claims", type=Path, default=ROOT / "data/focus_claims.json")
    p.add_argument("--registry", type=Path, default=ROOT / ".cache/audit/verified-registry.json")
    p.add_argument("--template", type=Path, default=ROOT / ".cache/template32")
    p.add_argument("--data", type=Path, default=ROOT / ".cache/audit/core")
    p.add_argument("--out", type=Path, default=ROOT / "docs/data/focus-audit.json")
    a = p.parse_args()
    result = audit(a.claims, a.registry, a.template, a.data / "sample_submission.tif", a.data / "labels.tif")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"lineage": result["lineage"], "sites": result["sites"]}, indent=2))

if __name__ == "__main__":
    main()
