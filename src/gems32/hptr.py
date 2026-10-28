"""KG2-S3-HPTR: Multi-Height Joint Gravity-Magnetic Cross-Gradient Persistence,
Plume-Dispersed Geothermal Vent Upflow & Un-Damped Seamless LiDAR-Void Synthesis.

Implements pre-registered Hypotheses H-S3-1, H-S3-2, and H-S3-3 frozen in:
  - knowledge/03_preregistered_hypotheses_hptr_20261027.md
  - registry/preregistration_hptr_20261027.json

Memory discipline: streams 2D float32 arrays one group at a time into
`.cache/gems_work/hptr_v1/X_hptr.f32.mmap` so peak RSS stays < 1.5 GiB on a 3.8 GiB 2-core box.
All 12 static HPTR channels are 100% label-free (zero access to labels.tif, existing_faults.tif,
SGMC traces, or Qfaults traces). Fold-visible strike-tensor concordance (`vis_strike_concord`)
is recomputed strictly from each split's `visible_full` mask.
"""
from __future__ import annotations

import gc
import heapq
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import (
    convolve,
    distance_transform_edt,
    gaussian_filter,
    map_coordinates,
    maximum_filter,
)
from skimage.morphology import skeletonize
from sklearn.metrics import roc_auc_score

from . import darp_mt10, dslup, holdout, htcads
from .metric import _OFFS

HPTR_FEATURE_NAMES: list[str] = [
    # Group A: Multi-Height (150/400/800m) Listric Cross-Gradient Persistence & Spectral Demag (0..3)
    "hptr_grav_listric_persist",    # 0: 3-horizon (150/400/800m) listric updip gravity ridge geometric persistence
    "hptr_rtp_listric_persist",     # 1: 3-horizon (150/400/800m) listric updip RTP ridge geometric persistence
    "hptr_xgrad_height_coalign",    # 2: Height-persistent Gallardo-Meju grav-mag ridge strike co-alignment (H-S3-1a)
    "hptr_spectral_demag_kring",    # 3: Deep/shallow RTP spectral decay + magnetite trough + bilateral K/eTh ring (H-S3-3)
    # Group B: Advective-Dispersive Geothermal Vent Plume & Playa-Deconfounded MT Baffle (4..7)
    "hptr_vent_plume_fan",          # 4: +-40 deg upslope/updip advective-dispersive thermal/sinter/geotherm fan (H-S3-1b)
    "hptr_mt_baffle_2p5km",         # 5: 2.5km high-pass playa-deconfounded asymmetric MT clay-cap step
    "hptr_vent_struct_intersect",   # 6: Multiplicative intersection of dispersed vent plume x persistent basement ridge
    "hptr_stress_comcat_conduit",   # 7: S_hmin/A_phi transtensional dilation x shallow ComCat seismic corridor
    # Group C: Un-Damped Seamless 10m + 3m USGS 3DEP Scarp & Piedmont-Junction Flexure (8..11)
    "hptr_dem10_onesided_deconf",   # 8: Road-cleared & shoreline-orthogonalized seamless 10m one-sided scarp step
    "hptr_dem10_worm_1200m",        # 9: Un-damped 1.2km steerable worm on 10m localized HGM/curvature ridge (100% footprint)
    "hptr_scarp3m_10m_fusion",      # 10: Quantile-aligned un-damped 3m + 10m USGS 3DEP scarp centerline
    "hptr_piedmont_junction_curv",  # 11: Concave piedmont-junction flexure x basement-depth gradient x updip grav
]

HPTR_REGIONAL_COLS: set[int] = {4}

HEIGHTS_M: tuple[float, float, float] = (150.0, 400.0, 800.0)


def _steerable_worm_2d(field_2d: np.ndarray, foot: np.ndarray, length_px: float = 10.0, n_az: int = 8) -> np.ndarray:
    """Compute multi-azimuth linear continuity ('worm') response without damping bedrock or piedmont."""
    H, W = field_2d.shape
    best = np.zeros((H, W), dtype=np.float32)
    half = int(round(length_px / 2.0))
    ts = np.linspace(-half, half, 2 * half + 1, dtype=np.float32)
    weights = np.exp(-0.5 * (ts / max(length_px * 0.35, 1.0)) ** 2).astype(np.float32)
    weights /= float(weights.sum())

    ksize = 2 * half + 1
    for k in range(n_az):
        ang = np.pi * k / n_az
        dy = np.sin(ang) * ts
        dx = np.cos(ang) * ts
        ker = np.zeros((ksize, ksize), dtype=np.float32)
        ry = np.clip(np.round(half + dy).astype(np.int32), 0, ksize - 1)
        rx = np.clip(np.round(half + dx).astype(np.int32), 0, ksize - 1)
        np.add.at(ker, (ry, rx), weights)
        resp = convolve(field_2d, ker, mode="nearest")
        np.maximum(best, resp, out=best)
    return htcads._pos_norm_2d(best, foot, q=99.5)


