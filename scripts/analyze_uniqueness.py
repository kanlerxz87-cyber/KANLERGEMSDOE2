#!/usr/bin/env python3
"""Read-only analysis: directional 3-px overlap of candidate dot sets vs locally
available registry rasters, plus surface rank correlation. Writes only to evidence/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import footprint, paths  # noqa: E402

REGISTRY = json.loads((ROOT / "registry" / "comparison_registry.json").read_text())["entries"]


def local_paths(entry):
    outs = []
    # Match by filename against docs/downloads (historical submissions are stored
    # there) and by manifest dest against data/.
    fname = entry.get("filename", "")
    if fname:
        p = ROOT / "docs" / "downloads" / fname
        if p.is_file():
            outs.append(p)
    cache = entry.get("cache_path", "")
    if cache:
        # cache_path like 'scored/name.tif' or 'docs/downloads/name.tif'
        if cache.startswith("docs/downloads/"):
            p = ROOT / cache
            if p.is_file():
                outs.append(p)
        else:
            p = ROOT / "data" / cache
            if p.is_file():
                outs.append(p)
            p2 = ROOT / "data" / Path(cache).name
            if p2.is_file():
                outs.append(p2)
    # dedupe preserve order
    seen = set()
    uniq = []
    for p in outs:
        if p not in seen:
            uniq.append(p); seen.add(p)
    return uniq


def dots_of(arr, fp):
    return fp & np.isfinite(arr) & (arr > 0)


def overlap(cand, ref):
    cp = np.argwhere(cand)
    rp = np.argwhere(ref)
    if not len(cp) or not len(rp):
        return 0.0, 0.0
    fwd = float(np.mean(cKDTree(rp).query(cp)[0] <= 3.0))
    rev = float(np.mean(cKDTree(cp).query(rp)[0] <= 3.0))
    return fwd, rev


def spearman(a, b, fp):
    ids = np.flatnonzero(fp)
    af = a.ravel()[ids]
    bf = b.ravel()[ids]
    m = np.isfinite(af) & np.isfinite(bf)
    if not m.any():
        return None
    af, bf = af[m], bf[m]
    ra = rankdata(af)
    rb = rankdata(bf)
    if np.ptp(ra) == 0 or np.ptp(rb) == 0:
        return None
    da, db = ra - ra.mean(), rb - rb.mean()
    return float(np.dot(da, db) / np.sqrt(np.dot(da, da) * np.dot(db, db)))


def main():
    fp = footprint.load_footprint()
    H, W = fp.shape
    with rasterio.open(paths.LABELS_PATH) as s:
        labels = (s.read(1) > 0) & fp

    dist = distance_transform_edt(~labels)
    sets = {
        "on_fault": fp & (dist <= 1.5),
        "near_fault_400m": fp & (dist <= 4.0),
        "off_catalogue_800m": fp & (dist > 8.0),
    }
    rng = np.random.default_rng(7)
    sampled = {}
    for name, mask in sets.items():
        ids = np.flatnonzero(mask)
        n = min(len(ids), 20000)
        pick = rng.choice(ids, size=n, replace=False) if len(ids) else ids
        m = np.zeros(fp.shape, bool)
        m.ravel()[pick] = True
        sampled[name] = m

    # Load available registry rasters (binary dots + array for rho).
    reg = []
    tried = 0
    for entry in REGISTRY:
        for p in local_paths(entry):
            tried += 1
            try:
                with rasterio.open(p) as ds:
                    a = ds.read(1)
                if ds.shape != fp.shape:
                    print("shape mismatch", p.name, ds.shape); continue
                ref = dots_of(a, fp)
                if not ref.any():
                    print("no dots", p.name); continue
                reg.append((entry.get("id", entry.get("sha256", ""))[:12], entry["filename"], ref, a))
                break
            except Exception as exc:
                print("FAIL", p.name, type(exc).__name__, exc)
                continue
    print(f"registry rasters available: {len(reg)} (tried {tried})")

    print(f"{'candidate':18s} {'registry':44s} {'fwd_ovlp':>10s} {'rev_ovlp':>10s} {'rho':>9s}")
    worst = {}
    for cname, cmask in sampled.items():
        surf = cmask.astype(np.float64)
        for rid, fname, ref, arr in reg:
            fwd, rev = overlap(cmask, ref)
            rho = spearman(surf, arr, fp)
            print(f"{cname:18s} {fname:44s} {fwd:10.4f} {rev:10.4f} "
                  f"{'nan' if rho is None else f'{rho:+.3f}':>9s}")
            worst[fname] = max(worst.get(fname, 0.0), fwd)

    print("\nWorst fwd overlap per registry raster:")
    for k, v in sorted(worst.items(), key=lambda x: -x[1])[:8]:
        print(f"  {k}: {v:.4f}")


if __name__ == "__main__":
    main()
