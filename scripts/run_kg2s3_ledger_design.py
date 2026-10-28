#!/usr/bin/env python3
"""KG2-S3 step 1: factor maps + exact LLI design rows for every USER-REPORTED scored raster.

Outputs (ignored work cache): $GEMS_WORK_DIR/kg2s3/factors.npz, ledger_design.npz.
Scores stay USER-REPORTED; this script fits nothing.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import lope  # noqa: E402
from gems32.ledger_inversion import design_row  # noqa: E402
from gems32.paths import data_dir, work_dir  # noqa: E402

H19_5 = "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif"


def load_grid(ddir: Path):
    with rasterio.open(ddir / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
        prof = s.profile
    with rasterio.open(ddir / "labels.tif") as s:
        cat = (s.read(1) > 0) & foot
    with rasterio.open(ddir / H19_5) as s:
        ref = (np.nan_to_num(s.read(1)) > 0) & foot
    return foot, cat, ref, prof


def read_pred(path: Path, shape, transform) -> np.ndarray | None:
    with rasterio.open(path) as s:
        if s.shape != shape or tuple(s.transform)[:6] != tuple(transform)[:6]:
            return None
        a = s.read(1).astype(np.float32)
        nd = s.nodata
    if nd is not None and np.isfinite(nd):
        a[a == nd] = np.nan
    return np.where(np.isfinite(a), a, 0.0).astype(np.float32)


def main() -> int:
    ddir, wdir = data_dir(), work_dir() / "kg2s3"
    wdir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    foot, cat, ref, prof = load_grid(ddir)
    fm = lope.build_factor_maps(ddir, foot, cat, ref)
    active = foot & ~cat
    spec = lope.full_spec(fm, active)
    np.savez_compressed(wdir / "factors.npz", lv_dcat=fm["lv_dcat"], lv_dref=fm["lv_dref"], lv_phys=fm["lv_phys"],
                        lv_strain=fm["lv_strain"], phys=fm["phys"], d_cat=fm["d_cat"], d_ref=fm["d_ref"])
    print(f"factor maps built in {time.time()-t0:.1f}s; strata={spec.n_strata}", flush=True)

    rec = json.loads((ROOT / "data/lb_ledger_fetch_receipt.json").read_text())
    rows = [r for r in rec["rows"] if r["status"] in ("present", "restored")]
    seen = {}
    A, B, N, S, meta = [], [], [], [], []
    for r in rows:
        key = r["sha256"]
        if key in seen:                # identical bytes reported twice: keep first, record alias
            meta[seen[key]]["aliases"].append(r["submission"])
            continue
        pred = read_pred(Path(r["local"]), foot.shape, prof["transform"])
        if pred is None:
            print("skip grid mismatch", r["submission"])
            continue
        if (pred[active] < -1e-6).any() or (pred[active] > 1 + 1e-6).any():
            print("skip out-of-range", r["submission"])
            continue
        d = design_row(pred, spec)
        seen[key] = len(meta)
        A.append(d["A"]); B.append(d["B"]); N.append(d["N"]); S.append(float(r["score"]))
        meta.append({"site": r["site"], "submission": r["submission"], "score": float(r["score"]),
                     "sha256": key, "dots": d["dots"], "binary": d["binary"], "aliases": []})
    A, B, N, S = map(np.asarray, (A, B, N, S))
    np.savez_compressed(wdir / "ledger_design.npz", A=A, B=B, N=N, S=S, sizes=spec.sizes)
    (wdir / "ledger_meta.json").write_text(json.dumps(meta, indent=1))
    print(f"design rows: {len(meta)} unique rasters in {time.time()-t0:.1f}s", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
