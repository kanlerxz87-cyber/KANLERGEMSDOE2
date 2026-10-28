#!/usr/bin/env python3
"""KG2-S3 fully automated submission gate (no human inspector, nothing copied from a run card).

Prints ONE verdict: ``OK_TO_SUBMIT`` (exit 0) or ``NOT_OK_DO_NOT_SUBMIT`` (exit 1) with every failed gate.

Gate 1  FORMAT        recomputed from the TIFF bytes: single float32 band, CRS/shape/transform equal to
                      sample_submission.tif, nodata unset, every one of the 12,279,160 cells finite and in
                      [0, 1] (the portal's "Predicted values must be in range [0, 1]" error), >= 1 positive
                      footprint pixel, 0 positive pixels outside the footprint, 0 on the public catalogue.
Gate 2  CANARY        holdout receipt bound to these exact dots (sha256 of the packed dot mask):
                      every single feature AUC <= 0.90 on withheld hide-and-recover truth.
Gate 3  UNIQUENESS    recomputed from bytes against EVERY registry raster (360) + scored-ledger rasters:
                      exact-hash uniqueness; final-dot Spearman <= 0.90; 3-px dot overlap <= 0.70 for every
                      non-space-filling reference; for space-filling controls (3-px halo covering >= 50 % of
                      the footprint, i.e. uninformative about copying) the null-calibrated excess
                      (obs - halo)/(1 - halo) <= 0.70.  The pre-placement surface rank correlation is
                      recomputed when the surface is supplied (--surface-npy).
Gate 4  HOLDOUT       receipt bound to these dots: HIDE-RECOVER-v3.0 pooled DTI > DSLUP 0.125925, paired
                      95 % CI vs champion strictly positive, SGMC-CAL-v3.0 > 0.098140.
Gate 5  METADATA      unique submission name (not any registry filename stem) and note <= 140 characters.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation
from scipy.spatial import cKDTree
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems32.paths import data_dir  # noqa: E402

DISK3 = np.array([[1 if (dy * dy + dx * dx) <= 9 else 0 for dx in range(-3, 4)] for dy in range(-3, 4)], bool)
DSLUP_HR, DSLUP_SGMC = 0.125925, 0.098140


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dots_sha(mask: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(mask.astype(bool).ravel()).tobytes()).hexdigest()


def gate_format(tif: Path, ddir: Path) -> tuple[dict, np.ndarray | None]:
    with rasterio.open(ddir / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
        tcrs, tshape, ttr = t.crs, t.shape, t.transform
    with rasterio.open(ddir / "labels.tif") as s:
        cat = (s.read(1) > 0) & foot
    with rasterio.open(tif) as s:
        a = s.read()
        info = {"count": s.count, "dtype": s.dtypes[0], "crs": str(s.crs), "shape": list(s.shape),
                "transform": list(s.transform)[:6], "nodata": s.nodata}
        same = (s.crs == tcrs) and (s.shape == tshape) and (s.transform == ttr)
    band = a[0] if a.shape[0] else None
    chk = {
        "single_band": info["count"] == 1,
        "float32": info["dtype"] == "float32",
        "crs_shape_transform_equal_template": bool(same),
        "nodata_unset": info["nodata"] is None,
    }
    if band is not None:
        fin = np.isfinite(band)
        chk.update({
            "all_cells_finite": bool(fin.all()),
            "all_cells_in_0_1": bool(fin.all() and band.min() >= 0.0 and band.max() <= 1.0),
            "positive_inside_footprint": bool((band[foot] > 0).any()),
            "zero_outside_footprint": bool(not (band[~foot] > 0).any()),
            "zero_on_public_catalogue": bool(not (band[cat] > 0).any()),
        })
    ok = all(chk.values())
    dots = (band > 0) & foot if (band is not None and ok) else None
    return {"checks": chk, "raster": info, "passed": ok,
            "n_positive": int(dots.sum()) if dots is not None else None}, dots


def reference_paths(ddir: Path) -> dict[str, Path]:
    refs = {}
    rec = ROOT / "data/registry_fetch_receipt.json"
    if not rec.exists():
        raise SystemExit("registry not fetched: run scripts/fetch_registry_rasters.py")
    for r in json.loads(rec.read_text())["rows"]:
        if r["local"]:
            refs[r["sha256"]] = Path(r["local"])
    led = ROOT / "data/lb_ledger_fetch_receipt.json"
    if led.exists():
        for r in json.loads(led.read_text())["rows"]:
            if r["status"] in ("present", "restored"):
                refs.setdefault(r["sha256"], Path(r["local"]))
    return refs


def gate_uniqueness(tif_sha: str, dots: np.ndarray, foot: np.ndarray, ddir: Path, surface: np.ndarray | None) -> dict:
    reg = json.loads((ROOT / "registry/comparison_registry.json").read_text())["entries"]
    n_reg = len(reg)
    refs = reference_paths(ddir)
    missing = [e["sha256"] for e in reg if e["sha256"] not in refs]
    pts = np.argwhere(dots)
    n = len(pts)
    fp_idx = np.flatnonzero(foot.ravel())
    d_vec = dots.ravel()[fp_idx].astype(np.float64)
    d_c = d_vec - d_vec.mean()
    d_norm = np.sqrt(np.dot(d_c, d_c))
    s_rank = None
    if surface is not None:
        s_rank = rankdata(surface.ravel()[fp_idx]).astype(np.float64)
        s_rank -= s_rank.mean()
        s_norm = np.sqrt(np.dot(s_rank, s_rank))
    rows = []
    for sha, p in refs.items():
        with rasterio.open(p) as s:
            if s.shape != foot.shape:
                rows.append({"sha256": sha, "file": p.name, "status": "grid_mismatch"})
                continue
            r = s.read(1).astype(np.float32)
        r = np.where(np.isfinite(r), r, 0.0)
        pos = (r > 0) & foot
        if not pos.any():
            rows.append({"sha256": sha, "file": p.name, "status": "empty"})
            continue
        halo = binary_dilation(pos, structure=DISK3)
        halo_cov = float(halo[foot].mean())
        ov = float(halo[dots].mean()) if n else 0.0
        rv = r.ravel()[fp_idx].astype(np.float64)
        binary = bool(np.isin(rv, [0.0, 1.0]).all())
        rr = rv if binary else rankdata(rv)
        rr = rr - rr.mean()
        rn = np.sqrt(np.dot(rr, rr))
        rho = float(np.dot(d_c, rr) / (d_norm * rn)) if rn > 0 and d_norm > 0 else None
        rho_s = float(np.dot(s_rank, rr) / (s_norm * rn)) if (s_rank is not None and rn > 0 and s_norm > 0) else None
        space_filling = halo_cov >= 0.50
        excess = (ov - halo_cov) / (1.0 - halo_cov) if halo_cov < 1.0 else 0.0
        dup = (rho is not None and abs(rho) > 0.90) or (rho_s is not None and abs(rho_s) > 0.90) or \
              ((excess > 0.70) if space_filling else (ov > 0.70))
        rows.append({"sha256": sha, "file": p.name, "status": "ok", "overlap_3px": ov, "halo_footprint_cov": halo_cov,
                     "space_filling_control": space_filling, "null_calibrated_excess": excess,
                     "final_dots_spearman": rho, "surface_spearman": rho_s, "duplicate": bool(dup)})
    ok_rows = [r for r in rows if r["status"] == "ok"]
    nsf = [r for r in ok_rows if not r["space_filling_control"]]
    sf = [r for r in ok_rows if r["space_filling_control"]]
    top = sorted(nsf, key=lambda r: -r["overlap_3px"])[:10]
    passed = (not missing) and (tif_sha not in refs) and not any(r["duplicate"] for r in ok_rows)
    return {
        "passed": bool(passed),
        "n_registry_entries": n_reg, "n_registry_missing": len(missing),
        "n_references_compared": len(ok_rows),
        "exact_sha256_unique": tif_sha not in refs,
        "max_overlap_3px_non_space_filling": max((r["overlap_3px"] for r in nsf), default=None),
        "max_abs_final_dots_spearman": max((abs(r["final_dots_spearman"]) for r in ok_rows if r["final_dots_spearman"] is not None), default=None),
        "max_abs_surface_spearman": max((abs(r["surface_spearman"]) for r in ok_rows if r["surface_spearman"] is not None), default=None),
        "space_filling_controls": [{k: r[k] for k in ("file", "overlap_3px", "halo_footprint_cov", "null_calibrated_excess")} for r in sf],
        "top10_overlap_non_space_filling": [{k: r[k] for k in ("file", "overlap_3px", "final_dots_spearman")} for r in top],
        "duplicates": [r["file"] for r in ok_rows if r["duplicate"]],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--tif", type=Path, required=True)
    ap.add_argument("--holdout", type=Path, default=ROOT / "evidence/kg2s3_lope_holdout.json")
    ap.add_argument("--name", required=True)
    ap.add_argument("--note", required=True)
    ap.add_argument("--surface-npy", type=Path, default=None)
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    ddir = data_dir()
    with rasterio.open(ddir / "sample_submission.tif") as t:
        foot = np.isfinite(t.read(1))
    tif_sha = sha256_file(args.tif)
    g1, dots = gate_format(args.tif, ddir)
    res = {"schema": "kg2s3.submission_gate.v1", "human_intervention_required": False,
           "tif": args.tif.name, "tif_sha256": tif_sha, "gates": {}}
    res["gates"]["gate_1_format_0_1"] = g1
    if dots is None:
        res["gates"]["gate_2_canary"] = res["gates"]["gate_3_uniqueness"] = res["gates"]["gate_4_holdout"] = {"passed": False, "reason": "format failed"}
    else:
        dsha = dots_sha(dots)
        ho = json.loads(args.holdout.read_text()) if args.holdout.exists() else {}
        bound = ho.get("candidate_dots_sha256") == dsha
        can = ho.get("leakage_canary", {})
        res["gates"]["gate_2_canary"] = {"passed": bool(bound and can.get("passed") and can.get("max_auc", 1) <= 0.90),
                                         "receipt_bound_to_these_dots": bound, "max_auc": can.get("max_auc"),
                                         "max_feature": can.get("max_feature")}
        surface = np.load(args.surface_npy) if args.surface_npy else None
        res["gates"]["gate_3_uniqueness"] = gate_uniqueness(tif_sha, dots, foot, ddir, surface)
        hr = ho.get("hide_and_recover", {})
        dh = ho.get("hide_and_recover_paired_delta_vs_champion", {})
        sg = ho.get("sgmc_cal", {})
        g4 = {"receipt_bound_to_these_dots": bound,
              "hr_pooled_dti": hr.get("pooled_dti"), "hr_ci95": hr.get("ci95_cluster_bootstrap"),
              "hr_n_withheld": hr.get("n_withheld_positives"), "hr_evaluator": hr.get("evaluator_version"),
              "hr_paired_delta_vs_champion": dh, "sgmc_cal_dti": sg.get("sgmc_prevalence_calibrated_dti"),
              "sgmc_evaluator": sg.get("evaluator_version"), "dslup_hr": DSLUP_HR, "dslup_sgmc": DSLUP_SGMC}
        g4["passed"] = bool(bound and (hr.get("pooled_dti") or 0) > DSLUP_HR and dh.get("ci95_strictly_positive")
                            and (sg.get("sgmc_prevalence_calibrated_dti") or 0) > DSLUP_SGMC)
        res["gates"]["gate_4_holdout"] = g4
    reg = json.loads((ROOT / "registry/comparison_registry.json").read_text())["entries"]
    stems = {Path(e["filename"]).stem for e in reg}
    res["gates"]["gate_5_metadata"] = {"passed": bool(args.name and args.name not in stems and 0 < len(args.note) <= 140),
                                       "name": args.name, "note": args.note, "note_chars": len(args.note)}
    ok = all(g.get("passed") for g in res["gates"].values())
    res["verdict"] = "OK_TO_SUBMIT" if ok else "NOT_OK_DO_NOT_SUBMIT"
    res["failed_gates"] = [k for k, g in res["gates"].items() if not g.get("passed")]
    txt = json.dumps(res, indent=1, allow_nan=False)
    if args.out:
        args.out.write_text(txt + "\n")
    print(txt)
    print("VERDICT:", res["verdict"], "failed:", res["failed_gates"])
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
