"""KG2-MGHV: Multi-Scale 10m/3m/1m Gap-Bridged Piedmont-Junction Kinematics +
Contrarian Shallow Hydrothermal Magnetite-Destruction & Blind Geothermal Vent Discovery.

Implements the preregistered specification in
``knowledge/01_preregistered_hypotheses_kg2_20261026.md`` reusing the shared
``gems`` template infrastructure (``SegmentHoldout``, ``dprf1``, ``gvc``, ``sahg1``,
``metric``, ``novelty``, ``submission``).

Zero label/catalogue features are ever constructed; every supervised/residualization
parameter is fit strictly inside ``train_mask`` on ``visible_mask`` only.
"""

from __future__ import annotations

import gc
from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from scipy.ndimage import convolve, distance_transform_edt, gaussian_filter
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from threadpoolctl import threadpool_limits

from . import dprf1, geofeatures, gvc, paths

KG2_EXTRA_NAMES: tuple[str, ...] = (
    # 6 official competition GeoDAWN bands omitted by DPRF1
    "kg2_mag_anom",
    "kg2_geod_2ndinv",
    "kg2_iso_grav_slope",
    "kg2_tc_rad",
    "kg2_deq_n100a15",
    "kg2_ieq_n100a15",
    # 11 seamless 10 m USGS 3DEP DEM scarp channels (100.0% footprint coverage = 0 LiDAR gap)
    "kg2_dem10_onesided",
    "kg2_dem10_onesided3",
    "kg2_dem10_hgm20_max",
    "kg2_dem10_hgm50_max",
    "kg2_dem10_hgm200_mean",
    "kg2_dem10_steep_ratio_max",
    "kg2_dem10_slope_mean",
    "kg2_dem10_slope_std",
    "kg2_dem10_resid_range",
    "kg2_dem10_curv_absmax",
    "kg2_dem10_piedmont_relnorm",
    # 5 multi-scale concave-up piedmont-junction & 3 m kinematic scarp channels
    "kg2_junc_100m_raw",
    "kg2_junc_100m_nms",
    "kg2_junc_10m_raw",
    "kg2_scarp3m_h_gate07",
    "kg2_scarp3m_antislope_kin",
    # 4 contrarian hydrothermal magnetite-destruction, clay-cap & cross-gradient channels
    "kg2_fft_rtp_demag_250m",
    "kg2_gallardo_meju_xgrad",
    "kg2_claycap_depth_resid",
    "kg2_transtension_seis_vent",
)

KG2_SELECTIVE_RESID_EXTRA: tuple[str, ...] = (
    "kg2_mag_anom",
    "kg2_tc_rad",
    "kg2_deq_n100a15",
    "kg2_claycap_depth_resid",
)

KG2_REGIME_B_EXTRA: tuple[str, ...] = (
    "kg2_fft_rtp_demag_250m",
    "kg2_gallardo_meju_xgrad",
    "kg2_claycap_depth_resid",
    "kg2_transtension_seis_vent",
)

KG2_PIEDMONT_BOOST_NAMES: tuple[str, ...] = (
    "kg2_dem10_piedmont_relnorm",
    "kg2_junc_10m_raw",
    "kg2_junc_100m_raw",
    "kg2_dem10_steep_ratio_max",
    "kg2_transtension_seis_vent",
    "gvc_piedmont_inflection",
)


def _slope_window(
    s: np.ndarray, a: float = 1.0, b: float = 3.0, c: float = 15.0, d: float = 25.0
) -> np.ndarray:
    w = np.zeros(s.shape, dtype=np.float32)
    rise = (s > a) & (s < b)
    w[rise] = (s[rise] - a) / (b - a)
    w[(s >= b) & (s <= c)] = 1.0
    fall = (s > c) & (s < d)
    w[fall] = (d - s[fall]) / (d - c)
    return w


