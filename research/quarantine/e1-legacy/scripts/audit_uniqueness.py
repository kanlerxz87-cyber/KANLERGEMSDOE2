#!/usr/bin/env python3
"""Uniqueness: surface Spearman (sampled) vs registry + final-dot 3px overlap vs every registry raster.
Registry = 9 focus-site best genuine scored submissions (data/registry). Calibration lattice probes excluded
and flagged separately in the run card (literal lattice blocks any dense map: max dist to a 5px lattice <=3.54px).
"""
import argparse, json, pathlib, sys
import numpy as np, rasterio
from scipy.ndimage import binary_dilation
from scipy.stats import spearmanr
ROOT=pathlib.Path(__file__).resolve().parents[1]

def load(p, foot):
    if p.suffix==".npy": a=np.load(p); return (a>0)&foot
    with rasterio.open(p) as ds: a=ds.read(1)
    return np.isfinite(a)&(a>0)&foot

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--surface", type=pathlib.Path, required=True); ap.add_argument("--dots", type=pathlib.Path, required=True); ap.add_argument("--out", type=pathlib.Path, required=True)
    a=ap.parse_args()
    with rasterio.open(ROOT/"data/sample_submission.tif") as ds: foot=np.isfinite(ds.read(1))
    surf=np.load(a.surface); dots=load(a.dots, foot)
    rng=np.random.default_rng(3); idx=np.argwhere(foot); sel=idx[rng.choice(len(idx),200000,replace=False)]
    sv=surf[sel[:,0],sel[:,1]]
    rows=[]
    for p in sorted((ROOT/"data/registry").glob("*.tif")):
        reg=load(p, foot); rv=reg[sel[:,0],sel[:,1]].astype(float)
        rho=float(spearmanr(sv,rv).statistic) if np.std(rv)>0 else 0.0
        near=binary_dilation(reg, iterations=3)
        overlap=float((dots & near).sum()/max(dots.sum(),1))
        rows.append({"registry":p.name,"surface_spearman":rho,"abs_surface_spearman":abs(rho),"dot_overlap_3px_frac":overlap,"registry_dots":int(reg.sum()),"duplicate_surface":bool(abs(rho)>0.90),"duplicate_dots":bool(overlap>0.70)})
        print(rows[-1], flush=True)
    out={"surface":str(a.surface),"dots":str(a.dots),"n_dots":int(dots.sum()),"max_abs_surface_spearman":max(r["abs_surface_spearman"] for r in rows),"max_dot_overlap_3px":max(r["dot_overlap_3px_frac"] for r in rows),"pass_surface":all(not r["duplicate_surface"] for r in rows),"pass_dots":all(not r["duplicate_dots"] for r in rows),"registry":rows}
    a.out.write_text(json.dumps(out,indent=2)); print(json.dumps({k:out[k] for k in out if k!="registry"},indent=2))
if __name__=="__main__": main()
