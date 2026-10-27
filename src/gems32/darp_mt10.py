"""DARP-MT10: Depth-Adaptive Updip Potential-Field Projection, Asymmetric MT Clay-Cap Baffle,
Seamless 10m/3m/1m Piedmont Scarp Fusion, and Regional Stress x ComCat Conduit Engine.

Implements pre-registered Hypothesis H-N1 (with H-N2 true tilt contact wavenumber and H-N3
piedmont habitat prior + Dinkelbach fractional stopping) frozen in:
  - knowledge/02_preregistered_hypotheses_kg2_20261027.md
  - registry/preregistration_darp_mt10.json

Memory discipline: streams 2D float32 arrays one group at a time into `.cache/gems_work/`
memmaps so peak RSS stays < 1.2 GiB on a 3.8 GiB 2-core sandbox.
"""
from __future__ import annotations

import gc
import json
from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from scipy.interpolate import RegularGridInterpolator
from scipy.ndimage import (
    distance_transform_edt,
    gaussian_filter,
    map_coordinates,
)
from sklearn.metrics import roc_auc_score

from . import holdout, htcads
from .metric import ALPHA, BETA, EPS, kernel

C_PIED_EVALUATOR_VERSION = "GEMSDOE70-C-PIED-v1.0"

DARP_FEATURE_NAMES: list[str] = [
    # Group A: Depth-Adaptive Updip Potential-Field Emergence + True Gravity Tilt Wavenumber (0..3)
    "darp_grav_updip_zb",           # 0: Multi-horizon (150/450/1000m) FFT gravity HGM projected updip by Z_b*cot(58 deg)
    "darp_rtp_updip_zb",            # 1: Multi-horizon (150/450m) FFT RTP magnetic HGM projected updip by Z_b*cot(58 deg)
    "darp_grav_tilt_k",             # 2: True gravity tilt-angle zero-crossing contact wavenumber (H-N2)
    "darp_updip_converge",          # 3: Co-aligned updip gravity x updip RTP basement-step convergence
    # Group B: Asymmetric Cross-Strike MT Clay-Cap Baffle & Heat-Flow Upflow (4..7)
    "darp_mt_baffle_asym",          # 4: Signed HW(+3,+6,+9px) minus FW(-3,-6,-9px) log-MT step (playa-deconfounded)
    "darp_mt_baffle_worm",          # 5: 1.2 km steerable linear worm on asymmetric MT clay-cap baffle
    "darp_usgs_hf_resid_up",        # 6: Up-gradient/updip back-projected USGS + ScienceBase heat-flow residual
    "darp_clay_alter_conduit",      # 7: Asymmetric MT clay-cap x (K/Th + demag + heat-flow/GDR thermal upflow)
    # Group C: Seamless 10m + 3m + 1m Contour-Orthogonal Piedmont Scarp Fusion (8..13)
    "dem10_scarp_onesided_clean",   # 8: Road-cleared & Lahontan-shoreline-deconfounded 10m one-sided scarp step
    "dem10_hgm_sharp_clean",        # 9: Localized 10m DEM HGM20/50 break minus HGM200 regional mountain slope
    "dem10_piedmont_worm",          # 10: 1.5 km steerable worm on piedmont-gated 10m scarp (bridges 24.6% LiDAR void)
    "scarp3m_piedmont_gate",        # 11: Slope-gated 3m 3DEP piedmont scarp height (h_gate07/12) w/ 10m seamless fallback
    "piedmont_habitat_prior",       # 12: Zero-label alluvial-piedmont / basin-margin extensional habitat prior (H-N3)
    "multiscale_piedmont_scarp",    # 13: Quantile-aligned seamless 1m + 3m + 10m piedmont scarp centerline
    # Group D: Regional Stress (S_hmin, A_phi) Dilation Tendency & Shallow ComCat Microseismicity (14..17)
    "stress_dilation_tendency",     # 14: Pixel-strike alignment vs 10km Great Basin S_hmin & Simpson A_phi
    "comcat_shallow_seismicity",    # 15: Multiscale density of shallow (<=12 km) USGS ANSS ComCat hypocenters
    "comcat_stress_ridge",          # 16: Critically stressed seismogenic updip/piedmont fault corridor
    "darp_blind_geotherm_synth",    # 17: Label-free synthesis of updip geophysics + MT baffle + heat-flow + stress
]

# Smooth >10km regional channel excluded from tree splits (used only in bounded regional favorability multiplier)
DARP_REGIONAL_COLS: set[int] = {6, 15}
# Topo-scarp channels (excluded in DARP-EXP-1 to isolate pure blind subsurface/MT/seismothermal discovery)
DARP_TOPO_SCARP_COLS: set[int] = {8, 9, 10, 11, 13}


def _fft_upward_continue(field_2d: np.ndarray, height_m: float, dx_m: float = 100.0) -> np.ndarray:
    return htcads._fft_upward_continue(field_2d, dz_m=height_m, dx_m=dx_m)