def compute_piedmont_junction(
    elev_filled: np.ndarray,
    slope_deg_filled: np.ndarray,
    fp: np.ndarray,
    *,
    sigma_elev: float = 1.5,
    sigma_slope: float = 1.5,
    window: tuple[float, float, float, float] = (1.0, 3.0, 15.0, 25.0),
) -> tuple[np.ndarray, np.ndarray]:
    """Directional concave-up slope-break J = max(0, -grad(slope).u_down) * window(slope)."""
    zs = gaussian_filter(elev_filled.astype(np.float32, copy=False), sigma_elev, mode="nearest")
    gy = gaussian_filter(zs, 1.0, order=(1, 0), mode="nearest")
    gx = gaussian_filter(zs, 1.0, order=(0, 1), mode="nearest")
    mag = np.hypot(gy, gx) + 1e-6
    uy = (-gy / mag).astype(np.float32)
    ux = (-gx / mag).astype(np.float32)
    del zs, gy, gx, mag

    ss = gaussian_filter(
        slope_deg_filled.astype(np.float32, copy=False), sigma_slope, mode="nearest"
    )
    sy = gaussian_filter(ss, 1.0, order=(1, 0), mode="nearest")
    sx = gaussian_filter(ss, 1.0, order=(0, 1), mode="nearest")
    d_down = sy * uy + sx * ux
    del sy, sx

    j_raw = (np.maximum(-d_down, 0.0) * _slope_window(ss, *window)).astype(np.float32)
    j_raw[~fp] = np.nan

    # Soft downslope NMS crest
    j0 = np.where(fp, j_raw, 0.0)
    h, w = j0.shape
    rows, cols = np.indices((h, w), dtype=np.int32)
    dy = np.rint(uy).astype(np.int32)
    dx = np.rint(ux).astype(np.int32)
    dx = np.where((dy == 0) & (dx == 0), 1, dx)
    rp, cp = np.clip(rows + dy, 0, h - 1), np.clip(cols + dx, 0, w - 1)
    rm, cm = np.clip(rows - dy, 0, h - 1), np.clip(cols - dx, 0, w - 1)
    m3 = np.maximum(j0, np.maximum(j0[rp, cp], j0[rm, cm])) + 1e-9
    j_nms = (j0 * (j0 / m3) ** 2).astype(np.float32)
    j_nms[~fp] = np.nan
    return j_raw, j_nms


def fft_upward_continue(
    grid_filled: np.ndarray, height_m: float = 250.0, dx_m: float = 100.0
) -> np.ndarray:
    """Exact 2D potential-field upward continuation exp(-2*pi*k*z) with edge-padded taper."""
    pad = 64
    gp = np.pad(grid_filled.astype(np.float32, copy=False), pad, mode="reflect")
    ny, nx = gp.shape
    ky = np.fft.fftfreq(ny, d=dx_m).astype(np.float32)[:, None]
    kx = np.fft.rfftfreq(nx, d=dx_m).astype(np.float32)[None, :]
    k = np.hypot(ky, kx)
    filt = np.exp(-2.0 * np.pi * k * float(height_m)).astype(np.float32)
    spec = np.fft.rfft2(gp)
    up = np.fft.irfft2(spec * filt, s=(ny, nx)).astype(np.float32)
    return up[pad:-pad, pad:-pad]


