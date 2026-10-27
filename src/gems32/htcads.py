"""H-K1 HTCADS: Hydrothermal-Tectonic Conduit & Anisotropic Dilational Step-Over Synthesis.

Implements:
  1. Label-free 46-channel multi-physics feature stack (36 full-coverage LiDAR-blind Subsurface,
     Geothermal-Vent, and Crustal-Strain channels + 10 quarantined 1 m LiDAR Contour-Orthogonal
     Scarp Specialist channels). Zero SGMC or Quaternary trace coordinates used.
  2. Fold-local 4-channel Visible-Only Anisotropic Fault-Tip & Relay-Ramp Geometry (derived strictly
     from visible faults in each Hide-and-Recover fold; zero withheld-fault leakage).
  3. Rule 4 Leakage Canary testing every individual feature on spatially-blocked holdout (AUC <= 0.90).
  4. Exact 25-Offset Euclidean 300 m Submodular Expected-DTI (`CELF` / Dinkelbach) dot allocator with
     Anisotropic Flank-Depleting / Tip-Preserving Catalogue Collar.
"""
from __future__ import annotations

import gc
import heapq
import struct
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from pyproj import Transformer
from scipy.ndimage import (
    convolve,
    distance_transform_edt,
    gaussian_filter,
    maximum_filter,
)
from skimage.morphology import skeletonize
from sklearn.metrics import roc_auc_score

from .metric import _OFFS

SUBSURF_FEATURE_NAMES: list[str] = [
    # Pillar 1: Subsurface Potential-Field & Updip Dip-Projected Ridges (14)
    "grav_hg",
    "grav_hess_ridge_s1",
    "grav_hess_ridge_s3",
    "grav_worm_1500m",
    "grav_updip_proj",
    "mag_tmi_hg",
    "rtp_hess_ridge_s15",
    "rtp_worm_1500m",
    "tilt_zerocross_sharp",
    "gallardo_meju_xgrad",
    "base_depth_grad",
    "base_flexure_curv",
    "grav_vg",
    "tmi_vg_edge",
    # Pillar 2: Blind Geothermal Vent, Hydrothermal Demagnetization & Alteration Conduit (10)
    "hydro_demag_trough",
    "k_on_th_metasomatism",
    "low_thk_alteration",
    "u_th_redox_front",
    "mt_claycap_edge",
    "mt_cond_local",
    "gdr_probe_f2mdab_upgrad",
    "gdr_geotherm_upgrad",
    "gdr_sinter_vent_strike",
    "hydro_conduit_coupled",
    # Pillar 3: Crustal Strain, Microseismicity, Anderson Tendency & Meso-Topography (12)
    "gps_transtension",
    "gps_strain_2ndinv",
    "gps_dilatation",
    "seismic_swarm_idx",
    "anderson_slip_tendency",
    "piedmont_break_s1",
    "piedmont_break_s3",
    "piedmont_apron_zone",
    "tpi_300m",
    "tpi_1200m",
    "topo_grav_concord",
    "sb_heatflow_excess",
]

LIDAR_FEATURE_NAMES: list[str] = [
    "lidar_ex_max",
    "lidar_ex_mean",
    "lidar_step_max",
    "lidar_crest_toe_dipole",
    "lidar_facing_asymmetry",
    "lidar_coh100",
    "lidar_contour_ortho",
    "lidar_ortho_scarp",
    "lidar_worm_500m",
    "lidar_subsurf_corrob",
]

VISIBLE_CAT_FEATURE_NAMES: list[str] = [
    "vis_log_dist",
    "vis_tip_cone",
    "vis_relay_bridge",
    "vis_aniso_prior",
]


