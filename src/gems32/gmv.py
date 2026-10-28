"""KG2-S3-GMV label-free feature builders (H1 tectonic-geomorphology + H2 vent alignment).

All features are derived ONLY from competition bridge rasters, GDR/USGS point CSVs
(paleo vents, wellsprings, volcanic vents, ComCat), and TIGER road distance. The
``dist_known_fault_px`` columns in GDR CSVs are NEVER read (catalogue leakage).
No labels, no SGMC, no submission rasters are touched here.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.ndimage import (
    binary_dilation,
    convolve,
    distance_transform_edt,
    gaussian_filter,
    label,
    maximum_filter,
    uniform_filter,
)
from skimage.morphology import skeletonize

from . import htcads

_RNG = np.random.default_rng(20261027)


def _read_bridge_band(ddir: Path, idx: int, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(ddir / "training_features.tif") as src:
        a = src.read(idx).astype(np.float32)
    valid = foot & np.isfinite(a) & (a > -1e30)
    filled, _ = htcads._fill_outside_with_inds(a, valid, None)
    return filled


def _front_sinuosity(slope: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Segment-scale mountain-front sinuosity score (1/Smf on skeletonized fronts)."""
    thr = float(np.percentile(slope[foot], 90.0))
    fronts = foot & (slope >= thr)
    skel = skeletonize(fronts)
    comp, n = label(skel, structure=np.ones((3, 3), int))
    out = np.zeros(foot.shape, dtype=np.float32)
    if n == 0:
        return out
    # Single full-grid neighbor count (IR-KG2S3-PERF-01: was one convolve per component).
    nb_k = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int16)
    cnt = convolve(skel.astype(np.int16), nb_k, mode="constant", cval=0)
    sizes = np.bincount(comp.ravel(), minlength=n + 1)
    for cid in range(1, n + 1):
        npx = int(sizes[cid])
        if npx < 25:
            continue
        m = comp == cid
        ey, ex = np.nonzero(m & (cnt == 1))  # skeleton endpoints: exactly 1 neighbor (kernel center is 0)
        if ey.size < 2:
            continue
        pts = np.column_stack([ey, ex]).astype(np.float32)
        dmax = float(np.hypot(pts[:, 0, None] - pts[:, 0], pts[:, 1, None] - pts[:, 1]).max())
        if dmax < 5.0:
            continue
        smf = npx / dmax  # >= ~1; straight fronts -> 1
        out[m] = float(np.clip(1.0 / smf, 0.0, 1.0))
    out = gaussian_filter(out, sigma=2.0, mode="nearest")
    out[~foot] = 0.0
    return htcads._pos_norm_2d(out, foot)


