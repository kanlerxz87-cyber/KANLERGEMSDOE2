#!/usr/bin/env python3
"""Reuse vendored template evaluator (GEMSDOE32-HIDE-RECOVER-v3.0 + SGMC-CAL-v3.0).
Scores a binary mask .npy or .tif against withheld catalogue segments (visible-only B gate)
and off-catalogue SGMC. Every number produced is HOLDOUT-DTI, never an organizer score.
"""
import argparse, json, pathlib, sys
import numpy as np, rasterio
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT/"src"))
from gems import holdout

def load_mask(p, foot):
    if p.suffix==".npy": a=np.load(p); return (a>0)&foot
    with rasterio.open(p) as ds: a=ds.read(1)
    return np.isfinite(a)&(a>0)&foot

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("candidates", nargs="+", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, required=True); ap.add_argument("--data-dir", type=pathlib.Path, default=ROOT/"data")
    a=ap.parse_args()
    ctx=holdout.load_holdout_context(a.data_dir)
    out={}
    for p in a.candidates:
        mask=load_mask(p, ctx.foot)
        r=holdout.evaluate_visible_gated_holdout(mask, ctx, b_gate_px=2.0, name=p.stem)
        # strip large fields
        keep={k:v for k,v in r.items() if k not in ("cells",)}
        out[p.name]=keep
        print(p.name, json.dumps(keep)[:800], flush=True)
    a.out.parent.mkdir(parents=True, exist_ok=True); a.out.write_text(json.dumps(out,indent=2,default=float))
if __name__=="__main__": main()