def build_kg2_extra_memmap(
    data_dir: Path,
    base_mm: np.ndarray,
    base_names: list[str],
    fp: np.ndarray,
    out_npy_path: Path,
    *,
    force: bool = False,
) -> tuple[np.ndarray, list[str]]:
    """Build or load the 26-channel label-free KG2-MGHV physical feature matrix."""
    h, w = fp.shape
    fp_ids = np.flatnonzero(fp.ravel())
    expected_shape = (len(fp_ids), len(KG2_EXTRA_NAMES))
    if out_npy_path.exists() and not force:
        mm = np.load(out_npy_path, mmap_mode="r")
        if mm.shape == expected_shape and mm.dtype == np.float32:
            return mm, list(KG2_EXTRA_NAMES)

    out_npy_path.parent.mkdir(parents=True, exist_ok=True)
    partial = out_npy_path.with_name(out_npy_path.stem + ".partial.npy")
    mm = np.lib.format.open_memmap(
        partial, mode="w+", dtype=np.float32, shape=expected_shape
    )

    def unpack_base(name: str) -> np.ndarray:
        col = base_names.index(name)
        g = np.full((h, w), np.nan, dtype=np.float32)
        g.ravel()[fp_ids] = base_mm[:, col]
        return g

    def write_col(name: str, vec_or_grid: np.ndarray) -> None:
        idx = KG2_EXTRA_NAMES.index(name)
        if vec_or_grid.ndim == 2:
            mm[:, idx] = vec_or_grid.ravel()[fp_ids].astype(np.float32, copy=False)
        else:
            mm[:, idx] = vec_or_grid.astype(np.float32, copy=False)

    # 1. Read the 6 omitted competition GeoDAWN bands (sanitizing float32 nodata sentinels)
    src_tif = data_dir / "training_features.tif"
    omitted_map = {
        "kg2_mag_anom": "mag_anom",
        "kg2_geod_2ndinv": "geod_2ndinv",
        "kg2_iso_grav_slope": "iso_grav_anom_slope",
        "kg2_tc_rad": "tc",
        "kg2_deq_n100a15": "deq_n100a15",
        "kg2_ieq_n100a15": "ieq_n100a15",
    }
    deq_grid = None
    with rasterio.open(src_tif) as ds:
        for out_name, band_name in omitted_map.items():
            bidx = geofeatures.BAND_ORDER.index(band_name) + 1
            a = ds.read(bidx).astype(np.float32)
            a[~fp | ~geofeatures._valid(a)] = np.nan
            write_col(out_name, a)
            if band_name == "deq_n100a15":
                deq_grid = a
            else:
                del a

    # 2. Load 10 m USGS 3DEP seamless DEM scarp vectors (100.0% footprint finite)
    dem10_dir = data_dir / "dem10"
    dem10_raw_map = {
        "kg2_dem10_onesided": "dem10_onesided.f32.npy",
        "kg2_dem10_onesided3": "dem10_onesided3.f32.npy",
        "kg2_dem10_hgm20_max": "dem10_hgm20_max.f32.npy",
        "kg2_dem10_hgm50_max": "dem10_hgm50_max.f32.npy",
        "kg2_dem10_hgm200_mean": "dem10_hgm200_mean.f32.npy",
        "kg2_dem10_steep_ratio_max": "dem10_steep_ratio_max.f32.npy",
        "kg2_dem10_slope_mean": "dem10_slope_mean.f32.npy",
        "kg2_dem10_slope_std": "dem10_slope_std.f32.npy",
        "kg2_dem10_resid_range": "dem10_resid_range.f32.npy",
        "kg2_dem10_curv_absmax": "dem10_curv_absmax.f32.npy",
    }
    for out_name, fn in dem10_raw_map.items():
        v = np.load(dem10_dir / fn, mmap_mode="r")
        if v.shape != (len(fp_ids),):
            raise ValueError(f"Unexpected shape for {fn}: {v.shape}")
        write_col(out_name, np.asarray(v, dtype=np.float32))

    os3 = np.asarray(np.load(dem10_dir / "dem10_onesided3.f32.npy", mmap_mode="r"), dtype=np.float32)
    hgm200 = np.asarray(
        np.load(dem10_dir / "dem10_hgm200_mean.f32.npy", mmap_mode="r"), dtype=np.float32
    )
    relnorm = os3 / (1.0 + 0.35 * np.maximum(hgm200, 0.0))
    write_col("kg2_dem10_piedmont_relnorm", relnorm)
    del os3, hgm200, relnorm

    # 3. Multi-scale concave-up piedmont-junction lines (100 m & 10 m)
    det_elev = unpack_base("det_elev")
    det_slope = unpack_base("det_elev_slope")
    elev_fill = gvc._nearest_fill(det_elev, fp & np.isfinite(det_elev))
    slope_fill = gvc._nearest_fill(det_slope, fp & np.isfinite(det_slope))
    j100_raw, j100_nms = compute_piedmont_junction(
        elev_fill, slope_fill, fp, sigma_elev=1.5, sigma_slope=1.5, window=(1.0, 3.0, 15.0, 25.0)
    )
    write_col("kg2_junc_100m_raw", j100_raw)
    write_col("kg2_junc_100m_nms", j100_nms)
    del j100_raw, j100_nms, slope_fill

    s10_grid = np.full((h, w), np.nan, dtype=np.float32)
    s10_grid.ravel()[fp_ids] = np.asarray(
        np.load(dem10_dir / "dem10_slope_mean.f32.npy", mmap_mode="r"), dtype=np.float32
    )
    s10_deg = np.rad2deg(np.arctan(np.maximum(s10_grid, 0.0)))
    s10_fill = gvc._nearest_fill(s10_deg, fp & np.isfinite(s10_deg))
    j10_raw, _ = compute_piedmont_junction(
        elev_fill, s10_fill, fp, sigma_elev=1.2, sigma_slope=1.2, window=(0.8, 2.5, 16.0, 28.0)
    )
    write_col("kg2_junc_10m_raw", j10_raw)
    del s10_grid, s10_deg, s10_fill, j10_raw

    # 4. 3 m DEM gated scarp & gravity-strike kinematic coherence
    iso_grav = unpack_base("iso_grav_anom")
    grav_fill = gvc._nearest_fill(iso_grav, fp & np.isfinite(iso_grav))
    ggy, ggx = np.gradient(gaussian_filter(grav_fill, 1.5, mode="nearest"), 100.0)
    grav_grad_mag = np.hypot(ggx, ggy).astype(np.float32)
    # Fault strike from gravity horizontal gradient vector is perpendicular to gradient
    theta_grav_strike = np.arctan2(ggy, ggx) + 0.5 * np.pi

    scarp3m_path = data_dir / "external/h52_scarp3m_100m.tif"
    with rasterio.open(scarp3m_path) as ds3:
        h07_raw = ds3.read(1)
        facing_raw = ds3.read(5)
        strike_raw = ds3.read(6)
        cov_raw = ds3.read(7)
    valid3 = fp & (cov_raw > 0) & (h07_raw > -32000) & (facing_raw > -32000) & (strike_raw > -32000)
    h07_m = np.full((h, w), np.nan, dtype=np.float32)
    h07_m[valid3] = np.maximum(h07_raw[valid3].astype(np.float32), 0.0) / 100.0
    write_col("kg2_scarp3m_h_gate07", h07_m)

    kin3 = np.full((h, w), np.nan, dtype=np.float32)
    anti_frac = np.clip(facing_raw[valid3].astype(np.float32) / 10000.0, 0.0, 1.0)
    th3 = np.deg2rad(strike_raw[valid3].astype(np.float32) / 100.0)
    strike_align = 0.5 + 0.5 * np.cos(2.0 * (th3 - theta_grav_strike[valid3]))
    kin3[valid3] = (anti_frac * np.log1p(h07_m[valid3]) * strike_align).astype(np.float32)
    write_col("kg2_scarp3m_antislope_kin", kin3)
    del h07_raw, facing_raw, strike_raw, cov_raw, valid3, h07_m, kin3, iso_grav, theta_grav_strike
    gc.collect()

    # 5. Exact 2D Fourier upward-continued shallow magnetite-destruction & Gallardo-Meju cross-gradient
    rtp = unpack_base("rtp")
    rtp_valid = fp & np.isfinite(rtp)
    rtp_fill = gvc._nearest_fill(rtp, rtp_valid)
    rtp_up250 = fft_upward_continue(rtp_fill, height_m=250.0, dx_m=100.0)
    shallow_demag = -(rtp_fill - rtp_up250)  # positive (nT) where shallow magnetite is destroyed
    demag_gated = (shallow_demag * np.log1p(grav_grad_mag * 1e4)).astype(np.float32)
    demag_gated[~rtp_valid] = np.nan
    write_col("kg2_fft_rtp_demag_250m", demag_gated)
    del rtp, shallow_demag, demag_gated

    rgy, rgx = np.gradient(gaussian_filter(rtp_up250, 1.2, mode="nearest"), 100.0)
    rtp_grad_mag = np.hypot(rgx, rgy).astype(np.float32)
    cross_sin = np.abs(ggx * rgy - ggy * rgx) / (grav_grad_mag * rtp_grad_mag + 1e-12)
    gm_prod = np.sqrt(grav_grad_mag * rtp_grad_mag)
    xgrad_align = ((1.0 - np.clip(cross_sin, 0.0, 1.0)) * gm_prod).astype(np.float32)
    xgrad_align[~rtp_valid] = np.nan
    write_col("kg2_gallardo_meju_xgrad", xgrad_align)
    del rtp_fill, rtp_up250, rgy, rgx, rtp_grad_mag, cross_sin, gm_prod, xgrad_align
    del grav_fill, ggy, ggx, grav_grad_mag
    gc.collect()

    # 6. Local 2.5 km high-pass clay-cap conductivity anomaly (playa-basin background suppressed)
    cond = unpack_base("cond_surf")
    c_valid = fp & np.isfinite(cond)
    log_cond = np.zeros((h, w), dtype=np.float32)
    log_cond[c_valid] = np.log1p(np.maximum(cond[c_valid], 0.0))
    log_cond_fill = gvc._nearest_fill(log_cond, c_valid)
    clay_res = (
        log_cond_fill - gaussian_filter(log_cond_fill, sigma=25.0, mode="nearest")
    ).astype(np.float32)
    clay_res[~c_valid] = np.nan
    write_col("kg2_claycap_depth_resid", clay_res)
    del cond, det_elev, elev_fill, log_cond, log_cond_fill, clay_res

    # 7. Walker Lane transtensional strain potency x declustered microseismic density
    dil = unpack_base("geod_dilaterate")
    shr = unpack_base("geod_shearrate")
    ts_valid = fp & np.isfinite(dil) & np.isfinite(shr)
    deq_pos = np.where(fp & np.isfinite(deq_grid), np.maximum(deq_grid, 0.0), 0.0)
    ts_vent = (
        np.sqrt(
            np.maximum(np.where(ts_valid, dil, 0.0), 0.0)
            * np.maximum(np.where(ts_valid, shr, 0.0), 0.0)
        )
        * (1.0 + np.log1p(deq_pos))
    ).astype(np.float32)
    ts_vent[~ts_valid] = np.nan
    write_col("kg2_transtension_seis_vent", ts_vent)
    del dil, shr, deq_grid, deq_pos, ts_vent
    gc.collect()

    mm.flush()
    del mm
    partial.replace(out_npy_path)
    return np.load(out_npy_path, mmap_mode="r"), list(KG2_EXTRA_NAMES)