def _valley_vf_score(elev: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Valley floor-width-to-height score on D8-routed valleys (low Vf -> high)."""
    H, W = foot.shape
    # Filter the nearest-filled grid (IR-KG2S3-NAN-01), then bar flow outside the footprint.
    esm = gaussian_filter(elev, sigma=1.5, mode="nearest")
    esm = np.where(foot, esm, np.inf).astype(np.float32)
    pad = np.pad(esm, 1, mode="constant", constant_values=np.inf)
    ys, xs = np.nonzero(foot)
    n = ys.size
    recv = np.full(n, -1, dtype=np.int64)
    low = esm[ys, xs].astype(np.float32)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            if dy == 0 and dx == 0:
                continue
            cand = pad[ys + 1 + dy, xs + 1 + dx].astype(np.float32)
            step = 1.4142135 if (dy and dx) else 1.0
            better = cand < low - 1e-6
            recv[better] = (ys[better] + dy) * W + (xs[better] + dx)
            low[better] = cand[better]
            del cand
    order = np.argsort(esm[ys, xs], kind="mergesort")[::-1]  # high -> low
    acc = np.ones(n, dtype=np.float32)
    flat_of = ys * W + xs
    index_of_flat = np.full(H * W, -1, dtype=np.int32)
    index_of_flat[flat_of] = np.arange(n, dtype=np.int32)
    for i in order:
        r = recv[i]
        if r >= 0:
            j = index_of_flat[r]
            if j >= 0:
                acc[j] += acc[i]
    acc2 = np.zeros(foot.shape, dtype=np.float32)
    acc2[ys, xs] = acc
    thr = float(np.percentile(acc[acc > 1.0], 99.0)) if (acc > 1.0).any() else 1e9
    valleys = foot & (acc2 >= max(thr, 25.0))
    del acc, acc2, recv, order, index_of_flat
    if not valleys.any():
        return np.zeros(foot.shape, dtype=np.float32)
    # floor width proxy: 2*EDT inside valley mask + 1 (px)
    half_w = distance_transform_edt(valleys).astype(np.float32)
    width_m = (2.0 * half_w + 1.0) * 100.0
    # divide height proxy: max elev in 9px window minus floor elev
    emax = maximum_filter(np.where(foot, elev, -np.inf), size=9, mode="nearest")
    height_m = np.maximum(emax - elev, 0.0) + 5.0
    vf = width_m / (np.maximum(height_m, 5.0))
    score = np.where(valleys, 1.0 / (1.0 + vf / 3.0), 0.0).astype(np.float32)
    score = gaussian_filter(score, sigma=1.5, mode="nearest")
    score[~foot] = 0.0
    return htcads._pos_norm_2d(score, foot)


def _tilt_coherence(elev: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Block-scale tilt coherence: |mean unit gradient| over 2-5 km windows x relief."""
    # IR-KG2S3-NAN-01: `elev` arrives nearest-filled (finite everywhere); filter the FILLED
    # grid. Masking with NaN before filtering poisoned percentiles grid-wide on the real
    # irregular footprint (np.percentile -> NaN -> all-NaN feature, caught by the canary).
    e20 = gaussian_filter(elev, sigma=20.0, mode="nearest")
    e50 = gaussian_filter(elev, sigma=50.0, mode="nearest")
    gy20, gx20 = htcads._grad_yx_f32(np.where(foot, e20, 0.0).astype(np.float32))
    gy50, gx50 = htcads._grad_yx_f32(np.where(foot, e50, 0.0).astype(np.float32))
    out = np.zeros(foot.shape, dtype=np.float32)
    for gy, gx, sz in ((gy20, gx20, 21), (gy50, gx50, 51)):
        nm = np.hypot(gy, gx).astype(np.float32) + 1e-6
        ux, uy = gx / nm, gy / nm
        mux = uniform_filter(np.where(foot, ux, 0.0), size=sz, mode="nearest")
        muy = uniform_filter(np.where(foot, uy, 0.0), size=sz, mode="nearest")
        coh = np.hypot(mux, muy).astype(np.float32)
        rel = htcads._pos_norm_2d(np.where(foot, nm, 0.0), foot)
        out = np.maximum(out, coh * (0.25 + 0.75 * rel))
    out[~foot] = 0.0
    return htcads._pos_norm_2d(out, foot)


def _tpi_discord_ridge(elev: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Hessian ridge of multi-scale TPI discordance |TPI300 - TPI1200|."""
    e = elev.astype(np.float32, copy=False)  # nearest-filled; mask applied after (IR-KG2S3-NAN-01)
    m300 = uniform_filter(e, size=7, mode="nearest")
    m1200 = uniform_filter(e, size=25, mode="nearest")
    disc = np.abs((e - m300) - (e - m1200)).astype(np.float32)
    disc[~foot] = 0.0
    ridge, _ = htcads._hessian_ridge_and_strike(disc, sigma=1.5, foot=foot)
    return htcads._pos_norm_2d(ridge, foot)


def build_h1_geomorph(ddir: Path, foot: np.ndarray) -> dict[str, np.ndarray]:
    """Compute the 4 H1 tectonic-geomorphology grids (float32, footprint-masked)."""
    det_elev = _read_bridge_band(ddir, 12, foot)
    slope = _read_bridge_band(ddir, 19, foot)
    feats = {
        "gmv_front_sinuosity": _front_sinuosity(slope, foot),
        "gmv_valley_vf": _valley_vf_score(det_elev, foot),
        "gmv_tilt_coherence": _tilt_coherence(det_elev, foot),
        "gmv_tpi_discord": _tpi_discord_ridge(det_elev, foot),
    }
    for nm, g in feats.items():
        if not np.all(np.isfinite(g)):
            raise ValueError(f"H1 feature {nm} is not all-finite (IR-KG2S3-NAN-01 fail-fast)")
        g[~foot] = 0.0
    del det_elev, slope
    return feats


# ---------------- H2: fossil-vent alignment corridors ----------------


def _load_h2_points(ddir: Path, transform, shape: tuple[int, int], foot: np.ndarray):
    H, W = shape
    pts_y, pts_x, pts_w = [], [], []

    def _add(r, c, w):
        r, c = int(r), int(c)
        if 0 <= r < H and 0 <= c < W and foot[r, c]:
            pts_y.append(r)
            pts_x.append(c)
            pts_w.append(float(w))

    # paleo vents (lon/lat EPSG:4269 -> grid)
    with zipfile.ZipFile(ddir / "external" / "paleo_geothermal_regional.zip") as zf:
        pal = pd.read_csv(zf.open("Paleo_geothermal_final.csv"), encoding="latin-1")
    tr = Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    px, py = tr.transform(pal["Long_deg_NAD83"].to_numpy(), pal["Lat_deg_NAD83"].to_numpy())
    pc = np.floor((px - transform.c) / transform.a).astype(int)
    pr = np.floor((py - transform.f) / transform.e).astype(int)
    for r, c, dt in zip(pr, pc, pal["Deposit_type"].fillna("").astype(str)):
        dl = dt.lower()
        w = 2.5 if ("sinter" in dl or "breccia" in dl or "explosion" in dl or "silic" in dl) else (0.2 if "tufa" in dl else 0.9)
        _add(r, c, w)

    # warm wellsprings (NEVER dist_known_fault_px)
    ws = pd.read_csv(ddir / "external" / "gdr_wellspring_in_footprint.csv")
    for row in ws.itertuples(index=False):
        tc = float(row.temp_c) if pd.notna(row.temp_c) else 0.0
        gq = float(row.geothermquartz_c) if pd.notna(row.geothermquartz_c) else 0.0
        gc = float(row.geothermchalc_c) if pd.notna(row.geothermchalc_c) else 0.0
        gk = float(row.geothermcat_c) if pd.notna(row.geothermcat_c) else 0.0
        gmax = max(gq, gc, gk)
        w = 0.0
        if tc >= 28.0:
            w += min((tc - 25.0) / 50.0, 2.5)
        if gmax >= 75.0:
            w += min((gmax - 70.0) / 90.0, 2.0)
        if w > 0:
            _add(row.row, row.col, w)

    # volcanic vents
    vv = pd.read_csv(ddir / "external" / "gdr_volcanic_vents_in_footprint.csv")
    for row in vv.itertuples(index=False):
        _add(row.row, row.col, 1.5)

    # ComCat: in-valid, depth<=12 km, weight by magnitude
    cc = pd.read_csv(ddir / "external" / "usgs_comcat_geodawn.csv")
    cc = cc[cc["in_geodawn_valid"] == 1]
    for row in cc.itertuples(index=False):
        d = float(row.depth_km) if pd.notna(row.depth_km) else -1.0
        if d < 0 or d > 12.0:
            continue
        m = float(row.magnitude) if pd.notna(row.magnitude) else 0.0
        w = 0.3 + 0.25 * max(m - 2.0, 0.0)
        _add(row.row_100m, row.col_100m, min(w, 2.0))

    return np.array(pts_y, dtype=np.int32), np.array(pts_x, dtype=np.int32), np.array(pts_w, dtype=np.float32)


def _ransac_lines(py, px, pw, n_iter: int = 4000, tol_px: float = 3.0):
    """Weighted RANSAC line fitting. Returns list of (ny, nx, c, support, length)."""
    n = py.size
    if n < 3:
        return []
    y = py.astype(np.float32)
    x = px.astype(np.float32)
    prob = pw / pw.sum()
    cands = []
    for _ in range(n_iter):
        i, j = _RNG.choice(n, size=2, replace=False, p=prob)
        dy, dx = y[j] - y[i], x[j] - x[i]
        L = float(np.hypot(dy, dx))
        if L < 8.0:
            continue
        ny, nx = -dy / L, dx / L  # unit normal
        c = -(ny * y[i] + nx * x[i])
        dist = np.abs(ny * y + nx * x + c)
        sup_m = dist <= tol_px
        if int(sup_m.sum()) < 3:
            continue
        support = float(pw[sup_m].sum())
        if support < 4.0:
            continue
        t = (y[sup_m] - y[i]) * (-nx) + (x[sup_m] - x[i]) * (ny)
        length = float(t.max() - t.min())
        if length < 15.0:
            continue
        cands.append((float(ny), float(nx), float(c), support, length))
    # merge near-duplicates (angle<5deg, offset<3px), keep max support
    cands.sort(key=lambda t: t[3], reverse=True)
    kept = []
    for ny, nx, c, s, ln in cands:
        dup = False
        for ky, kx, kc, *_ in kept:
            ang = abs(ny * ky + nx * kx)
            if ang > 0.9962 and abs(c - kc) < 3.0:
                dup = True
                break
        if not dup:
            kept.append((ny, nx, c, s, ln))
        if len(kept) >= 400:
            break
    return kept


def build_h2_corridors(
    ddir: Path, foot: np.ndarray, transform, shape: tuple[int, int], hg_gate: np.ndarray
) -> dict[str, np.ndarray]:
    """H2 vent-alignment corridors + vent density (float32, footprint-masked)."""
    H, W = shape
    py, px, pw = _load_h2_points(ddir, transform, shape, foot)
    dens = np.zeros(shape, dtype=np.float32)
    if py.size:
        np.add.at(dens, (py, px), pw)
        dens = gaussian_filter(dens, sigma=3.0, mode="nearest")
        dens[~foot] = 0.0
    dens_n = htcads._pos_norm_2d(dens, foot)

    corr = np.zeros(shape, dtype=np.float32)
    lines = _ransac_lines(py, px, pw) if py.size >= 3 else []
    if lines:
        smax = max(t[3] for t in lines)
        lmax = max(t[4] for t in lines)
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
        for ny, nx, c, s, ln in lines:
            dist = np.abs(ny * yy + nx * xx + c)
            m = dist <= 3.0
            if not m.any():
                continue
            v = float((s / smax) * (0.4 + 0.6 * ln / lmax))
            np.maximum(corr, np.where(m, v, 0.0).astype(np.float32), out=corr)
        del yy, xx
    # HG-step coincidence gate + TIGER road clearance
    hg = np.clip(hg_gate, 0.0, 1.0).astype(np.float32)
    corr = corr * (0.35 + 0.65 * hg)
    with rasterio.open(ddir / "external" / "tiger_road_distance_m.tif") as ds:
        rd = ds.read(1).astype(np.float32)
    rd = np.where(np.isfinite(rd), rd, 5000.0)
    corr = corr * (1.0 - 0.65 * np.exp(-rd / 150.0)).astype(np.float32)
    corr[~foot] = 0.0
    corr = htcads._pos_norm_2d(corr, foot)
    if not np.all(np.isfinite(corr)) or not np.all(np.isfinite(dens_n)):
        raise ValueError("H2 corridor/density not all-finite (IR-KG2S3-NAN-01 fail-fast)")
    return {"gmv_vent_corridor": corr, "gmv_vent_density": dens_n,
            "n_h2_points": int(py.size), "n_h2_lines": int(len(lines))}
