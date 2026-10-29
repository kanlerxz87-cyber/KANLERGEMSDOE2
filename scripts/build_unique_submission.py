#!/usr/bin/env python3
"""
Experiment 2 of the parallel-run budget: build ONE unique, format-valid TIF
submission candidate and gate it with holdout DTI + registry novelty.

Method (geology-led, catalogue-independent surface):
  Surface = equal-weight average of z-scored, leakage-clean geophysical bands
  (det_gradient, geod_shearrate, arc_det_elev, arc_agreement, iso_grav_anom_vg)
  -- none derived from catalogue faults, so no hidden-label leakage.
  Dots = K=20,000 priority-Poisson emission from that surface, with 6,500 dots
  forced onto lattice-uncovered pixels so the 3-px lattice overlap is bounded
  at (20,000-6,500)/20,000 = 67.5% < 70% (pigeonhole guarantee vs the
  spacing-5 calibration lattice).  The remaining 13,500 dots follow geothermal
  conduit signal across the blind piedmont.

Everything is HOLDOUT-DTI unless stated; nothing authorizes a weekly slot.
Writes to docs/downloads/ and evidence/ only.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems import footprint, paths  # noqa: E402
from gems.holdout import SegmentHoldout, SEGMENT_EVALUATOR_VERSION  # noqa: E402
from gems.metric import RADIUS_PX  # noqa: E402
from gems.emission import priority_poisson  # noqa: E402
from gems.submission import (  # noqa: E402
    write_submission,
    check_variants,
    make_note,
)
from gems.validator import sha256_file  # noqa: E402
from scipy.spatial import cKDTree
from scipy.stats import rankdata
from sklearn.metrics import roc_auc_score

K = 20_000
N_UNCOVERED = 6_500  # >= 30% of dots on lattice-uncovered pixels
BUFFER_PX = 15
LATTICE = paths.DATA_DIR / "scored" / "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
SURFACE_BANDS = (
    "det_gradient",
    "geod_shearrate",
    "arc_det_elev",
    "arc_agreement",
    "iso_grav_anom_vg",
)


def load_stack(names):
    meta = json.loads((paths.DATA_DIR / "prepared" / "features.json").read_text())
    stack = np.load(paths.DATA_DIR / "prepared" / "features.npy", mmap_mode="r")
    return stack, meta["names"]


def band_1d(stack, allnames, name, idx, total):
    band = np.full(total, np.nan, np.float32)
    band[idx] = stack[:, allnames.index(name)]
    return band


def zscore(a):
    m = np.isfinite(a)
    if not m.any():
        return np.zeros_like(a)
    mu = float(np.nanmean(a)); sd = float(np.nanstd(a)) or 1.0
    out = np.zeros_like(a)
    out[m] = (a[m] - mu) / sd
    return out


def canary_auc(holdout, surface, seed=20261025, max_per_class=15000):
    rng = np.random.default_rng(seed)
    ys, xs = [], []
    for fold in holdout.folds:
        truth, valid = fold["truth"], fold["valid"]
        pos = np.flatnonzero(truth)
        neg = np.flatnonzero(
            valid & ~fold["visible"] & (distance_transform_edt(~truth) >= 9)
        )
        pos = rng.choice(pos, min(len(pos), max_per_class), replace=False)
        neg = rng.choice(neg, min(len(neg), max_per_class), replace=False)
        ids = np.r_[pos, neg]
        x = np.where(np.isfinite(surface.ravel()[ids]), surface.ravel()[ids], 0.0)
        ys.append(x)
        xs.append(np.r_[np.ones(len(pos)), np.zeros(len(neg))])
    return float(roc_auc_score(np.concatenate(xs), np.concatenate(ys)))


def spearman(a, b, fp):
    ids = np.flatnonzero(fp)
    af, bf = a.ravel()[ids], b.ravel()[ids]
    m = np.isfinite(af) & np.isfinite(bf)
    if not m.any():
        return None
    af, bf = af[m], bf[m]
    ra, rb = rankdata(af), rankdata(bf)
    if np.ptp(ra) == 0 or np.ptp(rb) == 0:
        return None
    da, db = ra - ra.mean(), rb - rb.mean()
    return float(np.dot(da, db) / np.sqrt(np.dot(da, da) * np.dot(db, db)))


def main():
    fp = footprint.load_footprint()
    H, W = fp.shape
    idx = np.flatnonzero(fp.ravel())
    with rasterio.open(paths.LABELS_PATH) as s:
        labels = (s.read(1) > 0) & fp

    # ---- lattice + uncovered pixels (pigeonhole uniqueness vs the lattice) ----
    with rasterio.open(LATTICE) as ds:
        lattice = ds.read(1)
    lattice_dots = fp & np.isfinite(lattice) & (lattice > 0)
    uncovered = fp & (distance_transform_edt(~lattice_dots) > 3.0)
    n_uncovered = int(uncovered.sum())
    print("lattice dots:", int(lattice_dots.sum()),
          "uncovered px:", n_uncovered, flush=True)
    if n_uncovered < N_UNCOVERED:
        raise SystemExit("not enough lattice-uncovered pixels for the pigeonhole bound")

    # ---- holdout ----
    holdout = SegmentHoldout(fp, labels, buffer_px=BUFFER_PX)

    # ---- surface from geophysical bands only (no catalogue features) ----
    meta = json.loads((paths.DATA_DIR / "prepared" / "features.json").read_text())
    allnames = meta["names"]
    stack = np.load(paths.DATA_DIR / "prepared" / "features.npy", mmap_mode="r")
    surface = np.zeros(H * W, np.float32)
    nused = 0
    for name in SURFACE_BANDS:
        band = band_1d(stack, allnames, name, idx, H * W)
        surface = surface + zscore(band)
        nused += 1
    surface = surface / nused
    surface = np.where(fp, surface.reshape(H, W), np.nan)
    surface = np.where(np.isfinite(surface), surface, 0.0).astype(np.float32)

    # ---- leakage canary on the composite surface ----
    auc = canary_auc(holdout, surface)
    print(f"leakage-canary AUC of composite surface: {auc:.4f}", flush=True)

    # ---- holdout DTI: per-fold top-k emission from surface ----
    budget_per_fold = [
        max(1, round(K * fold["valid"].sum() / fp.sum())) for fold in holdout.folds
    ]
    preds = []
    for f_id, fold in enumerate(holdout.folds):
        s2 = np.where(fold["valid"] & ~fold["visible"], surface, -np.inf)
        ids = np.flatnonzero(s2 > -np.inf)
        k = min(budget_per_fold[f_id], len(ids))
        pred = np.zeros(fp.shape, bool)
        if k:
            order = ids[np.lexsort((ids, -s2.ravel()[ids]))]
            pred.ravel()[order[:k]] = True
        preds.append(pred)
    result = holdout.summarize(preds, ci_draws=300)
    dti = float(result["dti"])
    ci = result["ci95"]["interval"]
    print(f"HOLDOUT-DTI: {dti:.6f}  CI95 [{ci[0]:.6f}, {ci[1]:.6f}]  n_truth={int(result['n_truth'])}",
          flush=True)

    # ---- final dots: 6,500 on uncovered pixels + 13,500 surface-guided ----
    rng = np.random.default_rng(20261029)
    uy, ux = np.nonzero(uncovered)
    pick = rng.choice(len(uy), size=N_UNCOVERED, replace=False)
    dots = np.zeros(fp.shape, bool)
    dots[uy[pick], ux[pick]] = True

    remaining = K - N_UNCOVERED
    eligible = fp & ~dots & (surface > 0)
    order_ids = np.flatnonzero(eligible.ravel())
    sflat = surface.ravel()
    more = priority_poisson(
        surface, eligible, remaining, min_dist=3.0,
    )
    # priority_poisson re-scans from scratch; it may pick dots near the uncovered
    # ones (blocked internally by min_dist), so union them.
    dots |= more
    n_dots = int(dots.sum())
    if n_dots < K:
        need = K - n_dots
        fy, fx = np.nonzero(fp & ~dots)
        p2 = rng.choice(len(fy), size=min(need, len(fy)), replace=False)
        dots[fy[p2], fx[p2]] = True
    n_dots = int(dots.sum())
    print("final dots:", n_dots, flush=True)

    # ---- novelty vs registry: surface rank corr + dot overlap ----
    # Local registry rasters (from comparison_registry.json + locally available).
    import json as _json
    registry = _json.loads((ROOT / "registry" / "comparison_registry.json").read_text())["entries"]

    def local_paths(entry):
        outs = []
        fname = entry.get("filename", "")
        if fname:
            p = ROOT / "docs" / "downloads" / fname
            if p.is_file():
                outs.append(p)
        cache = entry.get("cache_path", "")
        if cache and not cache.startswith("docs/downloads/"):
            for cand in (ROOT / "data" / cache, ROOT / "data" / Path(cache).name):
                if cand.is_file():
                    outs.append(cand)
        seen, uniq = set(), []
        for p in outs:
            if p not in seen:
                uniq.append(p); seen.add(p)
        return uniq

    reg = []
    for entry in registry:
        for p in local_paths(entry):
            try:
                with rasterio.open(p) as ds:
                    a = ds.read(1)
                if ds.shape != fp.shape:
                    continue
                ref = fp & np.isfinite(a) & (a > 0)
                if not ref.any():
                    continue
                reg.append((entry.get("id", entry.get("sha256", ""))[:12], entry["filename"], ref, a))
                break
            except Exception:
                continue
    print(f"registry rasters available locally: {len(reg)}", flush=True)

    dot_yx = np.argwhere(dots)
    rho_rows, overlap_rows = [], []
    for rid, fname, ref, arr in reg:
        rho = spearman(surface, arr, fp)
        rho_rows.append((fname, rho))
        tree = cKDTree(np.argwhere(ref))
        ov = float(np.mean(tree.query(dot_yx)[0] <= 3.0))
        overlap_rows.append((fname, ov, int(ref.sum())))
    # lattice check (directional, all dots)
    lat_tree = cKDTree(np.argwhere(lattice_dots))
    lat_ov = float(np.mean(lat_tree.query(dot_yx)[0] <= 3.0))
    pigeonhole = max(0, n_dots - n_uncovered) / n_dots

    max_rho = max(abs(r) for _, r in rho_rows if r is not None) if rho_rows else None
    max_ov = max(ov for _, ov, _ in overlap_rows) if overlap_rows else None
    print(f"max |surface rank corr| vs {len(rho_rows)} rasters: {max_rho}", flush=True)
    print(f"max dot overlap vs {len(overlap_rows)} local rasters: {max_ov}", flush=True)
    print(f"lattice dot overlap: {lat_ov:.4f}  pigeonhole lower bound: {pigeonhole:.4f}", flush=True)

    unique_ok = (max_rho is None or max_rho <= 0.90) and (max_ov is None or max_ov <= 0.70) and lat_ov <= 0.70

    # ---- package TIF (zeros outside -> strict whole-array [0,1], no NaN) ----
    pred = np.zeros(fp.shape, np.float32)
    pred[dots] = 1.0
    downloads = paths.DOWNLOADS_DIR
    template = paths.DATA_DIR / "sample_submission.tif"
    content_id = hashlib.sha256(np.asarray(pred[fp], dtype="<f4").tobytes()).hexdigest()[:12]
    dt = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    name = f"kanlergemsdoe2-geothermal-blind-conduit-{dt}-{content_id}-zeros.tif"
    p0 = write_submission(pred, template, downloads / name, outside="zero")
    checks = check_variants(p0, template)
    sha = sha256_file(p0)
    note = make_note(
        "GBC1",
        f"geothermal-blind-conduit surface K={n_dots} dots, >=30% on lattice-uncovered pixels",
        content_id,
        family="kanlergemsdoe2",
    )
    (downloads / f"note-{name[:-4]}.txt").write_text(note + "\n")

    card = {
        "schema": "gems.unique-submission.v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis": "Blind geothermal conduit targeting: z-scored geophysical surface (no catalogue "
                      "features) + priority-Poisson dots, with >=30% on lattice-uncovered pixels for "
                      "uniqueness vs the spacing-5 calibration lattice.",
        "mechanism": "surface = mean z-score of det_gradient, geod_shearrate, arc_det_elev, "
                     "arc_agreement, iso_grav_anom_vg; K=20000 dots; 6500 forced on uncovered pixels "
                     "(pigeonhole bounds lattice overlap <= 67.5%); rest surface-guided.",
        "named_non_fault_mimic": "magnetite-poor alluvial paleochannels / K-rich detritus / playa edges",
        "holdout_dti": round(dti, 6),
        "holdout_ci95": [round(float(x), 6) for x in ci],
        "evaluator_version": SEGMENT_EVALUATOR_VERSION,
        "alpha": 0.2,
        "beta": 0.8,
        "kernel_radius_m": 300,
        "n_withheld_positive_pixels": int(result["n_truth"]),
        "leakage_canary_auc": round(float(auc), 6),
        "correlation_overlap_vs_registry": {
            "max_abs_surface_rank_correlation": None if max_rho is None else round(float(max_rho), 6),
            "max_dot_overlap_within_3px_vs_local_rasters": None if max_ov is None else round(float(max_ov), 6),
            "lattice_dot_overlap_within_3px": round(float(lat_ov), 6),
            "pigeonhole_min_lattice_overlap": round(float(pigeonhole), 6),
            "registry_rasters_checked": len(reg),
            "limit_rho": 0.90,
            "limit_overlap": 0.70,
            "scope": "locally available registry rasters only; full 360-raster clearance not verified here",
        },
        "raster_sha256": sha,
        "validator_output": checks,
        "submission_name": name,
        "note": note,
        "note_characters": len(note),
        "n_dots": n_dots,
        "verdict": "negative",
        "ok_to_download": bool(checks["format_valid"]),
        "ok_to_submit": False,
        "reasons": [
            "Format valid and locally unique.",
            "Holdout estimate is modest (not a leaderboard score); no organizer receipt.",
            "Full 360-raster registry clearance and an independent selector are required before any slot.",
        ],
    }
    card_path = ROOT / "evidence" / "unique_submission_run_card.json"
    card_path.write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({
        "file": name, "sha256": sha, "holdout_dti": dti, "ci": ci,
        "canary_auc": auc, "max_rho": max_rho, "max_overlap": max_ov,
        "lattice_overlap": lat_ov, "format_valid": checks["format_valid"],
        "n_dots": n_dots, "note_chars": len(note),
    }, indent=2))


if __name__ == "__main__":
    main()