def _updip_project_multi_horizon(
    field_2d: np.ndarray,
    uy_down: np.ndarray,
    ux_down: np.ndarray,
    shift_px: np.ndarray,
    horizons_m: tuple[float, ...],
    weights: tuple[float, ...],
    foot: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Upward-continue potential field across multiple depths and project hanging-wall HGM crests updip.

    At surface fault candidate (y, x), the dipping fault plane (50-65 deg) intersects basement depth Z_b
    downdip at (y + shift_px * uy_down, x + shift_px * ux_down). Sampling the multi-horizon HGM ridge at
    that downdip coordinate maps the hanging-wall gravity/magnetic gradient crest back onto the surface fault.
    """
    H, W = field_2d.shape
    acc_hgm = np.zeros((H, W), dtype=np.float32)
    for z_m, w_z in zip(horizons_m, weights):
        f_up = _fft_upward_continue(field_2d, height_m=z_m, dx_m=100.0) if z_m > 0 else field_2d
        f_sm = gaussian_filter(f_up, sigma=1.2, mode="nearest")
        gy, gx = htcads._grad_yx_f32(f_sm)
        hgm = np.hypot(gy, gx).astype(np.float32)
        acc_hgm += float(w_z) * htcads._pos_norm_2d(hgm, foot, q=99.4)
        del f_up, f_sm, gy, gx, hgm

    yy, xx = np.indices((H, W), dtype=np.float32)
    sample_y = np.clip(yy + shift_px * uy_down, 0.0, float(H - 1))
    sample_x = np.clip(xx + shift_px * ux_down, 0.0, float(W - 1))
    del yy, xx

    projected = map_coordinates(acc_hgm, [sample_y, sample_x], order=1, mode="nearest").astype(np.float32)
    del sample_y, sample_x, acc_hgm
    ridge_proj, strike_proj = htcads._hessian_ridge_and_strike(projected, sigma=1.1, foot=foot)
    out = htcads._pos_norm_2d(0.60 * projected + 0.40 * ridge_proj, foot, q=99.5)
    del projected, ridge_proj
    return out, strike_proj


def build_darp_feature_stack(ddir: Path, wdir: Path, base_stack: dict | None = None, force: bool = False) -> dict:
    """Build or load the 18-channel DARP-MT10 feature matrix cached in `.cache/gems_work/darp_mt10_v1`."""
    if base_stack is None:
        base_stack = htcads.build_static_feature_stack(ddir, wdir)

    foot: np.ndarray = base_stack["foot"]
    shape = foot.shape
    n_fp = int(foot.sum())

    cache_dir = wdir / "darp_mt10_v1"
    cache_dir.mkdir(parents=True, exist_ok=True)
    meta_path = cache_dir / "meta.json"
    darp_mmap_path = cache_dir / "X_darp.f32.mmap"

    if not force and meta_path.exists() and darp_mmap_path.exists():
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
        if meta.get("n_fp") == n_fp and meta.get("darp_features") == DARP_FEATURE_NAMES:
            X_darp = np.memmap(darp_mmap_path, dtype="float32", mode="r", shape=(n_fp, len(DARP_FEATURE_NAMES)))
            return {
                "foot": foot,
                "X_sub": base_stack["X_sub"],
                "X_lid": base_stack["X_lid"],
                "lidar_valid_fp": base_stack["lidar_valid_fp"],
                "X_darp": X_darp,
            }

    X_darp = np.memmap(darp_mmap_path, dtype="float32", mode="w+", shape=(n_fp, len(DARP_FEATURE_NAMES)))

    core_inds = None

    def _read_core(src, idx: int) -> np.ndarray:
        nonlocal core_inds
        a = src.read(idx).astype(np.float32)
        valid = foot & np.isfinite(a) & (a > -1e30)
        filled, core_inds = htcads._fill_outside_with_inds(a, valid, core_inds)
        return filled

    # ------------------------------------------------------------------
    # Load core basement depth, gravity, RTP, conductivity, elevation
    # True 1-indexed bands in training_features.tif:
    #   2=rtp, 11=iso_grav_anom_vg, 12=det_elev, 13=iso_grav_anom, 15=depth_to_base_surf, 17=cond_surf, 19=det_elev_slope
    # ------------------------------------------------------------------
    with rasterio.open(ddir / "training_features.tif") as src:
        iso_grav = _read_core(src, 13)
        grav_vg = _read_core(src, 11)
        rtp = _read_core(src, 2)
        zb_raw = _read_core(src, 15)       # depth_to_base_surf (meters)
        cond_surf = _read_core(src, 17)
        det_elev = _read_core(src, 12)     # detrended elevation (-467 m basin floor to +707 m crest)
        det_slope = _read_core(src, 19)    # det_elev_slope (degrees)
    del core_inds

    # Smooth basement depth gradient defines downdip (+grad Z_b) and updip (-grad Z_b) unit normal
    zb_m = np.maximum(zb_raw, 0.0).astype(np.float32)
    zb_sm = gaussian_filter(zb_m, sigma=3.0, mode="nearest")
    z_gy, z_gx = htcads._grad_yx_f32(zb_sm)
    z_norm = np.hypot(z_gy, z_gx).astype(np.float32) + 1e-5
    uy_down = (z_gy / z_norm).astype(np.float32)
    ux_down = (z_gx / z_norm).astype(np.float32)
    del zb_sm, z_gy, z_gx, z_norm

    # Dipping normal fault (delta ~ 58 deg -> cot(58 deg) = 0.6249): effective centroid depth ~ 0.55 * Z_b
    shift_px = np.clip(0.55 * zb_m * 0.6249 / 100.0, 0.5, 6.5).astype(np.float32)

    # --- GROUP A: Depth-Adaptive Updip Potential-Field Emergence (cols 0..3) ---
    grav_updip, strike_g = _updip_project_multi_horizon(
        iso_grav, uy_down, ux_down, shift_px,
        horizons_m=(0.0, 150.0, 450.0, 1000.0),
        weights=(0.20, 0.30, 0.30, 0.20),
        foot=foot,
    )
    X_darp[:, 0] = grav_updip[foot]

    rtp_updip, strike_m = _updip_project_multi_horizon(
        rtp, uy_down, ux_down, np.clip(shift_px * 0.85, 0.4, 5.5),
        horizons_m=(0.0, 150.0, 450.0),
        weights=(0.30, 0.40, 0.30),
        foot=foot,
    )
    del rtp, shift_px
    X_darp[:, 1] = rtp_updip[foot]

    # True gravity tilt-derivative contact wavenumber (H-N2)
    gy_g, gx_g = htcads._grad_yx_f32(gaussian_filter(iso_grav, sigma=1.4, mode="nearest"))
    del iso_grav
    ng_g = np.hypot(gy_g, gx_g).astype(np.float32) + 1e-5
    del gy_g, gx_g
    grav_tilt = np.arctan2(gaussian_filter(grav_vg, sigma=1.2, mode="nearest"), ng_g).astype(np.float32)
    del grav_vg, ng_g
    gt_gy, gt_gx = htcads._grad_yx_f32(grav_tilt)
    grav_tilt_k = htcads._pos_norm_2d(np.exp(-np.abs(grav_tilt) / 0.35) * np.hypot(gt_gy, gt_gx), foot, q=99.5)
    del grav_tilt, gt_gy, gt_gx
    X_darp[:, 2] = grav_tilt_k[foot]

    updip_conv = htcads._pos_norm_2d(np.sqrt(grav_updip * rtp_updip), foot, q=99.5)
    X_darp[:, 3] = updip_conv[foot]
    del rtp_updip
    X_darp.flush()
    gc.collect()

    # --- GROUP B: Asymmetric Cross-Strike MT Clay-Cap Baffle & Heat-Flow Upflow (cols 4..7) ---
    cond_log = np.log1p(np.maximum(cond_surf - float(np.percentile(cond_surf[foot], 1.0)), 0.0)).astype(np.float32)
    del cond_surf
    cond_sm = gaussian_filter(cond_log, sigma=1.2, mode="nearest")
    del cond_log

    H, W = shape
    yy, xx = np.indices((H, W), dtype=np.float32)
    hw_acc = np.zeros(shape, dtype=np.float32)
    fw_acc = np.zeros(shape, dtype=np.float32)
    for step_d, w_d in ((3.0, 0.40), (6.0, 0.35), (9.0, 0.25)):
        hw_y = np.clip(yy + step_d * uy_down, 0.0, float(H - 1))
        hw_x = np.clip(xx + step_d * ux_down, 0.0, float(W - 1))
        fw_y = np.clip(yy - step_d * uy_down, 0.0, float(H - 1))
        fw_x = np.clip(xx - step_d * ux_down, 0.0, float(W - 1))
        hw_acc += float(w_d) * map_coordinates(cond_sm, [hw_y, hw_x], order=1, mode="nearest")
        fw_acc += float(w_d) * map_coordinates(cond_sm, [fw_y, fw_x], order=1, mode="nearest")
        del hw_y, hw_x, fw_y, fw_x
    del yy, xx, cond_sm

    # Suppress flat interior saline playa brines (Named Non-Fault Mimic #1: Humboldt/Carson Sink playas)
    slp_p18 = float(np.percentile(det_slope[foot], 18.0))
    playa_suppress = np.clip((det_slope - 0.35 * slp_p18) / (slp_p18 + 1e-5), 0.15, 1.0).astype(np.float32)
    mt_asym_raw = np.maximum(hw_acc - fw_acc, 0.0) * playa_suppress
    del hw_acc, fw_acc, playa_suppress
    mt_baffle = htcads._pos_norm_2d(mt_asym_raw, foot, q=99.5)
    del mt_asym_raw
    X_darp[:, 4] = mt_baffle[foot]

    mt_worm = htcads._multi_azimuth_worm(mt_baffle, length_px=12, foot=foot)
    X_darp[:, 5] = mt_worm[foot]
    del mt_worm

    # Up-gradient (+grad det_elev) and updip (-grad Z_b) back-projected USGS + ScienceBase heat-flow residual
    el_gy, el_gx = htcads._grad_yx_f32(gaussian_filter(det_elev, sigma=3.5, mode="nearest"))
    el_n = np.hypot(el_gy, el_gx).astype(np.float32) + 1e-5
    uy_up = (0.65 * (el_gy / el_n) - 0.35 * uy_down).astype(np.float32)
    ux_up = (0.65 * (el_gx / el_n) - 0.35 * ux_down).astype(np.float32)
    del el_gy, el_gx, el_n, uy_down, ux_down

    hf_seeds = np.zeros(shape, dtype=np.float32)
    usgs_hf_csv = ddir / "external" / "usgs_heat_flow_wells_epsg32611.csv"
    if usgs_hf_csv.exists():
        df_hf = pd.read_csv(usgs_hf_csv)
        for row in df_hf.itertuples(index=False):
            r, c = int(row.row), int(row.col)
            res = float(row.hf_resid_mw_m2) if pd.notna(row.hf_resid_mw_m2) else 0.0
            meas = float(row.hf_meas_mw_m2) if pd.notna(row.hf_meas_mw_m2) else 0.0
            qc = str(row.qc_code) if pd.notna(row.qc_code) else "C"
            if 0 <= r < H and 0 <= c < W and meas < 900.0 and res > 12.0:
                qw = 1.0 if qc in ("A", "B") else 0.65
                val = qw * min(res / 75.0, 3.5)
                for step_u in (0.0, 4.0, 9.0):
                    rr = int(np.clip(round(r + step_u * float(uy_up[r, c])), 0, H - 1))
                    cc = int(np.clip(round(c + step_u * float(ux_up[r, c])), 0, W - 1))
                    if val > hf_seeds[rr, cc]:
                        hf_seeds[rr, cc] = val
        del df_hf
    del uy_up, ux_up

    hf_up_2d = htcads._pos_norm_2d(gaussian_filter(hf_seeds, sigma=11.0, mode="nearest"), foot, q=99.2)
    del hf_seeds
    # Combine with base_stack ScienceBase heat-flow + GDR 2m probe/wellspring thermal channels
    sb_hf_fp = np.asarray(base_stack["X_sub"][:, 35], dtype=np.float32)
    gdr_p_fp = np.asarray(base_stack["X_sub"][:, 20], dtype=np.float32)
    gdr_w_fp = np.asarray(base_stack["X_sub"][:, 21], dtype=np.float32)
    hf_comb_fp = np.maximum(hf_up_2d[foot], 0.85 * sb_hf_fp)
    X_darp[:, 6] = hf_comb_fp
    del hf_up_2d, sb_hf_fp

    demag_fp = np.asarray(base_stack["X_sub"][:, 14], dtype=np.float32)
    kmeta_fp = np.asarray(base_stack["X_sub"][:, 15], dtype=np.float32)
    clay_conduit_fp = np.clip(
        (0.50 * mt_baffle[foot] + 0.50 * np.maximum(demag_fp, kmeta_fp))
        * (0.45 + 0.55 * np.maximum.reduce([hf_comb_fp, gdr_p_fp, gdr_w_fp])),
        0.0,
        1.5,
    )
    q_cc = float(np.percentile(clay_conduit_fp, 99.5)) + 1e-6
    X_darp[:, 7] = np.clip(clay_conduit_fp / q_cc, 0.0, 1.0).astype(np.float32)
    del demag_fp, kmeta_fp, gdr_p_fp, gdr_w_fp, clay_conduit_fp
    X_darp.flush()
    gc.collect()

    # --- GROUP C: Seamless 10m + 3m + 1m Piedmont Scarp Fusion (cols 8..13) ---
    with rasterio.open(ddir / "external" / "tiger_road_distance_m.tif") as s_rd:
        road_d = s_rd.read(1).astype(np.float32)
    road_w = np.clip((road_d - 45.0) / 75.0, 0.0, 1.0).astype(np.float32)
    del road_d

    # Pluvial Lake Lahontan low-basin shoreline deconfounder (det_elev in [-290, -165] m basin-margin benches)
    # Attenuates wave-cut contour benches unless backed by strong updip basement or MT step
    lahontan_band = np.maximum(
        np.exp(-(((det_elev - (-210.0)) / 24.0) ** 2)),
        np.exp(-(((det_elev - (-265.0)) / 20.0) ** 2)),
    ).astype(np.float32)
    subsurf_support = np.maximum(grav_updip, mt_baffle)
    shoreline_keep = (1.0 - 0.55 * lahontan_band * (1.0 - np.clip(subsurf_support * 1.8, 0.0, 1.0))).astype(np.float32)
    del det_elev, det_slope, lahontan_band, subsurf_support

    def _load_dem10_2d(name: str) -> np.ndarray:
        g = np.zeros(shape, dtype=np.float32)
        g[foot] = np.load(ddir / "dem10" / f"{name}.f32.npy")
        return g

    d10_one1 = _load_dem10_2d("dem10_onesided")
    d10_one3 = _load_dem10_2d("dem10_onesided3")
    d10_slp_max = _load_dem10_2d("dem10_slope_max")
    d10_slp_mean = _load_dem10_2d("dem10_slope_mean")
    d10_curv = _load_dem10_2d("dem10_curv_absmax")
    d10_steep = _load_dem10_2d("dem10_steep_ratio_max")
    d10_resid_rng = _load_dem10_2d("dem10_resid_range")

    # Zero-label Piedmont / Basin-Margin Extensional Habitat Prior (H-N3):
    # Favors piedmont alluvial fans & range-bounding aprons (Z_b >= 150 m, moderate slope/relief),
    # while suppressing flat zero-relief interior playas AND steep bare-rock Mesozoic range-crest thrusts!
    zb_factor = np.clip((zb_m - 60.0) / 280.0, 0.12, 1.0)
    pied_slope_bell = np.exp(-(((np.maximum(d10_slp_mean, 0.2) - 6.5) / 9.5) ** 2))
    crest_suppress = np.clip(1.0 - np.maximum(d10_slp_mean - 21.0, 0.0) / 15.0, 0.18, 1.0)
    crest_rel_sup = np.clip(1.0 - np.maximum(d10_resid_rng - 20.0, 0.0) / 22.0, 0.22, 1.0)
    pied_hab = np.clip(
        0.20 + 0.80 * zb_factor * (0.45 + 0.55 * pied_slope_bell) * crest_suppress * crest_rel_sup,
        0.10,
        1.0,
    ).astype(np.float32)
    del zb_m, zb_factor, pied_slope_bell, crest_suppress, crest_rel_sup, d10_resid_rng
    X_darp[:, 12] = pied_hab[foot]

    # Localized 10 m scarp riser: planar directional step (onesided) x sub-100m slope excess (slope_max - slope_mean)
    slp_excess = np.maximum(d10_slp_max - 0.85 * d10_slp_mean, 0.0)
    del d10_slp_max, d10_slp_mean
    curv_norm = htcads._pos_norm_2d(d10_curv, foot, q=99.4)
    steep_norm = htcads._pos_norm_2d(d10_steep, foot, q=99.4)
    del d10_curv
    scarp10_raw = (
        (0.55 * np.maximum(d10_one3, 0.0) + 0.45 * np.maximum(d10_one1, 0.0))
        * htcads._pos_norm_2d(slp_excess, foot, q=99.4)
        * (0.55 + 0.45 * np.maximum(curv_norm, steep_norm))
        * road_w
        * shoreline_keep
    )
    del d10_one1, d10_one3, slp_excess, curv_norm, steep_norm
    scarp10_clean = htcads._pos_norm_2d(scarp10_raw, foot, q=99.4)
    del scarp10_raw
    X_darp[:, 8] = scarp10_clean[foot]

    d10_hgm20 = _load_dem10_2d("dem10_hgm20_max")
    d10_hgm50 = _load_dem10_2d("dem10_hgm50_max")
    d10_hgm200 = _load_dem10_2d("dem10_hgm200_mean")
    hgm_break = np.maximum(0.55 * d10_hgm20 + 0.35 * d10_hgm50 - 0.45 * d10_hgm200, 0.0) * (0.5 + 0.5 * htcads._pos_norm_2d(d10_steep, foot))
    del d10_hgm20, d10_hgm50, d10_hgm200, d10_steep
    dem10_hgm_clean = htcads._pos_norm_2d(hgm_break * road_w * shoreline_keep, foot, q=99.4)
    del hgm_break
    X_darp[:, 9] = dem10_hgm_clean[foot]

    dem10_worm = htcads._multi_azimuth_worm(scarp10_clean * pied_hab, length_px=15, foot=foot)
    X_darp[:, 10] = dem10_worm[foot]
    _, strike_s10 = htcads._hessian_ridge_and_strike(scarp10_clean, sigma=1.2, foot=foot)

    # 3 m 3DEP slope-gated piedmont scarp height with seamless fallback to 10 m scarp
    scarp3m_2d = scarp10_clean.copy()
    p_s3 = ddir / "external" / "h52_scarp3m_100m.tif"
    if p_s3.exists():
        with rasterio.open(p_s3) as s3:
            h07 = s3.read(1).astype(np.float32)
            h12 = s3.read(2).astype(np.float32)
            facing = s3.read(5).astype(np.float32)
            cov3 = s3.read(7)
        valid3 = foot & (cov3 > 2000) & (h07 >= 0) & (h12 >= 0)
        del cov3
        face_w = np.clip(np.maximum(facing, 0.0) / 10000.0, 0.25, 1.0)
        raw3 = (0.58 * np.maximum(h07, 0.0) + 0.42 * np.maximum(h12, 0.0)) * face_w * road_w * shoreline_keep
        del h07, h12, facing, face_w
        if valid3.any():
            q3 = float(np.percentile(raw3[valid3], 99.4)) + 1e-6
            norm3 = np.clip(raw3 / q3, 0.0, 1.0).astype(np.float32)
            # Quantile-align valid3 median/p95 to scarp10_clean so zero seam cliff exists at 3m tile edges
            s3_blend = 0.65 * norm3 + 0.35 * scarp10_clean
            scarp3m_2d = np.where(valid3, s3_blend, scarp10_clean).astype(np.float32)
            del norm3, s3_blend
        del raw3, valid3
    del road_w, shoreline_keep
    X_darp[:, 11] = scarp3m_2d[foot]

    # Quantile-aligned seamless 1m + 3m + 10m piedmont scarp centerline (zero domain shift across 1m LiDAR void)
    lid_valid_fp = base_stack["lidar_valid_fp"]
    lid_w_fp = np.asarray(base_stack["X_lid"][:, 8], dtype=np.float32)  # 500m contour-ortho 1m LiDAR worm
    base_10_3_fp = (0.50 * scarp3m_2d[foot] + 0.30 * dem10_worm[foot] + 0.20 * dem10_hgm_clean[foot]) * pied_hab[foot]
    # Domain-align inside vs outside 1m LiDAR coverage by matching robust mean & std to base_10_3_fp
    in_lid = base_10_3_fp.copy()
    raw_in = 0.55 * base_10_3_fp[lid_valid_fp] + 0.45 * (lid_w_fp[lid_valid_fp] * pied_hab[foot][lid_valid_fp])
    mu_ref = float(np.mean(base_10_3_fp[~lid_valid_fp]))
    sd_ref = float(np.std(base_10_3_fp[~lid_valid_fp])) + 1e-6
    mu_in = float(np.mean(raw_in))
    sd_in = float(np.std(raw_in)) + 1e-6
    in_lid[lid_valid_fp] = np.clip((raw_in - mu_in) * (sd_ref / sd_in) + mu_ref, 0.0, 1.0)
    q_ms = float(np.percentile(in_lid, 99.5)) + 1e-6
    X_darp[:, 13] = np.clip(in_lid / q_ms, 0.0, 1.0).astype(np.float32)
    del scarp10_clean, dem10_hgm_clean, dem10_worm, scarp3m_2d, lid_w_fp, base_10_3_fp, in_lid, raw_in
    X_darp.flush()
    gc.collect()

    # --- GROUP D: Regional Stress (S_hmin, A_phi) Dilation Tendency & Shallow ComCat (cols 14..17) ---
    # Dominant local fault strike: use 10m scarp strike where strong, else updip gravity/RTP strike
    ms_2d = np.zeros(shape, dtype=np.float32)
    ms_2d[foot] = X_darp[:, 13]
    strike_dom = np.where(ms_2d >= 0.18, strike_s10, np.where(grav_updip >= 0.18, strike_g, strike_m)).astype(np.float32)
    del strike_g, strike_m, strike_s10

    stress_csv = ddir / "external" / "gb_regional_stress_grid_10km.csv"
    if stress_csv.exists():
        sdf = pd.read_csv(stress_csv)
        r_centers = np.sort(sdf["center_row"].unique().astype(np.float64))
        c_centers = np.sort(sdf["center_col"].unique().astype(np.float64))
        nr, nc = r_centers.size, c_centers.size
        # Circular interpolation of 2 * shmin_az_deg (180-deg axial symmetry)
        rad2 = np.deg2rad(2.0 * sdf["shmin_az_deg"].to_numpy(dtype=np.float64))
        cos_grid = np.zeros((nr, nc), dtype=np.float64)
        sin_grid = np.zeros((nr, nc), dtype=np.float64)
        aphi_grid = np.full((nr, nc), 0.65, dtype=np.float64)
        r_map = {v: i for i, v in enumerate(r_centers)}
        c_map = {v: j for j, v in enumerate(c_centers)}
        for row_s, c2, s2 in zip(sdf.itertuples(index=False), np.cos(rad2), np.sin(rad2)):
            ri, ci = r_map[float(row_s.center_row)], c_map[float(row_s.center_col)]
            cos_grid[ri, ci] = c2
            sin_grid[ri, ci] = s2
            aphi_grid[ri, ci] = float(row_s.aphi)
        del sdf, rad2

        fy, fx = np.nonzero(foot)
        pts_q = np.column_stack([
            np.clip(fy.astype(np.float64), r_centers[0], r_centers[-1]),
            np.clip(fx.astype(np.float64), c_centers[0], c_centers[-1]),
        ])
        ic = RegularGridInterpolator((r_centers, c_centers), cos_grid, method="linear")(pts_q)
        is_ = RegularGridInterpolator((r_centers, c_centers), sin_grid, method="linear")(pts_q)
        aphi_fp = RegularGridInterpolator((r_centers, c_centers), aphi_grid, method="linear")(pts_q).astype(np.float32)
        del pts_q, fy, fx, cos_grid, sin_grid, aphi_grid

        # Convert compass azimuth (deg clockwise from North) to image row/col strike angle
        # In EPSG:32611 (x=East, y=North -> row=-North, col=+East), compass az alpha has (dy=-cos a, dx=sin a)
        shmin_az_rad = 0.5 * np.arctan2(is_, ic).astype(np.float32)
        opt_norm_strike = np.arctan2(-np.cos(shmin_az_rad + np.pi / 2.0), np.sin(shmin_az_rad + np.pi / 2.0)).astype(np.float32)
        del ic, is_, shmin_az_rad

        st_fp = strike_dom[foot]
        d_ang = np.abs(np.arctan2(np.sin(st_fp - opt_norm_strike), np.cos(st_fp - opt_norm_strike)))
        w_ss = np.clip((aphi_fp - 0.65) / 0.85, 0.0, 1.0)
        td_norm = np.cos(d_ang) ** 2
        td_ss = np.cos(d_ang - np.deg2rad(28.0)) ** 2
        # Gate by structural/scarp presence so random noise azimuths on featureless flats do not fire
        struct_env_fp = np.clip(np.maximum.reduce([ms_2d[foot], grav_updip[foot], updip_conv[foot], mt_baffle[foot]]) * 2.2, 0.05, 1.0)
        td_fp = ((1.0 - w_ss) * td_norm + w_ss * td_ss) * struct_env_fp
        X_darp[:, 14] = np.clip(td_fp, 0.0, 1.0).astype(np.float32)
        del st_fp, opt_norm_strike, d_ang, w_ss, td_norm, td_ss, struct_env_fp, aphi_fp
    else:
        X_darp[:, 14] = 0.5
    del strike_dom

    # Shallow (<= 12 km) USGS ANSS ComCat microseismicity kernel density
    seis_seeds = np.zeros(shape, dtype=np.float32)
    comcat_csv = ddir / "external" / "usgs_comcat_geodawn.csv"
    if comcat_csv.exists():
        cdf = pd.read_csv(comcat_csv)
        for row_c in cdf.itertuples(index=False):
            r, c = int(row_c.row_100m), int(row_c.col_100m)
            dep = float(row_c.depth_km) if pd.notna(row_c.depth_km) else 8.0
            mag = float(row_c.magnitude) if pd.notna(row_c.magnitude) else 2.0
            if 0 <= r < H and 0 <= c < W and dep <= 14.0:
                w_eq = (1.0 if dep <= 10.0 else 0.65) * (1.0 + 0.55 * max(mag - 1.5, 0.0))
                seis_seeds[r, c] += float(min(w_eq, 4.0))
        del cdf
    seis_2d = htcads._pos_norm_2d(
        0.60 * gaussian_filter(seis_seeds, sigma=6.0, mode="nearest")
        + 0.40 * gaussian_filter(seis_seeds, sigma=14.0, mode="nearest"),
        foot,
        q=99.3,
    )
    del seis_seeds
    X_darp[:, 15] = seis_2d[foot]

    seis_ridge_fp = X_darp[:, 14] * (0.55 * seis_2d[foot] + 0.45 * np.maximum(grav_updip[foot], ms_2d[foot]))
    q_sr = float(np.percentile(seis_ridge_fp, 99.5)) + 1e-6
    X_darp[:, 16] = np.clip(seis_ridge_fp / q_sr, 0.0, 1.0).astype(np.float32)
    del seis_2d, seis_ridge_fp

    # Label-free blind geothermal + updip basement + piedmont habitat synthesis
    blind_synth_fp = (
        (0.32 * grav_updip[foot] + 0.20 * grav_tilt_k[foot] + 0.18 * updip_conv[foot] + 0.30 * mt_baffle[foot])
        * (0.55 + 0.45 * pied_hab[foot])
        * (1.0 + 0.30 * hf_comb_fp + 0.25 * X_darp[:, 14])
    )
    q_bs = float(np.percentile(blind_synth_fp, 99.5)) + 1e-6
    X_darp[:, 17] = np.clip(blind_synth_fp / q_bs, 0.0, 1.0).astype(np.float32)
    del grav_updip, grav_tilt_k, updip_conv, mt_baffle, pied_hab, hf_comb_fp, ms_2d, blind_synth_fp

    X_darp.flush()
    meta = {
        "schema_version": "darp_mt10_v1",
        "n_fp": n_fp,
        "darp_features": DARP_FEATURE_NAMES,
    }
    meta_path.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    X_darp_ro = np.memmap(darp_mmap_path, dtype="float32", mode="r", shape=(n_fp, len(DARP_FEATURE_NAMES)))
    gc.collect()
    return {
        "foot": foot,
        "X_sub": base_stack["X_sub"],
        "X_lid": base_stack["X_lid"],
        "lidar_valid_fp": base_stack["lidar_valid_fp"],
        "X_darp": X_darp_ro,
    }


def run_full_darp_leakage_canary(darp_stack: dict, ctx: holdout.HoldoutContext, seed: int = 20261027) -> dict:
    """Protocol Rule 4: Single-feature holdout AUC <= 0.90 across ALL 68 channels (36 sub + 10 lid + 18 darp + 4 vis)."""
    base_res = htcads.run_leakage_canary(darp_stack, ctx, sample_cap=240_000, seed=seed)
    foot = darp_stack["foot"]
    X_darp = darp_stack["X_darp"]

    fp_idx_2d = np.full(foot.shape, -1, dtype=np.int32)
    fp_idx_2d[foot] = np.arange(int(foot.sum()), dtype=np.int32)
    rng = np.random.default_rng(seed)

    pos_fp_list, neg_fp_list = [], []
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
        if n_fp.size > 60_000:
            n_fp = rng.choice(n_fp, size=60_000, replace=False)
        pos_fp_list.append(p_fp)
        neg_fp_list.append(n_fp)

    pos_idx = np.concatenate(pos_fp_list)
    neg_idx = np.concatenate(neg_fp_list)
    y_eval = np.concatenate([np.ones(pos_idx.size, dtype=np.int8), np.zeros(neg_idx.size, dtype=np.int8)])
    all_idx = np.concatenate([pos_idx, neg_idx])

    features = list(base_res["features"])
    for j, name in enumerate(DARP_FEATURE_NAMES):
        vals = np.asarray(X_darp[all_idx, j], dtype=np.float32)
        assert np.isfinite(vals).all(), f"Non-finite values in DARP feature {name}"
        auc = float(roc_auc_score(y_eval, vals))
        sym_auc = max(auc, 1.0 - auc)
        features.append({
            "feature": name,
            "group": "darp_mt10_new",
            "raw_auc": round(auc, 6),
            "oriented_auc": round(sym_auc, 6),
        })

    features.sort(key=lambda r: r["oriented_auc"], reverse=True)
    max_auc = float(features[0]["oriented_auc"])
    return {
        "protocol_rule": "Rule 4 Leakage Canary (single-feature holdout AUC <= 0.90)",
        "evaluator": "GEMSDOE32-HIDE-RECOVER-v3.1 (draw20 spatially-blocked withheld segments)",
        "threshold": 0.90,
        "total_features_tested": len(features),
        "n_withheld_positive_pixels_tested": int(pos_idx.size),
        "n_negative_pixels_tested": int(neg_idx.size),
        "max_single_feature_auc": round(max_auc, 6),
        "max_feature_name": features[0]["feature"],
        "passed": bool(max_auc <= 0.90),
        "features": features,
    }


def prepare_c_pied_truth(ddir: Path, ctx: holdout.HoldoutContext) -> dict:
    """Prepare GEMSDOE70 Instrument C_pied (untouched off-catalogue piedmont/basin-margin SGMC faults)."""
    foot = ctx.foot
    cat = ctx.labels
    with rasterio.open(ddir / "external" / "derived_sgmc_faults_100m_u8.tif") as s:
        sgmc = foot & (s.read(1) > 0)
    with rasterio.open(ddir / "training_features.tif") as s:
        zb = s.read(15)
    rel10 = np.zeros(foot.shape, dtype=np.float32)
    rel10[foot] = np.load(ddir / "dem10" / "dem10_resid_range.f32.npy")
    slp10 = np.zeros(foot.shape, dtype=np.float32)
    slp10[foot] = np.load(ddir / "dem10" / "dem10_slope_max.f32.npy")

    d_cat = distance_transform_edt(~cat)
    p75_rel = float(np.percentile(rel10[cat], 75.0))
    p80_slp = float(np.percentile(slp10[cat], 80.0))
    c_pied = sgmc & (~cat) & (d_cat > 2.5) & (rel10 <= p75_rel) & (slp10 <= p80_slp) & np.isfinite(zb) & (zb >= 250.0)
    k_dg = kernel(distance_transform_edt(~c_pied))
    return {
        "truth": c_pied,
        "coords": np.nonzero(c_pied),
        "n_truth": int(c_pied.sum()),
        "k_dg": k_dg,
        "p75_rel_m": round(p75_rel, 4),
        "p80_slp_deg": round(p80_slp, 4),
    }


def evaluate_c_pied_with_ci(
    mask: np.ndarray,
    ctx: holdout.HoldoutContext,
    cp_ctx: dict,
    grid_n: int = 16,
    n_boot: int = 1000,
    seed: int = 20261027,
    name: str = "candidate",
) -> dict:
    """Evaluate pooled DTI + 256-block cluster bootstrap 95% CI on Instrument C_pied (N=9,847)."""
    h, w = ctx.foot.shape
    allow = ctx.foot & ~ctx.labels
    m_bool = (np.isfinite(mask) & (mask > 0)) & allow
    n_blocks = grid_n * grid_n
    tp_blk = np.zeros(n_blocks, dtype=np.float64)
    fp_blk = np.zeros(n_blocks, dtype=np.float64)
    fn_blk = np.zeros(n_blocks, dtype=np.float64)

    fy, fx = np.nonzero(ctx.foot)
    active_blocks = np.unique(holdout._spatial_block_index(fy, fx, (h, w), grid_n))
    ty, tx = cp_ctx["coords"]
    t_blk = holdout._spatial_block_index(ty, tx, (h, w), grid_n)

    if m_bool.any() and cp_ctx["n_truth"] > 0:
        dp = distance_transform_edt(~m_bool)
        t_cred = kernel(dp[cp_ctx["coords"]]).astype(np.float64)
        np.add.at(tp_blk, t_blk, t_cred)
        np.add.at(fn_blk, t_blk, 1.0 - t_cred)
        py, px = np.nonzero(m_bool)
        p_blk = holdout._spatial_block_index(py, px, (h, w), grid_n)
        fp_w = (1.0 - cp_ctx["k_dg"][m_bool]).astype(np.float64)
        np.add.at(fp_blk, p_blk, fp_w)
    else:
        np.add.at(fn_blk, t_blk, 1.0)

    pooled, ci95, boots = holdout._cluster_bootstrap_pooled_dti(
        tp_blk, fp_blk, fn_blk, active_blocks, n_boot=n_boot, seed=seed
    )
    return {
        "candidate_id": name,
        "evaluator_version": C_PIED_EVALUATOR_VERSION,
        "score_label": "HOLDOUT-DTI",
        "n_withheld_positives": int(cp_ctx["n_truth"]),
        "n_spatial_clusters": int(active_blocks.size),
        "n_bootstrap_reps": int(n_boot),
        "pooled_dti": pooled,
        "ci95_cluster_bootstrap": ci95,
        "_boots": boots,
    }


def emit_submodular_celf_with_trace(
    pi_2d: np.ndarray,
    eligible_2d: np.ndarray,
    max_dots: int = 44000,
    expected_total_truth: float = 12691.0,
    dinkelbach_stop: bool = False,
    min_dots: int = 28000,
    candidate_pool_size: int = 270_000,
) -> tuple[np.ndarray, dict]:
    """Exact 25-offset Euclidean 300 m Submodular Expected-DTI (`CELF`) allocator with optional Dinkelbach stop.

    Under expected Distance-Weighted Tversky (alpha=0.2, beta=0.8), adding k dots with cumulative expected
    weighted recall G(k) = sum_{i=1}^k g_i against total hidden truth K yields expected DTI:
        J(k) = G(k) / (ALPHA * k + BETA * K).
    By Dinkelbach's fractional-programming theorem, J(k) is maximized along the monotone concave gain curve
    at the unique k* where marginal expected recall g_k crosses ALPHA * J(k-1) = 0.2 * J(k-1).
    """
    import heapq
    from scipy.ndimage import convolve, maximum_filter
    from .metric import _OFFS

    H, W = pi_2d.shape
    pi_clean = np.where(np.isfinite(pi_2d) & (pi_2d > 0.0), pi_2d, 0.0).astype(np.float32)

    k_mat = np.zeros((7, 7), dtype=np.float32)
    for dy, dx, kw in _OFFS:
        k_mat[dy + 3, dx + 3] = float(kw)
    init_gain = convolve(pi_clean, k_mat, mode="constant", cval=0.0)
    init_gain = np.where(eligible_2d, init_gain, 0.0)

    local_peak = init_gain >= (maximum_filter(init_gain, size=3, mode="constant", cval=0.0) - 1e-12)
    cand_score = np.where(eligible_2d, init_gain * np.where(local_peak, 1.0, 0.92), 0.0)

    flat_cand = np.flatnonzero(cand_score.ravel() > 1e-9)
    if flat_cand.size == 0:
        return np.zeros((H, W), dtype=bool), {"n_emitted": 0, "cum_gain": 0.0}
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
    cum_gain = 0.0
    last_gain = 0.0

    # Calibrate total expected mass of pi_clean onto expected_total_truth so Dinkelbach J(k) is scale-consistent
    tot_pi = float(pi_clean[eligible_2d].sum())
    scale_k = expected_total_truth / max(tot_pi, 1.0) if dinkelbach_stop else 1.0

    while heap and n_sel < max_dots:
        neg_g, last_s, pidx, fidx = heapq.heappop(heap)
        g_up = -neg_g
        if dinkelbach_stop and n_sel >= min_dots:
            j_curr = (cum_gain * scale_k) / (ALPHA * n_sel + BETA * expected_total_truth + EPS)
            if (g_up * scale_k) < ALPHA * j_curr:
                break
        if last_s == step:
            selected[fidx] = True
            n_sel += 1
            step += 1
            cum_gain += g_up
            last_gain = g_up
            nbr = pidx + offs_pad
            cov_pad[nbr] = np.maximum(cov_pad[nbr], kws)
        else:
            nbr = pidx + offs_pad
            rem = kws - cov_pad[nbr]
            np.maximum(rem, 0.0, out=rem)
            new_g = float(np.dot(pi_pad[nbr], rem))
            if new_g > 1e-12:
                heapq.heappush(heap, (-new_g, step, pidx, fidx))

    return selected.reshape(H, W), {
        "n_emitted": int(n_sel),
        "cum_gain": round(float(cum_gain), 4),
        "last_marginal_gain": round(float(last_gain), 6),
        "dinkelbach_stop_used": bool(dinkelbach_stop),
    }