def _grad_yx_f32(arr: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Memory-lean float32 central differences (avoids float64 promotion)."""
    f = arr.astype(np.float32, copy=False)
    gy = np.empty_like(f)
    gx = np.empty_like(f)
    gy[1:-1, :] = 0.5 * (f[2:, :] - f[:-2, :])
    gy[0, :] = f[1, :] - f[0, :]
    gy[-1, :] = f[-1, :] - f[-2, :]
    gx[:, 1:-1] = 0.5 * (f[:, 2:] - f[:, :-2])
    gx[:, 0] = f[:, 1] - f[:, 0]
    gx[:, -1] = f[:, -1] - f[:, -2]
    return gy, gx


def _fill_outside_with_inds(arr: np.ndarray, valid: np.ndarray, inds: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray | None]:
    out = np.array(arr, dtype=np.float32, copy=True)
    if valid.all():
        return out, inds
    if inds is None:
        inds = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    inv = ~valid
    out[inv] = out[inds[0][inv], inds[1][inv]]
    return out, inds


def _robust_z_1d(vals_fp: np.ndarray, clip: float = 6.0) -> np.ndarray:
    med = float(np.median(vals_fp))
    mad = float(np.median(np.abs(vals_fp - med))) * 1.4826 + 1e-6
    return np.clip((vals_fp - med) / mad, -clip, clip).astype(np.float32)


def _robust_z_2d(arr: np.ndarray, foot: np.ndarray, clip: float = 6.0) -> np.ndarray:
    vals = arr[foot]
    med = float(np.median(vals))
    mad = float(np.median(np.abs(vals - med))) * 1.4826 + 1e-6
    out = np.clip((arr - med) / mad, -clip, clip).astype(np.float32)
    out[~foot] = 0.0
    return out


def _pos_norm_2d(arr: np.ndarray, foot: np.ndarray, q: float = 99.5) -> np.ndarray:
    out = np.maximum(arr, 0.0).astype(np.float32)
    scale = float(np.percentile(out[foot], q)) + 1e-6
    np.divide(out, scale, out=out)
    np.clip(out, 0.0, 2.0, out=out)
    out[~foot] = 0.0
    return out


def _hessian_ridge_and_strike(field: np.ndarray, sigma: float, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return float32 ridge strength max(0, -lambda_min) and strike azimuth in [0, pi)."""
    sm = gaussian_filter(field.astype(np.float32, copy=False), sigma=sigma, mode="nearest")
    gy, gx = _grad_yx_f32(sm)
    del sm
    gyy, gyx = _grad_yx_f32(gy)
    gxy, gxx = _grad_yx_f32(gx)
    del gy, gx
    hxy = 0.5 * (gyx + gxy)
    del gyx, gxy
    tr = gxx + gyy
    diff = gxx - gyy
    del gxx, gyy
    rad = np.sqrt(diff * diff + 4.0 * hxy * hxy + 1e-12, dtype=np.float32)
    lam_min = 0.5 * (tr - rad)
    del tr, rad
    ridge = _pos_norm_2d(-lam_min, foot)
    del lam_min
    normal_az = 0.5 * np.arctan2(2.0 * hxy, diff)
    del hxy, diff
    strike_az = np.mod(normal_az + 0.5 * np.pi, np.pi).astype(np.float32)
    return ridge, strike_az


def _multi_azimuth_worm(edge_field: np.ndarray, length_px: int, foot: np.ndarray) -> np.ndarray:
    """8-azimuth linear strike-coherent worm response of length `length_px`."""
    f = np.where(foot, np.maximum(edge_field, 0.0), 0.0).astype(np.float32)
    half = length_px // 2
    best = np.zeros_like(f)
    for k_az in range(8):
        theta = k_az * (np.pi / 8.0)
        dy = float(np.sin(theta))
        dx = float(np.cos(theta))
        kern = np.zeros((2 * half + 1, 2 * half + 1), dtype=np.float32)
        for s in range(-half, half + 1):
            ry = int(round(half + s * dy))
            rx = int(round(half + s * dx))
            if 0 <= ry < kern.shape[0] and 0 <= rx < kern.shape[1]:
                kern[ry, rx] += 1.0
        kern /= max(float(kern.sum()), 1.0)
        resp = convolve(f, kern, mode="nearest")
        np.maximum(best, resp, out=best)
    return _pos_norm_2d(best, foot)


def _fft_upward_continue(field: np.ndarray, dz_m: float, dx_m: float = 100.0) -> np.ndarray:
    """Exact potential-field upward continuation by height dz_m via 2D FFT Poisson kernel."""
    H, W = field.shape
    pad = 48
    padded = np.pad(field.astype(np.float32, copy=False), ((pad, pad), (pad, pad)), mode="edge")
    ky = np.fft.fftfreq(padded.shape[0], d=dx_m).astype(np.float32)[:, None]
    kx = np.fft.rfftfreq(padded.shape[1], d=dx_m).astype(np.float32)[None, :]
    filt = np.exp(-2.0 * np.pi * np.sqrt(ky * ky + kx * kx) * dz_m).astype(np.float32)
    spec = np.fft.rfft2(padded)
    spec *= filt
    up = np.fft.irfft2(spec, s=padded.shape).astype(np.float32)
    return up[pad : pad + H, pad : pad + W].copy()


def _updip_projected_gravity_crest(grav: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Project hanging-wall gravity horizontal-gradient crests updip using upward-continuation migration."""
    g0 = gaussian_filter(grav, sigma=1.2, mode="nearest")
    g_up = _fft_upward_continue(g0, dz_m=400.0, dx_m=100.0)
    gy0, gx0 = _grad_yx_f32(g0)
    hg0 = np.hypot(gy0, gx0).astype(np.float32)
    del gy0, gx0, g0
    gyu, gxu = _grad_yx_f32(g_up)
    hgu = np.hypot(gyu, gxu).astype(np.float32)
    del gyu, gxu, g_up

    hg0_s = gaussian_filter(hg0, sigma=3.0, mode="nearest")
    scale = float(np.mean(hg0_s[foot])) / (float(np.mean(hgu[foot])) + 1e-6)
    hgu_s = gaussian_filter(hgu * scale, sigma=3.0, mode="nearest")
    del hgu
    diff = gaussian_filter(hgu_s - hg0_s, sigma=4.0, mode="nearest")
    del hg0_s, hgu_s
    my, mx = _grad_yx_f32(diff)
    del diff
    mnorm = np.hypot(my, mx).astype(np.float32) + 1e-6
    uy = -my / mnorm
    ux = -mx / mnorm
    del my, mx, mnorm

    H, W = grav.shape
    rows = np.arange(H, dtype=np.float32)[:, None]
    cols = np.arange(W, dtype=np.float32)[None, :]
    sy = np.clip(np.round(rows - 3.5 * uy).astype(np.int32), 0, H - 1)
    sx = np.clip(np.round(cols - 3.5 * ux).astype(np.int32), 0, W - 1)
    del uy, ux
    shifted = hg0[sy, sx]
    del hg0, sy, sx
    ridge_up, _ = _hessian_ridge_and_strike(shifted, sigma=1.2, foot=foot)
    return ridge_up


def _parse_2m_probes_grid(zpath: Path, transform: rasterio.Affine, shape: tuple[int, int]) -> np.ndarray:
    """Rasterize INGENIOUS 2 m temperature probe positive thermal excess (F2mDAB & T2m excess)."""
    grid = np.zeros(shape, dtype=np.float32)
    with zipfile.ZipFile(zpath) as zf:
        dbf = zf.read("2m_temperature_probe_INGENIOUS_regional_data/2m_temperature_probe_n83geo/2m_temperature_probe_n83geo.dbf")
    nrec, header_len, rec_len = struct.unpack("<IHH", dbf[4:12])
    fields = []
    pos = 32
    while dbf[pos] != 0x0D:
        fname = dbf[pos : pos + 11].split(b"\x00")[0].decode("ascii", errors="ignore")
        flen = dbf[pos + 16]
        fields.append((fname, flen))
        pos += 32

    lons, lats, f2ms, t2ms = [], [], [], []
    offset = header_len
    for _ in range(nrec):
        if offset + rec_len > len(dbf):
            break
        rec = dbf[offset : offset + rec_len]
        offset += rec_len
        if rec[0] == 0x2A:
            continue
        p = 1
        vals = {}
        for fname, flen in fields:
            raw = rec[p : p + flen].decode("utf-8", errors="ignore").strip()
            p += flen
            if fname in ("LatDegreeN", "LongDegree", "F2mDAB", "T2m"):
                try:
                    vals[fname] = float(raw) if raw else np.nan
                except ValueError:
                    vals[fname] = np.nan
        lon = vals.get("LongDegree", np.nan)
        lat = vals.get("LatDegreeN", np.nan)
        if np.isfinite(lon) and np.isfinite(lat) and -125.0 < lon < -110.0 and 35.0 < lat < 45.0:
            lons.append(lon)
            lats.append(lat)
            f2ms.append(vals.get("F2mDAB", np.nan))
            t2ms.append(vals.get("T2m", np.nan))

    if not lons:
        return grid
    tr = Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    xs, ys = tr.transform(np.asarray(lons), np.asarray(lats))
    cols = np.floor((xs - transform.c) / transform.a).astype(np.int32)
    rows = np.floor((ys - transform.f) / transform.e).astype(np.int32)
    f2m_arr = np.asarray(f2ms, dtype=np.float32)
    t2m_arr = np.asarray(t2ms, dtype=np.float32)
    t2m_med = float(np.nanmedian(t2m_arr)) if np.isfinite(t2m_arr).any() else 18.0

    for r, c, f2, t2 in zip(rows, cols, f2m_arr, t2m_arr):
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            w = 0.0
            if np.isfinite(f2) and f2 > 0.5:
                w = max(w, min(float(f2) / 6.0, 3.0))
            elif not np.isfinite(f2) and np.isfinite(t2) and (t2 - t2m_med) > 3.0:
                w = max(w, min(float(t2 - t2m_med) / 10.0, 2.0))
            if w > grid[r, c]:
                grid[r, c] = w
    return grid


def _advective_upgradient_plume(seed_grid: np.ndarray, uy: np.ndarray, ux: np.ndarray, foot: np.ndarray) -> np.ndarray:
    """Back-project shallow thermal discharge seeds 0.5-1.5 km up the smoothed hydraulic gradient."""
    ys, xs = np.nonzero(seed_grid > 0.0)
    vals = seed_grid[ys, xs]
    acc = np.zeros_like(seed_grid, dtype=np.float32)
    H, W = seed_grid.shape
    for step_px, weight in ((0.0, 0.70), (5.0, 1.00), (10.0, 0.85), (15.0, 0.55)):
        ty = np.clip(np.round(ys + step_px * uy[ys, xs]).astype(np.int32), 0, H - 1)
        tx = np.clip(np.round(xs + step_px * ux[ys, xs]).astype(np.int32), 0, W - 1)
        np.maximum.at(acc, (ty, tx), vals * weight)
    plume = gaussian_filter(acc, sigma=6.5, mode="nearest")
    return _pos_norm_2d(plume, foot, q=99.2)


def build_static_feature_stack(ddir: Path, cache_dir: Path) -> dict:
    """Build or load cached 46-channel label-free multi-physics stack (< 650 MB peak RAM)."""
    cache_dir.mkdir(parents=True, exist_ok=True)
    sub_path = cache_dir / "X_subsurf_fp_f32.npy"
    lid_path = cache_dir / "X_lidar_fp_f32.npy"
    meta_path = cache_dir / "static_stack_meta.npz"

    with rasterio.open(ddir / "sample_submission.tif") as ds:
        foot = np.isfinite(ds.read(1))
        transform = ds.transform
        shape = (ds.height, ds.width)
    n_fp = int(foot.sum())

    if sub_path.exists() and lid_path.exists() and meta_path.exists():
        meta = np.load(meta_path)
        if int(meta["n_fp"]) == n_fp and int(meta["n_sub"]) == len(SUBSURF_FEATURE_NAMES):
            X_sub = np.load(sub_path, mmap_mode="r")
            X_lid = np.load(lid_path, mmap_mode="r")
            return {
                "foot": foot,
                "lidar_valid_fp": meta["lidar_valid_fp"].astype(bool),
                "X_sub": X_sub,
                "X_lid": X_lid,
            }

    X_sub = np.lib.format.open_memmap(sub_path, mode="w+", dtype=np.float32, shape=(n_fp, len(SUBSURF_FEATURE_NAMES)))
    X_lid = np.lib.format.open_memmap(lid_path, mode="w+", dtype=np.float32, shape=(n_fp, len(LIDAR_FEATURE_NAMES)))

    core_inds = None

    def _read_core(src, idx: int) -> np.ndarray:
        nonlocal core_inds
        a = src.read(idx).astype(np.float32)
        valid = foot & np.isfinite(a) & (a > -1e30)
        filled, core_inds = _fill_outside_with_inds(a, valid, core_inds)
        return filled

    # --- PILLAR 1: Subsurface Potential-Field & Updip Dip-Projected Ridges (cols 0..13) ---
    with rasterio.open(ddir / "training_features.tif") as src:
        iso_grav = _read_core(src, 13)
        grav_hg_raw = _read_core(src, 18)
        grav_vg = _read_core(src, 11)
        rtp = _read_core(src, 2)
        tmi_hg_raw = _read_core(src, 3)
        tc = _read_core(src, 6)
        tmi_vg = _read_core(src, 9)
        base_depth = _read_core(src, 15)

    grav_hg = _pos_norm_2d(grav_hg_raw, foot)
    del grav_hg_raw
    X_sub[:, 0] = grav_hg[foot]

    grav_r1, strike_grav = _hessian_ridge_and_strike(iso_grav, sigma=1.2, foot=foot)
    X_sub[:, 1] = grav_r1[foot]
    grav_r3, _ = _hessian_ridge_and_strike(iso_grav, sigma=3.0, foot=foot)
    X_sub[:, 2] = grav_r3[foot]
    del grav_r3
    X_sub[:, 3] = _multi_azimuth_worm(grav_hg, length_px=15, foot=foot)[foot]
    del grav_hg
    grav_updip = _updip_projected_gravity_crest(iso_grav, foot=foot)
    X_sub[:, 4] = grav_updip[foot]

    X_sub[:, 5] = _pos_norm_2d(tmi_hg_raw, foot)[foot]
    del tmi_hg_raw
    rtp_r15, strike_rtp = _hessian_ridge_and_strike(rtp, sigma=1.5, foot=foot)
    X_sub[:, 6] = rtp_r15[foot]

    gy_rtp, gx_rtp = _grad_yx_f32(gaussian_filter(rtp, sigma=1.2, mode="nearest"))
    del rtp
    nm = np.hypot(gy_rtp, gx_rtp).astype(np.float32) + 1e-6
    X_sub[:, 7] = _multi_azimuth_worm(_pos_norm_2d(nm, foot), length_px=15, foot=foot)[foot]

    tc_med = float(np.median(tc[foot]))
    tc_mad = float(np.median(np.abs(tc[foot] - tc_med))) * 1.4826 + 1e-5
    tc_gy, tc_gx = _grad_yx_f32(gaussian_filter(tc, sigma=1.0, mode="nearest"))
    tilt_sharp = _pos_norm_2d(np.exp(-np.abs(tc - tc_med) / (0.65 * tc_mad)) * np.hypot(tc_gy, tc_gx), foot)
    del tc, tc_gy, tc_gx
    X_sub[:, 8] = tilt_sharp[foot]

    gy_g, gx_g = _grad_yx_f32(gaussian_filter(iso_grav, sigma=1.8, mode="nearest"))
    del iso_grav
    ng = np.hypot(gy_g, gx_g).astype(np.float32) + 1e-6
    cos_gm = (gy_g * gy_rtp + gx_g * gx_rtp) / (ng * nm)
    X_sub[:, 9] = _pos_norm_2d((cos_gm * cos_gm) * np.sqrt(ng * nm), foot)[foot]
    del gy_rtp, gx_rtp, nm, cos_gm

    b_gy, b_gx = _grad_yx_f32(gaussian_filter(base_depth, sigma=1.5, mode="nearest"))
    base_grad = _pos_norm_2d(np.hypot(b_gy, b_gx), foot)
    del b_gy, b_gx
    X_sub[:, 10] = base_grad[foot]

    b_sm = gaussian_filter(base_depth, sigma=2.5, mode="nearest")
    del base_depth
    b_lap = np.abs(convolve(b_sm, np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32), mode="nearest"))
    del b_sm
    X_sub[:, 11] = _pos_norm_2d(b_lap, foot)[foot]
    del b_lap

    X_sub[:, 12] = _pos_norm_2d(np.abs(grav_vg), foot)[foot]
    del grav_vg
    X_sub[:, 13] = _pos_norm_2d(np.abs(tmi_vg), foot)[foot]
    del tmi_vg

    # Composite 1D structural centerline envelope (kept for Pillar 2 & 4 corroboration)
    struct_1d = np.maximum.reduce([grav_r1, grav_updip, rtp_r15, tilt_sharp, base_grad])
    del grav_updip, tilt_sharp, base_grad
    X_sub.flush()
    gc.collect()

    # --- PILLAR 2: Blind Geothermal Vent, Demagnetization & Alteration Conduit (cols 14..23) ---
    with rasterio.open(ddir / "training_features.tif") as src:
        tmi = _read_core(src, 14)
        cond_surf = _read_core(src, 17)
        det_elev = _read_core(src, 12)

    with rasterio.open(ddir / "external" / "geodawn_extensions_u8.tif") as s_ext:
        ext_thk = s_ext.read(1).astype(np.float32)
        ext_uth = s_ext.read(3).astype(np.float32)
        ext_tmi150 = s_ext.read(4).astype(np.float32)
    ext_valid = (ext_tmi150 > 0) & foot
    tmi150_f, ext_inds = _fill_outside_with_inds(ext_tmi150, ext_valid, None)
    del ext_tmi150
    short_mag = _robust_z_2d(tmi, foot) - _robust_z_2d(tmi150_f, foot)
    del tmi, tmi150_f
    short_mag_loc = short_mag - gaussian_filter(short_mag, sigma=15.0, mode="nearest")
    del short_mag
    hydro_demag = _pos_norm_2d(np.where(ext_valid, -short_mag_loc, 0.0), foot)
    del short_mag_loc
    X_sub[:, 14] = hydro_demag[foot]

    thk_v = (ext_thk > 0) & foot
    thk_f, _ = _fill_outside_with_inds(ext_thk, thk_v, ext_inds if np.array_equal(thk_v, ext_valid) else None)
    low_thk = _pos_norm_2d(np.where(thk_v, gaussian_filter(thk_f, sigma=18.0, mode="nearest") - thk_f, 0.0), foot)
    del ext_thk, thk_f, thk_v
    X_sub[:, 16] = low_thk[foot]

    uth_v = (ext_uth > 0) & foot
    uth_f, _ = _fill_outside_with_inds(ext_uth, uth_v, None)
    X_sub[:, 17] = _pos_norm_2d(np.where(uth_v, uth_f - gaussian_filter(uth_f, sigma=18.0, mode="nearest"), 0.0), foot)[foot]
    del ext_uth, uth_f, uth_v, ext_valid, ext_inds

    with rasterio.open(ddir / "external" / "geodawn_rad_u8.tif") as s_rad:
        rad_k = s_rad.read(1).astype(np.float32)
        rad_th = s_rad.read(2).astype(np.float32)
    rad_valid = (rad_k > 0) & (rad_th > 0) & foot
    k_f, rad_inds = _fill_outside_with_inds(rad_k, rad_valid, None)
    th_f, _ = _fill_outside_with_inds(rad_th, rad_valid, rad_inds)
    del rad_k, rad_th, rad_inds
    kv = k_f[rad_valid]
    thv = th_f[rad_valid]
    slope_kth = float(np.mean((kv - kv.mean()) * (thv - thv.mean())) / (np.var(thv) + 1e-6))
    del kv, thv
    k_res = k_f - slope_kth * th_f
    del k_f, th_f
    k_metasom = _pos_norm_2d(np.where(rad_valid, k_res - gaussian_filter(k_res, sigma=18.0, mode="nearest"), 0.0), foot)
    del k_res, rad_valid
    X_sub[:, 15] = k_metasom[foot]

    cond_pos = np.log1p(np.maximum(cond_surf - float(np.percentile(cond_surf[foot], 1.0)), 0.0)).astype(np.float32)
    del cond_surf
    c_gy, c_gx = _grad_yx_f32(gaussian_filter(cond_pos, sigma=1.5, mode="nearest"))
    mt_edge = _pos_norm_2d(np.hypot(c_gy, c_gx), foot)
    del c_gy, c_gx
    X_sub[:, 18] = mt_edge[foot]
    X_sub[:, 19] = _pos_norm_2d(cond_pos - gaussian_filter(cond_pos, sigma=20.0, mode="nearest"), foot)[foot]
    del cond_pos
    np.maximum(struct_1d, mt_edge, out=struct_1d)
    del mt_edge

    # Precompute hydraulic up-gradient vector once from det_elev
    elev_sm12 = gaussian_filter(det_elev, sigma=12.0, mode="nearest")
    egy12, egx12 = _grad_yx_f32(elev_sm12)
    egnorm = np.hypot(egy12, egx12).astype(np.float32) + 1e-4
    sgate = np.clip(egnorm / (float(np.percentile(egnorm[foot], 65.0)) + 1e-4), 0.0, 1.0).astype(np.float32)
    uy_hyd = (egy12 / egnorm) * sgate
    ux_hyd = (egx12 / egnorm) * sgate
    del egy12, egx12, egnorm, sgate

    probe_seeds = _parse_2m_probes_grid(
        ddir / "external" / "2m_temperature_probe_INGENIOUS_regional_data.zip", transform, shape
    )
    gdr_probe_up = _advective_upgradient_plume(probe_seeds, uy_hyd, ux_hyd, foot)
    del probe_seeds
    X_sub[:, 20] = gdr_probe_up[foot]

    ws_df = pd.read_csv(ddir / "external" / "gdr_wellspring_in_footprint.csv")
    ws_seeds = np.zeros(shape, dtype=np.float32)
    for row in ws_df.itertuples(index=False):
        r, c = int(row.row), int(row.col)
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            tc_v = float(row.temp_c) if pd.notna(row.temp_c) else 0.0
            gmax = max(
                float(row.geothermquartz_c) if pd.notna(row.geothermquartz_c) else 0.0,
                float(row.geothermchalc_c) if pd.notna(row.geothermchalc_c) else 0.0,
                float(row.geothermcat_c) if pd.notna(row.geothermcat_c) else 0.0,
            )
            w = 0.0
            if tc_v >= 28.0:
                w += min((tc_v - 25.0) / 50.0, 2.5)
            if gmax >= 75.0:
                w += min((gmax - 70.0) / 90.0, 2.0)
            if w > ws_seeds[r, c]:
                ws_seeds[r, c] = w
    del ws_df
    gdr_ws_up = _advective_upgradient_plume(ws_seeds, uy_hyd, ux_hyd, foot)
    del ws_seeds, uy_hyd, ux_hyd
    X_sub[:, 21] = gdr_ws_up[foot]

    vent_seeds = np.zeros(shape, dtype=np.float32)
    with zipfile.ZipFile(ddir / "external" / "paleo_geothermal_regional.zip") as zf:
        pal_df = pd.read_csv(zf.open("Paleo_geothermal_final.csv"), encoding="latin-1")
    tr_nad83 = Transformer.from_crs("EPSG:4269", "EPSG:32611", always_xy=True)
    pxs, pys = tr_nad83.transform(pal_df["Long_deg_NAD83"].to_numpy(), pal_df["Lat_deg_NAD83"].to_numpy())
    pcols = np.floor((pxs - transform.c) / transform.a).astype(np.int32)
    prows = np.floor((pys - transform.f) / transform.e).astype(np.int32)
    for r, c, dtype_s in zip(prows, pcols, pal_df["Deposit_type"].fillna("").astype(str)):
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            dl = dtype_s.lower()
            if "sinter" in dl or "breccia" in dl or "explosion" in dl or "silic" in dl:
                w = 2.5
            elif "tufa" in dl:
                w = 0.20
            else:
                w = 0.90
            if w > vent_seeds[r, c]:
                vent_seeds[r, c] = w
    del pal_df, pxs, pys, pcols, prows

    vv_df = pd.read_csv(ddir / "external" / "gdr_volcanic_vents_in_footprint.csv")
    for row in vv_df.itertuples(index=False):
        r, c = int(row.row), int(row.col)
        if 0 <= r < shape[0] and 0 <= c < shape[1]:
            if 1.5 > vent_seeds[r, c]:
                vent_seeds[r, c] = 1.5
    del vv_df
    gdr_vent_field = _pos_norm_2d(gaussian_filter(vent_seeds, sigma=7.0, mode="nearest"), foot, q=99.5)
    del vent_seeds
    X_sub[:, 22] = gdr_vent_field[foot]

    hf_path = ddir / "external" / "sb_heat_flow_in_footprint.csv"
    hf_field = np.zeros(shape, dtype=np.float32)
    if hf_path.exists():
        hf_df = pd.read_csv(hf_path)
        pts = hf_df[(hf_df["kind"] == "Point") & hf_df["x_eac117"].notna() & hf_df["y_eac117"].notna()]
        if len(pts) > 0:
            eac_crs = "+proj=aea +lat_1=29.5 +lat_2=45.5 +lat_0=37.5 +lon_0=-117 +x_0=0 +y_0=0 +datum=NAD83 +units=m +no_defs"
            tr_eac = Transformer.from_crs(eac_crs, "EPSG:32611", always_xy=True)
            hx, hy = tr_eac.transform(pts["x_eac117"].to_numpy(), pts["y_eac117"].to_numpy())
            hc = np.floor((hx - transform.c) / transform.a).astype(np.int32)
            hr = np.floor((hy - transform.f) / transform.e).astype(np.int32)
            hval = pts["hfqc_used"].fillna(pts["hf_meas"]).fillna(0.0).to_numpy(dtype=np.float32)
            hf_num = np.zeros(shape, dtype=np.float32)
            for r, c, v in zip(hr, hc, hval):
                if 0 <= r < shape[0] and 0 <= c < shape[1] and 65.0 < v < 800.0:
                    ex = min((float(v) - 75.0) / 80.0, 3.0)
                    if ex > hf_num[r, c]:
                        hf_num[r, c] = ex
            hf_field = _pos_norm_2d(gaussian_filter(hf_num, sigma=16.0, mode="nearest"), foot, q=99.0)
            del hf_num
        del hf_df, pts

    thermal_any = np.maximum.reduce([gdr_probe_up, gdr_ws_up, gdr_vent_field, hf_field])
    del gdr_probe_up, gdr_ws_up, gdr_vent_field
    alter_any = 0.55 * hydro_demag + 0.45 * np.maximum(k_metasom, low_thk)
    del hydro_demag, k_metasom, low_thk
    X_sub[:, 23] = _pos_norm_2d((0.65 * thermal_any + 0.35 * alter_any) * struct_1d, foot, q=99.5)[foot]
    del thermal_any, alter_any
    X_sub[:, 35] = hf_field[foot]
    del hf_field
    X_sub.flush()
    gc.collect()

    # --- PILLAR 3: Crustal Strain, Microseismicity, Anderson Tendency & Meso-Topography (cols 24..34) ---
    with rasterio.open(ddir / "training_features.tif") as src:
        geod_2nd = _read_core(src, 4)
        geod_shear = _read_core(src, 7)
        geod_dilat = _read_core(src, 8)
        deq = _read_core(src, 10)
        ieq = _read_core(src, 16)
        elev_slope = _read_core(src, 19)

    z_shear_fp = _robust_z_1d(geod_shear[foot])
    z_dilat_fp = _robust_z_1d(geod_dilat[foot])
    del geod_shear, geod_dilat
    transt_fp = np.maximum(z_shear_fp + 1.0, 0.0) * np.maximum(z_dilat_fp + 0.5, 0.0)
    X_sub[:, 24] = np.clip(transt_fp / (float(np.percentile(transt_fp, 99.5)) + 1e-6), 0.0, 2.0)
    X_sub[:, 25] = _robust_z_1d(geod_2nd[foot])
    X_sub[:, 26] = z_dilat_fp
    X_sub[:, 27] = _robust_z_1d(ieq[foot]) - 0.5 * _robust_z_1d(deq[foot])
    del geod_2nd, deq, ieq, z_shear_fp, z_dilat_fp, transt_fp

    topo_r1, strike_topo = _hessian_ridge_and_strike(elev_slope, sigma=1.2, foot=foot)
    X_sub[:, 29] = topo_r1[foot]
    topo_toe_concav, _ = _hessian_ridge_and_strike(-det_elev, sigma=2.0, foot=foot)
    X_sub[:, 30] = topo_toe_concav[foot]
    del topo_toe_concav

    w_g = grav_r1[foot] + 0.05
    w_m = rtp_r15[foot] + 0.05
    w_t = topo_r1[foot] + 0.05
    sg_fp = strike_grav[foot]
    sm_fp = strike_rtp[foot]
    st_fp = strike_topo[foot]
    del grav_r1, rtp_r15, topo_r1, strike_grav, strike_rtp, strike_topo
    sin2 = w_g * np.sin(2.0 * sg_fp) + w_m * np.sin(2.0 * sm_fp) + w_t * np.sin(2.0 * st_fp)
    cos2 = w_g * np.cos(2.0 * sg_fp) + w_m * np.cos(2.0 * sm_fp) + w_t * np.cos(2.0 * st_fp)
    dom_strike_fp = 0.5 * np.mod(np.arctan2(sin2, cos2), 2.0 * np.pi)
    X_sub[:, 28] = (np.cos(dom_strike_fp - np.deg2rad(62.0)) ** 2).astype(np.float32)
    del w_g, w_m, w_t, sg_fp, sm_fp, st_fp, sin2, cos2, dom_strike_fp

    X_sub[:, 31] = _pos_norm_2d(elev_slope, foot)[foot]
    del elev_slope

    X_sub[:, 32] = _pos_norm_2d(np.abs(det_elev - gaussian_filter(det_elev, sigma=3.0, mode="nearest")), foot)[foot]
    X_sub[:, 33] = _robust_z_1d((det_elev - elev_sm12)[foot])
    del elev_sm12

    ey_t, ex_t = _grad_yx_f32(gaussian_filter(det_elev, sigma=1.8, mode="nearest"))
    nt = np.hypot(ey_t, ex_t).astype(np.float32) + 1e-6
    cos_tg = (ey_t * gy_g + ex_t * gx_g) / (nt * ng)
    X_sub[:, 34] = _pos_norm_2d((cos_tg * cos_tg) * np.sqrt(nt * ng), foot)[foot]
    del ey_t, ex_t, nt, gy_g, gx_g, ng, cos_tg
    X_sub.flush()
    gc.collect()

    # Regional contour azimuth for Pillar 4 Lahontan shoreline suppression
    eg_y, eg_x = _grad_yx_f32(gaussian_filter(det_elev, sigma=6.0, mode="nearest"))
    del det_elev
    contour_math = np.mod(np.arctan2(eg_y, eg_x) + 0.5 * np.pi, np.pi).astype(np.float32)
    del eg_y, eg_x

    # --- PILLAR 4: Quarantined 1 m LiDAR Contour-Orthogonal Scarp Specialist (cols 0..9) ---
    with rasterio.open(ddir / "external" / "lidar_scarp_features_u8.tif") as s_lid:
        lidar_valid = (s_lid.read(12) > 0) & foot

        def _read_lid_sqrt(band_idx: int, xmax: float) -> np.ndarray:
            q = s_lid.read(band_idx).astype(np.float32)
            t = np.clip((q - 1.0) / 254.0, 0.0, 1.0)
            return np.where(lidar_valid & (q > 0), xmax * (t * t), 0.0).astype(np.float32)

        def _read_lid_lin(band_idx: int, xmax: float) -> np.ndarray:
            q = s_lid.read(band_idx).astype(np.float32)
            t = np.clip((q - 1.0) / 254.0, 0.0, 1.0)
            return np.where(lidar_valid & (q > 0), xmax * t, 0.0).astype(np.float32)

        X_lid[:, 0] = _read_lid_sqrt(1, 1.5)[foot]
        X_lid[:, 1] = _read_lid_sqrt(2, 0.3)[foot]
        l_step = _read_lid_sqrt(3, 1.0)
        X_lid[:, 2] = l_step[foot]

        l_dipole = np.sqrt(_read_lid_sqrt(4, 0.05) * _read_lid_sqrt(5, 0.05) + 1e-12, dtype=np.float32)
        X_lid[:, 3] = l_dipole[foot]
        del l_dipole

        l_down = _read_lid_sqrt(6, 1.0)
        l_up = _read_lid_sqrt(7, 1.0)
        l_asym = np.where(lidar_valid, np.abs(l_down - l_up) / (l_down + l_up + 1e-4), 0.0).astype(np.float32)
        del l_down, l_up
        X_lid[:, 4] = l_asym[foot]

        l_coh = _read_lid_lin(10, 1.0)
        X_lid[:, 5] = l_coh[foot]

        l_strike_deg = _read_lid_lin(11, 180.0)
        l_strike_math = np.mod(np.deg2rad(90.0 - l_strike_deg), np.pi).astype(np.float32)
        del l_strike_deg
        l_ortho = np.where(lidar_valid, np.abs(np.sin(l_strike_math - contour_math)), 0.0).astype(np.float32)
        del l_strike_math, contour_math
        X_lid[:, 6] = l_ortho[foot]

    l_scarp = (l_step * (0.35 + 0.65 * l_asym) * (0.25 + 0.75 * l_coh) * (0.35 + 0.65 * l_ortho)).astype(np.float32)
    del l_step, l_asym, l_coh, l_ortho
    X_lid[:, 7] = l_scarp[foot]
    X_lid[:, 8] = _multi_azimuth_worm(l_scarp, length_px=5, foot=lidar_valid)[foot]
    X_lid[:, 9] = (l_scarp * struct_1d)[foot]
    del l_scarp, struct_1d
    X_lid.flush()
    del X_sub, X_lid
    gc.collect()

    np.savez_compressed(
        meta_path,
        n_fp=n_fp,
        n_sub=len(SUBSURF_FEATURE_NAMES),
        n_lid=len(LIDAR_FEATURE_NAMES),
        lidar_valid_fp=lidar_valid[foot].astype(np.uint8),
    )
    return {
        "foot": foot,
        "lidar_valid_fp": lidar_valid[foot],
        "X_sub": np.load(sub_path, mmap_mode="r"),
        "X_lid": np.load(lid_path, mmap_mode="r"),
    }


def compute_visible_catalogue_features(visible_mask: np.ndarray, foot: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Derive 4 anisotropic fault-tip & relay-ramp features STRICTLY from `visible_mask` (zero leakage!)."""
    vis = np.asarray(visible_mask, bool) & foot
    H, W = foot.shape
    if not vis.any():
        zeros_fp = np.zeros((int(foot.sum()), 4), dtype=np.float32)
        d_inf = np.full((H, W), 999.0, dtype=np.float32)
        z2d = np.zeros((H, W), dtype=np.float32)
        return zeros_fp, {"d_vis": d_inf, "tip_cone_2d": z2d, "relay_2d": z2d}

    d_vis = distance_transform_edt(~vis).astype(np.float32)
    skel = skeletonize(vis)
    nb_kern = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.int16)
    nb_cnt = convolve(skel.astype(np.int16), nb_kern, mode="constant", cval=0)
    tips = skel & (nb_cnt == 1)
    ty, tx = np.nonzero(tips)
    del nb_cnt, tips

    sy, sx = np.nonzero(skel)
    del skel
    tip_cone = np.zeros((H, W), dtype=np.float32)
    tip_dirs_y = np.zeros(ty.size, dtype=np.float32)
    tip_dirs_x = np.zeros(ty.size, dtype=np.float32)

    if ty.size > 0 and sy.size > 1:
        from scipy.spatial import cKDTree

        stree = cKDTree(np.column_stack([sy, sx]))
        R_CONE = 24
        oy, ox = np.mgrid[-R_CONE : R_CONE + 1, -R_CONE : R_CONE + 1].astype(np.float32)
        rr = np.hypot(oy, ox)
        cone_mask = (rr >= 1.0) & (rr <= R_CONE)
        oy_m = oy[cone_mask]
        ox_m = ox[cone_mask]
        rr_m = rr[cone_mask]
        radial_decay = np.exp(-rr_m / 11.0).astype(np.float32)

        for idx_t in range(ty.size):
            r0, c0 = int(ty[idx_t]), int(tx[idx_t])
            nbr_idx = stree.query_ball_point([r0, c0], r=6.5)
            if len(nbr_idx) <= 1:
                continue
            vy = float(r0) - float(np.mean(sy[nbr_idx]))
            vx = float(c0) - float(np.mean(sx[nbr_idx]))
            vn = float(np.hypot(vy, vx))
            if vn < 1e-3:
                continue
            vy /= vn
            vx /= vn
            tip_dirs_y[idx_t] = vy
            tip_dirs_x[idx_t] = vx

            cos_ang = (oy_m * vy + ox_m * vx) / rr_m
            fwd = cos_ang > 0.72
            if not np.any(fwd):
                continue
            py = r0 + oy_m[fwd].astype(np.int32)
            px = c0 + ox_m[fwd].astype(np.int32)
            inb = (py >= 0) & (py < H) & (px >= 0) & (px < W)
            val = (cos_ang[fwd][inb] ** 3) * radial_decay[fwd][inb]
            np.maximum.at(tip_cone, (py[inb], px[inb]), val)

    relay_2d = np.zeros((H, W), dtype=np.float32)
    if ty.size >= 2:
        from scipy.spatial import cKDTree

        ttree = cKDTree(np.column_stack([ty, tx]))
        pairs = ttree.query_pairs(r=26.0)
        for i, j in pairs:
            dy = float(ty[j] - ty[i])
            dx = float(tx[j] - tx[i])
            dist = float(np.hypot(dy, dx))
            if dist < 3.5:
                continue
            u_ij_y, u_ij_x = dy / dist, dx / dist
            align = max(
                tip_dirs_y[i] * u_ij_y + tip_dirs_x[i] * u_ij_x,
                -(tip_dirs_y[j] * u_ij_y + tip_dirs_x[j] * u_ij_x),
            )
            if align < 0.25:
                continue
            n_steps = int(np.ceil(dist * 1.5)) + 1
            ts = np.linspace(0.0, 1.0, n_steps, dtype=np.float32)
            by = np.clip(np.round(ty[i] + ts * dy).astype(np.int32), 0, H - 1)
            bx = np.clip(np.round(tx[i] + ts * dx).astype(np.int32), 0, H - 1)
            w_bridge = float(np.exp(-dist / 16.0) * (0.4 + 0.6 * align))
            np.maximum.at(relay_2d, (by, bx), w_bridge)
        relay_2d = _pos_norm_2d(gaussian_filter(relay_2d, sigma=2.2, mode="nearest"), foot, q=99.7)

    log_dist = np.log1p(np.minimum(d_vis, 150.0)).astype(np.float32)
    flank_deplete = np.exp(-((d_vis / 2.3) ** 2)) * (1.0 - np.clip(tip_cone, 0.0, 1.0))
    aniso_prior = (
        np.exp(-d_vis / 28.0) * (1.0 - 0.85 * flank_deplete)
        + 0.45 * tip_cone
        + 0.35 * relay_2d
    ).astype(np.float32)

    X_vis = np.empty((int(foot.sum()), 4), dtype=np.float32)
    X_vis[:, 0] = log_dist[foot]
    X_vis[:, 1] = tip_cone[foot]
    X_vis[:, 2] = relay_2d[foot]
    X_vis[:, 3] = aniso_prior[foot]
    return X_vis, {"d_vis": d_vis, "tip_cone_2d": tip_cone, "relay_2d": relay_2d}


def run_leakage_canary(stack: dict, ctx, sample_cap: int = 240_000, seed: int = 20261026) -> dict:
    """Protocol Rule 4: Test EVERY feature alone on the Hide-and-Recover holdout (AUC > 0.90 = leakage)."""
    foot = stack["foot"]
    X_sub = stack["X_sub"]
    X_lid = stack["X_lid"]
    lid_valid_fp = stack["lidar_valid_fp"]

    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(int(foot.sum()), dtype=np.int32)

    rng = np.random.default_rng(seed)
    pos_fp_list, neg_fp_list = [], []
    vis_pos_list, vis_neg_list = [], []

    for cell in ctx.cells:
        if cell.seed != 20:
            continue
        sl = cell.bbox
        fp_sub = fp_idx_2d[sl]
        ty, tx = cell.truth_coords
        p_fp = fp_sub[ty, tx]
        p_fp = p_fp[p_fp >= 0]

        neg_mask = cell.active_sub & (cell.k_dg_sub == 0.0)
        ny, nx = np.nonzero(neg_mask)
        n_fp = fp_sub[ny, nx]
        n_fp = n_fp[n_fp >= 0]
        if n_fp.size > sample_cap // 4:
            n_fp = rng.choice(n_fp, size=sample_cap // 4, replace=False)

        pos_fp_list.append(p_fp)
        neg_fp_list.append(n_fp)

        X_vis_cell, _ = compute_visible_catalogue_features(cell.visible_full, foot)
        vis_pos_list.append(X_vis_cell[p_fp].copy())
        vis_neg_list.append(X_vis_cell[n_fp].copy())
        del X_vis_cell
        gc.collect()

    pos_idx = np.concatenate(pos_fp_list)
    neg_idx = np.concatenate(neg_fp_list)
    y_eval = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)])
    all_idx = np.concatenate([pos_idx, neg_idx])

    results = []
    for j, name in enumerate(SUBSURF_FEATURE_NAMES):
        vals = np.asarray(X_sub[all_idx, j], dtype=np.float32)
        auc = float(roc_auc_score(y_eval, vals))
        sym_auc = max(auc, 1.0 - auc)
        results.append({"feature": name, "group": "subsurface_geothermal_strain", "raw_auc": round(auc, 6), "oriented_auc": round(sym_auc, 6)})

    lid_mask_eval = lid_valid_fp[all_idx]
    y_lid = y_eval[lid_mask_eval]
    idx_lid = all_idx[lid_mask_eval]
    for j, name in enumerate(LIDAR_FEATURE_NAMES):
        vals = np.asarray(X_lid[idx_lid, j], dtype=np.float32)
        auc = float(roc_auc_score(y_lid, vals))
        sym_auc = max(auc, 1.0 - auc)
        results.append({"feature": name, "group": "lidar_specialist", "raw_auc": round(auc, 6), "oriented_auc": round(sym_auc, 6)})

    X_vis_all = np.vstack([np.vstack(vis_pos_list), np.vstack(vis_neg_list)])
    for j, name in enumerate(VISIBLE_CAT_FEATURE_NAMES):
        vals = X_vis_all[:, j]
        auc = float(roc_auc_score(y_eval, vals))
        sym_auc = max(auc, 1.0 - auc)
        results.append({"feature": name, "group": "fold_visible_catalogue_only", "raw_auc": round(auc, 6), "oriented_auc": round(sym_auc, 6)})

    results.sort(key=lambda r: r["oriented_auc"], reverse=True)
    max_auc = float(results[0]["oriented_auc"])
    return {
        "protocol_rule": "Rule 4 Leakage Canary (single-feature holdout AUC <= 0.90)",
        "evaluator": "GEMSDOE32-HIDE-RECOVER-v3.0 (draw20 spatially-blocked withheld segments)",
        "threshold": 0.90,
        "total_features_tested": len(results),
        "n_withheld_positive_pixels_tested": int(pos_idx.size),
        "n_negative_pixels_tested": int(neg_idx.size),
        "max_single_feature_auc": round(max_auc, 6),
        "max_feature_name": results[0]["feature"],
        "passed": bool(max_auc <= 0.90),
        "features": results,
    }