def _listric_shift_and_unit_down(zb_raw: np.ndarray, grav_0: np.ndarray, foot: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute per-pixel listric horizontal heave s_px(Z_b) and smooth downdip unit vector (uy_down, ux_down)."""
    zb_m = np.clip(zb_raw, 0.0, None).astype(np.float32)
    frac = np.clip(zb_m / dslup.DEPTH_FULL_M, 0.0, 1.0)
    dip_eff = np.deg2rad(dslup.DIP_SURF_DEG - (dslup.DIP_SURF_DEG - dslup.DIP_DEEP_DEG) * frac).astype(np.float32)
    s_px = np.clip(zb_m / np.tan(dip_eff) / dslup.PX_M, dslup.S_MIN_PX, dslup.S_MAX_PX).astype(np.float32)

    # Combine regional basement-depth downdip normal (+grad Z_b) with 800m-0m gravity continuation shift
    zb_sm = gaussian_filter(zb_m, sigma=4.5, mode="nearest")
    zy, zx = htcads._grad_yx_f32(zb_sm)
    zn = np.hypot(zy, zx) + 1e-6
    zy_u, zx_u = (zy / zn).astype(np.float32), (zx / zn).astype(np.float32)
    del zb_sm, zy, zx, zn

    gy0, gx0 = htcads._grad_yx_f32(grav_0)
    hg0_s = gaussian_filter(np.hypot(gy0, gx0).astype(np.float32), sigma=3.0, mode="nearest")
    del gy0, gx0
    g800 = htcads._fft_upward_continue(grav_0, dz_m=800.0, dx_m=100.0)
    gy8, gx8 = htcads._grad_yx_f32(g800)
    hg8 = np.hypot(gy8, gx8).astype(np.float32)
    del g800, gy8, gx8
    sc = float(np.mean(hg0_s[foot])) / (float(np.mean(hg8[foot])) + 1e-6)
    diff = gaussian_filter(gaussian_filter(hg8 * sc, sigma=3.0, mode="nearest") - hg0_s, sigma=4.0, mode="nearest")
    del hg0_s, hg8
    my, mx = htcads._grad_yx_f32(diff)
    del diff
    mn = np.hypot(my, mx) + 1e-6
    # +diff points downdip toward the deep basinward-migrated continuation crest
    uy_d = 0.55 * (my / mn) + 0.45 * zy_u
    ux_d = 0.55 * (mx / mn) + 0.45 * zx_u
    un = np.hypot(uy_d, ux_d) + 1e-6
    return s_px, (uy_d / un).astype(np.float32), (ux_d / un).astype(np.float32)


def build_hptr_feature_stack(
    ddir: Path,
    wdir: Path,
    base_stack: dict | None = None,
    darp_stack: dict | None = None,
    force: bool = False,
) -> dict:
    """Build or load the 12-channel HPTR feature matrix + cached structural strike map in `.cache/gems_work/hptr_v1`."""
    if base_stack is None:
        base_stack = htcads.build_static_feature_stack(ddir, wdir)
    if darp_stack is None:
        darp_stack = darp_mt10.build_darp_feature_stack(ddir, wdir, base_stack=base_stack)

    foot: np.ndarray = base_stack["foot"]
    H, W = foot.shape
    n_fp = int(foot.sum())

    cache_dir = wdir / "hptr_v1"
    cache_dir.mkdir(parents=True, exist_ok=True)
    meta_path = cache_dir / "meta.json"
    mmap_path = cache_dir / "X_hptr.f32.mmap"
    strike_path = cache_dir / "struct_strike_2d.f32.npy"

    if not force and meta_path.exists() and mmap_path.exists() and strike_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("n_fp") == n_fp and meta.get("hptr_features") == HPTR_FEATURE_NAMES:
            X_hptr = np.memmap(mmap_path, dtype="float32", mode="r", shape=(n_fp, len(HPTR_FEATURE_NAMES)))
            return {
                "foot": foot,
                "X_sub": base_stack["X_sub"],
                "X_lid": base_stack["X_lid"],
                "lidar_valid_fp": base_stack["lidar_valid_fp"],
                "X_darp": darp_stack["X_darp"],
                "X_hptr": X_hptr,
                "struct_strike_path": strike_path,
            }

    X_hptr = np.memmap(mmap_path, dtype="float32", mode="w+", shape=(n_fp, len(HPTR_FEATURE_NAMES)))

    core_inds = None

    def _read_core(src, idx: int) -> np.ndarray:
        nonlocal core_inds
        a = src.read(idx).astype(np.float32)
        valid = foot & np.isfinite(a) & (a > -1e30)
        filled, core_inds = htcads._fill_outside_with_inds(a, valid, core_inds)
        return filled

    with rasterio.open(ddir / "training_features.tif") as src:
        rtp = _read_core(src, 2)
        det_elev = _read_core(src, 12)
        iso_grav = _read_core(src, 13)
        zb_raw = _read_core(src, 15)
        cond_surf = _read_core(src, 17)
        det_slope = _read_core(src, 19)
    del core_inds

    g0 = gaussian_filter(iso_grav, sigma=1.15, mode="nearest")
    m0 = gaussian_filter(rtp, sigma=1.15, mode="nearest")
    del iso_grav

    s_px, uy_down, ux_down = _listric_shift_and_unit_down(zb_raw, g0, foot)
    yy, xx = np.indices((H, W), dtype=np.float32)
    samp_y = np.clip(yy + s_px * uy_down, 0.0, float(H - 1))
    samp_x = np.clip(xx + s_px * ux_down, 0.0, float(W - 1))
    del yy, xx

    # ------------------------------------------------------------------
    # Group A (0..3): Multi-Height (150/400/800m) Listric Cross-Gradient Persistence
    # ------------------------------------------------------------------
    g_ridges: list[np.ndarray] = []
    m_ridges: list[np.ndarray] = []
    g_strikes: list[np.ndarray] = []
    m_strikes: list[np.ndarray] = []
    hg_m_150 = None
    hg_m_800 = None

    for z_m in HEIGHTS_M:
        gu = htcads._fft_upward_continue(g0, dz_m=z_m, dx_m=100.0)
        gy, gx = htcads._grad_yx_f32(gu)
        hgg = np.hypot(gy, gx).astype(np.float32)
        del gu, gy, gx
        hgg_proj = map_coordinates(hgg, [samp_y, samp_x], order=1, mode="nearest").astype(np.float32)
        del hgg
        rg, stg = htcads._hessian_ridge_and_strike(hgg_proj, sigma=1.15, foot=foot)
        g_ridges.append(htcads._pos_norm_2d(0.55 * rg + 0.45 * htcads._pos_norm_2d(hgg_proj, foot, q=99.4), foot, q=99.5))
        g_strikes.append(stg)
        del hgg_proj, rg

        mu = htcads._fft_upward_continue(m0, dz_m=z_m, dx_m=100.0)
        my, mx = htcads._grad_yx_f32(mu)
        hgm = np.hypot(my, mx).astype(np.float32)
        del mu, my, mx
        if z_m == 150.0:
            hg_m_150 = hgm.copy()
        elif z_m == 800.0:
            hg_m_800 = hgm.copy()
        hgm_proj = map_coordinates(hgm, [samp_y, samp_x], order=1, mode="nearest").astype(np.float32)
        del hgm
        rm, stm = htcads._hessian_ridge_and_strike(hgm_proj, sigma=1.15, foot=foot)
        m_ridges.append(htcads._pos_norm_2d(0.55 * rm + 0.45 * htcads._pos_norm_2d(hgm_proj, foot, q=99.4), foot, q=99.5))
        m_strikes.append(stm)
        del hgm_proj, rm
        gc.collect()

    del g0, m0, samp_y, samp_x

    coh_g = (0.5 + 0.5 * np.cos(2.0 * (g_strikes[0] - g_strikes[2]))).astype(np.float32)
    g_geom = np.cbrt(np.maximum(g_ridges[0], 1e-4) * np.maximum(g_ridges[1], 1e-4) * np.maximum(g_ridges[2], 1e-4))
    g_mean = (g_ridges[0] + g_ridges[1] + g_ridges[2]) / 3.0
    ch0_grav_persist = htcads._pos_norm_2d((0.55 * g_geom + 0.45 * g_mean) * (0.58 + 0.42 * coh_g), foot, q=99.5)
    X_hptr[:, 0] = ch0_grav_persist[foot]
    del coh_g, g_geom, g_mean

    coh_m = (0.5 + 0.5 * np.cos(2.0 * (m_strikes[0] - m_strikes[2]))).astype(np.float32)
    m_geom = np.cbrt(np.maximum(m_ridges[0], 1e-4) * np.maximum(m_ridges[1], 1e-4) * np.maximum(m_ridges[2], 1e-4))
    m_mean = (m_ridges[0] + m_ridges[1] + m_ridges[2]) / 3.0
    ch1_rtp_persist = htcads._pos_norm_2d((0.55 * m_geom + 0.45 * m_mean) * (0.58 + 0.42 * coh_m), foot, q=99.5)
    X_hptr[:, 1] = ch1_rtp_persist[foot]
    del coh_m, m_geom, m_mean

    # Height-persistent Gallardo-Meju joint grav-mag co-alignment across all 3 continuation heights
    xco_layers = []
    for k in range(3):
        align_k = (0.5 + 0.5 * np.cos(2.0 * (g_strikes[k] - m_strikes[k]))).astype(np.float32)
        xco_layers.append(np.sqrt(np.maximum(g_ridges[k] * m_ridges[k], 0.0)) * (0.35 + 0.65 * align_k))
    xco_geom = np.cbrt(np.maximum(xco_layers[0], 1e-5) * np.maximum(xco_layers[1], 1e-5) * np.maximum(xco_layers[2], 1e-5))
    ch2_xgrad_coalign = htcads._pos_norm_2d(0.60 * xco_geom + 0.40 * ((xco_layers[0] + xco_layers[1] + xco_layers[2]) / 3.0), foot, q=99.5)
    X_hptr[:, 2] = ch2_xgrad_coalign[foot]
    struct_strike_base = g_strikes[1].copy()  # 400m listric-migrated gravity strike
    del g_ridges, m_ridges, g_strikes, m_strikes, xco_layers, xco_geom
    gc.collect()

    # Channel 3 (H-S3-3): Spectral RTP decay + shallow magnetite destruction + bilateral K/eTh shoulders
    rtp_up300 = htcads._fft_upward_continue(rtp, dz_m=300.0, dx_m=100.0)
    demag_core = np.maximum(-(rtp - rtp_up300), 0.0).astype(np.float32)
    del rtp, rtp_up300
    demag_norm = htcads._pos_norm_2d(demag_core, foot, q=99.3)
    del demag_core

    spec_deep_ratio = np.log1p(hg_m_800 / (hg_m_150 + 1e-3)).astype(np.float32)
    spec_norm = htcads._pos_norm_2d(spec_deep_ratio, foot, q=99.3)
    del hg_m_150, hg_m_800, spec_deep_ratio

    with rasterio.open(ddir / "external" / "geodawn_rad_u8.tif") as srad:
        k_band = srad.read(1).astype(np.float32)
        th_band = srad.read(2).astype(np.float32)
    k_th = np.where(foot & (th_band > 1.0), k_band / (th_band + 8.0), 0.0).astype(np.float32)
    del k_band, th_band
    k_annulus = np.maximum(
        gaussian_filter(k_th, sigma=3.8, mode="nearest") - 0.75 * gaussian_filter(k_th, sigma=1.1, mode="nearest"),
        0.0,
    )
    k_ring_norm = htcads._pos_norm_2d(k_annulus, foot, q=99.3)
    del k_th, k_annulus
    ch3_spec_demag = htcads._pos_norm_2d(
        (0.45 * demag_norm + 0.30 * spec_norm + 0.25 * k_ring_norm) * (0.55 + 0.45 * k_ring_norm),
        foot,
        q=99.5,
    )
    X_hptr[:, 3] = ch3_spec_demag[foot]
    del demag_norm, spec_norm, k_ring_norm
    gc.collect()

    # ------------------------------------------------------------------
    # Group B (4..7): Dispersed Geothermal Vent Plume & Playa-Deconfounded MT Baffle
    # ------------------------------------------------------------------
    X_sub = base_stack["X_sub"]
    X_darp = darp_stack["X_darp"]

    # Seed thermal/vent field from GDR 2m probes, geothermometers, sinter vents, and USGS heat-flow
    therm_seed = np.zeros((H, W), dtype=np.float32)
    therm_seed[foot] = (
        0.34 * np.asarray(X_sub[:, 20], dtype=np.float32)
        + 0.26 * np.asarray(X_sub[:, 21], dtype=np.float32)
        + 0.22 * np.asarray(X_sub[:, 22], dtype=np.float32)
        + 0.18 * np.asarray(X_darp[:, 6], dtype=np.float32)
    )
    # Composite upslope (+grad det_elev) and updip (-uy_down, -ux_down) unit transport vector
    ey, ex = htcads._grad_yx_f32(gaussian_filter(det_elev, sigma=3.5, mode="nearest"))
    en = np.hypot(ey, ex) + 1e-6
    up_y = 0.55 * (ey / en) - 0.45 * uy_down
    up_x = 0.55 * (ex / en) - 0.45 * ux_down
    un = np.hypot(up_y, up_x) + 1e-6
    up_y = (up_y / un).astype(np.float32)
    up_x = (up_x / un).astype(np.float32)
    del ey, ex, en, un

    # Anisotropic +-40 deg dispersion fan across r in {4, 9, 16} px
    yy, xx = np.indices((H, W), dtype=np.float32)
    fan_acc = therm_seed.copy()
    therm_blur = gaussian_filter(therm_seed, sigma=2.0, mode="nearest")
    for deg in (-40.0, -20.0, 0.0, 20.0, 40.0):
        rad = np.deg2rad(deg)
        ca, sa = float(np.cos(rad)), float(np.sin(rad))
        dy_f = ca * up_y - sa * up_x
        dx_f = sa * up_y + ca * up_x
        w_ang = float(np.cos(rad) ** 1.5)
        for r_px, w_r in ((4.0, 0.42), (9.0, 0.34), (16.0, 0.24)):
            # Sample down-gradient (opposite up_y, up_x) to pull advected plume back onto upflow fault!
            sy = np.clip(yy - r_px * dy_f, 0.0, float(H - 1))
            sx = np.clip(xx - r_px * dx_f, 0.0, float(W - 1))
            fan_acc += (w_ang * w_r * 0.25) * map_coordinates(therm_blur, [sy, sx], order=1, mode="nearest").astype(np.float32)
            del sy, sx
    del therm_seed, therm_blur, up_y, up_x
    ch4_plume_fan = htcads._pos_norm_2d(fan_acc, foot, q=99.4)
    X_hptr[:, 4] = ch4_plume_fan[foot]
    del fan_acc

    # Channel 5: 2.5km high-pass playa-deconfounded asymmetric MT clay-cap step
    log_cond = np.log1p(np.maximum(cond_surf, 0.0)).astype(np.float32)
    cond_hp = log_cond - gaussian_filter(log_cond, sigma=25.0, mode="nearest")
    del log_cond, cond_surf
    hw_c = np.zeros((H, W), dtype=np.float32)
    fw_c = np.zeros((H, W), dtype=np.float32)
    for r_step, w_s in ((3.0, 0.45), (6.0, 0.35), (9.0, 0.20)):
        hw_c += w_s * map_coordinates(cond_hp, [np.clip(yy + r_step * uy_down, 0, H - 1), np.clip(xx + r_step * ux_down, 0, W - 1)], order=1, mode="nearest")
        fw_c += w_s * map_coordinates(cond_hp, [np.clip(yy - r_step * uy_down, 0, H - 1), np.clip(xx - r_step * ux_down, 0, W - 1)], order=1, mode="nearest")
    del cond_hp, yy, xx, uy_down, ux_down
    playa_damp = np.where((det_elev < -140.0) & (det_slope < 0.65), 0.30, 1.0).astype(np.float32)
    mt_step = np.abs(hw_c - fw_c) * playa_damp
    del hw_c, fw_c, playa_damp
    ch5_mt_baffle = htcads._pos_norm_2d(0.60 * mt_step + 0.40 * _steerable_worm_2d(mt_step, foot, length_px=10.0, n_az=8), foot, q=99.5)
    X_hptr[:, 5] = ch5_mt_baffle[foot]
    del mt_step
    gc.collect()

    # Channel 6: Multiplicative intersection of dispersed hydrothermal plume x persistent subsurface ridge
    hydro_support = 0.40 * ch4_plume_fan + 0.32 * ch5_mt_baffle + 0.28 * ch3_spec_demag
    struct_support = 0.44 * ch0_grav_persist + 0.34 * ch2_xgrad_coalign + 0.22 * ch1_rtp_persist
    ch6_intersect = htcads._pos_norm_2d(np.sqrt(np.maximum(hydro_support * struct_support, 0.0)) + 0.25 * struct_support * ch5_mt_baffle, foot, q=99.5)
    X_hptr[:, 6] = ch6_intersect[foot]
    del ch4_plume_fan, ch5_mt_baffle, ch3_spec_demag, hydro_support, struct_support, ch1_rtp_persist, ch6_intersect

    # Channel 7: Critically stressed ComCat seismogenic structural corridor
    stress_fp = (
        0.42 * np.asarray(X_darp[:, 16], dtype=np.float32)
        + 0.30 * np.asarray(X_darp[:, 14], dtype=np.float32)
        + 0.28 * np.maximum(np.asarray(X_sub[:, 24], dtype=np.float32), 0.0)
    )
    stress_2d = np.zeros((H, W), dtype=np.float32)
    stress_2d[foot] = stress_fp
    ch7_stress = htcads._pos_norm_2d(stress_2d * (0.45 + 0.55 * (0.6 * ch0_grav_persist + 0.4 * ch2_xgrad_coalign)), foot, q=99.5)
    X_hptr[:, 7] = ch7_stress[foot]
    del stress_fp, stress_2d, ch7_stress
    gc.collect()

    # ------------------------------------------------------------------
    # Group C (8..11): Un-Damped Seamless 10m + 3m USGS 3DEP Scarp & Piedmont Flexure
    # ------------------------------------------------------------------
    def _load_dem10(name: str) -> np.ndarray:
        arr = np.zeros((H, W), dtype=np.float32)
        raw = np.load(ddir / "dem10" / f"{name}.f32.npy").astype(np.float32)
        arr[foot] = np.where(np.isfinite(raw), raw, 0.0)
        return arr

    d10_one1 = _load_dem10("dem10_onesided")
    d10_one3 = _load_dem10("dem10_onesided3")
    d10_hgm20 = _load_dem10("dem10_hgm20_max")
    d10_hgm50 = _load_dem10("dem10_hgm50_max")
    d10_hgm200 = _load_dem10("dem10_hgm200_mean")
    d10_curv = _load_dem10("dem10_curv_absmax")

    with rasterio.open(ddir / "external" / "tiger_road_distance_m.tif") as srd:
        road_m_raw = srd.read(1).astype(np.float32)
    road_m = np.where(np.isfinite(road_m_raw), road_m_raw, 5000.0).astype(np.float32)
    del road_m_raw
    road_gate = np.clip((road_m - 70.0) / 90.0, 0.15, 1.0).astype(np.float32)
    del road_m

    # Contour-orthogonality mimic gate vs Lake Lahontan horizontal shorelines (~1280-1340 m / flat det_elev contours)
    ey2, ex2 = htcads._grad_yx_f32(gaussian_filter(det_elev, sigma=2.5, mode="nearest"))
    contour_strike = np.arctan2(-ex2, ey2).astype(np.float32)
    del ey2, ex2

    one_raw = (0.55 * htcads._pos_norm_2d(d10_one1, foot, q=99.5) + 0.45 * htcads._pos_norm_2d(d10_one3, foot, q=99.5)) * road_gate
    del d10_one1, d10_one3
    r_one, st_d10 = htcads._hessian_ridge_and_strike(one_raw, sigma=1.1, foot=foot)
    # Mildly damp pure contour-parallel terrace/shoreline steps on gentle basin margins without hurting range-front faults!
    contour_parallel = (0.5 + 0.5 * np.cos(2.0 * (st_d10 - contour_strike))).astype(np.float32)
    shoreline_zone = ((det_slope >= 0.5) & (det_slope <= 4.5) & (det_elev < -20.0)).astype(np.float32)
    shoreline_deconf = (1.0 - 0.38 * shoreline_zone * contour_parallel).astype(np.float32)
    del contour_strike, contour_parallel, shoreline_zone, det_elev, det_slope

    ch8_d10_onesided = htcads._pos_norm_2d((0.60 * one_raw + 0.40 * r_one) * shoreline_deconf, foot, q=99.5)
    X_hptr[:, 8] = ch8_d10_onesided[foot]
    del one_raw, r_one

    # Localized 10m HGM sharpness (20m/50m scarp step minus 200m broad mountain slope) — UN-DAMPED across all depths!
    loc_hgm = np.maximum(
        0.55 * htcads._pos_norm_2d(d10_hgm20, foot, q=99.5)
        + 0.45 * htcads._pos_norm_2d(d10_hgm50, foot, q=99.5)
        - 0.42 * htcads._pos_norm_2d(d10_hgm200, foot, q=99.5),
        0.0,
    ) * road_gate * shoreline_deconf
    del d10_hgm20, d10_hgm50, d10_hgm200
    loc_input = 0.55 * ch8_d10_onesided + 0.30 * loc_hgm + 0.15 * htcads._pos_norm_2d(d10_curv, foot, q=99.5) * road_gate
    ch9_d10_worm = _steerable_worm_2d(loc_input, foot, length_px=12.0, n_az=8)
    X_hptr[:, 9] = ch9_d10_worm[foot]
    del loc_hgm, loc_input

    # Channel 10: Seamless un-damped 3m + 10m USGS 3DEP scarp fusion
    with rasterio.open(ddir / "external" / "h52_scarp3m_100m.tif") as s3:
        b3_1 = s3.read(1).astype(np.float32)
        b3_2 = s3.read(min(2, s3.count)).astype(np.float32)
    v3 = foot & np.isfinite(b3_1) & (b3_1 > -1e20)
    s3_raw = np.where(v3, np.maximum(b3_1, 0.0) + 0.5 * np.where(np.isfinite(b3_2), np.maximum(b3_2, 0.0), 0.0), 0.0).astype(np.float32)
    del b3_1, b3_2
    s3_norm = htcads._pos_norm_2d(s3_raw * road_gate * shoreline_deconf, foot, q=99.5)
    del s3_raw, road_gate, shoreline_deconf
    d10_blend = 0.55 * ch9_d10_worm + 0.45 * ch8_d10_onesided
    ch10_s3_s10 = htcads._pos_norm_2d(np.where(v3 & (s3_norm > 0.01), 0.52 * s3_norm + 0.48 * d10_blend, d10_blend), foot, q=99.5)
    X_hptr[:, 10] = ch10_s3_s10[foot]
    del v3, s3_norm, d10_blend

    # Channel 11: Piedmont-junction curvature x basement-depth gradient x listric updip gravity
    bgrad_2d = np.zeros((H, W), dtype=np.float32)
    bgrad_2d[foot] = 0.55 * np.asarray(X_sub[:, 10], dtype=np.float32) + 0.45 * np.asarray(X_sub[:, 30], dtype=np.float32)
    curv_n = htcads._pos_norm_2d(d10_curv, foot, q=99.5)
    del d10_curv
    ch11_junc = htcads._pos_norm_2d((0.40 * ch10_s3_s10 + 0.32 * ch0_grav_persist + 0.28 * curv_n) * (0.50 + 0.50 * bgrad_2d), foot, q=99.5)
    X_hptr[:, 11] = ch11_junc[foot]

    # Save composite structural strike (blending 10m scarp strike where strong with 400m listric gravity strike)
    w_d10 = np.clip(ch9_d10_worm * 1.5, 0.0, 0.70)
    # Axial doubling (2*theta) average so pi-periodic strikes blend without branch-cut wrap discontinuities!
    c2 = (1.0 - w_d10) * np.cos(2.0 * struct_strike_base) + w_d10 * np.cos(2.0 * st_d10)
    s2 = (1.0 - w_d10) * np.sin(2.0 * struct_strike_base) + w_d10 * np.sin(2.0 * st_d10)
    struct_strike_2d = (0.5 * np.arctan2(s2, c2)).astype(np.float32)
    np.save(strike_path, struct_strike_2d[foot])

    del ch0_grav_persist, ch2_xgrad_coalign, ch8_d10_onesided, ch9_d10_worm, ch10_s3_s10, ch11_junc
    del bgrad_2d, curv_n, struct_strike_base, st_d10, w_d10, c2, s2, struct_strike_2d, zb_raw
    np.nan_to_num(X_hptr, copy=False, nan=0.0, posinf=1.0, neginf=0.0)
    assert np.isfinite(X_hptr).all(), "Non-finite value detected in X_hptr"
    X_hptr.flush()
    gc.collect()

    meta_path.write_text(
        json.dumps({"n_fp": n_fp, "hptr_features": HPTR_FEATURE_NAMES}, indent=2) + "\n",
        encoding="utf-8",
    )
    X_hptr_ro = np.memmap(mmap_path, dtype="float32", mode="r", shape=(n_fp, len(HPTR_FEATURE_NAMES)))
    return {
        "foot": foot,
        "X_sub": base_stack["X_sub"],
        "X_lid": base_stack["X_lid"],
        "lidar_valid_fp": base_stack["lidar_valid_fp"],
        "X_darp": darp_stack["X_darp"],
        "X_hptr": X_hptr_ro,
        "struct_strike_path": strike_path,
    }


def compute_hptr_visible_tip_concord(
    visible_2d: np.ndarray,
    struct_strike_fp: np.ndarray,
    foot: np.ndarray,
) -> tuple[np.ndarray, dict]:
    """H-S3-2: Fold-visible fault-tip & en-echelon relay strike-tensor concordance.

    Strictly uses ONLY `visible_2d` (`cell.visible_full` during holdout; `ctx.labels` at live emission).
    Returns `(X_vis5_fp, aux_dict)` where column 4 is `vis_strike_concord`.
    """
    from scipy.spatial import cKDTree

    X_vis4, aux = htcads.compute_visible_catalogue_features(visible_2d, foot)
    H, W = foot.shape
    n_fp = int(foot.sum())

    skel = skeletonize(visible_2d & foot)
    sy, sx = np.nonzero(skel)
    prop_c2 = np.zeros((H, W), dtype=np.float32)
    prop_s2 = np.zeros((H, W), dtype=np.float32)
    prop_w = np.zeros((H, W), dtype=np.float32)

    if sy.size >= 8:
        k_nb = np.ones((3, 3), dtype=np.int16)
        k_nb[1, 1] = 0
        deg = convolve(skel.astype(np.int16), k_nb, mode="constant", cval=0)
        ty, tx = np.nonzero(skel & (deg == 1))
        if ty.size > 0:
            stree = cKDTree(np.column_stack([sy, sx]))
            R = 16
            oy, ox = np.mgrid[-R : R + 1, -R : R + 1]
            rr = np.hypot(oy, ox).astype(np.float32)
            cmask = (rr >= 1.5) & (rr <= float(R))
            oy_m = oy[cmask]
            ox_m = ox[cmask]
            rr_m = rr[cmask]
            r_dec = np.exp(-rr_m / 10.5).astype(np.float32)

            for idx_t in range(ty.size):
                r0, c0 = int(ty[idx_t]), int(tx[idx_t])
                nbr = stree.query_ball_point([r0, c0], r=6.5)
                if len(nbr) <= 1:
                    continue
                vy = float(r0) - float(np.mean(sy[nbr]))
                vx = float(c0) - float(np.mean(sx[nbr]))
                vn = float(np.hypot(vy, vx))
                if vn < 1e-3:
                    continue
                vy /= vn
                vx /= vn
                cos_ang = (oy_m * vy + ox_m * vx) / rr_m
                fwd = cos_ang > 0.68
                if not np.any(fwd):
                    continue
                py = r0 + oy_m[fwd].astype(np.int32)
                px = c0 + ox_m[fwd].astype(np.int32)
                inb = (py >= 0) & (py < H) & (px >= 0) & (px < W)
                py_i, px_i = py[inb], px[inb]
                wt = (cos_ang[fwd][inb] ** 2.5) * r_dec[fwd][inb]
                # Local ray azimuth
                ray_ang = np.arctan2(oy_m[fwd][inb], ox_m[fwd][inb]).astype(np.float32)
                better = wt > prop_w[py_i, px_i]
                if np.any(better):
                    pb_y, pb_x = py_i[better], px_i[better]
                    prop_w[pb_y, pb_x] = wt[better]
                    prop_c2[pb_y, pb_x] = np.cos(2.0 * ray_ang[better])
                    prop_s2[pb_y, pb_x] = np.sin(2.0 * ray_ang[better])

    prop_theta_fp = 0.5 * np.arctan2(prop_s2[foot], prop_c2[foot])
    pw_fp = prop_w[foot]
    relay_fp = X_vis4[:, 2]
    align_fp = (0.5 + 0.5 * np.cos(2.0 * (prop_theta_fp - struct_strike_fp))).astype(np.float32)
    concord_fp = np.clip((pw_fp * (0.30 + 0.70 * align_fp)) + 0.45 * relay_fp * align_fp, 0.0, 1.0).astype(np.float32)

    X_vis5 = np.empty((n_fp, 5), dtype=np.float32)
    X_vis5[:, :4] = X_vis4
    X_vis5[:, 4] = concord_fp
    concord_2d = np.zeros((H, W), dtype=np.float32)
    concord_2d[foot] = concord_fp
    aux["concord_2d"] = concord_2d
    return X_vis5, aux


def run_hptr_leakage_canary(stack: dict, ctx: holdout.HoldoutContext, sample_cap: int = 240_000, seed: int = 20261027) -> dict:
    """Protocol Rule 4: Test ALL 81 features individually on spatially-blocked holdout (AUC <= 0.90 required)."""
    foot = stack["foot"]
    X_sub = stack["X_sub"]
    X_lid = stack["X_lid"]
    X_darp = stack["X_darp"]
    X_hptr = stack["X_hptr"]
    lid_valid_fp = stack["lidar_valid_fp"]
    struct_strike_fp = np.load(stack["struct_strike_path"]).astype(np.float32)

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

        X_vis5_cell, _ = compute_hptr_visible_tip_concord(cell.visible_full, struct_strike_fp, foot)
        vis_pos_list.append(X_vis5_cell[p_fp].copy())
        vis_neg_list.append(X_vis5_cell[n_fp].copy())
        del X_vis5_cell
        gc.collect()

    pos_idx = np.concatenate(pos_fp_list)
    neg_idx = np.concatenate(neg_fp_list)
    y_eval = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)])
    all_idx = np.concatenate([pos_idx, neg_idx])

    features = []
    for j, name in enumerate(htcads.SUBSURF_FEATURE_NAMES):
        vals = np.asarray(X_sub[all_idx, j], dtype=np.float32)
        assert np.isfinite(vals).all(), f"Non-finite in {name}"
        auc = float(roc_auc_score(y_eval, vals))
        features.append({"feature": name, "group": "subsurface_base", "raw_auc": round(auc, 6), "oriented_auc": round(max(auc, 1.0 - auc), 6)})

    lid_m = lid_valid_fp[all_idx]
    for j, name in enumerate(htcads.LIDAR_FEATURE_NAMES):
        vals = np.asarray(X_lid[all_idx[lid_m], j], dtype=np.float32)
        assert np.isfinite(vals).all(), f"Non-finite in {name}"
        auc = float(roc_auc_score(y_eval[lid_m], vals))
        features.append({"feature": name, "group": "lidar_1m_specialist", "raw_auc": round(auc, 6), "oriented_auc": round(max(auc, 1.0 - auc), 6)})

    for j, name in enumerate(darp_mt10.DARP_FEATURE_NAMES):
        vals = np.asarray(X_darp[all_idx, j], dtype=np.float32)
        assert np.isfinite(vals).all(), f"Non-finite in {name}"
        auc = float(roc_auc_score(y_eval, vals))
        features.append({"feature": name, "group": "darp_mt10_stack", "raw_auc": round(auc, 6), "oriented_auc": round(max(auc, 1.0 - auc), 6)})

    for j, name in enumerate(HPTR_FEATURE_NAMES):
        vals = np.asarray(X_hptr[all_idx, j], dtype=np.float32)
        assert np.isfinite(vals).all(), f"Non-finite in {name}"
        auc = float(roc_auc_score(y_eval, vals))
        features.append({"feature": name, "group": "hptr_s3_new", "raw_auc": round(auc, 6), "oriented_auc": round(max(auc, 1.0 - auc), 6)})

    vis_names = list(htcads.VISIBLE_CAT_FEATURE_NAMES) + ["vis_strike_concord"]
    X_vis_all = np.vstack([np.vstack(vis_pos_list), np.vstack(vis_neg_list)])
    for j, name in enumerate(vis_names):
        vals = X_vis_all[:, j]
        assert np.isfinite(vals).all(), f"Non-finite in {name}"
        auc = float(roc_auc_score(y_eval, vals))
        features.append({"feature": name, "group": "fold_visible_only", "raw_auc": round(auc, 6), "oriented_auc": round(max(auc, 1.0 - auc), 6)})

    features.sort(key=lambda r: r["oriented_auc"], reverse=True)
    max_auc = float(features[0]["oriented_auc"])
    return {
        "protocol_rule": "Rule 4 Leakage Canary (single-feature holdout AUC <= 0.90)",
        "evaluator": "GEMSDOE32-HIDE-RECOVER-v3.0.1 (draw20 spatially-blocked withheld segments)",
        "threshold": 0.90,
        "total_features_tested": len(features),
        "n_withheld_positive_pixels_tested": int(pos_idx.size),
        "n_negative_pixels_tested": int(neg_idx.size),
        "max_single_feature_auc": round(max_auc, 6),
        "max_feature_name": features[0]["feature"],
        "passed": bool(max_auc <= 0.90),
        "features": features,
    }


def emit_hptr_portfolio_celf(
    pi_main_2d: np.ndarray,
    eligible_2d: np.ndarray,
    pi_pied_2d: np.ndarray | None = None,
    pied_domain_2d: np.ndarray | None = None,
    pied_budget: int = 0,
    total_budget: int = 37654,
    peer_halos_flat: list[tuple[np.ndarray, int]] | None = None,
    marginal_bar: float = 0.0,
    candidate_pool_size: int = 950_000,
) -> tuple[np.ndarray, dict]:
    """Two-Stage Shared-Kernel Submodular CELF Allocator with Multi-Peer Halo Uniqueness Caps.

    Stage 1 allocates up to `pied_budget` dots inside `eligible_2d & pied_domain_2d` using `pi_pied_2d`
    while updating the EXACT shared 25-offset Euclidean 300 m kernel coverage array `cov_pad` and
    respecting every `(halo_flat_bool, q_cap)` in `peer_halos_flat`.
    Stage 2 seamlessly continues on the SAME `cov_pad` and `peer_counts` using `pi_main_2d` across
    `eligible_2d` up to `total_budget`, eliminating inter-stage kernel collisions.
    """
    H, W = pi_main_2d.shape
    PAD = 3
    Wp = W + 2 * PAD
    offs_pad = np.array([dy * Wp + dx for dy, dx, _ in _OFFS], dtype=np.int32)
    kws = np.array([kw for _, _, kw in _OFFS], dtype=np.float32)

    k_mat = np.zeros((7, 7), dtype=np.float32)
    for dy, dx, kw in _OFFS:
        k_mat[dy + 3, dx + 3] = float(kw)

    cov_pad = np.zeros((H + 2 * PAD) * Wp, dtype=np.float32)
    selected = np.zeros(H * W, dtype=bool)
    peer_list = peer_halos_flat or []
    peer_counts = [0 for _ in peer_list]

    def _run_stage(pi_stage_2d: np.ndarray, dom_2d: np.ndarray, stage_target_total: int, bar: float, pool_sz: int) -> tuple[int, float]:
        nonlocal cov_pad, selected, peer_counts
        n_before = int(selected.sum())
        if stage_target_total <= n_before:
            return 0, 0.0

        pi_clean = np.where(np.isfinite(pi_stage_2d) & (pi_stage_2d > 0.0), pi_stage_2d, 0.0).astype(np.float32)
        pi_pad = np.pad(pi_clean, PAD, mode="constant", constant_values=0.0).ravel()
        # Account for coverage already accumulated in earlier stages!
        rem_2d = (pi_pad * (1.0 - cov_pad)).reshape(H + 2 * PAD, Wp)[PAD : PAD + H, PAD : PAD + W]
        init_gain = convolve(rem_2d, k_mat, mode="constant", cval=0.0)
        elig_now = dom_2d & (~selected.reshape(H, W))
        init_gain = np.where(elig_now, init_gain, 0.0)
        del rem_2d

        local_peak = init_gain >= (maximum_filter(init_gain, size=3, mode="constant", cval=0.0) - 1e-12)
        cand_score = np.where(elig_now, init_gain * np.where(local_peak, 1.0, 0.93), 0.0)
        flat_cand = np.flatnonzero(cand_score.ravel() > max(bar, 1e-9))
        if flat_cand.size == 0:
            return 0, 0.0
        if flat_cand.size > pool_sz:
            sc_sub = cand_score.ravel()[flat_cand]
            keep = np.argpartition(sc_sub, -pool_sz)[-pool_sz:]
            flat_cand = flat_cand[keep]

        rows = flat_cand // W
        cols = flat_cand % W
        pad_indices = (rows + PAD) * Wp + (cols + PAD)
        init_vals = init_gain.ravel()[flat_cand]

        heap = [(-float(g), 0, int(pidx), int(fidx)) for g, pidx, fidx in zip(init_vals, pad_indices, flat_cand)]
        heapq.heapify(heap)

        n_sel = int(selected.sum())
        step = 0
        cum_g = 0.0

        while heap and n_sel < stage_target_total:
            neg_g, last_s, pidx, fidx = heapq.heappop(heap)
            if selected[fidx]:
                continue
            # Enforce hard multi-peer 3-px halo caps
            blocked = False
            for m_idx, (h_flat, q_cap) in enumerate(peer_list):
                if h_flat[fidx] and peer_counts[m_idx] >= q_cap:
                    blocked = True
                    break
            if blocked:
                continue

            if last_s == step:
                g_val = -neg_g
                if g_val < bar:
                    break
                selected[fidx] = True
                for m_idx, (h_flat, _q_cap) in enumerate(peer_list):
                    if h_flat[fidx]:
                        peer_counts[m_idx] += 1
                nbr = pidx + offs_pad
                cov_pad[nbr] = np.maximum(cov_pad[nbr], kws)
                n_sel += 1
                step += 1
                cum_g += g_val
            else:
                nbr = pidx + offs_pad
                cur_cov = cov_pad[nbr]
                inc = np.maximum(kws - cur_cov, 0.0)
                new_g = float(np.dot(pi_pad[nbr], inc))
                if new_g >= bar and new_g > 1e-9:
                    heapq.heappush(heap, (-new_g, step, pidx, fidx))

        return n_sel - n_before, cum_g

    n_s1 = 0
    g_s1 = 0.0
    if pi_pied_2d is not None and pied_domain_2d is not None and pied_budget > 0:
        n_s1, g_s1 = _run_stage(
            pi_pied_2d,
            eligible_2d & pied_domain_2d,
            stage_target_total=min(pied_budget, total_budget),
            bar=marginal_bar,
            pool_sz=min(candidate_pool_size, 450_000),
        )

    n_s2, g_s2 = _run_stage(
        pi_main_2d,
        eligible_2d,
        stage_target_total=total_budget,
        bar=marginal_bar,
        pool_sz=candidate_pool_size,
    )

    # Top-up fallback if marginal_bar stopped early while caller requested exact total_budget
    n_topup = 0
    if marginal_bar > 0.0 and int(selected.sum()) < total_budget:
        n_topup, _ = _run_stage(
            pi_main_2d,
            eligible_2d,
            stage_target_total=total_budget,
            bar=0.0,
            pool_sz=candidate_pool_size,
        )

    return selected.reshape(H, W), {
        "n_emitted": int(selected.sum()),
        "stage1_piedmont_dots": int(n_s1),
        "stage2_main_dots": int(n_s2),
        "topup_dots": int(n_topup),
        "cum_gain_stage1": round(g_s1, 4),
        "cum_gain_stage2": round(g_s2, 4),
        "peer_halo_counts": [int(c) for c in peer_counts],
    }