def _sample_soft_dti_rows(
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    fp_ids: np.ndarray,
    *,
    max_core: int = 25_000,
    max_halo: int = 25_000,
    max_far: int = 65_000,
    seed: int = 20261026,
) -> tuple[np.ndarray, np.ndarray]:
    """Sample training rows and exact 300 m Soft-DTI kernel target strictly from visible faults."""
    rng = np.random.default_rng(seed)
    dist_vis = distance_transform_edt(~visible_mask).astype(np.float32)
    # Multi-strand 300 m step-over density strictly on visible faults
    yy, xx = np.ogrid[-3:4, -3:4]
    kern = np.maximum(0.0, 1.0 - np.hypot(yy, xx) / 3.0).astype(np.float32)
    vis_density = convolve(visible_mask.astype(np.float32), kern, mode="constant", cval=0.0)
    # Soft-DTI target in [0, 1]: triangular kernel to nearest visible fault + mild step-over bonus
    k_nearest = np.maximum(0.0, 1.0 - dist_vis / 3.0)
    stepover_bonus = np.clip((vis_density - 1.5) * 0.08, 0.0, 0.20)
    y_soft_grid = np.clip(k_nearest + np.where(k_nearest > 0.0, stepover_bonus, 0.0), 0.0, 1.0)
    del dist_vis, vis_density, k_nearest, stepover_bonus

    t_fp = train_mask.ravel()[fp_ids]
    v_fp = visible_mask.ravel()[fp_ids]
    y_fp = y_soft_grid.ravel()[fp_ids]

    core_ids = np.flatnonzero(t_fp & v_fp)
    halo_ids = np.flatnonzero(t_fp & (~v_fp) & (y_fp > 0.0))
    far_ids = np.flatnonzero(t_fp & (y_fp == 0.0))

    c_sel = (
        rng.choice(core_ids, size=max_core, replace=False) if len(core_ids) > max_core else core_ids
    )
    h_sel = (
        rng.choice(halo_ids, size=max_halo, replace=False) if len(halo_ids) > max_halo else halo_ids
    )
    f_sel = rng.choice(far_ids, size=max_far, replace=False) if len(far_ids) > max_far else far_ids

    rows = np.concatenate([c_sel, h_sel, f_sel])
    order = np.argsort(rows)
    rows = rows[order]
    return rows, y_fp[rows].astype(np.float32)


