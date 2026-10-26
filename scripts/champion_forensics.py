#!/usr/bin/env python3
"""Byte-level autopsy of the 9 focus-site best rasters (education only).

Verifies from decoded pixels (not README prose): dot counts, set nesting,
distance-to-catalogue distributions (B-gate), nearest-neighbour spacing
(D-thinning), and kernel redundancy. Output: evidence/champion_forensics.json
All numbers are RASTER-AUDIT measurements, never scores.
"""
import json, pathlib, sys
import numpy as np, rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems.metric import credit_audit

def load(p):
    with rasterio.open(p) as ds:
        return np.isfinite(ds.read(1)) & (ds.read(1) > 0) if False else (lambda a: np.isfinite(a) & (a > 0))(ds.read(1))

def main():
    with rasterio.open(ROOT / "data/sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
    with rasterio.open(ROOT / "data/labels.tif") as ds:
        labels = (ds.read(1) > 0) & foot
    d_lab = distance_transform_edt(~labels)
    files = sorted((ROOT / "data/registry").glob("*.tif"))
    masks = {f.stem: load(f) & foot for f in files}
    out = {"label": "RASTER-AUDIT (decoded pixels; not scores)",
           "footprint_px": int(foot.sum()), "label_px": int(labels.sum()), "files": {}}
    for name, m in masks.items():
        pts = np.argwhere(m)
        nn = cKDTree(pts).query(pts, k=2)[0][:, 1] if len(pts) > 1 else np.array([])
        dl = d_lab[m]
        ca = credit_audit(m)
        out["files"][name] = {
            "dots": int(m.sum()),
            "frac_on_catalogue_d0": float((dl == 0).mean()),
            "frac_d_le1": float((dl <= 1).mean()),
            "frac_d_le2": float((dl <= 2).mean()),
            "min_dist_to_catalogue_px": float(dl.min()) if len(dl) else None,
            "nn_spacing_px": {"median": float(np.median(nn)), "p10": float(np.percentile(nn, 10)),
                              "frac_nn_lt3": float((nn < 3).mean()), "frac_nn_lt2": float((nn < 2).mean())},
            "kernel_redundancy_fraction": ca.redundancy_fraction,
            "mean_self_kernel": ca.mean_self_kernel,
        }
        print(name, out["files"][name]["dots"], "d<=2:", round(out["files"][name]["frac_d_le2"], 4),
              "nnmed:", round(out["files"][name]["nn_spacing_px"]["median"], 2), flush=True)
    # exact nesting / overlap among the D2.8 lineage + champion
    keys = list(masks)
    nest = {}
    for a in keys:
        for b in keys:
            if a < b:
                inter = int((masks[a] & masks[b]).sum())
                nest[f"{a}__{b}"] = {"exact_intersection": inter,
                                     "frac_of_a": inter / max(1, int(masks[a].sum())),
                                     "frac_of_b": inter / max(1, int(masks[b].sum())),
                                     "pixel_identical_in_footprint": bool(inter == int(masks[a].sum()) == int(masks[b].sum()))}
    out["pairwise_exact_overlap"] = nest
    (ROOT / "evidence/champion_forensics.json").write_text(json.dumps(out, indent=2))
    for k, v in nest.items():
        if v["frac_of_a"] > 0.85 or v["frac_of_b"] > 0.85:
            print("NESTED", k, {kk: (round(vv, 4) if isinstance(vv, float) else vv) for kk, vv in v.items()})

if __name__ == "__main__":
    main()
