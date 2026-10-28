#!/usr/bin/env python3
"""KG2-S3 step 2 (preregistered design selection): leave-site-out CV of LLI designs.

Fits the log-additive Live-Ledger-Inversion density on USER-REPORTED live scores of 123 unique pinned
rasters, for 4 preregistered designs x 5 ridge strengths, and selects the (design, ridge) with the
lowest leave-SITE-out MAE (sites share lineages, so leave-one-raster-out would be optimistic).
Output: evidence/kg2s3_lli_design_cv.json.  Every number about a new raster is a PROJECTION.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32 import ledger_inversion as li  # noqa: E402
from gems32 import lope  # noqa: E402
from gems32.ledger_inversion import StrataSpec  # noqa: E402
from gems32.paths import data_dir, work_dir  # noqa: E402

# Coarse remaps (full-level code -> coarse code); reference level stays code 0.
DREF_COARSE = np.array([0, 1, 1, 2, 2, 3, 3, 4, 4])          # >15 | <=1 | 1.4-3 | 3.2-5 | 5-15
DREF_COARSE_LABELS = [">15", "<=1", "1.4-3", "3.2-5", "5-15"]
DESIGNS = {
    "C0_dcat_x_dH19": ["dcat", "dref"],
    "C1_dcat_x_dH19_x_phys": ["dcat", "dref", "phys"],
    "C2_dcat_x_dH19_x_phys_x_shear": ["dcat", "dref", "phys", "strain"],
    "C3_dcat_x_phys_x_shear": ["dcat", "phys", "strain"],
}
RIDGES = [1e-3, 1e-2, 3e-2, 1e-1, 3e-1]
FACTOR_INFO = {
    "dcat": (0, None, lope.DCAT_LABELS, "d_catalogue_px"),
    "dref": (1, DREF_COARSE, DREF_COARSE_LABELS, "d_H19-5_px"),
    "phys": (2, None, lope.PHYS_LABELS, "phys_scarp"),
    "strain": (3, None, lope.STRAIN_LABELS, "geod_shear"),
}


def load():
    ddir, wdir = data_dir(), work_dir() / "kg2s3"
    z = np.load(wdir / "ledger_design.npz")
    f = np.load(wdir / "factors.npz")
    meta = json.loads((wdir / "ledger_meta.json").read_text())
    with rasterio.open(ddir / "sample_submission.tif") as s:
        foot = np.isfinite(s.read(1))
    with rasterio.open(ddir / "labels.tif") as s:
        cat = (s.read(1) > 0) & foot
    fm = {k: f[k] for k in f.files}
    return z, fm, meta, foot & ~cat


def design_spec(fm, active, factors):
    levels, n_levels, labels, names = [], [], [], []
    for fac in factors:
        idx, remap, labs, name = FACTOR_INFO[fac]
        raw = [fm["lv_dcat"], fm["lv_dref"], fm["lv_phys"], fm["lv_strain"]][idx]
        lv = remap[raw] if remap is not None else raw
        levels.append(lv.astype(np.int8)); n_levels.append(len(labs)); labels.append(labs); names.append(name)
    return StrataSpec(names=names, levels=levels, n_levels=n_levels, level_labels=labels, active=active)


def collapse(M, full: StrataSpec, factors):
    """Map full 648-strata design columns onto a (possibly coarser) design exactly."""
    lv = full.stratum_levels
    code = np.zeros(full.n_strata, np.int64)
    mult = 1
    for fac in factors:
        idx, remap, labs, _ = FACTOR_INFO[fac]
        l = lv[:, idx].astype(np.int64)
        if remap is not None:
            l = remap[l]
        code += l * mult
        mult *= len(labs)
    out = np.zeros((M.shape[0], mult))
    for j in range(mult):
        sel = code == j
        if sel.any():
            out[:, j] = M[:, sel].sum(axis=1)
    return out


def main() -> int:
    t0 = time.time()
    z, fm, meta, active = load()
    A, B, N, S, sizes = z["A"], z["B"], z["N"], z["S"], z["sizes"]
    full = lope.full_spec(fm, active)
    groups = np.array([m["site"] for m in meta])
    results = {}
    for dname, factors in DESIGNS.items():
        sp = design_spec(fm, active, factors)
        Am, Bm = collapse(A, full, factors), collapse(B, full, factors)
        assert np.allclose(collapse(sizes[None, :], full, factors)[0], sp.sizes)
        rows = []
        for ridge in RIDGES:
            r = li.loo(Am, Bm, N, S, sp, groups=groups, ridge=ridge)
            f = li.fit(Am, Bm, N, S, sp, ridge=ridge)
            rows.append({"ridge": ridge, "leave_site_out_mae": r["mae"], "leave_site_out_rmse": r["rmse"],
                         "leave_site_out_spearman": r["spearman"], "leave_site_out_abs_err_q90": r["abs_err_q90"],
                         "leave_site_out_max_abs_err": r["max_abs_err"],
                         "in_sample_mae": float(np.mean(np.abs(f["pred"] - S))), "g_total": f["g"],
                         "factor_effects": li.factor_effects(f["theta"], sp)})
            print(f"{dname:34s} ridge={ridge:<6} LSO-MAE={r['mae']:.4f} rho={r['spearman']:.3f} "
                  f"q90={r['abs_err_q90']:.4f} G={f['g']:.0f}  ({time.time()-t0:.0f}s)", flush=True)
        results[dname] = {"factors": factors, "n_strata": sp.n_strata, "n_params": li.n_params(sp), "grid": rows}
    best = min(((d, r) for d, v in results.items() for r in v["grid"]), key=lambda x: x[1]["leave_site_out_mae"])
    out = {
        "schema": "kg2s3.lli_design_cv.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "instrument": "LLI log-additive (src/gems32/ledger_inversion.fit) on exact design rows; leave-SITE-out CV",
        "score_evidence_class": "USER-REPORTED live scores (GEMSDOE32 ledger + 2026-10-27 brief additions); no organizer receipts",
        "n_unique_rasters": int(len(S)), "n_sites": int(len(set(groups))),
        "selection_rule": "lowest leave-site-out MAE over preregistered designs x ridges",
        "selected": {"design": best[0], "ridge": best[1]["ridge"], "leave_site_out_mae": best[1]["leave_site_out_mae"],
                     "leave_site_out_spearman": best[1]["leave_site_out_spearman"],
                     "leave_site_out_abs_err_q90": best[1]["leave_site_out_abs_err_q90"]},
        "designs": results,
    }
    (ROOT / "evidence/kg2s3_lli_design_cv.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    print("SELECTED", out["selected"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