def fit_and_predict_dualhead_fold(
    base_mm: np.ndarray,
    gvc_mm: np.ndarray,
    sahg_mm: np.ndarray,
    kg2_mm: np.ndarray,
    nuisance_fp: np.ndarray,
    all_names: list[str],
    fp: np.ndarray,
    fp_ids: np.ndarray,
    *,
    train_mask: np.ndarray,
    visible_mask: np.ndarray,
    predict_mask: np.ndarray,
    seed: int,
    core_weight: float = 0.56,
    chunk_size: int = 200_000,
    precomputed_core: tuple[np.ndarray, np.ndarray, dict[str, Any]] | None = None,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict[str, Any]]:
    """Fit Core Classifier + 300 m Soft-DTI Kernel Regressor strictly on (train_mask, visible_mask).

    Returns:
      - ``p_dual_sharp``: primary ridge-sharpened Dual-Head fault expectancy surface
      - ``p_piedmont``: low-slope (<= 6.5 deg) alluvial piedmont & step-over specialist surface
      - ``p_conduit``: concealed basin & blind geothermal vent / demagnetization conduit surface
      - ``diag``: fold diagnostics
    """
    # 1. Core calibrated classifier head (reusing shared DPRF1 pipeline with 78 channels)
    if precomputed_core is not None:
        p_core_sharp, p_core_cond, core_meta = precomputed_core
    else:
        p_core_sharp, p_core_cond, core_meta = dprf1.fit_and_predict_fold(
            base_mm,
            gvc_mm,
            sahg_mm,
            nuisance_fp,
            all_names,
            fp,
            fp_ids,
            train_mask=train_mask,
            visible_mask=visible_mask,
            predict_mask=predict_mask,
            neg_mode="stratified_d3",
            seed=seed,
            chunk_size=chunk_size,
            extra_mm=kg2_mm,
            regime_b_extra_names=KG2_REGIME_B_EXTRA,
            selective_extra_names=KG2_SELECTIVE_RESID_EXTRA,
        )

    # 2. 300 m Soft-DTI Kernel Expectancy Regressor head
    sel_names = sorted(set(dprf1.SELECTIVE_RESID_NAMES) | set(KG2_SELECTIVE_RESID_EXTRA))
    sel_indices = [all_names.index(nm) for nm in sel_names]
    g_sat_idx = all_names.index("sahg_g_sat")
    slope_idx = all_names.index(dprf1.STEEP_SLOPE_NAME)
    rel_idx = all_names.index(dprf1.LOCAL_RELIEF_NAME)
    pied_col_map = {nm: all_names.index(nm) for nm in KG2_PIEDMONT_BOOST_NAMES}

    soft_rows, y_soft = _sample_soft_dti_rows(train_mask, visible_mask, fp_ids, seed=seed + 7)
    bg_mask = train_mask & (~visible_mask)
    bg_pool = np.flatnonzero(bg_mask.ravel()[fp_ids])
    bg_disjoint = np.setdiff1d(bg_pool, soft_rows, assume_unique=False)
    if len(bg_disjoint) < 5_000:
        bg_disjoint = bg_pool
    rng_bg = np.random.default_rng(seed + 83)
    bg_sel = np.sort(rng_bg.choice(bg_disjoint, size=min(35_000, len(bg_disjoint)), replace=False))

    x_bg = dprf1.read_stack_rows(bg_sel, base_mm, gvc_mm, sahg_mm, kg2_mm)
    c_bg = np.asarray(nuisance_fp[bg_sel], dtype=np.float32)
    resid = dprf1.SelectiveNonTopographicResidualizer(sel_indices, alpha=100.0).fit(c_bg, x_bg)
    pied_scaler = dprf1.TrainQuantileGateScaler(pied_col_map).fit(x_bg)
    x_bg_res = resid.transform_inplace(c_bg, x_bg.copy())

    x_soft = dprf1.read_stack_rows(soft_rows, base_mm, gvc_mm, sahg_mm, kg2_mm)
    c_soft = np.asarray(nuisance_fp[soft_rows], dtype=np.float32)
    resid.transform_inplace(c_soft, x_soft)

    reg_models: list[HistGradientBoostingRegressor] = []
    with threadpool_limits(limits=2):
        for s_off in (310, 410):
            reg = HistGradientBoostingRegressor(
                loss="squared_error",
                max_iter=185,
                learning_rate=0.055,
                max_leaf_nodes=31,
                min_samples_leaf=85,
                l2_regularization=3.0,
                early_stopping=False,
                random_state=seed + s_off,
            )
            reg.fit(x_soft, y_soft)
            reg_models.append(reg)

        p_bg_soft = np.clip(
            0.5 * (reg_models[0].predict(x_bg_res) + reg_models[1].predict(x_bg_res)),
            1e-5,
            1.0 - 1e-5,
        ).astype(np.float32)
        soft_cal = dprf1.ReliefConditionedCalibrator(alpha=100.0).fit(
            p_bg_soft,
            has_lidar_bg=np.isfinite(x_bg[:, g_sat_idx]),
            nuisance_bg=c_bg,
            slope_bg=x_bg[:, slope_idx],
            local_relief_bg=x_bg[:, rel_idx],
        )
        del x_soft, c_soft, x_bg, x_bg_res, c_bg, p_bg_soft
        gc.collect()

        pred_rows = np.flatnonzero(predict_mask.ravel()[fp_ids])
        p_soft_vec = np.empty(len(pred_rows), dtype=np.float32)
        pied_mult_vec = np.empty(len(pred_rows), dtype=np.float32)

        for start in range(0, len(pred_rows), chunk_size):
            sl = pred_rows[start : start + chunk_size]
            x_raw = dprf1.read_stack_rows(sl, base_mm, gvc_mm, sahg_mm, kg2_mm)
            c_sl = np.asarray(nuisance_fp[sl], dtype=np.float32)

            # Compute low-slope alluvial piedmont specialist multiplier before residualization
            slope_vals = np.where(np.isfinite(x_raw[:, slope_idx]), x_raw[:, slope_idx], 10.0)
            low_slope_gate = np.clip((7.5 - slope_vals) / 4.5, 0.0, 1.0).astype(np.float32)
            sigs = []
            for nm, cidx in pied_col_map.items():
                med, sc = pied_scaler.stats_[nm]
                v = x_raw[:, cidx]
                z = np.where(np.isfinite(v), (v - med) / sc, 0.0)
                sigs.append(1.0 / (1.0 + np.exp(-np.clip(z, -8.0, 8.0))))
            pied_score = np.mean(sigs, axis=0).astype(np.float32)
            pied_mult_vec[start : start + len(sl)] = low_slope_gate * (0.45 + 0.95 * pied_score)

            has_lid = np.isfinite(x_raw[:, g_sat_idx])
            slp_s = x_raw[:, slope_idx].copy()
            rel_s = x_raw[:, rel_idx].copy()
            resid.transform_inplace(c_sl, x_raw)
            ps = np.clip(
                0.5 * (reg_models[0].predict(x_raw) + reg_models[1].predict(x_raw)),
                1e-5,
                1.0 - 1e-5,
            ).astype(np.float32)
            p_soft_vec[start : start + len(sl)] = soft_cal.transform(
                ps, has_lidar=has_lid, nuisance=c_sl, slope=slp_s, local_relief=rel_s
            )
            del x_raw, c_sl, has_lid, slp_s, rel_s, ps

    p_soft_grid = np.zeros(fp.shape, dtype=np.float32)
    p_soft_grid.ravel()[fp_ids[pred_rows]] = p_soft_vec
    p_soft_sharp = dprf1.sharpen_ridge_coherence(p_soft_grid, predict_mask, half_len_px=4)
    del p_soft_grid, p_soft_vec

    pied_mult_grid = np.zeros(fp.shape, dtype=np.float32)
    pied_mult_grid.ravel()[fp_ids[pred_rows]] = pied_mult_vec
    del pied_mult_vec

    w_c = float(core_weight)
    p_dual_sharp = (w_c * p_core_sharp + (1.0 - w_c) * p_soft_sharp).astype(np.float32)
    p_piedmont = np.clip(p_dual_sharp * pied_mult_grid, 0.0, 1.0).astype(np.float32)
    # Enhance concealed hydrothermal/vent conduit surface with soft-DTI kernel expectancy
    ratio_cond = np.where(p_core_sharp > 1e-6, p_core_cond / (p_core_sharp + 1e-6), 0.0)
    p_conduit = np.clip(p_dual_sharp * ratio_cond, 0.0, 1.0).astype(np.float32)

    diag = {
        **core_meta,
        "soft_dti_train_rows": int(len(soft_rows)),
        "core_weight": w_c,
        "dual_mean_pred": float(p_dual_sharp[predict_mask].mean()),
        "piedmont_mean_pred": float(p_piedmont[predict_mask].mean()),
        "conduit_mean_pred": float(p_conduit[predict_mask].mean()),
    }
    return p_dual_sharp, p_piedmont, p_conduit, diag


