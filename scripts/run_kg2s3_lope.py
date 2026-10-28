#!/usr/bin/env python3
"""KG2-S3 E2: LOPE emission (preregistered in knowledge/03_preregistered_hypotheses_kg2s3_20261027.md).

1. Fit the design selected by E1 (evidence/kg2s3_lli_design_cv.json) on all 123 USER-REPORTED rasters.
2. Unconstrained greedy emission (diagnostic) and uniqueness-constrained emission: a per-dot Lagrangian
   cost ``mu`` inside the 3-px halo of the binding registry reference (the public H19-5 ridge network,
   registry sha ef2ae808/ec1f9b56) is bisected until <= 68 % of dots fall inside that halo.
3. In-model projections (PROJECTION, quoting the leave-site-out error) for the candidate, the champion
   (G32) and DSLUP, all through the same exact design_row identity.
Outputs: $GEMS_WORK_DIR/kg2s3/lope_dots.npz, evidence/kg2s3_lope_emission.json.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import run_kg2s3_lli_cv as cv  # noqa: E402
from gems32 import ledger_inversion as li  # noqa: E402
from gems32 import lope  # noqa: E402
from gems32.paths import data_dir, docs_dir, work_dir  # noqa: E402

HALO_CAP = 0.68          # margin under the 0.70 protocol threshold
DISK3 = np.array([[1 if (dy * dy + dx * dx) <= 9 else 0 for dx in range(-3, 4)] for dy in range(-3, 4)], bool)


def halo3(mask: np.ndarray) -> np.ndarray:
    return binary_dilation(mask, structure=DISK3)


def fitted_lambda_map(design: str, ridge: float):
    z, fm, meta, active = cv.load()
    full = lope.full_spec(fm, active)
    fac = cv.DESIGNS[design]
    sp = cv.design_spec(fm, active, fac)
    Am, Bm = cv.collapse(z["A"], full, fac), cv.collapse(z["B"], full, fac)
    f = li.fit(Am, Bm, z["N"], z["S"], sp, ridge=ridge)
    lam_map = np.zeros(active.shape, np.float32)
    lam_map[active] = f["lambda"][sp.stratum[active]].astype(np.float32)
    return lam_map, f, sp, fm, active, meta


def project_mask(mask: np.ndarray, sp, lam: np.ndarray) -> dict:
    row = li.design_row(mask.astype(np.float32), sp)
    return li.project(row, sp, lam)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-bisect", type=int, default=5)
    args = ap.parse_args()
    t0 = time.time()
    sel = json.loads((ROOT / "evidence/kg2s3_lli_design_cv.json").read_text())["selected"]
    lam_map, f, sp, fm, active, meta = fitted_lambda_map(sel["design"], sel["ridge"])
    g_total = float(f["g"])
    ddir = data_dir()
    with rasterio.open(ddir / "scored" / "gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") as s:
        h19 = (np.nan_to_num(s.read(1)) > 0) & active
    halo = halo3(h19)
    print(f"[{time.time()-t0:.0f}s] lambda fitted ({sel['design']}, ridge {sel['ridge']}); G={g_total:.0f}", flush=True)

    # Hard per-reference novelty quota (protocol: <= 70 % of dots within 3 px of ONE registry raster).
    # Phase A: DTI-greedy inside the H19-5 halo.  Phase B: quota-filling greedy OUTSIDE the halo (best
    # marginal truth gain first, seeded with phase-A coverage).  Phase C: choose the inside budget N_in
    # (first-N truncation of phase A) that maximises the projected DTI with N_out = ceil(N_in*0.32/0.68).
    dots_in, info_in = lope.emit_threshold_greedy(lam_map, active & halo, g_total)
    proj_u = project_mask(dots_in, sp, f["lambda"])
    print(f"[{time.time()-t0:.0f}s] phase A (inside halo): n={dots_in.sum()} proj={proj_u['dti']:.4f}", flush=True)
    n_in_max = int(dots_in.sum())
    q_max = int(np.ceil(n_in_max * (1 - HALO_CAP) / HALO_CAP)) + 16
    dots_out, info_out = lope.emit_threshold_greedy(lam_map, active & ~halo, g_total, force=True, max_dots=q_max,
                                                    kmax0=info_in["kmax"])
    print(f"[{time.time()-t0:.0f}s] phase B (outside halo, forced quota): n={dots_out.sum()}", flush=True)
    trace = []
    best = None
    for frac_keep in (1.0, 0.85, 0.70, 0.55, 0.40, 0.30):
        n_in = int(round(n_in_max * frac_keep))
        n_out = int(np.ceil(n_in * (1 - HALO_CAP) / HALO_CAP))
        d = lope.first_n(dots_in, info_in, n_in) | lope.first_n(dots_out, info_out, n_out)
        pj = project_mask(d, sp, f["lambda"])
        fr = float(halo[d].mean())
        trace.append({"n_in": n_in, "n_out": n_out, "n": int(d.sum()), "frac_in_h19_halo": fr, "projected_dti": pj["dti"]})
        print(f"[{time.time()-t0:.0f}s] keep={frac_keep:.2f} n_in={n_in} n_out={n_out} frac={fr:.3f} proj={pj['dti']:.4f}", flush=True)
        if fr <= HALO_CAP and (best is None or pj["dti"] > best[2]["dti"]):
            best = (frac_keep, d, pj, fr)
    if best is None:
        raise SystemExit("no budget satisfied the halo cap")
    mu, dots, pj, frac = best
    dots_u, info_u, frac_u = dots_in, info_in, float(halo[dots_in].mean())

    # Reference projections through the same identity
    refs = {}
    for name, rel in [("champion_G32", "focus_20261027/GEMSDOE32__gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
                      ("G25_d2.8", "focus_20261027/GEMSDOE25__gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")]:
        with rasterio.open(ddir / rel) as s:
            m = (np.nan_to_num(s.read(1)) > 0) & active
        refs[name] = {"n": int(m.sum()), "projected_dti": project_mask(m, sp, f["lambda"])["dti"],
                      "frac_in_h19_halo": float(halo[m].mean())}
    dslup = docs_dir() / "downloads" / "kanlergems2-dslup-uniq-q15k-37654dots-20261027T181253Z-c71122d5-zeros.tif"
    if dslup.exists():
        with rasterio.open(dslup) as s:
            m = (np.nan_to_num(s.read(1)) > 0) & active
        refs["DSLUP_KG2S2"] = {"n": int(m.sum()), "projected_dti": project_mask(m, sp, f["lambda"])["dti"],
                               "frac_in_h19_halo": float(halo[m].mean())}
    cvres = json.loads((ROOT / "evidence/kg2s3_lli_design_cv.json").read_text())
    err = cvres["selected"]
    out = {
        "schema": "kg2s3.lope_emission.v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "label": "PROJECTION (LLI in-model; not a score)",
        "design": sel["design"], "ridge": sel["ridge"], "g_total_projected": g_total,
        "projection_error_band": {"leave_site_out_mae": err["leave_site_out_mae"],
                                  "leave_site_out_abs_err_q90": err["leave_site_out_abs_err_q90"]},
        "unconstrained": {"n": int(dots_u.sum()), "projected_dti": proj_u["dti"], "frac_in_h19_halo": frac_u,
                          "rounds": info_u["rounds"]},
        "constrained": {"mu": 0.0, "inside_keep_fraction": mu, "n": int(dots.sum()), "projected_dti": pj["dti"],
                        "frac_in_h19_halo": frac, "halo_cap": HALO_CAP, "budget_trace": trace},
        "references_same_identity": refs,
    }
    (ROOT / "evidence/kg2s3_lope_emission.json").write_text(json.dumps(out, indent=1, allow_nan=False) + "\n")
    wdir = work_dir() / "kg2s3"
    np.savez_compressed(wdir / "lope_dots.npz", constrained=dots, unconstrained=dots_u, lam=lam_map, halo=halo,
                        inside_all=dots_in, outside_all=dots_out, order_in=info_in["order"], gain_in=info_in["acc_gain"],
                        order_out=info_out["order"], gain_out=info_out["acc_gain"])
    print(json.dumps({k: v for k, v in out.items() if k != "constrained"}, indent=1))
    print("constrained", {k: v for k, v in out["constrained"].items() if k != "budget_trace"})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