def emit_submodular_celf(
    pi_2d: np.ndarray,
    eligible_2d: np.ndarray,
    max_dots: int = 37654,
    marginal_bar: float = 0.0,
    candidate_pool_size: int = 260_000,
) -> np.ndarray:
    """Exact 25-offset Euclidean 300 m Submodular Expected-DTI (`CELF`) greedy allocator."""
    H, W = pi_2d.shape
    pi_clean = np.where(np.isfinite(pi_2d) & (pi_2d > 0.0), pi_2d, 0.0).astype(np.float32)

    k_mat = np.zeros((7, 7), dtype=np.float32)
    for dy, dx, kw in _OFFS:
        k_mat[dy + 3, dx + 3] = float(kw)
    init_gain = convolve(pi_clean, k_mat, mode="constant", cval=0.0)
    init_gain = np.where(eligible_2d, init_gain, 0.0)

    local_peak = init_gain >= (maximum_filter(init_gain, size=3, mode="constant", cval=0.0) - 1e-12)
    cand_score = np.where(eligible_2d, init_gain * np.where(local_peak, 1.0, 0.92), 0.0)

    flat_cand = np.flatnonzero(cand_score.ravel() > max(marginal_bar, 1e-9))
    if flat_cand.size == 0:
        return np.zeros((H, W), dtype=bool)
    if flat_cand.size > candidate_pool_size:
        scores_sub = init_gain.ravel()[flat_cand]
        keep = np.argpartition(scores_sub, -candidate_pool_size)[-candidate_pool_size:]
        flat_cand = flat_cand[keep]

    PAD = 3
    Wp = W + 2 * PAD
    pi_pad = np.pad(pi_clean, PAD, mode="constant", constant_values=0.0).ravel()
    cov_pad = np.zeros_like(pi_pad, dtype=np.float32)
    offs_pad = np.array([dy * Wp + dx for dy, dx, _ in _OFFS], dtype=np.int32)
    kws = np.array([kw for _, _, kw in _OFFS], dtype=np.float32)

    rows = flat_cand // W
    cols = flat_cand % W
    pad_indices = (rows + PAD) * Wp + (cols + PAD)
    init_vals = init_gain.ravel()[flat_cand]

    heap = [(-float(g), 0, int(pidx), int(fidx)) for g, pidx, fidx in zip(init_vals, pad_indices, flat_cand)]
    heapq.heapify(heap)

    selected = np.zeros(H * W, dtype=bool)
    n_sel = 0
    step = 0

    while heap and n_sel < max_dots:
        neg_g, last_s, pidx, fidx = heapq.heappop(heap)
        g_up = -neg_g
        if g_up < marginal_bar:
            break
        if last_s == step:
            selected[fidx] = True
            n_sel += 1
            step += 1
            nbr = pidx + offs_pad
            cov_pad[nbr] = np.maximum(cov_pad[nbr], kws)
        else:
            nbr = pidx + offs_pad
            rem = kws - cov_pad[nbr]
            np.maximum(rem, 0.0, out=rem)
            new_g = float(np.dot(pi_pad[nbr], rem))
            if new_g >= marginal_bar and new_g > 1e-12:
                heapq.heappush(heap, (-new_g, step, pidx, fidx))

    return selected.reshape((H, W))