def three_regime_submodular_allocate(
    p_primary: np.ndarray,
    p_piedmont: np.ndarray,
    p_conduit: np.ndarray,
    domain_mask: np.ndarray,
    visible_catalogue: np.ndarray,
    *,
    budget: int,
    shares: tuple[float, float, float] = (0.54, 0.22, 0.24),
    min_spacing_px: float = 3.0,
    catalogue_clearance_px: float = 2.0,
) -> np.ndarray:
    """Sequential Three-Regime 300 m Triangular-Kernel Submodular CELF Allocator.

    Stage 1 (shares[0]): Exposed & 10m-gap-bridged range-front / piedmont junctions.
    Stage 2 (shares[1]): Low-slope (<= 6.5 deg) alluvial piedmont & step-over splays,
                         inheriting exact 300 m kernel coverage from Stage 1.
    Stage 3 (remaining): Concealed basin & blind geothermal vent / demagnetization conduits,
                         inheriting exact 300 m kernel coverage from Stages 1 + 2.
    """
    if budget <= 0:
        return np.zeros(p_primary.shape, dtype=np.float32)
    s1, s2, s3 = shares
    if abs((s1 + s2 + s3) - 1.0) > 1e-5:
        raise ValueError("Three-regime shares must sum to 1.0")

    k1 = max(0, min(budget, int(round(budget * s1))))
    k2 = max(0, min(budget - k1, int(round(budget * s2))))

    # Stage 1: Primary multi-scale scarp & junction surface
    dots = dprf1._submodular_stage(
        p_primary,
        domain_mask,
        visible_catalogue,
        target_add=k1,
        min_spacing_px=min_spacing_px,
        catalogue_clearance_px=catalogue_clearance_px,
        existing_dots=None,
    )
    # Stage 2: Low-slope alluvial piedmont & step-over splays
    rem_after_1 = max(0, budget - int((dots > 0.5).sum()))
    if k2 > 0 and rem_after_1 > 0:
        dots = dprf1._submodular_stage(
            p_piedmont,
            domain_mask,
            visible_catalogue,
            target_add=min(k2, rem_after_1),
            min_spacing_px=min_spacing_px,
            catalogue_clearance_px=catalogue_clearance_px,
            existing_dots=dots,
        )
    # Stage 3: Concealed basin & blind geothermal vent / hydrothermal conduits (fills exact budget)
    rem_after_2 = max(0, budget - int((dots > 0.5).sum()))
    if rem_after_2 > 0:
        dots = dprf1._submodular_stage(
            p_conduit,
            domain_mask,
            visible_catalogue,
            target_add=rem_after_2,
            min_spacing_px=min_spacing_px,
            catalogue_clearance_px=catalogue_clearance_px,
            existing_dots=dots,
        )
    # Fallback top-up on primary if specialist thresholds left any unspent budget
    rem_final = max(0, budget - int((dots > 0.5).sum()))
    if rem_final > 0:
        dots = dprf1._submodular_stage(
            p_primary,
            domain_mask,
            visible_catalogue,
            target_add=rem_final,
            min_spacing_px=min_spacing_px,
            catalogue_clearance_px=catalogue_clearance_px,
            existing_dots=dots,
        )
    return dots.astype(np.float32)
